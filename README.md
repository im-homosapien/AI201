# The Unofficial Guide — Texas State University

**CodePath AI201 Project 1** | [github.com/im-homosapien/AI201](https://github.com/im-homosapien/AI201)

A RAG system that makes scattered TXST student knowledge (professor reviews, housing, dining, campus tips) searchable and answerable with grounded, cited responses.

## Domain and Document Sources

**Domain:** Texas State University unofficial student knowledge — the kind shared on Rate My Professors and r/txst, not in the official course catalog.

**Why it matters:** Students need quick answers like "Is Jones harsh for CS 1428?" or "Which dorm is near the library?" but that info is buried in threads and review pages.

| Source file | Origin |
|-------------|--------|
| `documents/rmp_cs1428_smith.txt` | [Rate My Professors](https://www.ratemyprofessors.com/) |
| `documents/rmp_cs1428_jones.txt` | Rate My Professors |
| `documents/rmp_cs1428_garcia.txt` | Rate My Professors |
| `documents/reddit_housing_*.txt` (4 files) | [r/txst](https://www.reddit.com/r/txst/) housing threads |
| `documents/reddit_dining_*.txt` (2 files) | r/txst dining threads |
| `documents/reddit_campus_*.txt` (3 files) | r/txst campus threads |
| `documents/reddit_academics_cs_advising.txt` | r/txst CS advising |

**13 documents** collected manually as plain text (Spring 2026).

## Setup

```powershell
git clone https://github.com/im-homosapien/AI201.git
cd AI201
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY from https://aistudio.google.com/apikey
```

## Run

```powershell
python app.py          # Gradio UI at http://localhost:7860
python evaluate.py     # Run 5-question evaluation report
python ingest.py       # Re-index documents only
```

## Chunking Strategy

- **Size:** 300 characters max per chunk
- **Overlap:** 80 characters between adjacent chunks (long documents only)
- **Rule:** Short review files (most of our corpus) = **one chunk per document**

**Why:** Reviews are 1–3 sentences with one opinion each. Splitting "Prof. Jones has pop quizzes. Rating 2/10." across chunks would break retrieval for professor queries. The longer CS advising file uses sentence-boundary splitting with overlap so facts at boundaries stay retrievable.

See `planning.md` for full rationale.

## Sample Chunks

| Source | Chunk text |
|--------|------------|
| `rmp_cs1428_smith.txt` | Prof. Smith teaches CS 1428... clear lectures and generous extra credit on labs... Rating: 4.5/5. |
| `rmp_cs1428_jones.txt` | Prof. Jones also teaches CS 1428... frequent pop quizzes and strict attendance... Rating: 2/10. |
| `reddit_housing_san_jacinto.txt` | San Jacinto Hall sits near Alkek Library and the LBJ Student Center... |
| `reddit_dining_jones_hall.txt` | Jones Dining Hall (JDH)... widest hours on main campus. |
| `reddit_campus_alkek_library.txt` | Alkek Library floor 4 is the go-to quiet study zone at Texas State. |

## Embedding Model

**Model:** `all-MiniLM-L6-v2` (sentence-transformers, runs locally)

**Production tradeoffs I'd consider:**
- **Cost:** Local embeddings are free; API embeddings (OpenAI, Gemini) add per-token cost but may improve quality
- **Context length:** MiniLM handles short reviews well; long housing PDFs might need a longer-context model
- **Multilingual:** TXST has international students — multilingual embeddings (e.g. `paraphrase-multilingual-MiniLM`) for non-English forum posts
- **Domain fit:** Fine-tuning on education/review text for better professor-name matching

## Retrieval Test Results

### Query 1: "What do students say about Prof. Smith for CS 1428?"
- **Top chunk:** `rmp_cs1428_smith.txt` (distance ~0.32)
- **Why relevant:** Contains Smith, CS 1428, extra credit, and 4.5/5 rating — direct match.

### Query 2: "Which on-campus housing is near Alkek Library?"
- **Top chunk:** `reddit_housing_san_jacinto.txt` (distance ~0.46)
- **Why relevant:** Explicitly names San Jacinto Hall and Alkek Library proximity.

### Query 3: "Who is better for CS 1428, Prof. Jones or Prof. Smith?"
- **Top chunks:** `rmp_cs1428_smith.txt`, `rmp_cs1428_jones.txt` (both under distance 0.50)
- **Why relevant:** Comparison needs both professor reviews in top-k; k=4 retrieves both.

## Grounded Generation

Enforced via:
1. **System prompt** — "Answer ONLY using CONTEXT; refuse if not present"
2. **temperature=0.0** — deterministic, less creative hallucination
3. **Programmatic source list** — `Retrieved from:` block appended after every answer with filenames and URLs (not left to the LLM alone)

## Example Responses

**In-scope (with citations):**
> Prof. Smith is praised for clear lectures and extra credit [rmp_cs1428_smith.txt]. Prof. Jones has pop quizzes and a 2/10 rating [rmp_cs1428_jones.txt].
>
> Retrieved from:
> - rmp_cs1428_smith.txt
> - rmp_cs1428_jones.txt

**Out-of-scope (refusal):**
> I don't have enough information on that in my unofficial guide.

## Query Interface

**Type:** Gradio web UI (`python app.py` -> http://localhost:7860)

| Field | Description |
|-------|-------------|
| Your question | Free-text student question |
| Answer | Grounded LLM response with inline citations |
| Retrieved from | Source filenames + URLs from vector search |

**Sample interaction:**
```
Question: Which dining hall has the widest hours on main campus?
Answer:   Jones Dining Hall (JDH) has the widest hours on main campus [reddit_dining_jones_hall.txt].
Sources:  - reddit_dining_jones_hall.txt (https://www.reddit.com/r/txst/)
```

## Evaluation Report

See `evaluation_report.md`. Summary of 5 test questions from `planning.md`:

| # | Question | Expected | Typical accuracy |
|---|----------|----------|------------------|
| 1 | Prof. Smith CS 1428 | Extra credit, 4.5/5 | Accurate |
| 2 | Prof. Jones good? | No, pop quizzes, 2/10 | Accurate |
| 3 | Housing near library | San Jacinto Hall | Accurate |
| 4 | Dining hall hours | Jones Dining Hall | Accurate |
| 5 | MATH 2471 professor | Should refuse | Accurate (refusal) |

## Failure Case

**Question:** Who is the best professor for MATH 2471?

**Stage:** Retrieval — returns CS 1428 professor chunks because they semantically match "professor" queries, even though MATH 2471 is absent from the corpus.

**Why:** Embedding similarity connects "professor" + "course" queries to the nearest professor reviews available. This is a classic RAG failure when the corpus lacks the target topic.

**Fix:** Strict refusal prompt + user sees retrieved sources are CS files, not math. Future: metadata filtering by department/course number.

## Spec Reflection

**Helped:** Planning chunk size (300 chars, one review per file) before coding prevented over-splitting short reviews — the main failure mode in naive RAG.

**Diverged:** Assignment recommends Groq; I used **Gemini 2.5 Flash** because I already had a working API key. Grounding approach is identical (temperature=0, context-only prompt).

## AI Usage

1. **Ingestion + ChromaDB:** Asked Cursor to implement `ingest.py` from my `planning.md` chunking section. **I changed** chunk overlap from 50 to 80 chars after inspecting the CS advising split.

2. **Gradio UI:** AI generated the `app.py` skeleton from Milestone 5 spec. **I added** error handling for missing API key and wired it to my `ask()` function instead of a generic stub.

3. **Evaluation:** AI drafted `evaluate.py`; **I replaced** generic pass/fail with the 5 specific questions and expected answers from `planning.md`.

## Demo Video

Record 3–5 minutes showing:
- 3+ queries with citations in the Gradio UI
- One strong retrieval example (professor comparison)
- One failure or edge case (MATH 2471 refusal)
- Walkthrough of `evaluation_report.md`

## Project Structure

```
AI201/
  planning.md          # Spec (written before implementation)
  README.md            # This file
  documents/           # 13 source .txt files
  ingest.py            # Load, clean, chunk, embed, store
  rag.py               # Retrieve + generate
  app.py               # Gradio UI
  evaluate.py          # Evaluation runner
  evaluation_report.md # Results
```
