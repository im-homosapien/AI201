# The Unofficial Guide — Texas State University

CodePath AI201 Project 1: production RAG pipeline over local TXST student knowledge.

**Repo:** [github.com/im-homosapien/AI201](https://github.com/im-homosapien/AI201)

## What it does

1. **Ingest** — reads `txst_data.txt`, strips comments/blanks, chunks by line, embeds with `all-MiniLM-L6-v2`, stores in **ChromaDB**
2. **Retrieve** — semantic top-3 search over embeddings
3. **Generate** — `gemini-2.5-flash` answers with citations (`[chunk_XXX]`), temperature `0.0`

## Setup

```powershell
git clone https://github.com/im-homosapien/AI201.git
cd AI201
pip install -r requirements.txt
```

Set your Gemini API key (pick one):

```powershell
# Option A: per terminal session
$env:GEMINI_API_KEY="your_key_here"

# Option B: copy .env.example to .env and fill in your key
copy .env.example .env
```

## Run

```powershell
# Live demo (re-ingests data, runs sample question)
python app.py

# Full evaluation suite + writes evaluation_report.md
python evaluate.py

# Ingest only
python ingest.py
```

## Files

| File | Purpose |
|------|---------|
| `txst_data.txt` | Source documents (RMP reviews, housing, dining, campus tips) |
| `ingest.py` | Clean → chunk → embed → ChromaDB |
| `rag.py` | Vector retrieval + grounded Gemini generation |
| `evaluate.py` | Structured retrieval/generation tests |
| `evaluation_report.md` | Auto-generated evaluation results |

## Failure mode (see report)

The keyword-only prototype retrieved only one professor for comparison questions, causing correct but unhelpful "I don't know" answers. Fixed by top-k vector retrieval.
