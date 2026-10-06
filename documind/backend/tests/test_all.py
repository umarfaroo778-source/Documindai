import os
import pytest
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_auth_workflow():
    # Test Registration
    email = f"student_{os.urandom(4).hex()}@university.edu"
    reg_payload = {
        "name": "Alex Smith",
        "email": email,
        "password": "Password123!",
        "university": "State University"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    token = data["access_token"]

    # Test Login
    login_res = client.post("/api/auth/login", data={"username": email, "password": "Password123!"})
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Test Protected /me endpoint
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

def test_document_and_rag_pipeline():
    # Register test user
    email = f"rag_tester_{os.urandom(4).hex()}@university.edu"
    reg_res = client.post("/api/auth/register", json={
        "name": "RAG Tester",
        "email": email,
        "password": "SecurePassword123",
        "university": "Tech Institute"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload test text file
    sample_text = """
    Chapter 1: Quantum Computing Fundamentals.
    Quantum mechanics forms the theoretical foundation of quantum computation.
    Superposition allows qubits to exist in multiple states simultaneously.
    Entanglement links qubit states regardless of physical distance.
    Page 2: Quantum Algorithms.
    Shor's algorithm efficiently factors large composite integers in polynomial time.
    Grover's algorithm provides a quadratic speedup for unstructured database searches.
    """
    
    files = {"file": ("quantum_notes.txt", sample_text.encode('utf-8'), "text/plain")}
    upload_res = client.post("/api/documents/upload", headers=headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Test Chat / RAG QA
    qa_res = client.post("/api/chat/ask", headers=headers, json={
        "document_id": doc_id,
        "question": "What is Shor's algorithm used for?"
    })
    assert qa_res.status_code == 200
    qa_data = qa_res.json()
    assert "Shor" in qa_data["answer"] or "factor" in qa_data["answer"]
    assert qa_data["grounded"] is True

    # Test Summary Generation
    sum_res = client.post(f"/api/summaries/generate/{doc_id}", headers=headers)
    assert sum_res.status_code == 200
    assert "executive_summary" in sum_res.json()

    # Test MCQ Quiz Generation
    quiz_res = client.post(f"/api/quizzes/generate/{doc_id}", headers=headers)
    assert quiz_res.status_code == 200
    assert len(quiz_res.json()["questions"]) > 0

    # Test Flashcard Generation
    card_res = client.post(f"/api/flashcards/generate/{doc_id}", headers=headers)
    assert card_res.status_code == 200
    assert len(card_res.json()["cards"]) > 0

    # Test Study Notes Generation
    note_res = client.post(f"/api/notes/generate/{doc_id}", headers=headers)
    assert note_res.status_code == 200
    assert "markdown_content" in note_res.json()
