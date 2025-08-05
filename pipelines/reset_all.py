import os
import shutil
from qdrant_client import QdrantClient

# === 1. RESET QDRANT ===
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "docs"

client = QdrantClient(QDRANT_URL)
try:
    client.delete_collection(collection_name=QDRANT_COLLECTION)
    print(f"âœ… Collection Qdrant '{QDRANT_COLLECTION}' supprimÃ©e !")
except Exception as e:
    print(f"âš ï¸ Impossible de supprimer la collection QdrantÂ : {e}")

# === 2. RESET WHOOSH ===
WHOOSH_INDEX_DIR = os.path.join(os.path.dirname(__file__), "../whoosh_index")
whoosh_dir = os.path.abspath(WHOOSH_INDEX_DIR)

if os.path.isdir(whoosh_dir):
    try:
        shutil.rmtree(whoosh_dir)
        print(f"âœ… Dossier Whoosh index '{whoosh_dir}' supprimÃ© !")
    except Exception as e:
        print(f"âš ï¸ Impossible de supprimer l'index WhooshÂ : {e}")
else:
    print(f"â„¹ï¸ Dossier Whoosh index '{whoosh_dir}' inexistant (dÃ©jÃ  clean)")

print("\nðŸŽ¯ RESET ALL terminÃ©. Tu peux relancer tes imports !")



