"""Shared test fixtures.

These fakes stand in for the two EXTERNAL boundaries only (the embedding model
and the LLM client), per CLAUDE.md section 4. The logic under test (chunking,
indexing, retrieval, prompt building) is never mocked.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

# Make the project root importable so `import core` works from tests/.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIXTURES = Path(__file__).parent / "fixtures"

# A tiny fixed vocabulary lets the fake embedder produce deterministic,
# inspectable vectors (bag-of-words counts) so retrieval ordering is predictable.
VOCAB = ["apple", "banana", "cherry", "date"]


class FakeEmbedder:
    """Deterministic bag-of-words embedder over a fixed vocabulary.

    Mirrors the SentenceTransformer interface used by core: an ``encode`` method
    accepting ``convert_to_numpy`` / ``show_progress_bar`` keyword arguments.
    """

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        vecs = []
        for t in texts:
            words = t.lower().split()
            vecs.append([float(words.count(term)) for term in VOCAB])
        return np.array(vecs, dtype=float)


class FakeChatCompletions:
    """Records the last call and returns a canned, OpenAI-shaped response."""

    def __init__(self, reply="canned answer"):
        self.reply = reply
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        message = SimpleNamespace(content=self.reply)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class FakeClient:
    """Minimal stand-in for an OpenAI-compatible client."""

    def __init__(self, reply="canned answer"):
        self.chat = SimpleNamespace(completions=FakeChatCompletions(reply))


@pytest.fixture
def embedder():
    return FakeEmbedder()


@pytest.fixture
def fake_client():
    return FakeClient(reply="The answer is 42. [Source 1]")


@pytest.fixture
def sample_pdf_path():
    return str(FIXTURES / "sample.pdf")
