import logging
from core.logging import get_logger
from qdrant_client import QdrantClient

logger = get_logger(__name__)

QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "docs"

client = QdrantClient(QDRANT_URL)
res = client.scroll(collection_name=QDRANT_COLLECTION, limit=5)
for doc in res[0]:
    logger.info("---")
    logger.info(doc.payload.get("page_content", "NO CONTENT"))
    logger.info(doc.payload)



