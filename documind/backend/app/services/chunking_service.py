import re
from typing import List, Dict, Any

class ChunkingService:
    @staticmethod
    def chunk_pages(pages: List[Dict[str, Any]], chunk_size: int = 600, overlap: int = 100) -> List[Dict[str, Any]]:
        """
        Splits extracted pages into overlapping text chunks with associated page_number and chunk_index.
        """
        chunks = []
        global_chunk_index = 0

        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"]

            if not page_text.strip():
                continue

            # Split into sentence-based units if possible
            sentences = re.split(r'(?<=[.!?])\s+', page_text)
            current_chunk = []
            current_len = 0

            for sentence in sentences:
                sentence_len = len(sentence)
                if current_len + sentence_len > chunk_size and current_chunk:
                    chunk_str = " ".join(current_chunk).strip()
                    if chunk_str:
                        chunks.append({
                            "chunk_text": chunk_str,
                            "page_number": page_num,
                            "chunk_index": global_chunk_index
                        })
                        global_chunk_index += 1

                    # Overlap: keep last few sentences that fit within overlap budget
                    overlap_chunk = []
                    overlap_len = 0
                    for s in reversed(current_chunk):
                        if overlap_len + len(s) <= overlap:
                            overlap_chunk.insert(0, s)
                            overlap_len += len(s)
                        else:
                            break
                    current_chunk = overlap_chunk
                    current_len = overlap_len

                current_chunk.append(sentence)
                current_len += sentence_len

            if current_chunk:
                chunk_str = " ".join(current_chunk).strip()
                if chunk_str:
                    chunks.append({
                        "chunk_text": chunk_str,
                        "page_number": page_num,
                        "chunk_index": global_chunk_index
                    })
                    global_chunk_index += 1

        return chunks
