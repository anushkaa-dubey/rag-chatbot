```md
# RAG Chatbot (Groq + Ollama + FAISS)

This project is a **Retrieval-Augmented Generation (RAG) chatbot** built using:
- **Groq API** for fast LLM inference
- **Ollama** for local embeddings
- **FAISS** as the vector database
- **Streamlit** for the frontend UI

---

## 📁 Project Structure
```

RAG-CHATBOT/
│
├── frontend.py          # Streamlit UI
├── rag_pipeline.py      # RAG logic (retrieval + LLM)
├── vector_database.py   # PDF loading, chunking, FAISS
├── pdfs/                # Uploaded PDFs
├── .env                 # API keys (ignored by git)
├── .gitignore
└── README.md

````

---

## ⚙️ Prerequisites
- Python **3.10+**
- Git
- Internet connection (for Groq API)
- Ollama installed locally

---

## 🛠️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/anushkaa-dubey/rag-chatbot.git
cd rag-chatbot
````

---

### 2️⃣ Create and activate virtual environment (recommended)

```bash
python -m venv .venv
```

**Windows**

```bash
.venv\Scripts\activate
```

**Mac/Linux**

```bash
source .venv/bin/activate
```

---

### 3️⃣ Install dependencies

```bash
pip install streamlit langchain langchain-groq langchain-community langchain-ollama faiss-cpu python-dotenv pdfplumber
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY="your_groq_api_key_here"
```

⚠️ `.env` is ignored by git for security reasons.

---

## 🤖 Ollama Setup (Local Embeddings)

### Install Ollama

Download from 👉 [https://ollama.com](https://ollama.com)

### Start Ollama server

```bash
ollama serve
```

### Pull embedding model

```bash
ollama pull deepseek-r1:1.5b
```

---

## ▶️ Run the Application

Open a **new terminal** (with venv activated):

```bash
python -m streamlit run frontend.py
```

Then open in browser:

```
http://localhost:8501
```

---

## 🧠 How the RAG Pipeline Works

1. User uploads a PDF
2. PDF is split into chunks
3. Chunks are embedded **locally using Ollama**
4. Embeddings are stored in **FAISS**
5. User query retrieves relevant chunks
6. Context + query sent to **Groq LLM**
7. Answer displayed in Streamlit UI

---

## ⚠️ Important Notes

* FAISS index is static unless rebuilt after a new PDF upload
* Groq is used **only for generation**, not embeddings
* Ollama must be running before querying
* API keys should never be hardcoded

---

## 🚀 Future Improvements

* Rebuild FAISS index on every PDF upload
* Multi-PDF support
* Source citations in answers
* Better prompt tuning

---

## 👩‍💻 Author

**Anushkaa Dubey**

---

## 📜 License

This project is for educational and hackathon purposes only.

````

---

### ✅ Final step (don’t forget)
```bash
git add README.md
git commit -m "Add README with setup instructions"
git push
````

