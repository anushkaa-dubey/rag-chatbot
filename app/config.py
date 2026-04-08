"""
Central configuration for the RAG Legal Assistant.
All environment variables and tunable constants live here.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ────────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# ── Embeddings ──────────────────────────────────────────────────────────────
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ── FAISS / Vector Store ────────────────────────────────────────────────────
FAISS_DB_PATH: str = os.getenv("FAISS_DB_PATH", "vectorstore/db_faiss")
PDFS_DIR: str = os.getenv("PDFS_DIR", "pdfs")

# ── Chunking ────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))

# ── Retrieval ───────────────────────────────────────────────────────────────
RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
SIMILARITY_SCORE_THRESHOLD: float = float(
    os.getenv("SIMILARITY_SCORE_THRESHOLD", "0.35")
)

# ── Caching ─────────────────────────────────────────────────────────────────
CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "128"))

# ── API Server ──────────────────────────────────────────────────────────────
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))

# ── Logging ─────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", "logs/rag_app.log")
