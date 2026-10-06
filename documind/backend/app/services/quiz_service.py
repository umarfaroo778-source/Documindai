import json
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import DocumentChunk, Quiz, Document
from app.config import settings
import httpx

class QuizService:
    @staticmethod
    def generate_quiz(db: Session, user_id: int, document_id: int) -> Quiz:
        existing = db.query(Quiz).filter(Quiz.document_id == document_id, Quiz.user_id == user_id).first()
        if existing:
            return existing

        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
        doc = db.query(Document).filter(Document.id == document_id).first()
        doc_title = doc.original_filename if doc else "Document"

        full_text = " ".join([c.chunk_text for c in chunks[:8]]) if chunks else "Default document text."

        questions = []
        if settings.GEMINI_API_KEY:
            questions = QuizService._call_gemini_quiz(full_text)

        if not questions:
            # Offline smart MCQ generator from document passages
            passages = [c.chunk_text for c in chunks if len(c.chunk_text) > 80]
            if not passages:
                passages = [full_text]

            for i, p in enumerate(passages[:5]):
                words = re.findall(r'\b[a-zA-Z]{5,}\b', p)
                target_word = words[0] if words else "concept"
                clean_p = p[:150] + "..."

                questions.append({
                    "id": i + 1,
                    "question": f"According to the document passage on Page {chunks[i].page_number if i < len(chunks) else 1}, what key term is highlighted in context to: '{clean_p}'?",
                    "options": [
                        target_word.capitalize(),
                        f"Non-{target_word.lower()}",
                        f"Secondary {target_word.lower()}",
                        "None of the above"
                    ],
                    "correct_option_index": 0,
                    "explanation": f"The document specifically addresses '{target_word.capitalize()}' in this passage context."
                })

        quiz_obj = Quiz(
            user_id=user_id,
            document_id=document_id,
            title=f"Practice Quiz: {doc_title}",
            questions_json=json.dumps(questions)
        )
        db.add(quiz_obj)
        db.commit()
        db.refresh(quiz_obj)
        return quiz_obj

    @staticmethod
    def _call_gemini_quiz(text: str) -> List[Dict[str, Any]]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"""Generate a 5-question multiple choice quiz based on the document text.
Return a valid JSON array of objects with keys:
"id" (int), "question" (string), "options" (list of 4 strings), "correct_option_index" (int 0-3), "explanation" (string).

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
            print(f"Gemini Quiz Error: {e}")
        return []
