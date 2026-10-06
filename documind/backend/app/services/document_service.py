import os
import uuid
import json
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import Document, DocumentChunk
from app.services.extraction_service import ExtractionService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService

class DocumentService:
    @staticmethod
    async def process_and_save_document(db: Session, user_id: int, file: UploadFile) -> Document:
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower().strip('.')
        if ext not in ['pdf', 'docx', 'doc', 'txt', 'md']:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, or TXT.")

        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        # Read content and save file locally
        contents = await file.read()
        file_size = len(contents)

        with open(file_path, "wb") as f:
            f.write(contents)

        # Create Document record
        doc = Document(
            user_id=user_id,
            filename=unique_filename,
            original_filename=filename,
            file_type=ext,
            file_size=file_size,
            page_count=1,
            status="processing"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        try:
            # Step 1: Extract text page by page
            extracted_pages = ExtractionService.extract_document_pages(file_path, ext)
            doc.page_count = len(extracted_pages)

            # Step 2: Chunk extracted text
            chunks_data = ChunkingService.chunk_pages(extracted_pages)

            # Step 3: Embed & store chunks
            for chunk_dict in chunks_data:
                vec = EmbeddingService.get_embedding(chunk_dict["chunk_text"])
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    chunk_text=chunk_dict["chunk_text"],
                    page_number=chunk_dict["page_number"],
                    chunk_index=chunk_dict["chunk_index"],
                    embedding_reference=json.dumps(vec)
                )
                db.add(chunk_record)

            doc.status = "ready"
            db.commit()
            db.refresh(doc)
            return doc
        except Exception as e:
            doc.status = "error"
            db.commit()
            print(f"Error processing document {filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

    @staticmethod
    def get_user_documents(db: Session, user_id: int) -> List[Document]:
        return db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).all()

    @staticmethod
    def get_document_by_id(db: Session, document_id: int, user_id: int) -> Optional[Document]:
        return db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()

    @staticmethod
    def delete_document(db: Session, document_id: int, user_id: int) -> bool:
        doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
        if not doc:
            return False
        
        # Delete local upload file
        file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        db.delete(doc)
        db.commit()
        return True
