"""
Generation Service
──────────────────
Responsible for:
  1. Building prompts from retrieved context.
  2. Streaming / non-streaming calls to Groq LLM.
  3. Parsing structured response (answer + confidence hint).
  4. Multi-turn conversation history management.

WHY separated?  The generation strategy (model, prompt, streaming) can
change independently of retrieval or ingestion logic.
"""
import logging
import time
from typing import List, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from app.config import GROQ_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)

# ── Prompt ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an AI Legal Assistant specialised in helping users understand legal documents.

Guidelines:
- Answer ONLY from the provided CONTEXT. Do not fabricate information.
- If the context does not contain enough information, say clearly: "I don't have enough information in the provided documents to answer this question."
- Cite the source document and page number when available (e.g., "According to [filename], page X...").
- Keep answers concise, plain-language, and actionable.
- Do NOT provide personal legal advice. Recommend consulting a qualified lawyer for serious matters.
- After your answer, rate your own confidence as: [Confidence: High | Medium | Low]
"""

HUMAN_TEMPLATE = """CONTEXT (retrieved from legal documents):
{context}

---

USER QUESTION: {question}

Please answer based strictly on the context above.
"""


def _build_context_string(retrieved_docs: List[dict]) -> str:
    """Format retrieved chunks into a numbered context block with citations."""
    if not retrieved_docs:
        return "No relevant document sections found."

    parts = []
    for i, doc in enumerate(retrieved_docs, 1):
        source = doc.get("source", "unknown")
        page = doc.get("page")
        page_str = f", page {page}" if page is not None else ""
        score = doc.get("score", 0)
        parts.append(
            f"[{i}] Source: {source}{page_str} (relevance score: {score:.3f})\n"
            f"{doc['content']}"
        )
    return "\n\n---\n\n".join(parts)


def _parse_confidence(response_text: str) -> str:
    """Extract confidence tag from LLM output."""
    text_lower = response_text.lower()
    if "[confidence: high]" in text_lower:
        return "High"
    elif "[confidence: medium]" in text_lower:
        return "Medium"
    elif "[confidence: low]" in text_lower:
        return "Low"
    # Fallback: estimate from response keywords
    if "i don't have enough information" in text_lower or "i cannot find" in text_lower:
        return "Low"
    return "Medium"


# ── Session Memory ────────────────────────────────────────────────────────────

class ConversationSession:
    """
    Maintains multi-turn conversation history per session.
    WHY: Stateless single-shot queries lose context between follow-ups.
    This enables coherent, context-aware legal conversations.
    """

    MAX_HISTORY = 10  # Keep last 10 turns to avoid context overflow

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: List[dict] = []
        logger.debug("New ConversationSession: %s", session_id)

    def add_turn(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        # Trim to max history
        if len(self.history) > self.MAX_HISTORY * 2:
            self.history = self.history[-(self.MAX_HISTORY * 2):]

    def get_messages(self) -> List:
        """Convert history to LangChain message objects."""
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        for turn in self.history:
            if turn["role"] == "user":
                messages.append(HumanMessage(content=turn["content"]))
            else:
                messages.append(AIMessage(content=turn["content"]))
        return messages

    def clear(self) -> None:
        self.history = []
        logger.info("Session %s cleared.", self.session_id)


# In-memory session store (replace with Redis for production multi-instance)
_sessions: dict[str, ConversationSession] = {}


def get_session(session_id: str) -> ConversationSession:
    if session_id not in _sessions:
        _sessions[session_id] = ConversationSession(session_id)
    return _sessions[session_id]


def clear_session(session_id: str) -> None:
    if session_id in _sessions:
        _sessions[session_id].clear()


# ── Public API ────────────────────────────────────────────────────────────────

def generate_answer(
    query: str,
    retrieved_docs: List[dict],
    session_id: Optional[str] = None,
) -> dict:
    """
    Generate an LLM response given a query and retrieved context.

    Returns:
    {
      "answer": str,
      "confidence": str,          # "High" | "Medium" | "Low"
      "sources": List[dict],      # attributed source chunks
      "latency_ms": float,
      "model": str,
    }
    """
    if not GROQ_API_KEY:
        raise EnvironmentError("GROQ_API_KEY is not set. Check your .env file.")

    llm = ChatGroq(model=LLM_MODEL, api_key=GROQ_API_KEY, temperature=0.1)

    context_str = _build_context_string(retrieved_docs)
    human_message_content = HUMAN_TEMPLATE.format(
        context=context_str, question=query
    )

    # Build message list (with history if session provided)
    if session_id:
        session = get_session(session_id)
        session.add_turn("user", query)
        messages = session.get_messages()
        # Replace last HumanMessage with the enriched one (context + question)
        messages[-1] = HumanMessage(content=human_message_content)
    else:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=human_message_content),
        ]

    t0 = time.perf_counter()
    try:
        response = llm.invoke(messages)
        answer_text = response.content
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    # Store AI turn in session
    if session_id:
        session.add_turn("assistant", answer_text)

    confidence = _parse_confidence(answer_text)

    logger.info(
        "Generated answer [session=%s, confidence=%s, latency=%.0fms]",
        session_id, confidence, latency_ms,
    )

    return {
        "answer": answer_text,
        "confidence": confidence,
        "sources": [
            {
                "file": d.get("source", "unknown"),
                "page": d.get("page"),
                "score": d.get("score"),
                "excerpt": d["content"][:200] + "..." if len(d["content"]) > 200 else d["content"],
            }
            for d in retrieved_docs
        ],
        "latency_ms": latency_ms,
        "model": LLM_MODEL,
    }
