import json
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import DocumentChunk, StudyNote, Document
from app.config import settings
import httpx

class NotesService:
    @staticmethod
    def generate_notes(db: Session, user_id: int, document_id: int) -> StudyNote:
        existing = db.query(StudyNote).filter(StudyNote.document_id == document_id, StudyNote.user_id == user_id).first()
        if existing:
            return existing

        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
        doc = db.query(Document).filter(Document.id == document_id).first()
        doc_title = doc.original_filename if doc else "Document"

        full_text = "\n\n".join([f"[Page {c.page_number}]: {c.chunk_text}" for c in chunks[:10]])

        markdown_content = ""
        key_concepts = []

        if settings.GEMINI_API_KEY:
            notes_res = NotesService._call_gemini_notes(full_text)
            if notes_res:
                markdown_content = notes_res.get("markdown", "")
                key_concepts = notes_res.get("concepts", [])

        if not markdown_content:
            # Offline structured markdown notes generator
            markdown_content = f"# Study Notes: {doc_title}\n\n"
            markdown_content += "## 📌 Core Concepts & Overview\n"
            markdown_content += f"These study notes summarize the essential material extracted from `{doc_title}` for rapid review and exam preparation.\n\n"

            markdown_content += "## 📚 Chapter Breakdown & Page Citations\n"
            concepts_set = []

            page_map = {}
            for c in chunks:
                page_map.setdefault(c.page_number, []).append(c.chunk_text)

            for page_num, text_list in page_map.items():
                markdown_content += f"### Page {page_num} Highlights\n"
                combined = " ".join(text_list)
                sentences = re.split(r'(?<=[..?])\s+', combined)
                for s in sentences[:3]:
                    if len(s.strip()) > 15:
                        markdown_content += f"- **Key Point**: {s.strip()}\n"
                        words = re.findall(r'\b[A-Z][a-z]{4,}\b', s)
                        if words and len(concepts_set) < 5:
                            concepts_set.append(words[0])
                markdown_content += "\n"

            markdown_content += "## 💡 Study Tips & Formulas\n"
            markdown_content += "- Re-read cited pages for contextual depth.\n"
            markdown_content += "- Use the MCQ Quiz tool to test active recall on these concepts.\n"
            key_concepts = list(set(concepts_set)) if concepts_set else ["Course Fundamentals", "Document Analysis"]

        note_obj = StudyNote(
            user_id=user_id,
            document_id=document_id,
            title=f"Study Notes: {doc_title}",
            markdown_content=markdown_content,
            key_concepts_json=json.dumps(key_concepts)
        )
        db.add(note_obj)
        db.commit()
        db.refresh(note_obj)
        return note_obj

    @staticmethod
    def _call_gemini_notes(text: str) -> Dict[str, Any]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"""Generate comprehensive structured Markdown study notes for a student from the document text.
Return a JSON object with keys: "markdown" (formatted string with headers, bullet points, and code/formula blocks), "concepts" (list of 5 key concept strings).

TEXT:
{text[:4000]}
"""
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = httpx.post(url, json=payload, timeout=20.0)
            if response.status_code == 200:
                raw_txt = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                match = re.search(r'\{.*\}', raw_txt, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            print(f"Gemini Notes Error: {e}")
        return None
