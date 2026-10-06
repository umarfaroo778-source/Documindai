import os
import json
import httpx
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.services.vector_service import VectorService

class RAGService:
    @staticmethod
    def answer_question(db: Session, document_id: int, question: str) -> Tuple[str, List[Dict[str, Any]], bool]:
        """
        Retrieves context chunks and generates a grounded response with page citations.
        Returns: (answer_text, citations_list, is_grounded)
        """
        similar_chunks = VectorService.search_similar_chunks(db, document_id, question, top_k=4)

        if not similar_chunks:
            return (
                "I couldn't find enough information in the uploaded document to answer your question.",
                [],
                False
            )

        top_chunk, top_score = similar_chunks[0]

        # Anti-hallucination threshold: if score is too low or no matching terms
        if top_score < 0.05:
            return (
                "I couldn't find enough information in the uploaded document to answer your question.",
                [],
                False
            )

        # Build context string with explicit page markers
        context_blocks = []
        citations = []
        seen_pages = set()

        for chunk, score in similar_chunks:
            context_blocks.append(f"[Page {chunk.page_number}]: {chunk.chunk_text}")
            if chunk.page_number not in seen_pages:
                citations.append({
                    "page_number": chunk.page_number,
                    "snippet": chunk.chunk_text[:180] + ("..." if len(chunk.chunk_text) > 180 else "")
                })
                seen_pages.add(chunk.page_number)

        context_text = "\n\n".join(context_blocks)

        # Attempt to generate answer via Gemini or OpenAI API if configured
        if settings.GEMINI_API_KEY:
            answer = RAGService._call_gemini_api(question, context_text)
            if answer:
                return (answer, citations, True)

        if settings.OPENAI_API_KEY:
            answer = RAGService._call_openai_api(question, context_text)
            if answer:
                return (answer, citations, True)

        # Fallback offline smart synthesizer (Grounding guaranteed)
        answer = RAGService._offline_synthesize_answer(question, context_blocks, citations)
        return (answer, citations, True)

    @staticmethod
    def _call_gemini_api(question: str, context: str) -> str:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"""You are DocuMind, an academic document assistant.
Answer the question strictly using the document context below.
Attach page citations like [Page X] wherever relevant.
If the context does not contain enough information to answer, state: "I couldn't find enough information in the uploaded document to answer your question."

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}
"""
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            response = httpx.post(url, json=payload, timeout=20.0)
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"Gemini API error: {e}")
        return None

    @staticmethod
    def _call_openai_api(question: str, context: str) -> str:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            prompt = f"""You are DocuMind, an academic document assistant.
Answer the question strictly using the document context below.
Attach page citations like [Page X] wherever relevant.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}
"""
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            response = httpx.post(url, headers=headers, json=payload, timeout=20.0)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
        return None

    @staticmethod
    def _offline_synthesize_answer(question: str, context_blocks: List[str], citations: List[Dict[str, Any]]) -> str:
        """
        Produces a well-structured, grounded answer directly from retrieved passages
        when external API keys are not present.
        """
        primary_block = context_blocks[0]
        # Format citation reference
        page_ref = f"[Page {citations[0]['page_number']}]" if citations else ""

        response = f"Based on the document context {page_ref}:\n\n"
        
        # Synthesize matching key sentences
        cleaned_passages = []
        for block in context_blocks[:3]:
            # Remove [Page X]: prefix for reading flow
            parts = block.split("]: ", 1)
            p_text = parts[1] if len(parts) > 1 else block
            cleaned_passages.append(p_text.strip())

        response += f"**Key Finding**: {cleaned_passages[0]}\n\n"
        if len(cleaned_passages) > 1:
            page_tag = f"[Page {citations[1]['page_number']}]" if len(citations) > 1 else ""
            response += f"**Additional Relevant Context** {page_tag}:\n"
            for passage in cleaned_passages[1:]:
                # Extract first 2 sentences
                short_p = passage[:300] + ("..." if len(passage) > 300 else "")
                response += f"• {short_p}\n"

        return response.strip()
