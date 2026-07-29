import chromadb
from incidents import INCIDENTS

# Create a persistent Chroma database (saved to disk, not just in memory)
client = chromadb.PersistentClient(path="./chroma_db")

# Create (or get) a collection - think of this like a "table" for our incidents
collection = client.get_or_create_collection(name="incidents")

# Add each incident note to the collection
# Chroma automatically converts the text into embeddings behind the scenes
collection.add(
    documents=[inc["text"] for inc in INCIDENTS],
    ids=[inc["id"] for inc in INCIDENTS]
)

print(f"Added {len(INCIDENTS)} incidents to the vector store.")
print(f"Total items in collection: {collection.count()}")