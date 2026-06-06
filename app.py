"""
RAG-Powered Document Assistant — Streamlit UI.

Thin presentation layer. All the RAG logic lives in ``core.py`` so it can be
unit-tested without the Streamlit runtime.

Author: Abin Oommen Thomas
"""

import os

import streamlit as st
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from core import (
    EMBED_MODEL,
    LLM_BASE_URL,
    answer_question,
    build_index,
    chunk_text,
    extract_text,
    retrieve,
)

st.set_page_config(page_title="RAG Document Assistant", page_icon="📄")


@st.cache_resource(show_spinner="Loading embedding model...")
def load_embedder() -> SentenceTransformer:
    """Load (and cache) the sentence-transformer embedding model."""
    return SentenceTransformer(EMBED_MODEL)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("📄 RAG Document Assistant")
st.caption("Upload PDFs and ask questions — answers are grounded in your documents.")

with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input(
        "Groq API key", type="password", value=os.getenv("GROQ_API_KEY", "")
    )
    uploaded = st.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True)
    process = st.button("📥 Process documents", use_container_width=True)

embedder = load_embedder()

if process and uploaded:
    with st.spinner("Reading & indexing documents..."):
        raw = extract_text(uploaded)
        chunks = chunk_text(raw)
        index = build_index(chunks, embedder)
        st.session_state.update(chunks=chunks, index=index)
    st.success(f"Indexed {len(chunks)} chunks from {len(uploaded)} file(s). Ask away!")

if "chunks" in st.session_state:
    question = st.chat_input("Ask a question about your documents...")
    if question:
        if not api_key:
            st.error("Please enter your Groq API key in the sidebar.")
        else:
            client = OpenAI(api_key=api_key, base_url=LLM_BASE_URL)
            contexts, scores = retrieve(
                question, st.session_state.chunks, st.session_state.index, embedder
            )
            with st.spinner("Thinking..."):
                answer = answer_question(client, question, contexts)
            st.chat_message("user").write(question)
            st.chat_message("assistant").write(answer)
            with st.expander("🔎 Retrieved sources"):
                for i, (c, s) in enumerate(zip(contexts, scores, strict=True)):
                    st.markdown(f"**Source {i + 1}** (similarity {s:.2f})")
                    st.write(c)
else:
    st.info("👈 Upload PDFs and click **Process documents** to begin.")
