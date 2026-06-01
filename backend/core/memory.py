import chromadb
from chromadb.config import Settings
from datetime import datetime
import uuid

class VectorMemory:
    def __init__(self, persist_dir="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection("effiong_heritage_memory")

    def add(self, text: str, metadata: dict = None):
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {"timestamp": datetime.now().isoformat()}],
            ids=[str(uuid.uuid4())]
        )

    def query(self, query_text: str, n_results: int = 5):
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results.get('documents', [[]])[0]
