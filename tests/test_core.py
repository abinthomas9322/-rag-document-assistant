"""Unit tests for the core RAG logic.

Covers the happy path plus edge/negative cases for every pure function, and
mocks only the external boundaries (embedder, LLM client). See CLAUDE.md s4.
"""

import numpy as np
import pytest

import core


# ---------------------------------------------------------------------------
# chunk_text
# ---------------------------------------------------------------------------
class TestChunkText:
    def test_short_text_is_single_chunk(self):
        assert core.chunk_text("hello world", size=100, overlap=10) == ["hello world"]

    def test_normalises_whitespace(self):
        # Collapsed whitespace means the messy input fits in one clean chunk.
        assert core.chunk_text("a\n\n  b\t c", size=100, overlap=0) == ["a b c"]

    def test_splits_into_expected_number_of_chunks(self):
        text = "x" * 1000
        chunks = core.chunk_text(text, size=400, overlap=0)
        assert chunks == ["x" * 400, "x" * 400, "x" * 200]

    def test_overlap_shares_characters_between_chunks(self):
        text = "abcdefghij"  # 10 chars
        chunks = core.chunk_text(text, size=5, overlap=2)
        # step = size - overlap = 3 -> starts at 0, 3, 6, 9
        assert chunks == ["abcde", "defgh", "ghij", "j"]
        # the overlap is real: end of chunk 0 overlaps start of chunk 1
        assert chunks[0][-2:] == chunks[1][:2]

    @pytest.mark.parametrize("text", ["", "   ", "\n\t  \n"])
    def test_empty_or_whitespace_yields_no_chunks(self, text):
        assert core.chunk_text(text) == []

    def test_invalid_size_raises(self):
        with pytest.raises(ValueError):
            core.chunk_text("hello", size=0)

    @pytest.mark.parametrize("overlap", [-1, 5, 6])
    def test_invalid_overlap_raises(self, overlap):
        with pytest.raises(ValueError):
            core.chunk_text("hello", size=5, overlap=overlap)


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------
class TestBuildIndex:
    def test_returns_one_row_per_chunk(self, embedder):
        chunks = ["apple apple", "banana", "cherry date"]
        index = core.build_index(chunks, embedder)
        assert index.shape[0] == len(chunks)

    def test_vectors_are_unit_normalised(self, embedder):
        chunks = ["apple apple banana", "cherry", "date date date"]
        index = core.build_index(chunks, embedder)
        norms = np.linalg.norm(index, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6)


# ---------------------------------------------------------------------------
# retrieve
# ---------------------------------------------------------------------------
class TestRetrieve:
    def test_returns_most_similar_chunk_first(self, embedder):
        chunks = ["apple apple", "banana banana", "cherry cherry"]
        index = core.build_index(chunks, embedder)
        contexts, scores = core.retrieve("apple", chunks, index, embedder, k=3)
        assert contexts[0] == "apple apple"
        # scores come back in descending order
        assert scores == sorted(scores, reverse=True)

    def test_k_limits_number_of_results(self, embedder):
        chunks = ["apple", "banana", "cherry", "date"]
        index = core.build_index(chunks, embedder)
        contexts, scores = core.retrieve("apple", chunks, index, embedder, k=2)
        assert len(contexts) == 2
        assert len(scores) == 2


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------
class TestBuildPrompt:
    def test_includes_question_and_contexts(self):
        prompt = core.build_prompt("What colour?", ["the sky is blue", "grass green"])
        assert "What colour?" in prompt
        assert "the sky is blue" in prompt
        assert "grass green" in prompt

    def test_numbers_each_source(self):
        prompt = core.build_prompt("q", ["first", "second"])
        assert "[Source 1]" in prompt
        assert "[Source 2]" in prompt

    def test_instructs_to_avoid_hallucination(self):
        prompt = core.build_prompt("q", ["ctx"])
        assert "don't know" in prompt.lower()


# ---------------------------------------------------------------------------
# answer_question  (LLM boundary mocked)
# ---------------------------------------------------------------------------
class TestAnswerQuestion:
    def test_returns_model_reply(self, fake_client):
        out = core.answer_question(fake_client, "q?", ["some context"])
        assert out == "The answer is 42. [Source 1]"

    def test_passes_model_and_grounded_prompt_to_client(self, fake_client):
        core.answer_question(fake_client, "What is X?", ["X is Y"], model="my-model")
        kwargs = fake_client.chat.completions.last_kwargs
        assert kwargs["model"] == "my-model"
        sent = kwargs["messages"][0]["content"]
        assert "What is X?" in sent
        assert "X is Y" in sent


# ---------------------------------------------------------------------------
# extract_text  (real PDF fixture)
# ---------------------------------------------------------------------------
class TestExtractText:
    def test_extracts_text_from_real_pdf(self, sample_pdf_path):
        text = core.extract_text([sample_pdf_path])
        assert "UNIQUETOKEN_XYZ789" in text

    def test_multiple_files_are_concatenated(self, sample_pdf_path):
        text = core.extract_text([sample_pdf_path, sample_pdf_path])
        assert text.count("UNIQUETOKEN_XYZ789") == 2
