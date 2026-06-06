# 🗺️ ROADMAP — RAG-Powered Document Assistant

Cumulative progress toward the **10/10 portfolio-grade** bar (see `CLAUDE.md` §13).
Each slice is one coherent change = one commit. Tick + update % + note commit hash when green.

---

## Milestones

- [x] 0.1 Scaffold app + env + requirements .............. 8%  (commit b9caa58)
- [x] 0.2 Working RAG pipeline (PDF→chunks→embed→retrieve→LLM) 16% (commit b9caa58)
- [x] 0.3 Switch LLM to free Groq provider ............... 20%  (commit b9caa58)
- [x] 0.4 Git init, clean history, push to GitHub ........ 24%  (pushed)
- [x] 0.5 Add CLAUDE.md rules + handoff report ........... 28%  (commits 79c0078, f6eca49)
- [x] 0.6 ROADMAP.md ..................................... 30%  (this slice)
- [x] 1.0 Extract core RAG logic into a testable module .. 36%  (commit 08e0155)
- [x] 1.1 Unit tests for core (chunking, retrieval) ...... 46%  (commit 2159a7a)
- [x] 1.2 Edge/negative tests + LLM-boundary mock ........ 54%  (commit 2159a7a)
- [ ] 2.0 CI/CD pipeline (ruff, mypy, bandit, pip-audit, pytest, gitleaks, Trivy, CodeQL) 66%
- [ ] 2.1 Dependabot config ............................. 68%
- [ ] 3.0 Replace fake sample data with a REAL document .. 74%
- [ ] 3.1 Capture ≥4 real-run screenshots ............... 78%
- [ ] 4.0 Mermaid diagrams (architecture, DFD, sequence) . 84%
- [ ] 5.0 Rebuild README to canonical 21-section structure 92%
- [ ] 5.1 docs/JOURNAL.md + docs/TECHNICAL_REPORT.md ..... 98%
- [ ] 6.0 (Optional) Deploy live demo on Streamlit Cloud . 100%

---

## 🐞 Known issues
- `sample_document.pdf` is fabricated data — violates §5; must be replaced before portfolio use.
- No CI/CD pipeline yet (§6).
- README not yet in canonical 21-section form (§7a).
- GitHub repo name has a leading hyphen (`-rag-document-assistant`) — rename pending.

## ⏭️ Next
**Slice 2.0** — add the canonical CI/CD pipeline (§6): GitHub Actions running ruff,
ruff format check, mypy, bandit, pip-audit, pytest, plus gitleaks, Trivy and CodeQL, with
a Dependabot config. Must run on push + PR and be green.

## ✍️ TODO: my words
*(Abin — your own notes on priorities, scope, and what "done" means to you go here.)*
