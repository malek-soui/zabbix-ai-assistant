import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="incidents")

query = "CPU usage is very high on HV-HOST-01"

results = collection.query(
    query_texts=[query],
    n_results=3
)

print(f"Query: {query}\n")
print("Top 3 similar past incidents:")
for i, doc in enumerate(results["documents"][0]):
    print(f"{i+1}. {doc}")