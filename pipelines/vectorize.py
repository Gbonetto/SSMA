# pipelines/vectorize.py

import os
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant as QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# --- CONFIG ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = "docs"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_SIZE = 384

# --- UTILS ---
def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

def ensure_qdrant_collection(client, collection_name=QDRANT_COLLECTION, embedding_size=EMBEDDING_SIZE):
    try:
        exists = any(col.name == collection_name for col in client.get_collections().collections)
        if not exists:
            logging.info(f"CrÃ©ation de la collection Qdrant '{collection_name}' (size={embedding_size})")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE)
            )
    except Exception as e:
        logging.error(f"Erreur Qdrant collection : {e}")
        raise

def store_text_in_qdrant(text: str, metadata: dict = {}) -> int:
    """
    DÃ©coupe le texte, embed chaque chunk, indexe dans Qdrant avec metadata.
    Retourne le nombre de chunks ajoutÃ©s.
    """
    if not text or not text.strip():
        raise ValueError("Texte vide, rien Ã  indexer.")
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_text(text)
    if not chunks:
        raise ValueError("DÃ©coupage impossible ou texte trop court.")
    
    # Ajoute l'index de chunk Ã  chaque meta
    docs = []
    for idx, chunk in enumerate(chunks):
        meta_chunk = metadata.copy()
        meta_chunk["chunk_index"] = idx
        docs.append({"page_content": chunk, "metadata": meta_chunk})
    
    # Conversion pour LangChain
    from langchain.schema import Document
    langchain_docs = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in docs]
    
    # Embeddings & Qdrant
    embeddings = get_embeddings()
    client = QdrantClient(QDRANT_URL)
    ensure_qdrant_collection(client)
    try:
        vectorstore = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION,
            embeddings=embeddings,
        )
        vectorstore.add_documents(langchain_docs)
        logging.info(f"{len(langchain_docs)} chunks ajoutÃ©s Ã  la collection '{QDRANT_COLLECTION}'.")
        return len(langchain_docs)
    except Exception as e:
        logging.error(f"Erreur ajout dans Qdrant : {e}")
        raise



