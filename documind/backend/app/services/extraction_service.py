import os
from typing import List, Dict, Any
from app.utils.text_cleaner import clean_text

class ExtractionService:
    @staticmethod
    def extract_document_pages(file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF, DOCX, or TXT files page by page.
        Returns a list of dicts: [{'page_number': int, 'text': str}]
        """
        extension = file_type.lower().strip('.')
        if extension in ['pdf']:
            return ExtractionService._extract_pdf(file_path)
        elif extension in ['docx', 'doc']:
            return ExtractionService._extract_docx(file_path)
        elif extension in ['txt', 'md']:
            return ExtractionService._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_type}")

    @staticmethod
    def _extract_pdf(file_path: str) -> List[Dict[str, Any]]:
        pages = []
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                cleaned = clean_text(raw_text)
                if cleaned:
                    pages.append({"page_number": idx + 1, "text": cleaned})
        except Exception as e:
            # Fallback plain text read if pdf library encounters issue
            print(f"PDF Extraction warning: {e}")
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
                pages.append({"page_number": 1, "text": clean_text(content)})
        
        if not pages:
            pages.append({"page_number": 1, "text": "Document content could not be read or is empty."})
        return pages

    @staticmethod
    def _extract_docx(file_path: str) -> List[Dict[str, Any]]:
        pages = []
        try:
            import docx
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            
            combined_text = "\n\n".join(full_text)
            cleaned = clean_text(combined_text)

            # Estimate page splits approx every 3000 chars or 500 words for Word documents
            chunks = [cleaned[i:i+3000] for i in range(0, len(cleaned), 3000)]
            if not chunks:
                chunks = [cleaned]

            for idx, chunk in enumerate(chunks):
                pages.append({"page_number": idx + 1, "text": chunk})
        except Exception as e:
            print(f"DOCX Extraction error: {e}")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                pages.append({"page_number": 1, "text": clean_text(f.read())})
        
        return pages

    @staticmethod
    def _extract_txt(file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.read()
        cleaned = clean_text(raw)

        # Estimate page splits for long TXT files (approx 2500 chars per page)
        pages = []
        chunks = [cleaned[i:i+2500] for i in range(0, len(cleaned), 2500)]
        if not chunks:
            chunks = [""]

        for idx, chunk in enumerate(chunks):
            pages.append({"page_number": idx + 1, "text": chunk})

        return pages
