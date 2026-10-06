from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import User, Document
from app.schemas.schemas import DocumentResponse
from app.utils.auth_utils import get_current_user
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await DocumentService.process_and_save_document(db, current_user.id, file)

@router.get("", response_model=List[DocumentResponse])
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return DocumentService.get_user_documents(db, current_user.id)

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = DocumentService.get_document_by_id(db, document_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = DocumentService.delete_document(db, document_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or permission denied")
    return None
