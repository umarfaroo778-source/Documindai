import sys
import os
import uvicorn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if __name__ == "__main__":
    print("=" * 60)
    print(" 🚀 Starting DocuMind AI Document & Study Assistant...")
    print(" 🌐 Application URL: http://127.0.0.1:8000/static/index.html")
    print(" 🔌 API Health:      http://127.0.0.1:8000/api/health")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
