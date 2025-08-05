# pipelines/rag_chain.py

import logging
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant  # Remplace l'ancien import deprecated
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAI  # Remplace l'ancien import deprecated
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from core.config import settings

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def detect_intention(question: str) -> str:
    q = question.lower()
    if "tout le texte" in q or "texte complet" in q or "copie intÃ©grale" in q:
        return "copie"
    if "rÃ©sum" in q or "synthÃ¨se" in q:
        return "synthese"
    if "montant" in q or "combien" in q:
        return "combien"
    if "quand" in q or "date" in q:
        return "quand"
    # ... ajoute d'autres rÃ¨gles ici au besoin
    return "par_defaut"

def get_prompt_for_intention(intention: str) -> PromptTemplate:
    templates = {
        "copie": """
Tu dois simplement recopier le texte du document entre <DOCUMENTS> et </DOCUMENTS> ci-dessous, sans rien omettre. Ne reformule rien, ne change pas l'ordre, ne saute rien. Si le texte est trop long, copie tout ce qui est affichÃ©.
<DOCUMENTS>
{context}
</DOCUMENTS>
Recopie intÃ©graleÂ :
""",
        "synthese": """
Tu es un expert en analyse documentaire.
<DOCUMENTS>
{context}
</DOCUMENTS>
Question : {question}
RÃ©ponse :
""",
        "combien": """
Tu es un assistant financier.
<DOCUMENTS>
{context}
</DOCUMENTS>
Question : {question}
RÃ©ponse :
""",
        "quand": """
Tu es un assistant temporel.
<DOCUMENTS>
{context}
</DOCUMENTS>
Question : {question}
RÃ©ponse :
""",
        # Prompt par dÃ©faut renforcÃ©
        "par_defaut": """
Tu es un assistant juridique. Tu dois toujours rÃ©pondre, mÃªme si l'information n'est pas complÃ¨te.
Si tu ne trouves pas la rÃ©ponse exacte, produis la meilleure synthÃ¨se possible Ã  partir du contexte ci-dessous. Ne rÃ©ponds jamais "je ne sais pas" ni "dÃ©solÃ©".

<DOCUMENTS>
{context}
</DOCUMENTS>
Question : {question}
RÃ©ponse :
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
    # Selon ta version de langchain-core, tu peux utiliser invoke() (synchrone) ou ainvoke() (async)
    retrieved_docs = retriever.invoke(question)

    print("\n=== Chunks retrouvÃ©s pour la question:", question)
    if not retrieved_docs:
        print("!!! Aucun chunk retrouvÃ©")
    for doc in retrieved_docs:
        print("---", doc.page_content[:200])

    if not settings.OPENAI_API_KEY:
        return {"answer": "", "sources": [], "entities": {}, "error": "OPENAI_API_KEY non configurÃ©e"}

    # --- chaÃ®ne RAG ---
    intention = detect_intention(question)
    prompt = get_prompt_for_intention(intention)

    # Affiche le prompt rÃ©el (simulateur "ce que voit le LLM")
    ctx_concat = "\n".join([d.page_content for d in retrieved_docs])
    print("\n=== PROMPT FINAL ENVOYÃ‰ AU LLM ===")
    print(prompt.format(context=ctx_concat, question=question))

    llm = OpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    result = qa({"query": question})

    print("\n=== RAW RESULT DE LLM ===")
    print(result)

    # SÃ©curitÃ©Â : vÃ©rifie la prÃ©sence de "result" (peut varier selon version)
    answer = result.get("result", "")
    docs = result.get("source_documents", [])

    # DEBUGÂ : affiche le contexte passÃ© effectivement au LLM (source_documents)
    print("\n=== CONTEXT EFFECTIVEMENT PASSE AU LLM ===")
    for d in docs:
        print(d.page_content[:400])

    # --- format de sortie basique ---
    sources = [{"text": d.page_content, "metadata": d.metadata} for d in docs]
    logging.info(f"RAG >> question={question} answer={answer[:60]}...")
    return {"answer": answer, "sources": sources, "entities": {}}



