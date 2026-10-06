import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import User, Document, Conversation, Message
from app.schemas.schemas import QuestionRequest, ChatResponse, ConversationResponse, MessageResponse, Citation
from app.utils.auth_utils import get_current_user
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])

@router.post("/ask", response_model=ChatResponse)
def ask_question(
    req: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify document ownership
    doc = db.query(Document).filter(Document.id == req.document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get or create conversation
    conversation = None
    if req.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == req.conversation_id,
            Conversation.user_id == current_user.id
        ).first()

    if not conversation:
        title = req.question[:40] + ("..." if len(req.question) > 40 else "")
        conversation = Conversation(
            user_id=current_user.id,
            document_id=req.document_id,
            title=f"QA: {title}"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save User message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=req.question
    )
    db.add(user_msg)

    # Run RAG Grounded Answer pipeline
    answer, citations_list, is_grounded = RAGService.answer_question(db, req.document_id, req.question)

    # Save Assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        citations_json=json.dumps(citations_list)
    )
    db.add(assistant_msg)
    db.commit()

    citations_objs = [Citation(page_number=c["page_number"], snippet=c["snippet"]) for c in citations_list]

    return ChatResponse(
        conversation_id=conversation.id,
        answer=answer,
        citations=citations_objs,
        grounded=is_grounded
    )

@router.get("/conversations/{document_id}", response_model=List[ConversationResponse])
def get_conversations(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Conversation).filter(
        Conversation.document_id == document_id,
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()

@router.get("/history/{conversation_id}", response_model=List[MessageResponse])
def get_message_history(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    
    result = []
    for m in messages:
        cits = []
        if m.citations_json:
            try:
                raw_cits = json.loads(m.citations_json)
                cits = [Citation(page_number=c["page_number"], snippet=c["snippet"]) for c in raw_cits]
            except Exception:
                pass
        result.append(MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            citations=cits,
            created_at=m.created_at
        ))

    return result
