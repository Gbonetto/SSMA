import logging
from core.logging import get_logger
from qdrant_client import QdrantClient

logger = get_logger(__name__)

client = QdrantClient("http://localhost:6333")
client.delete_collection(collection_name="docs")
logger.info("✅ Collection Qdrant 'docs' supprimée !")
