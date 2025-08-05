# pipelines/hybrid_retrieval.py
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
import os

from core.config import settings
from pipelines.rerank import BGEReranker

# Initialise le reranker global (une seule instance)
reranker = BGEReranker()

def semantic_search(query: str, top_k=10):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    client = QdrantClient(url=settings.QDRANT_URL)
    vectorstore = Qdrant(
        client=client,
        collection_name=settings.QDRANT_COLLECTION,
        embeddings=embeddings,
    )
    docs_and_scores = vectorstore.similarity_search_with_score(query, k=top_k)
    return [
        {
            "text": doc.page_content,
            "metadata": doc.metadata,
            "score": float(score),
            "source": "semantic"
        }
        for doc, score in docs_and_scores
    ]

def keyword_search(query: str, top_k=10):
    ix_path = os.path.join(os.path.dirname(__file__), "../whoosh_index")
    if not os.path.exists(ix_path):
        return []
    ix = open_dir(ix_path)
    results = []
    with ix.searcher() as searcher:
        parser = QueryParser("content", ix.schema)
        myquery = parser.parse(query)
        hits = searcher.search(myquery, limit=top_k)
        for hit in hits:
            results.append({
                "text": hit["content"],
                "metadata": {"whoosh_id": hit.get("id")},
                "score": hit.score,
                "source": "keyword"
            })
    return results

def hybrid_search(query: str, top_k=7):
    # 1. On rÃ©cupÃ¨re plus large pour un vrai reranking (x2 top_k)
    semantic_results = semantic_search(query, top_k=top_k*2)
    keyword_results = keyword_search(query, top_k=top_k*2)

    # 2. Fusion & dÃ©duplication (on conserve le maximum de diversitÃ©)
    all_results = semantic_results + keyword_results
    seen = set()
    unique_results = []
    for r in all_results:
        key = r["text"][:120].strip().lower()
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    # 3. Rerank avec BGE
    reranked = reranker.rerank(query, unique_results, top_k=top_k)
    return reranked



