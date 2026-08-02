import os
from qdrant_client import AsyncQdrantClient
from app.core.config import settings
from app.infrastructure.qdrant import QdrantConnection

def get_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(url=settings.QDRANT_URL)

async def check_qdrant_health() -> dict:
    """
    Checks Qdrant health. Tries async HTTP client first; if unreachable, 
    falls back to persistent local disk vector storage (qdrant_db).
    """
    try:
        client = get_qdrant_client()
        collections = await client.get_collections()
        return {
            "status": "ok",
            "mode": "remote",
            "collections": len(collections.collections),
        }
    except Exception as http_err:
        try:
            sync_client = QdrantConnection.get_client()
            collections = sync_client.get_collections()
            return {
                "status": "ok",
                "mode": "local_disk",
                "collections": len(collections.collections),
            }
        except Exception as local_err:
            raise RuntimeError(f"Qdrant connection failed (HTTP: {http_err}, Local: {local_err})")

