"""
Evaluation Module (Offline Testing)
─────────────────────────────────────
Run this to measure retrieval quality and response correctness
against a curated test set.

WHY: Without measurable metrics you can't improve systematically.
This module provides:
  - Retrieval Hit Rate (did the right chunk come back?)
  - Mean Reciprocal Rank (how high in the list was the answer?)
  - Latency percentiles (p50, p95)
  - Placeholder for LLM-as-judge scoring

Usage:
    python -m app.evaluation
"""
import json
import logging
import statistics
import time
from typing import List

from app.ingestion import ingest_pdf
from app.logger import configure_logging
from app.retrieval import retrieve

configure_logging()
logger = logging.getLogger(__name__)

# ── Test Dataset ──────────────────────────────────────────────────────────────
# Format: {"query": str, "expected_keywords": [str], "expected_source": str}
EVAL_DATASET = [
    {
        "query": "What are tenant rights if a landlord evicts without notice?",
        "expected_keywords": ["notice", "eviction", "tenant", "landlord"],
        "expected_source": None,  # Set to filename if known
    },
    {
        "query": "What is the process for filing a consumer complaint?",
        "expected_keywords": ["complaint", "consumer", "forum", "filing"],
        "expected_source": None,
    },
    {
        "query": "Can an employer terminate an employee without cause?",
        "expected_keywords": ["termination", "employer", "employee", "cause"],
        "expected_source": None,
    },
]


# ── Evaluation Functions ──────────────────────────────────────────────────────

def keyword_hit_rate(results: List[dict], expected_keywords: List[str]) -> float:
    """Fraction of expected keywords found in the top retrieved chunks."""
    combined = " ".join(r["content"].lower() for r in results)
    hits = sum(1 for kw in expected_keywords if kw.lower() in combined)
    return hits / len(expected_keywords) if expected_keywords else 0.0


def mean_reciprocal_rank(results: List[dict], expected_keywords: List[str]) -> float:
    """MRR: finds the rank of the first result containing any expected keyword."""
    for rank, result in enumerate(results, 1):
        content = result["content"].lower()
        if any(kw.lower() in content for kw in expected_keywords):
            return 1.0 / rank
    return 0.0


def run_evaluation(top_k: int = 5) -> dict:
    """Run the full evaluation pipeline and return aggregated metrics."""
    results_summary = []
    latencies = []

    for test in EVAL_DATASET:
        query = test["query"]
        expected = test["expected_keywords"]

        t0 = time.perf_counter()
        results = retrieve(query, top_k=top_k)
        latency_ms = (time.perf_counter() - t0) * 1000

        latencies.append(latency_ms)
        hit_rate = keyword_hit_rate(results, expected)
        mrr = mean_reciprocal_rank(results, expected)

        results_summary.append({
            "query": query[:60],
            "chunks_returned": len(results),
            "keyword_hit_rate": round(hit_rate, 3),
            "mrr": round(mrr, 3),
            "latency_ms": round(latency_ms, 1),
        })

        logger.info(
            "Query='%.50s' | HitRate=%.2f | MRR=%.2f | Latency=%.1fms",
            query, hit_rate, mrr, latency_ms,
        )

    metrics = {
        "total_queries": len(EVAL_DATASET),
        "avg_keyword_hit_rate": round(statistics.mean(r["keyword_hit_rate"] for r in results_summary), 3),
        "avg_mrr": round(statistics.mean(r["mrr"] for r in results_summary), 3),
        "p50_latency_ms": round(statistics.median(latencies), 1),
        "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 1),
        "details": results_summary,
    }

    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    logger.info("Starting evaluation run...")
    run_evaluation()
