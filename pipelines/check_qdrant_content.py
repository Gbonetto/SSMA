from qdrant_client import QdrantClient

QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "docs"

client = QdrantClient(QDRANT_URL)
res = client.scroll(collection_name=QDRANT_COLLECTION, limit=5)
for doc in res[0]:
    print("---")
    print(doc.payload.get("page_content", "NO CONTENT"))
    print(doc.payload)



