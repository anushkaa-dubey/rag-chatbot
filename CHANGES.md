# 🚀 Production Upgrade: Changes & Engineering Documentation

> **Author:** Anushkaa Dubey  
> **Upgrade Date:** April 2026  
> **From:** Prototype (3 files, ~70 LOC) → **To:** Production-ready system (8+ modules, ~900 LOC)

---

## 📊 Before vs. After — At a Glance

| Dimension | Before | After |
|---|---|---|
| Architecture | 3 flat files | Modular `app/` package (config, ingestion, retrieval, generation, API) |
| API Layer | None (Streamlit only) | FastAPI REST backend + Streamlit client |
| PDF Ingestion | Static `eng.pdf` hardcoded | Dynamic upload → embed → store → query pipeline |
| Multi-document | ❌ | ✅ Merge into shared FAISS index |
| Duplicate detection | ❌ | ✅ SHA-256 hash per file |
| Source attribution | ❌ | ✅ Filename + page + excerpt + score |
| Confidence score | ❌ | ✅ High / Medium / Low (LLM self-rating) |
| Conversation memory | ❌ | ✅ Multi-turn session with history |
| Error handling | Minimal | Typed HTTP errors, fallbacks, empty-input guards |
| Logging | `print()` | Structured rotating logs (`logs/rag_app.log`) |
| Caching | None | LRU query cache (128 entries) |
| Evaluation | None | Hit-rate, MRR, latency percentile pipeline |
| Containerisation | None | `Dockerfile` + `docker-compose.yml` |
| Config management | Hardcoded strings | `.env` → `app/config.py` (all tunable values) |

---

## 1. 🏗️ Architecture & Modularity

### Problem
All logic (loading, chunking, embedding, retrieval, LLM call) lived in 3 tightly coupled files. Any change to one broke the others.

### Solution: Clean Service Separation

```
app/
├── config.py       ← All env vars & tunable constants
├── logger.py       ← Rotating file + console logger
├── ingestion.py    ← PDF → chunks → FAISS (Ingestion Service)
├── retrieval.py    ← FAISS similarity search + scoring (Retrieval Service)
├── generation.py   ← Prompt building + Groq LLM call (Generation Service)
├── api.py          ← FastAPI REST endpoints (API Layer)
└── evaluation.py   ← Offline evaluation pipeline (Metrics Layer)
```

### Why It Matters
- **Independent scaling:** The retrieval service can be swapped to Pinecone without touching the LLM layer.
- **Testability:** Each service can be unit-tested in isolation.
- **Team collaboration:** Backend and frontend developers can work in parallel.

---

## 2. ⚡ Performance & Optimization

### Chunking Strategy Improved
| Setting | Before | After | Why |
|---|---|---|---|
| `chunk_size` | 1000 tokens | 800 tokens | Reduces noise per chunk, tighter retrieval signal |
| `chunk_overlap` | 200 | 150 | Still preserves cross-boundary context |
| Separators | Default | `["\n\n", "\n", ".", " ", ""]` | Legal-doc aware: splits at paragraphs first |

### LRU Query Cache
```python
@lru_cache(maxsize=128)
def retrieve_cached(query: str, top_k: int) -> tuple:
    ...
```
**Why:** Identical queries skip FAISS entirely. Latency drops from ~500ms → <1ms for cached hits.

### Similarity Score Thresholding
Only chunks within `SIMILARITY_SCORE_THRESHOLD=0.35` are returned. This prevents hallucination from irrelevant weak matches while still falling back gracefully.

---

## 3. 📥 Data Handling & Ingestion

### Problem
`vector_database.py` loaded a hardcoded `eng.pdf` at module import time — blocking every request. Uploaded PDFs via Streamlit weren't actually ingested.

### Solution: Dynamic Ingestion Pipeline

```
User uploads PDF(s)
      ↓
POST /api/v1/ingest
      ↓
save_pdf() → pdfs/ directory
      ↓
ingest_pdf():
  ├── SHA-256 duplicate check
  ├── PDFPlumberLoader (page-aware)
  ├── RecursiveCharacterTextSplitter (legal-optimized)
  ├── OllamaEmbeddings (local, private)
  └── FAISS.merge_from() ← merges into shared index
      ↓
faiss_db.save_local() ← persisted to disk
```

