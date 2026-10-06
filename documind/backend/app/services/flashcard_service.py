import json
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import DocumentChunk, FlashcardDeck, Document
from app.config import settings
import httpx

class FlashcardService:
    @staticmethod
    def generate_flashcards(db: Session, user_id: int, document_id: int) -> FlashcardDeck:
        existing = db.query(FlashcardDeck).filter(FlashcardDeck.document_id == document_id, FlashcardDeck.user_id == user_id).first()
        if existing:
            return existing

        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
        doc = db.query(Document).filter(Document.id == document_id).first()
        doc_title = doc.original_filename if doc else "Document"

        full_text = " ".join([c.chunk_text for c in chunks[:8]]) if chunks else "Default content."

        cards = []
        if settings.GEMINI_API_KEY:
            cards = FlashcardService._call_gemini_flashcards(full_text)

        if not cards:
            for i, chunk in enumerate(chunks[:6]):
                sentences = re.split(r'(?<=[.!?])\s+', chunk.chunk_text)
                front_question = f"What is the key takeaway on Page {chunk.page_number} regarding: '{sentences[0][:80]}...'?"
                back_answer = sentences[1] if len(sentences) > 1 else chunk.chunk_text[:200]

                cards.append({
                    "id": i + 1,
                    "front": front_question,
                    "back": back_answer
                })

            if not cards:
                cards.append({
                    "id": 1,
                    "front": "Document Main Topic",
                    "back": full_text[:200]
                })

        deck_obj = FlashcardDeck(
            user_id=user_id,
            document_id=document_id,
            title=f"Flashcard Deck: {doc_title}",
            cards_json=json.dumps(cards)
        )
        db.add(deck_obj)
        db.commit()
        db.refresh(deck_obj)
        return deck_obj

    @staticmethod
    def _call_gemini_flashcards(text: str) -> List[Dict[str, Any]]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"""Generate a study deck of 6 flashcards from the text.
Return a JSON array of objects with keys: "id" (int), "front" (string prompt/question), "back" (string answer/explanation).

TEXT:
{text[:4000]}
"""
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = httpx.post(url, json=payload, timeout=20.0)
            if response.status_code == 200:
                raw_txt = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                match = re.search(r'\[.*\]', raw_txt, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            print(f"Gemini Flashcards Error: {e}")
        return []
