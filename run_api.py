"""
API Server Entrypoint
Run this first (in a separate terminal) before launching the Streamlit frontend.

Usage:
    python run_api.py
"""
import uvicorn
from app.config import API_HOST, API_PORT
from app.logger import configure_logging

configure_logging()

if __name__ == "__main__":
    print(f"Starting RAG Legal Assistant API on http://{API_HOST}:{API_PORT}")
    print(f"Swagger docs: http://localhost:{API_PORT}/docs")
    uvicorn.run(
        "app.api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info",
    )
