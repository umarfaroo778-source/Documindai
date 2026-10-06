import json
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import DocumentChunk, Summary, Document
from app.config import settings
import httpx

class SummaryService:
    @staticmethod
    def generate_summary(db: Session, user_id: int, document_id: int) -> Summary:
        # Check if summary already exists
        existing = db.query(Summary).filter(Summary.document_id == document_id, Summary.user_id == user_id).first()
        if existing:
            return existing

        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
        if not chunks:
            text_sample = "Empty document."
        else:
            text_sample = "\n\n".join([c.chunk_text for c in chunks[:10]])

        doc = db.query(Document).filter(Document.id == document_id).first()
        doc_name = doc.original_filename if doc else "Document"

        exec_summary = ""
        key_takeaways = []

        # Attempt Gemini / OpenAI API if present
        if settings.GEMINI_API_KEY:
            ai_res = SummaryService._call_gemini_summary(text_sample)
            if ai_res:
                exec_summary = ai_res.get("summary", "")
                key_takeaways = ai_res.get("takeaways", [])

        if not exec_summary:
            # Offline smart summary extractor
            sentences = re.split(r'(?<=[.!?])\s+', text_sample)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            exec_summary = (
                f"This document, '{doc_name}', provides comprehensive course material and structured academic reference. "
                + " ".join(sentences[:3])
            )
            
            takeaway_candidates = sentences[3:9] if len(sentences) > 3 else sentences
            key_takeaways = [s for s in takeaway_candidates[:5]]
            if not key_takeaways:
                key_takeaways = ["Contains foundational course concepts.", "Covers definitions and core principles."]

        summary_obj = Summary(
            user_id=user_id,
            document_id=document_id,
            executive_summary=exec_summary,
            key_takeaways_json=json.dumps(key_takeaways)
        )
        db.add(summary_obj)
        db.commit()
        db.refresh(summary_obj)
        return summary_obj

    @staticmethod
    def _call_gemini_summary(text: str) -> Dict[str, Any]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"""Summarize the document text below into a JSON object with keys "summary" (string) and "takeaways" (list of 5 string bullet points).
TEXT:
{text[:4000]}
"""
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = httpx.post(url, json=payload, timeout=20.0)
            if response.status_code == 200:
                raw_txt = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                # Extract JSON
                match = re.search(r'\{.*\}', raw_txt, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            print(f"Gemini Summary Error: {e}")
        return None
