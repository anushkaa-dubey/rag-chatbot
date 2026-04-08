"""
RAG Legal Assistant — Streamlit Frontend v2
────────────────────────────────────────────
Features:
  • Dynamic PDF upload → live ingestion via API
  • Multi-turn conversation with session memory
  • Source attribution panel with expandable excerpts
  • Confidence badge per answer
  • Latency & document stats in sidebar
  • Clear session button
  • Graceful error messages for all failure scenarios
"""
import time
import uuid

import requests
import streamlit as st

# ── Configuration ─────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="AI Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State Init ────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # [{"role": user/assistant, "content": ..., "meta": {...}}]
if "ingested_docs" not in st.session_state:
    st.session_state.ingested_docs = []


# ── Helper Functions ──────────────────────────────────────────────────────────

def check_api_health() -> dict | None:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def ingest_pdf_via_api(uploaded_file) -> dict | None:
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        r = requests.post(f"{API_BASE}/ingest", files=files, timeout=120)
        if r.status_code == 200:
            return r.json()
        st.error(f"Ingestion error ({r.status_code}): {r.json().get('detail', 'Unknown error')}")
    except requests.ConnectionError:
        st.error("⚠️ Cannot connect to the backend API. Make sure `run_api.py` is running.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    return None


def query_api(question: str, top_k: int = 5) -> dict | None:
    try:
        payload = {
            "question": question,
            "session_id": st.session_state.session_id,
            "top_k": top_k,
        }
        r = requests.post(f"{API_BASE}/query", json=payload, timeout=60)
        if r.status_code == 200:
            return r.json()
        detail = r.json().get("detail", "Unknown error")
        st.error(f"Query error ({r.status_code}): {detail}")
    except requests.ConnectionError:
        st.error("⚠️ Cannot connect to the backend API. Make sure `run_api.py` is running.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    return None


def fetch_documents() -> list:
    try:
        r = requests.get(f"{API_BASE}/documents", timeout=5)
        if r.status_code == 200:
            return r.json().get("documents", [])
    except Exception:
        pass
    return []


def clear_session_via_api():
    try:
        requests.delete(f"{API_BASE}/session/{st.session_state.session_id}", timeout=5)
    except Exception:
        pass
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []


def confidence_badge(confidence: str) -> str:
    colors = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    return f"{colors.get(confidence, '⚪')} Confidence: **{confidence}**"


# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    .main-header h1 {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #a18cd1, #fbc2eb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: #b8b8d1;
        font-size: 1.05rem;
    }
    .chat-user {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 16px 16px 4px 16px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        color: white;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-assistant {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px 16px 16px 4px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        color: #e8e8f0;
        max-width: 90%;
        backdrop-filter: blur(10px);
    }
    .source-card {
        background: rgba(255,255,255,0.05);
        border-left: 3px solid #764ba2;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        margin: 0.3rem 0;
        font-size: 0.88rem;
        color: #c8c8e0;
    }
    .metric-card {
        background: rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 0.8rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .stTextArea textarea {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: white !important;
    }
    div[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.85) !important;
        border-right: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ Legal Assistant")
    st.markdown("---")

    # API Health
    health = check_api_health()
    if health:
        st.success(f"✅ API Online — {health['documents_loaded']} doc(s) loaded")
    else:
        st.error("❌ API Offline — Start `run_api.py`")
        st.info("Run in a separate terminal:\n```\npython run_api.py\n```")

    st.markdown("---")
    st.markdown("### 📄 Upload Legal Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF(s)",
        type="pdf",
        accept_multiple_files=True,
        key="pdf_uploader",
        label_visibility="collapsed",
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.ingested_docs:
                with st.spinner(f"Ingesting `{uploaded_file.name}`..."):
                    result = ingest_pdf_via_api(uploaded_file)
                    if result:
                        if result["status"] == "success":
                            st.success(
                                f"✅ `{result['filename']}`\n"
                                f"Pages: {result['pages']} | Chunks: {result['chunks']} | "
                                f"Time: {result['ingestion_time_s']}s"
                            )
                            st.session_state.ingested_docs.append(uploaded_file.name)
                        elif result["status"] == "skipped":
                            st.info(f"⏭️ Already ingested: `{result['filename']}`")
                            st.session_state.ingested_docs.append(uploaded_file.name)

    # List ingested docs
    docs = fetch_documents()
    if docs:
        st.markdown("**Currently in vector store:**")
        for d in docs:
            st.markdown(f"- 📑 `{d}`")

    st.markdown("---")
    top_k = st.slider("Retrieval chunks (top-k)", min_value=1, max_value=10, value=5)

    st.markdown("---")
    st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        clear_session_via_api()
        st.rerun()

    st.markdown("---")
    st.markdown("**Disclaimer:** This tool provides general legal information, not legal advice. Always consult a qualified lawyer for serious matters.")


# ── Main Panel ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>⚖️ AI Legal Assistant</h1>
  <p>Upload legal documents and ask questions in plain language</p>
</div>
""", unsafe_allow_html=True)

# Render chat history
chat_container = st.container()
with chat_container:
    for turn in st.session_state.chat_history:
        if turn["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(turn["content"])
        else:
            with st.chat_message("assistant", avatar="⚖️"):
                st.markdown(turn["content"])
                meta = turn.get("meta", {})
                if meta:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.caption(confidence_badge(meta.get("confidence", "Unknown")))
                    with col2:
                        st.caption(f"⏱️ {meta.get('latency_ms', '?')} ms | 🤖 {meta.get('model', '?')}")

                    sources = meta.get("sources", [])
                    if sources:
                        with st.expander(f"📚 View {len(sources)} Source(s)", expanded=False):
                            for s in sources:
                                page_str = f", page {s['page']}" if s.get("page") is not None else ""
                                score_str = f" (score: {s['score']:.3f})" if s.get("score") else ""
                                st.markdown(
                                    f'<div class="source-card">'
                                    f'<strong>📄 {s["file"]}{page_str}{score_str}</strong><br>'
                                    f'{s["excerpt"]}'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

# Input area
st.markdown("---")
user_question = st.chat_input("Ask your legal question here... (e.g. 'What are my tenant rights?')")

if user_question:
    user_question = user_question.strip()
    if not user_question:
        st.warning("Please enter a valid question.")
    elif not fetch_documents() and not st.session_state.ingested_docs:
        st.warning("⚠️ Please upload at least one legal document before asking questions.")
    else:
        # Display user message immediately
        st.session_state.chat_history.append({"role": "user", "content": user_question})

        with st.spinner("🔍 Searching documents and generating answer..."):
            result = query_api(user_question, top_k=top_k)

        if result:
            answer = result.get("answer", "No answer returned.")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "meta": {
                    "confidence": result.get("confidence", "Unknown"),
                    "sources": result.get("sources", []),
                    "latency_ms": result.get("latency_ms"),
                    "model": result.get("model"),
                },
            })

        st.rerun()
