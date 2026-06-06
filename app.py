"""
RAG-Powered Document Assistant
--------------------------------
Upload PDF documents and ask questions about them in natural language.
The app retrieves the most relevant passages (vector search) and uses an
LLM to generate a grounded, cited answer.

Pipeline:  PDF -> text chunks -> embeddings -> vector search -> LLM answer

Author: Abin Oommen Thomas
"""

import os
import numpy as np
import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
EMBED_MODEL = "all-MiniLM-L6-v2"   # small, fast, runs on CPU (~80 MB)
CHUNK_SIZE = 800                    # characters per chunk
CHUNK_OVERLAP = 120                # overlap keeps context across chunks
TOP_K = 4                          # passages retrieved per question

# --- LLM provider: Groq (free, OpenAI-compatible) ---
LLM_BASE_URL = "https://api.groq.com/openai/v1"
LLM_MODEL = "llama-3.3-70b-versatile"   # free Groq model; change if you like

st.set_page_config(page_title="RAG Document Assistant", page_icon="📄")


# ---------------------------------------------------------------------------
# Cached resources
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading embedding model...")
def load_embedder():
    return SentenceTransformer(EMBED_MODEL)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------
def extract_text(uploaded_files):
    """Read all uploaded PDFs into one big string."""
    text = ""
    for f in uploaded_files:
        reader = PdfReader(f)
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
    return text


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks so context isn't lost at edges."""
    chunks, start = [], 0
    text = " ".join(text.split())  # normalise whitespace
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


def build_index(chunks, embedder):
    """Embed every chunk once and L2-normalise for cosine similarity."""
    vecs = embedder.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
    vecs = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-10)
    return vecs


def retrieve(question, chunks, index, embedder, k=TOP_K):
    """Return the k most similar chunks to the question."""
    q = embedder.encode([question], convert_to_numpy=True)[0]
    q = q / (np.linalg.norm(q) + 1e-10)
    scores = index @ q                       # cosine similarity
    top = np.argsort(scores)[::-1][:k]
    return [chunks[i] for i in top], [float(scores[i]) for i in top]


def answer_question(client, question, contexts):
    """Ask the LLM to answer using ONLY the retrieved context."""
    context_block = "\n\n---\n\n".join(
        f"[Source {i+1}]\n{c}" for i, c in enumerate(contexts)
    )
    prompt = (
        "You are a helpful assistant. Answer the question using ONLY the "
        "context below. If the answer is not in the context, say you don't "
        "know. Cite sources as [Source N].\n\n"
        f"Context:\n{context_block}\n\nQuestion: {question}\n\nAnswer:"
    )
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("📄 RAG Document Assistant")
st.caption("Upload PDFs and ask questions — answers are grounded in your documents.")

with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("Groq API key", type="password",
                            value=os.getenv("GROQ_API_KEY", ""))
    uploaded = st.file_uploader("Upload PDF(s)", type="pdf",
                                accept_multiple_files=True)
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
            contexts, scores = retrieve(question, st.session_state.chunks,
                                        st.session_state.index, embedder)
            with st.spinner("Thinking..."):
                answer = answer_question(client, question, contexts)
            st.chat_message("user").write(question)
            st.chat_message("assistant").write(answer)
            with st.expander("🔎 Retrieved sources"):
                for i, (c, s) in enumerate(zip(contexts, scores)):
                    st.markdown(f"**Source {i+1}** (similarity {s:.2f})")
                    st.write(c)
else:
    st.info("👈 Upload PDFs and click **Process documents** to begin.")
