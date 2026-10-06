import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import User, Document
from app.schemas.schemas import StudyNoteResponse
from app.utils.auth_utils import get_current_user
from app.services.notes_service import NotesService

router = APIRouter(prefix="/api/notes", tags=["Study Notes"])

@router.post("/generate/{document_id}", response_model=StudyNoteResponse)
def generate_notes(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    note_obj = NotesService.generate_notes(db, current_user.id, document_id)
    concepts = json.loads(note_obj.key_concepts_json) if note_obj.key_concepts_json else []

    return StudyNoteResponse(
        id=note_obj.id,
        document_id=note_obj.document_id,
        title=note_obj.title,
        markdown_content=note_obj.markdown_content,
        key_concepts=concepts,
        created_at=note_obj.created_at
    )
