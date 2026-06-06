# Example document

This folder provides a **real, public document** for trying the app and capturing
the README screenshots — so the demo uses genuine data, not fabricated content
(see `CLAUDE.md` §5).

## The document
**"Attention Is All You Need"** — Vaswani et al., 2017 · arXiv:1706.03762
<https://arxiv.org/abs/1706.03762>

It is the foundational paper behind the Transformer architecture, which makes it a
fitting test for a retrieval-augmented question-answering tool.

## How to get it
The PDF is **not committed** to this repository (to avoid redistributing a
third-party paper). Download it locally with:

```bash
python examples/download_example.py
```

This saves `examples/attention-is-all-you-need.pdf`.

## Try it
Run the app (`streamlit run app.py`), upload the downloaded PDF, click
**Process documents**, then ask, for example:

- "What is the Transformer architecture?"
- "What is multi-head attention?"
- "What datasets were used for evaluation?"

The credit for the document belongs to its original authors; it is used here purely
as example input.
