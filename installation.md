# 🧠 RAG Chatbot (Local Setup – Ollama Only)

This project is a **RAG-based chatbot** built with:

* Streamlit (UI)
* LangChain
* FAISS (Vector DB)
* Ollama (Local LLM + Embeddings)

⚠️ This project uses **Ollama only** (no OpenAI API required).

---

# ✅ 1️⃣ Prerequisites

* Python 3.10 or 3.11
* Ollama installed
* 8GB+ RAM recommended

---

# 🦙 2️⃣ Install Ollama

Download and install:

👉 [https://ollama.com/download](https://ollama.com/download)

Verify installation:

```bash
ollama --version
```

---

# 📥 3️⃣ Pull Required Models

For embeddings:

```bash
ollama pull nomic-embed-text
```

For LLM:

```bash
ollama pull llama3
```

(Replace model names if different in code.)

---

# 🐍 4️⃣ Setup Python Environment

From project root:

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

# 📦 5️⃣ Install Dependencies

```bash
pip install streamlit langchain langchain-community faiss-cpu python-dotenv pypdf
```

---

# ▶ 6️⃣ Start Ollama Server

Ollama must be running before launching the app.

Run:

```bash
ollama run llama3
```

OR open the Ollama desktop app.

Default server runs at:

```
http://localhost:11434
```

---

# 🚀 7️⃣ Run The Application

```bash
streamlit run frontend.py
```

Open:

```
http://localhost:8501
```

---

# ⚠️ Common Error

### Error:

```
Connection refused on localhost:11434
```

### Fix:

Ollama is not running. Start it first.

---
