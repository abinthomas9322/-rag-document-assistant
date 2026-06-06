# Architecture

Diagrams for the RAG Document Assistant, derived directly from the code
(`app.py` and `core.py`). They render natively on GitHub.

There is **no entity-relationship diagram**: the app holds no database — indexed
chunks and their embeddings live only in Streamlit's per-session state.

---

## 1. Component architecture

How the UI layer, the core logic, and external libraries/services fit together.

```mermaid
flowchart TB
    subgraph UI["app.py — Streamlit UI"]
        upload["File uploader"]
        process["Process documents button"]
        chat["Chat input"]
        cache["load_embedder() cached"]
        session[("st.session_state:<br/>chunks + index")]
    end

    subgraph Core["core.py — RAG logic"]
        extract["extract_text()"]
        chunk["chunk_text()"]
        build["build_index()"]
        retrieve["retrieve()"]
        prompt["build_prompt()"]
        answer["answer_question()"]
    end

    subgraph Ext["External libraries & services"]
        pypdf["pypdf"]
        model["sentence-transformers<br/>all-MiniLM-L6-v2"]
        numpy["NumPy<br/>cosine similarity"]
        groq["Groq LLM<br/>OpenAI-compatible API"]
    end

    upload --> extract
    process --> extract --> chunk --> build --> session
    cache --> build
    extract --> pypdf
    build --> model
    build --> numpy
    chat --> retrieve
    session --> retrieve
    cache --> retrieve
    retrieve --> numpy
    retrieve --> prompt --> answer --> groq
```

---

## 2. Data-flow diagram (DFD)

How a document and a question flow through the system.

```mermaid
flowchart LR
    user(["User"])
    pdf[/"PDF file"/]

    user -->|uploads| pdf
    pdf --> P1["extract_text"]
    P1 -->|raw text| P2["chunk_text"]
    P2 -->|chunks| P3["build_index embed"]
    P3 -->|unit vectors| DS[("session_state:<br/>chunks + index")]

    user -->|question| P4["retrieve"]
    DS --> P4
    P4 -->|top-k chunks| P5["build_prompt"]
    P5 -->|grounded prompt| P6["answer_question"]
    P6 -->|API request| LLM[["Groq LLM"]]
    LLM -->|cited answer| user
```

---

## 3. Sequence — asking a question

The request lifecycle from upload to a grounded, cited answer.

```mermaid
sequenceDiagram
    actor U as User
    participant UI as Streamlit UI
    participant C as Core logic
    participant E as Embedder
    participant L as Groq LLM

    U->>UI: Upload PDF + click Process
    UI->>C: extract_text() then chunk_text()
    UI->>C: build_index(chunks, embedder)
    C->>E: encode(chunks)
    E-->>C: chunk embeddings
    C-->>UI: index (stored in session_state)

    U->>UI: Ask a question
    UI->>C: retrieve(question, chunks, index, embedder)
    C->>E: encode([question])
    E-->>C: query vector
    C-->>UI: top-k chunks + scores

    UI->>C: answer_question(client, question, contexts)
    C->>L: chat.completions.create(prompt)
    L-->>C: answer
    C-->>UI: answer text
    UI-->>U: answer + retrieved sources
```
