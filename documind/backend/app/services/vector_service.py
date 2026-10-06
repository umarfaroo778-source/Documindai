import json
import math
import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.models import DocumentChunk
from app.services.embedding_service import EmbeddingService

class VectorService:
    @staticmethod
    def search_similar_chunks(db: Session, document_id: int, query: str, top_k: int = 4) -> List[Tuple[DocumentChunk, float]]:
        """
        Retrieves the top_k most semantically relevant document chunks for a query.
        Returns a list of tuples: (DocumentChunk, similarity_score).
        """
        query_vec = EmbeddingService.get_embedding(query)
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()

        if not chunks:
            return []

        scored_chunks = []
        for chunk in chunks:
            if not chunk.embedding_reference:
                # Compute on the fly if missing
                chunk_vec = EmbeddingService.get_embedding(chunk.chunk_text)
            else:
                try:
                    chunk_vec = json.loads(chunk.embedding_reference)
                except Exception:
                    chunk_vec = EmbeddingService.get_embedding(chunk.chunk_text)

            score = VectorService._cosine_similarity(query_vec, chunk_vec)
            
            # Also boost score if query terms explicitly match in chunk text (hybrid BM25/keyword boost)
            query_words = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', query.lower()))
            chunk_words = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', chunk.chunk_text.lower()))
            overlap = len(query_words.intersection(chunk_words))
            keyword_boost = 0.15 * (overlap / max(1, len(query_words)))
            
            final_score = min(1.0, score + keyword_boost)
            scored_chunks.append((chunk, final_score))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot_product / (norm1 * norm2)
