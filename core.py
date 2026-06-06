"""
Core RAG logic — pure, UI-free, and unit-testable.

This module holds the Retrieval-Augmented Generation pipeline functions with no
dependency on Streamlit, so they can be imported and tested in isolation:

    PDF text -> chunks -> embeddings -> vector search -> LLM answer

The embedding model and the LLM client are passed in as arguments (dependency
injection) so tests can substitute lightweight fakes for these external
boundaries (see CLAUDE.md sections 4 and 9).

Author: Abin Oommen Thomas
"""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np
from pypdf import PdfReader

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
EMBED_MODEL = "all-MiniLM-L6-v2"   # small, fast, runs on CPU (~80 MB)
CHUNK_SIZE = 800                   # characters per chunk
CHUNK_OVERLAP = 120                # overlap keeps context across chunks
TOP_K = 4                          # passages retrieved per question

# --- LLM provider: Groq (free, OpenAI-compatible) ---
LLM_BASE_URL = "https://api.groq.com/openai/v1"
LLM_MODEL = "llama-3.3-70b-versatile"   # free Groq model; change if you like


def extract_text(uploaded_files: Iterable[Any]) -> str:
    """Read all uploaded PDFs into one combined string.

    Args:
        uploaded_files: An iterable of file paths or file-like objects that
            ``pypdf.PdfReader`` can open.

    Returns:
        The concatenated text of every page, one page per newline.
    """
    text = ""
    for f in uploaded_files:
        reader = PdfReader(f)
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
    return text


def chunk_text(
    text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """Split text into overlapping chunks so context isn't lost at edges.

    Whitespace is normalised first. Chunks are ``size`` characters long and each
    starts ``size - overlap`` characters after the previous one. Empty/whitespace
    chunks are dropped.

    Args:
        text: The source text.
        size: Chunk length in characters (must be > 0).
        overlap: Characters shared between consecutive chunks (0 <= overlap < size).

    Returns:
        A list of non-empty text chunks.

    Raises:
        ValueError: If ``size <= 0`` or ``overlap`` is out of range.
    """
    if size <= 0:
        raise ValueError("size must be greater than 0")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must satisfy 0 <= overlap < size")

    chunks: list[str] = []
    text = " ".join(text.split())  # normalise whitespace
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


def build_index(chunks: list[str], embedder: Any) -> np.ndarray:
    """Embed every chunk and L2-normalise the vectors for cosine similarity.

    Args:
        chunks: The text chunks to embed.
        embedder: Any object with an ``encode(list[str], convert_to_numpy=True,
            show_progress_bar=False) -> np.ndarray`` method.

    Returns:
        A 2-D array of unit-length embedding vectors, one row per chunk.
    """
    vecs = embedder.encode(
        chunks, convert_to_numpy=True, show_progress_bar=False
    )
    vecs = np.asarray(vecs, dtype=float)
    vecs = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-10)
    return vecs


def retrieve(
    question: str,
    chunks: list[str],
    index: np.ndarray,
    embedder: Any,
    k: int = TOP_K,
) -> tuple[list[str], list[float]]:
    """Return the ``k`` chunks most similar to the question.

    Args:
        question: The user's question.
        chunks: The chunk texts (aligned row-for-row with ``index``).
        index: Unit-normalised chunk embeddings from :func:`build_index`.
        embedder: The same embedder interface used in :func:`build_index`.
        k: Number of chunks to return.

    Returns:
        A tuple ``(top_chunks, scores)`` ordered from most to least similar.
    """
    q = embedder.encode([question], convert_to_numpy=True)[0]
    q = np.asarray(q, dtype=float)
    q = q / (np.linalg.norm(q) + 1e-10)
    scores = index @ q                       # cosine similarity
    top = np.argsort(scores)[::-1][:k]
    return [chunks[i] for i in top], [float(scores[i]) for i in top]


def build_prompt(question: str, contexts: list[str]) -> str:
    """Build the grounded RAG prompt from a question and retrieved contexts.

    Kept separate from the LLM call so the prompt construction can be tested
    without touching the network.
    """
    context_block = "\n\n---\n\n".join(
        f"[Source {i + 1}]\n{c}" for i, c in enumerate(contexts)
    )
    return (
        "You are a helpful assistant. Answer the question using ONLY the "
        "context below. If the answer is not in the context, say you don't "
        "know. Cite sources as [Source N].\n\n"
        f"Context:\n{context_block}\n\nQuestion: {question}\n\nAnswer:"
    )


def answer_question(
    client: Any, question: str, contexts: list[str], model: str = LLM_MODEL
) -> str:
    """Ask the LLM to answer using ONLY the retrieved context.

    Args:
        client: An OpenAI-compatible client with
            ``chat.completions.create(...)``.
        question: The user's question.
        contexts: The retrieved chunks to ground the answer in.
        model: The chat model id to use.

    Returns:
        The model's answer text.
    """
    prompt = build_prompt(question, contexts)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return resp.choices[0].message.content
