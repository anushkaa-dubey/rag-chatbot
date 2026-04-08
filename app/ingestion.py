"""
Ingestion Service
─────────────────
Responsible for:
  1. Saving uploaded PDF bytes to disk.
  2. Loading & chunking PDF pages.
  3. Building / updating the FAISS vector store.
  4. Tracking which documents have been ingested (prevents duplicates).

WHY separated?  Ingestion is I/O and CPU-heavy; decoupling it lets us
replace FAISS with Pinecone/Chroma without touching retrieval or generation.
"""
import hashlib
import logging
import os
import time
from pathlib import Path
from typing import List, Optional

from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    FAISS_DB_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    PDFS_DIR,
)

logger = logging.getLogger(__name__)

# In-memory registry: filename → sha256 hash (detects re-uploads of same file)
_ingested: dict[str, str] = {}
_faiss_db: Optional[FAISS] = None


# ── Helpers ─────────────────────────────────────────────────────────────────

def _get_embedding_model() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)


def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
        separators=["\n\n", "\n", ".", " ", ""],  # legal-doc aware hierarchy
    )
    return splitter.split_documents(documents)


# ── Public API ───────────────────────────────────────────────────────────────

def get_vector_store() -> Optional[FAISS]:
    """Return the current in-memory FAISS index (may be None if nothing ingested)."""
    global _faiss_db
    # Attempt to load persisted store if not in memory
    if _faiss_db is None and os.path.exists(FAISS_DB_PATH):
        try:
            logger.info("Loading persisted FAISS index from %s", FAISS_DB_PATH)
            _faiss_db = FAISS.load_local(
                FAISS_DB_PATH,
                _get_embedding_model(),
                allow_dangerous_deserialization=True,
            )
            logger.info("FAISS index loaded successfully.")
        except Exception as exc:
            logger.warning("Could not load persisted FAISS index: %s", exc)
    return _faiss_db


def save_pdf(file_bytes: bytes, filename: str) -> str:
    """Persist uploaded bytes to the pdfs directory. Returns the saved file path."""
    os.makedirs(PDFS_DIR, exist_ok=True)
    dest = os.path.join(PDFS_DIR, filename)
    with open(dest, "wb") as f:
        f.write(file_bytes)
    logger.info("PDF saved to %s (%d bytes)", dest, len(file_bytes))
    return dest


def ingest_pdf(file_path: str) -> dict:
    """
    Full ingestion pipeline for a single PDF file.
    Returns a status dict with metadata.
    Skips re-ingestion if the exact same file (by hash) was already processed.
    """
    global _faiss_db

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    # Duplicate detection
    file_hash = _file_sha256(file_path)
    filename = os.path.basename(file_path)
    if _ingested.get(filename) == file_hash:
        logger.info("Skipping already-ingested file: %s", filename)
        return {"status": "skipped", "filename": filename, "reason": "already ingested"}

    t0 = time.perf_counter()

    # 1. Load
    logger.info("Loading PDF: %s", file_path)
    loader = PDFPlumberLoader(file_path)
    documents = loader.load()

    # Attach source metadata to every page
    for doc in documents:
        doc.metadata["source_file"] = filename

    # 2. Chunk
    chunks = _split_documents(documents)
    logger.info("Split into %d chunks (pages=%d)", len(chunks), len(documents))

    # 3. Embed & store
    embeddings = _get_embedding_model()
    if _faiss_db is None:
        _faiss_db = FAISS.from_documents(chunks, embeddings)
    else:
        # Merge into existing index so multi-doc queries work correctly
        new_db = FAISS.from_documents(chunks, embeddings)
        _faiss_db.merge_from(new_db)

    # 4. Persist
    os.makedirs(os.path.dirname(FAISS_DB_PATH) or ".", exist_ok=True)
    _faiss_db.save_local(FAISS_DB_PATH)

    elapsed = time.perf_counter() - t0
    _ingested[filename] = file_hash

    result = {
        "status": "success",
        "filename": filename,
        "pages": len(documents),
        "chunks": len(chunks),
        "ingestion_time_s": round(elapsed, 2),
    }
    logger.info("Ingestion complete: %s", result)
    return result


def list_ingested_documents() -> List[str]:
    """Return the list of document filenames currently in the vector store."""
    return list(_ingested.keys())
