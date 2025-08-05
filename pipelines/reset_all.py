import os
import shutil
from qdrant_client import QdrantClient

# === 1. RESET QDRANT ===
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "docs"

client = QdrantClient(QDRANT_URL)
try:
    client.delete_collection(collection_name=QDRANT_COLLECTION)
    print(f"✅ Collection Qdrant '{QDRANT_COLLECTION}' supprimée !")
except Exception as e:
    print(f"⚠ Impossible de supprimer la collection Qdrant : {e}")

# === 2. RESET WHOOSH ===
WHOOSH_INDEX_DIR = os.path.join(os.path.dirname(__file__), "../whoosh_index")
whoosh_dir = os.path.abspath(WHOOSH_INDEX_DIR)

if os.path.isdir(whoosh_dir):
    try:
        shutil.rmtree(whoosh_dir)
        print(f"✅ Dossier Whoosh index '{whoosh_dir}' supprimé !")
    except Exception as e:
        print(f"⚠ Impossible de supprimer l'index Whoosh : {e}")
else:
    print(f"ℹ Dossier Whoosh index '{whoosh_dir}' inexistant (déjà clean)")

print("\n🎯 RESET ALL terminé. Tu peux relancer tes imports !")



