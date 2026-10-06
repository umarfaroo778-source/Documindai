import os
import sys

# Ensure backend directory is in python path for Vercel
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database.init_db import init_db
from app.api import auth, documents, chat, summaries, quizzes, flashcards, notes

# Initialize tables
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    description="DocuMind - AI-Powered Document Question Answering & Study Assistant",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(summaries.router)
app.include_router(quizzes.router)
app.include_router(flashcards.router)
app.include_router(notes.router)

# Serve Frontend static assets
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
