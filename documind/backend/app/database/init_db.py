from app.database.database import engine, Base
from app.models.models import User, Document, DocumentChunk, Conversation, Message, Summary, Quiz, FlashcardDeck, StudyNote

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
