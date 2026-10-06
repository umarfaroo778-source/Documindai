from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    university: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    university: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Document Schemas ---
class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    page_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Chat & RAG Schemas ---
class Citation(BaseModel):
    page_number: int
    snippet: str

class QuestionRequest(BaseModel):
    document_id: int
    question: str
    conversation_id: Optional[int] = None

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: List[Citation] = []
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    title: str
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    citations: List[Citation]
    grounded: bool

# --- AI Study Tools Schemas ---
class SummaryResponse(BaseModel):
    id: int
    document_id: int
    executive_summary: str
    key_takeaways: List[str]
    created_at: datetime

class QuestionItem(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_option_index: int
    explanation: str

class QuizResponse(BaseModel):
    id: int
    document_id: int
    title: str
    questions: List[QuestionItem]
    created_at: datetime

class FlashcardItem(BaseModel):
    id: int
    front: str
    back: str

class FlashcardDeckResponse(BaseModel):
    id: int
    document_id: int
    title: str
    cards: List[FlashcardItem]
    created_at: datetime

class StudyNoteResponse(BaseModel):
    id: int
    document_id: int
    title: str
    markdown_content: str
    key_concepts: List[str] = []
    created_at: datetime
