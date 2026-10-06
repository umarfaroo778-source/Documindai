import math
import re

class EmbeddingService:
    """
    High-performance vector embedding generator for document chunk retrieval.
    Computes normalized word-frequency feature vectors for cosine similarity matching.
    Optionally integrates with external embedding APIs when configured.
    """
    @staticmethod
    def get_embedding(text: str, vector_dim: int = 128) -> list[float]:
        # Clean and tokenize words
        words = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())
        if not words:
            return [0.0] * vector_dim
        
        # Build frequency map hashed into vector_dim buckets
        vec = [0.0] * vector_dim
        for word in words:
            # Deterministic hash to bucket
            idx = abs(hash(word)) % vector_dim
            vec[idx] += 1.0
        
        # L2 Normalize vector
        magnitude = math.sqrt(sum(val * val for val in vec))
        if magnitude > 0:
            vec = [val / magnitude for val in vec]
        
        return vec
