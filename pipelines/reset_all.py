import os
import shutil
from core.logging import get_logger
from qdrant_client import QdrantClient

logger = get_logger(__name__)

# === 1. RESET QDRANT ===
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "docs"

client = QdrantClient(QDRANT_URL)
try:
    client.delete_collection(collection_name=QDRANT_COLLECTION)
    logger.info("✅ Collection Qdrant '%s' supprimée !", QDRANT_COLLECTION)
except Exception as e:
    logger.error("⚠️ Impossible de supprimer la collection Qdrant : %s", e)

# === 2. RESET WHOOSH ===
WHOOSH_INDEX_DIR = os.path.join(os.path.dirname(__file__), "../whoosh_index")
whoosh_dir = os.path.abspath(WHOOSH_INDEX_DIR)

if os.path.isdir(whoosh_dir):
    try:
        shutil.rmtree(whoosh_dir)
        logger.info("✅ Dossier Whoosh index '%s' supprimé !", whoosh_dir)
    except Exception as e:
        logger.error("⚠️ Impossible de supprimer l'index Whoosh : %s", e)
else:
    logger.info("ℹ️ Dossier Whoosh index '%s' inexistant (déjà clean)", whoosh_dir)

logger.info("🎯 RESET ALL terminé. Tu peux relancer tes imports !")
