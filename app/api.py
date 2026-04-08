"""
FastAPI Backend — REST API Layer
─────────────────────────────────
Endpoints:
  POST /api/v1/ingest          — Upload & process a PDF
  POST /api/v1/query           — Ask a question (optionally with session)
  GET  /api/v1/documents       — List ingested documents
  DELETE /api/v1/session/{id}  — Clear conversation session
  GET  /api/v1/health          — Health check

WHY FastAPI?
  - Auto-generates OpenAPI/Swagger docs at /docs
  - Async support for non-blocking I/O
  - Pydantic models for request/response validation
  - Easy to containerise and deploy behind a load balancer
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import API_HOST, API_PORT
from app.generation import clear_session, generate_answer
from app.ingestion import ingest_pdf, list_ingested_documents, save_pdf
from app.logger import configure_logging
from app.retrieval import retrieve

configure_logging()
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 RAG Legal Assistant API starting up.")
    yield
    logger.info("🛑 RAG Legal Assistant API shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG Legal Assistant API",
    description="Production-ready Retrieval-Augmented Generation API for legal documents.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000, description="User's legal question")
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Session ID for multi-turn conversation. Generate once per chat session.",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")


class SourceChunk(BaseModel):
    file: str
    page: int | None
    score: float | None
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    confidence: str
    sources: list[SourceChunk]
    latency_ms: float
    model: str
    session_id: str


class IngestResponse(BaseModel):
    status: str
    filename: str
    pages: int | None = None
    chunks: int | None = None
    ingestion_time_s: float | None = None
    reason: str | None = None


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    documents_loaded: int


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Returns API health and count of ingested documents."""
    return HealthResponse(
        status="ok",
        timestamp=time.time(),
        documents_loaded=len(list_ingested_documents()),
    )


@app.post("/api/v1/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_document(file: UploadFile = File(...)):
    """
    Upload a PDF file to be embedded and added to the vector store.
    Subsequent queries will automatically search across all ingested documents.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        saved_path = save_pdf(file_bytes, file.filename)
        result = ingest_pdf(saved_path)
        return IngestResponse(**result)

    except FileNotFoundError as exc:
        logger.error("File not found during ingestion: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during ingestion")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")


@app.post("/api/v1/query", response_model=QueryResponse, tags=["Query"])
async def query_documents(request: QueryRequest):
    """
    Ask a legal question. Returns an LLM-generated answer with source citations
    and a confidence rating.

    Pass the same `session_id` across multiple requests to enable multi-turn
    conversation with contextual memory.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # 1. Retrieve
        docs = retrieve(question, top_k=request.top_k)

        # 2. Generate
        result = generate_answer(
            query=question,
            retrieved_docs=docs,
            session_id=request.session_id,
        )
        return QueryResponse(**result, session_id=request.session_id)

    except RuntimeError as exc:
        logger.error("Generation error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected query error")
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}")


@app.get("/api/v1/documents", tags=["Ingestion"])
async def list_documents():
    """Return the list of documents currently in the vector store."""
    docs = list_ingested_documents()
    return {"documents": docs, "count": len(docs)}


@app.delete("/api/v1/session/{session_id}", tags=["Session"])
async def delete_session(session_id: str):
    """Clear the conversation history for a given session ID."""
    clear_session(session_id)
    return {"message": f"Session '{session_id}' cleared successfully."}


# ── Dev entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api:app", host=API_HOST, port=API_PORT, reload=True)
