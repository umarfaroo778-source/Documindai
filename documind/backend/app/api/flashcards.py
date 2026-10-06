import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import User, Document
from app.schemas.schemas import FlashcardDeckResponse, FlashcardItem
from app.utils.auth_utils import get_current_user
from app.services.flashcard_service import FlashcardService

router = APIRouter(prefix="/api/flashcards", tags=["Flashcards"])

@router.post("/generate/{document_id}", response_model=FlashcardDeckResponse)
def generate_flashcards(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    deck_obj = FlashcardService.generate_flashcards(db, current_user.id, document_id)
    cards_raw = json.loads(deck_obj.cards_json) if deck_obj.cards_json else []
    cards = [FlashcardItem(**c) for c in cards_raw]

    return FlashcardDeckResponse(
        id=deck_obj.id,
        document_id=deck_obj.document_id,
        title=deck_obj.title,
        cards=cards,
        created_at=deck_obj.created_at
    )
