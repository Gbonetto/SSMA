# scripts/ingest.py
import sys
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_community.vectorstores import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Configuration Qdrant – vous pouvez aussi importer core.config.settings
QDRANT_URL = "http://localhost:6333"
COLLECTION = "docs"
EMBEDDING_SIZE = 384

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

def ingest_text(text: str, metadata: dict = {}):
    # Split & vectorise
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_text(text)
    docs = [
        Document(page_content=chunk, metadata={**metadata, "chunk_id": idx})
        for idx, chunk in enumerate(chunks)
    ]

    # (Re)création manuelle de la collection
    client = QdrantClient(url=QDRANT_URL)
    # Supprime si existe
    existing = [col.name for col in client.get_collections().collections]
    if COLLECTION in existing:
        client.delete_collection(collection_name=COLLECTION)
    # Crée à  nouveau
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE)
    )

    # Ajouter les docs
    vectorstore = Qdrant(client=client, collection_name=COLLECTION, embeddings=get_embeddings())
    vectorstore.add_documents(docs)
    print(f"Ingested {len(docs)} chunks into '{COLLECTION}'.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ingest.py path/to/file.txt")
        sys.exit(1)
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        sys.exit(1)

    ingest_text(raw, {"source": path})



