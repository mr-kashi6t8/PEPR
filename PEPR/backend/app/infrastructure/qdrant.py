import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from app.core.config import settings

class QdrantConnection:
    _client = None

    @classmethod
    def get_client(cls) -> QdrantClient:
        if cls._client is None:
            storage_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "qdrant_db"))
            os.makedirs(storage_path, exist_ok=True)
            
            qdrant_host = getattr(settings, 'QDRANT_HOST', None)
            qdrant_key = getattr(settings, 'QDRANT_API_KEY', None)
            
            try:
                if qdrant_host and "localhost" not in qdrant_host and "127.0.0.1" not in qdrant_host:
                    cls._client = QdrantClient(url=qdrant_host, api_key=qdrant_key)
                else:
                    cls._client = QdrantClient(path=storage_path)
            except Exception as e:
                print(f"Connecting to persistent local Qdrant disk storage at {storage_path}. Details: {e}")
                cls._client = QdrantClient(path=storage_path)
            
            # Ensure the collection exists
            cls.init_collection("research_documents")
            
        return cls._client
        
    @classmethod
    def init_collection(cls, collection_name: str, vector_size: int = 384):
        """Initializes the collection if it doesn't exist."""
        client = cls.get_client()
        try:
            client.get_collection(collection_name)
        except Exception:
            try:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
            except Exception:
                pass
