import sys
import os
import logging
from core.logging import get_logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, open_dir, exists_in
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from core.config import settings

logger = get_logger(__name__)

INDEX_DIR = os.path.join(os.path.dirname(__file__), "../whoosh_index")

def build_schema():
    return Schema(id=ID(stored=True, unique=True), content=TEXT(stored=True))

def get_all_docs_from_qdrant():
    # Utilise Qdrant pour rÃ©cupÃ©rer tous les passages dÃ©jÃ  vectorisÃ©s
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    client = QdrantClient(url=settings.QDRANT_URL)
    vectorstore = Qdrant(
        client=client,
        collection_name=settings.QDRANT_COLLECTION,
        embeddings=embeddings,
    )
    # RÃ©cupÃ©rer tout (attention Ã  la volumÃ©trie)
    docs = vectorstore.similarity_search(" ", k=10000)  # " " = match all (pas optimal mais fait le job)
    return docs

def build_index():
    os.makedirs(INDEX_DIR, exist_ok=True)
    if exists_in(INDEX_DIR):
        ix = open_dir(INDEX_DIR)
    else:
        schema = build_schema()
        ix = create_in(INDEX_DIR, schema)

    writer = ix.writer()
    docs = get_all_docs_from_qdrant()
    logger.info("Indexation Whoosh de %d passages...", len(docs))
    for idx, doc in enumerate(docs):
        writer.add_document(id=str(idx), content=doc.page_content)
    writer.commit()
    logger.info("✅ Index Whoosh créé/mis à jour.")

if __name__ == "__main__":
    build_index()



