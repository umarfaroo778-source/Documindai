import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import User, Document
from app.schemas.schemas import SummaryResponse
from app.utils.auth_utils import get_current_user
from app.services.summary_service import SummaryService

router = APIRouter(prefix="/api/summaries", tags=["Summaries"])

@router.post("/generate/{document_id}", response_model=SummaryResponse)
def generate_summary(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    summary_obj = SummaryService.generate_summary(db, current_user.id, document_id)
    takeaways = json.loads(summary_obj.key_takeaways_json) if summary_obj.key_takeaways_json else []

    return SummaryResponse(
        id=summary_obj.id,
        document_id=summary_obj.document_id,
        executive_summary=summary_obj.executive_summary,
        key_takeaways=takeaways,
        created_at=summary_obj.created_at
    )
