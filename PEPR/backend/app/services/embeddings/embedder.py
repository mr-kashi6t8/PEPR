from typing import List, Optional
import logging
import hashlib
import numpy as np

logger = logging.getLogger("pepr.embedder")

class CentralizedEmbedder:
    """
    A centralized embedding service using lightweight local sentence transformer models.
    Uses lazy initialization and deterministic hash-vector fallback to ensure Qdrant
    and vector search operations never fail due to environment or library version conflicts.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", vector_size: int = 384):
        self.model_name = model_name
        self.vector_size = vector_size
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"SentenceTransformer model '{self.model_name}' loaded successfully")
            except Exception as e:
                logger.warning(
                    f"SentenceTransformer not loaded ({e}). "
                    f"Falling back to deterministic feature vector generator (dim={self.vector_size})."
                )
                self._model = False # Mark as failed to avoid re-attempting import

    def _deterministic_vector(self, text: str) -> List[float]:
        """Generates a normalized deterministic 384-dimensional float vector for text fallback."""
        if not text:
            return [0.0] * self.vector_size
        # Create seed from SHA256 of input text
        hash_digest = hashlib.sha256(text.encode('utf-8')).digest()
        seed = int.from_bytes(hash_digest[:4], 'big')
        rng = np.random.RandomState(seed)
        vec = rng.randn(self.vector_size).astype(float)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_text(self, text: str) -> List[float]:
        """Returns the vector embedding for a single text string."""
        self._load_model()
        if self._model and self._model is not False:
            try:
                return self._model.encode(text).tolist()
            except Exception:
                pass
        return self._deterministic_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Returns vector embeddings for a list of text strings."""
        return [self.embed_text(t) for t in texts]

# Singleton instance
embedder = CentralizedEmbedder()
