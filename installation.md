# RAG Chatbot (Local Ollama Setup)

## Overview

This project implements a Retrieval-Augmented Generation (RAG) chatbot using:

- Streamlit (UI)
- LangChain (RAG pipeline)
- FAISS (vector database)
- Ollama (local LLM + embeddings)
- pypdf (PDF parsing)

All inference runs locally using Ollama. No OpenAI API is required.

---

## System Requirements

- Python 3.10 or 3.11
- Ollama installed
- 8 GB RAM recommended
- Windows / macOS / Linux

---

## 1. Clone Repository

```bash
git clone <repository-url>
cd RAG-CHATBOT
```

---

## 2. Install Ollama

Download from:

https://ollama.com/download

Verify installation:

```bash
ollama --version
```

---

## 3. Pull Required Models

Pull embedding model:

```bash
ollama pull nomic-embed-text
```

Pull LLM model:

```bash
ollama pull llama3
```

If your code uses different model names, pull those instead.

---

## 4. Create Virtual Environment

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 5. Install Dependencies

```bash
pip install streamlit langchain langchain-community faiss-cpu python-dotenv pypdf
```

---

## 6. Start Ollama Server

Ollama must be running before starting the application.

Option 1: Open the Ollama desktop application

Option 2: Run in terminal

```bash
ollama run llama3
```

Ollama runs at:

```
http://localhost:11434
```

Verify server:

```bash
ollama list
```

---

## 7. Run the Application

From project root:

```bash
streamlit run frontend.py
```

Open in browser:

```
http://localhost:8501
```

---

## Project Structure

```
RAG-CHATBOT/
│
├── frontend.py
├── rag_pipeline.py
├── vector_database.py
├── pdfs/
├── vectorstore/
└── .venv/
```

---

## Troubleshooting

### Connection Refused (localhost:11434)

Cause:
Ollama is not running.

Solution:
Start Ollama before running Streamlit.

---

### Model Not Found

Cause:
Required model not pulled.

Solution:

```bash
ollama pull <model-name>
```

---

## Notes

- All embeddings and LLM inference run locally.
- No external API keys required.
- First run may take longer due to model loadi