### Multi-Document Support
`FAISS.merge_from()` merges new document embeddings into the existing global index. Queries transparently search across all ingested PDFs.

---

## 4. 📏 Evaluation & Metrics

### Module: `app/evaluation.py`

| Metric | Formula | Target |
|---|---|---|
| **Keyword Hit Rate** | % of expected keywords in top-k chunks | > 0.8 |
| **Mean Reciprocal Rank (MRR)** | 1/rank of first relevant result | > 0.6 |
| **p50 Retrieval Latency** | Median ms across queries | < 300ms |
| **p95 Retrieval Latency** | 95th percentile ms | < 800ms |

```bash
python -m app.evaluation
```

---

## 5. 🛡️ Reliability & Edge Cases

| Scenario | Old Behavior | New Behavior |
|---|---|---|
| Empty question | Crashes | `400 Bad Request` + friendly message |
| No documents ingested | FAISS error | `"Please upload at least one PDF"` guard |
| Duplicate PDF upload | Re-embeds everything | SHA-256 check → skip with status |
| API offline | Streamlit crash | Sidebar banner + ConnectionError catch |
| Groq API failure | Uncaught exception | `503 Service Unavailable` |
| Missing GROQ_API_KEY | Python exception | `500` with clear message |

---

## 6. 💬 User Experience

### Multi-Turn Conversation Memory
Each session has a UUID. Same `session_id` reconstructs full LangChain message history for follow-up questions.

### Source Attribution
Every answer shows: filename, page number, relevance score, and 200-char excerpt.

### Confidence Badges
- 🟢 **High** — Strong evidence in context
- 🟡 **Medium** — Partial evidence
- 🔴 **Low** — Context missing; recommend consulting a lawyer

---

## 7. 🔧 Backend Engineering Standards

### FastAPI REST API (`app/api.py`)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/health` | GET | Health check + document count |
| `/api/v1/ingest` | POST | Upload PDF for ingestion |
| `/api/v1/query` | POST | Ask a question (multi-turn) |
| `/api/v1/documents` | GET | List all ingested documents |
| `/api/v1/session/{id}` | DELETE | Clear conversation session |

Swagger UI auto-generated at `http://localhost:8000/docs`

### Structured Logging
```
[2026-04-09 10:30:15] INFO  app.ingestion - Split into 47 chunks (pages=12)
[2026-04-09 10:30:18] INFO  app.retrieval - Retrieved 5 chunks [234ms]
[2026-04-09 10:30:22] INFO  app.generation - Generated [confidence=High, latency=3842ms]
```

---

## 8. 🌐 Scalability & Deployment

### Running Locally

**Terminal 1 — API Backend:**
```bash
.venv\Scripts\activate
python run_api.py
```

**Terminal 2 — Streamlit Frontend:**
```bash
streamlit run frontend.py
```

### Docker Compose
```bash
docker-compose up --build
```
Starts: Ollama (11434) → FastAPI API (8000) → Streamlit (8501)

### AWS EC2 Deployment
```
1. Launch t3.medium EC2 instance
2. Install Docker + Docker Compose
3. Clone repo, add GROQ_API_KEY to .env
4. docker-compose up -d
5. docker exec rag_ollama ollama pull deepseek-r1:1.5b
6. Open Security Group: ports 8000, 8501
```

---

## 📁 New Project Structure

```
RAG-CHATBOT/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── logger.py
│   ├── ingestion.py
│   ├── retrieval.py
│   ├── generation.py
│   ├── api.py
│   └── evaluation.py
│
├── frontend.py         ← Upgraded Streamlit UI
├── run_api.py          ← API server entrypoint
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── CHANGES.md          ← This file
```

---

## 🔮 Recommended Next Steps

1. **Hybrid Search** — BM25 + vector for precise legal code lookups
2. **Reranking** — Cross-encoder reranker for top-20 → top-5
3. **Redis Session Store** — Replace in-memory sessions for multi-instance
4. **Async Ingestion Queue** — Celery + Redis for large PDF background processing
5. **Multilingual Support** — Hindi/regional language detection + translation
6. **LLM-as-Judge Evaluation** — Automated answer scoring against gold standards
7. **Pinecone/Weaviate** — Replace FAISS with managed distributed vector DB
