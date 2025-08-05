# api/debug.py
from fastapi import APIRouter
from qdrant_client import QdrantClient

router = APIRouter()

QDRANT_URL = "http://localhost:6333"
COLLECTION = "docs"

@router.get("/api/debug_qdrant")
def debug_qdrant(limit: int = 10):
    client = QdrantClient(url=QDRANT_URL)
    results = client.scroll(collection_name=COLLECTION, limit=limit)
    return {"count": len(results[0]), "payloads": [p.payload for p in results[0]]}



