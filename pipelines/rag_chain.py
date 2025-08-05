import logging
from core.logging import get_logger
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from core.config import settings

logger = get_logger(__name__)

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def detect_intention(question: str) -> str:
    q = question.lower()
    if "tout le texte" in q or "texte complet" in q or "copie intégrale" in q:
        return "copie"
    if "résum" in q or "synthèse" in q:
        return "synthese"
    if "montant" in q or "combien" in q:
        return "combien"
    if "quand" in q or "date" in q:
        return "quand"
    # ... ajoute d'autres règles ici au besoin
    return "par_defaut"

def get_prompt_for_intention(intention: str) -> PromptTemplate:
    templates = {
        "copie": """
Tu dois simplement recopier le texte du document entre <DOCUMENTS> et </DOCUMENTS> ci-dessous, sans rien omettre. Ne reformule rien, ne change pas l'ordre, ne saute rien. Si le texte est trop long, copie tout ce qui est affiché.
<DOCUMENTS>
{context}
</DOCUMENTS>
Recopie intégrale :
""",
        "synthese": """
Tu es un expert en analyse documentaire.
<DOCUMENTS>
{context}
</DOCUMENTS>
Question : {question}
Réponse :
""",
        "combien": """
Tu es un assistant financier.
<DOCUMENTS>
{context}
</DOCUMENTS>
Question : {question}
Réponse :
""",
        "quand": """
Tu es un assistant temporel.
<DOCUMENTS>
{context}
</DOCUMENTS>
Question : {question}
Réponse :
""",
        "par_defaut": """
Tu es un assistant juridique. Tu dois toujours répondre, même si l'information n'est pas complète.
Si tu ne trouves pas la réponse exacte, produis la meilleure synthèse possible à partir du contexte ci-dessous. Ne réponds jamais "je ne sais pas" ni "désolé".

<DOCUMENTS>
{context}
</DOCUMENTS>
Question : {question}
Réponse :
"""
    }
    tpl = templates.get(intention, templates["par_defaut"])
    return PromptTemplate(input_variables=["context", "question"], template=tpl)

def answer_with_rag(question: str, top_k: int = 8, user: str = None) -> dict:
    # --- installation du vector store Qdrant ---
    embeddings = get_embeddings()
    client = QdrantClient(url=settings.QDRANT_URL)
    vectorstore = Qdrant(
        client=client,
        collection_name=settings.QDRANT_COLLECTION,
        embeddings=embeddings,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    retrieved_docs = retriever.invoke(question)

    logger.debug("=== Chunks retrouvés pour la question: %s", question)
    if not retrieved_docs:
        logger.debug("!!! Aucun chunk retrouvé")
    for doc in retrieved_docs:
        logger.debug("--- %s", doc.page_content[:200])

    if not settings.OPENAI_API_KEY:
        return {"answer": "", "sources": [], "entities": {}, "error": "OPENAI_API_KEY non configurée"}

    # --- chaîne RAG ---
    intention = detect_intention(question)
    prompt = get_prompt_for_intention(intention)

    ctx_concat = "\n".join([d.page_content for d in retrieved_docs])
    logger.debug("=== PROMPT FINAL ENVOYÉ AU LLM ===")
    logger.debug(prompt.format(context=ctx_concat, question=question))

    llm = OpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    result = qa({"query": question})

    logger.debug("=== RAW RESULT DE LLM ===")
    logger.debug(result)

    answer = result.get("result", "")
    docs = result.get("source_documents", [])

    logger.debug("=== CONTEXT EFFECTIVEMENT PASSE AU LLM ===")
    for d in docs:
        logger.debug(d.page_content[:400])

    sources = [{"text": d.page_content, "metadata": d.metadata} for d in docs]
    logger.info("RAG >> question=%s answer=%s...", question, answer[:60])
    return {"answer": answer, "sources": sources, "entities": {}}
