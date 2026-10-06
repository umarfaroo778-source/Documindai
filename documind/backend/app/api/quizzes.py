import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import User, Document
from app.schemas.schemas import QuizResponse, QuestionItem
from app.utils.auth_utils import get_current_user
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])

@router.post("/generate/{document_id}", response_model=QuizResponse)
def generate_quiz(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    quiz_obj = QuizService.generate_quiz(db, current_user.id, document_id)
    questions_raw = json.loads(quiz_obj.questions_json) if quiz_obj.questions_json else []
    
    questions = [QuestionItem(**q) for q in questions_raw]

    return QuizResponse(
        id=quiz_obj.id,
        document_id=quiz_obj.document_id,
        title=quiz_obj.title,
        questions=questions,
        created_at=quiz_obj.created_at
    )
