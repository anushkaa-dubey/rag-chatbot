"""
Retrieval Service
─────────────────
Responsible for:
  1. Similarity search with score thresholding.
  2. Returning ranked, deduplicated source chunks with metadata.
  3. LRU-caching repeated identical queries (latency win).

WHY separated?  Retrieval strategy (FAISS → hybrid BM25+vector, Reranking)
can evolve independently of ingestion or generation.
"""
import logging
import time
from functools import lru_cache
from typing import List, Tuple

from langchain_community.vectorstores import FAISS

from app.config import CACHE_MAX_SIZE, RETRIEVAL_TOP_K, SIMILARITY_SCORE_THRESHOLD
from app.ingestion import get_vector_store

logger = logging.getLogger(__name__)


# ── Internal helpers ─────────────────────────────────────────────────────────

def _deduplicate(
    docs_and_scores: List[Tuple],
) -> List[Tuple]:
    """Remove chunks with identical page_content (can occur with overlapping chunks)."""
    seen = set()
    unique = []
    for doc, score in docs_and_scores:
        key = doc.page_content.strip()
        if key not in seen:
            seen.add(key)
            unique.append((doc, score))
    return unique


# ── Public API ───────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = RETRIEVAL_TOP_K) -> List[dict]:
    """
    Search the vector store for the top-k most relevant chunks.

    Returns a list of result dicts:
      {
        "content": str,
        "score": float,          # cosine-similarity distance (lower = more similar)
        "source": str,           # filename
        "page": int | None,
        "chunk_index": int,
      }

    Falls back to empty list if vector store is not ready or query is blank.
    """
    query = query.strip()
    if not query:
        logger.warning("retrieve() called with empty query")
        return []

    db: FAISS = get_vector_store()
    if db is None:
        logger.error("Vector store not initialized. Please ingest at least one PDF.")
        return []

    t0 = time.perf_counter()

    # similarity_search_with_score returns (Document, L2-distance)
    raw = db.similarity_search_with_score(query, k=top_k)
    elapsed = time.perf_counter() - t0

    # Deduplicate and threshold
    raw = _deduplicate(raw)
    filtered = [
        (doc, score) for doc, score in raw if score <= SIMILARITY_SCORE_THRESHOLD
    ]

    if not filtered:
        logger.info(
            "No results above threshold (%.2f) for query='%.60s...' [%.3fs]",
            SIMILARITY_SCORE_THRESHOLD, query, elapsed,
        )
        # Fall back to raw top-k without threshold so the LLM can say "I don't know"
        filtered = raw

    results = []
    for idx, (doc, score) in enumerate(filtered):
        results.append(
            {
                "content": doc.page_content,
                "score": round(float(score), 4),
                "source": doc.metadata.get("source_file", doc.metadata.get("source", "unknown")),
                "page": doc.metadata.get("page", None),
                "chunk_index": idx,
            }
        )

    logger.info(
        "Retrieved %d chunks for query='%.60s...' [%.3fs]",
        len(results), query, elapsed,
    )
    return results


@lru_cache(maxsize=CACHE_MAX_SIZE)
def retrieve_cached(query: str, top_k: int = RETRIEVAL_TOP_K) -> tuple:
    """
    LRU-cached version of retrieve().
    Returns a tuple of frozen dicts (hashable) for cache compatibility.
    Use retrieve() for the full list-of-dicts interface.
    """
    return tuple(retrieve(query, top_k))
