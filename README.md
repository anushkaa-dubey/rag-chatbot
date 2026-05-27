# RAG Legal Assistant

Production-oriented Retrieval-Augmented Generation (RAG) system for legal document understanding using FastAPI, FAISS, Ollama embeddings, and Groq LLMs.

The application allows users to upload legal PDFs and ask questions in natural language. The system performs semantic retrieval over uploaded documents and generates grounded answers with source attribution and confidence scoring.

---

## Features

- PDF document ingestion
- Semantic search using vector embeddings
- Conversational RAG pipeline
- FastAPI backend with Swagger documentation
- FAISS vector database
- Ollama local embeddings
- Groq LLM integration
- Multi-turn conversation memory
- Confidence scoring
- Source attribution
- Duplicate document detection
- Evaluation pipeline for retrieval testing
- Docker-ready architecture

---

## Architecture

```text
User Query
    ↓
FastAPI API Layer
    ↓
Retrieval Service
    ↓
FAISS Vector Search
    ↓
Relevant Chunks Retrieved
    ↓
Groq LLM Generation
    ↓
Grounded Response Returned
```

---

## Tech Stack

### Backend
- FastAPI
- Python

### AI / NLP
- LangChain
- Groq
- Ollama
- FAISS

### Document Processing
- PDFPlumber
- RecursiveCharacterTextSplitter

### Infrastructure
- Docker
- Uvicorn

---

## Project Structure

```text
app/
│
├── api.py
├── config.py
├── ingestion.py
├── retrieval.py
├── generation.py
├── evaluation.py
├── logger.py
│
vectorstore/
pdfs/

run_api.py
requirements.txt
README.md
```

---

## RAG Pipeline

### 1. Document Ingestion
- PDF uploaded through API
- PDF text extracted
- Documents split into semantic chunks

### 2. Embedding Generation
- Ollama generates vector embeddings
- Embeddings stored in FAISS vector database

### 3. Retrieval
- User query converted into vector representation
- Top relevant chunks retrieved using semantic similarity

### 4. Generation
- Retrieved context passed to Groq LLM
- Grounded response generated with citations

---

## Why This Architecture?

The system is designed with modular separation between:
- ingestion
- retrieval
- generation
- API layer

This allows:
- easier scaling
- independent component upgrades
- production deployment flexibility
- easier debugging and testing

---

## API Endpoints

### Health Check

```http
GET /api/v1/health
```

### Upload Document

```http
POST /api/v1/ingest
```

### Query Documents

```http
POST /api/v1/query
```

### List Documents

```http
GET /api/v1/documents
```

### Clear Session

```http
DELETE /api/v1/session/{session_id}
```

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/anushkaa-dubey/rag-chatbot.git
cd rag-chatbot
```

---

### 2. Create Virtual Environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux / Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Ollama Setup

### Install Ollama

Download:
https://ollama.com/download

---

### Pull Embedding Model

```bash
ollama pull deepseek-r1:1.5b
```

---

### Start Ollama Server

```bash
ollama serve
```

Default Ollama endpoint:

```text
http://localhost:11434
```

---

## Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key

LLM_MODEL=llama-3.3-70b-versatile

OLLAMA_MODEL=deepseek-r1:1.5b
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Running the Project

### Start FastAPI Server

```bash
python run_api.py
```

Server:
```text
http://localhost:8000
```

Swagger Docs:
```text
http://localhost:8000/docs
```

---

## Example Query Request

```json
{
  "question": "Can someone be arrested unfairly?",
  "top_k": 5
}
```

---

## Example Response

```json
{
  "answer": "According to the uploaded legal documents...",
  "confidence": "Medium",
  "sources": [],
  "latency_ms": 1240.2,
  "model": "llama-3.3-70b-versatile"
}
```

---

## Evaluation Pipeline

The project includes an offline evaluation module for:
- retrieval hit rate
- mean reciprocal rank (MRR)
- latency measurement

Run:

```bash
python -m app.evaluation
```

---

## Current Limitations

- Single-machine FAISS deployment
- In-memory session storage
- No user-level document isolation
- Local Ollama dependency
- Basic retrieval strategy

---

## Production Improvements

Potential production improvements:
- Redis session storage
- Pinecone / Qdrant vector database
- Hybrid search
- Reranking models
- Kubernetes deployment
- Async ingestion pipelines
- Multi-tenant document isolation
- AWS CloudWatch monitoring

---

## Future Enhancements

- Graph RAG
- Multi-agent workflows
- Legal citation extraction
- Multilingual legal support
- OCR support for scanned PDFs
- Streaming responses
- Fine-grained access control

---

## Key Learnings

This project helped explore:
- Retrieval-Augmented Generation (RAG)
- semantic search
- embeddings
- vector databases
- conversational memory
- FastAPI backend architecture
- modular AI system design
- production-oriented API development

---

## License

MIT License
