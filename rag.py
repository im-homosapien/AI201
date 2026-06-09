"""
RAG core: semantic retrieval from ChromaDB + grounded Gemini generation with citations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from ingest import CHROMA_DIR, get_chroma_collection

load_dotenv(Path(__file__).parent / ".env")

MODEL_ID = "gemini-2.5-flash"
TOP_K = 4

SYSTEM_INSTRUCTION = """You are 'The Unofficial Guide' for Texas State University.

RULES:
- Answer ONLY using the CONTEXT sources below.
- Cite sources inline using [source_file] tags when stating facts.
- If the context does not contain enough information to answer, say exactly:
  "I don't have enough information on that in my unofficial guide."
- Do not use outside knowledge. Do not invent professors, ratings, or housing details.
- For comparisons, only compare facts explicitly present in the context."""


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source_file: str
    source_url: str
    distance: float | None


def get_collection():
    return get_chroma_collection(CHROMA_DIR)


def retrieve_relevant_chunks(user_query: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
    collection = get_collection()
    results = collection.query(query_texts=[user_query], n_results=top_k)

    retrieved: list[RetrievedChunk] = []
    for i, chunk_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        distances = results.get("distances", [[]])[0]
        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                text=results["documents"][0][i],
                source_file=meta.get("source_file", "unknown"),
                source_url=meta.get("source_url", "unknown"),
                distance=distances[i] if distances else None,
            )
        )
    return retrieved


def format_context(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for c in chunks:
        dist = f" (distance={c.distance:.4f})" if c.distance is not None else ""
        lines.append(f"[{c.source_file}]{dist}\n{c.text}")
    return "\n\n".join(lines)


def format_sources(chunks: list[RetrievedChunk]) -> str:
    seen: set[str] = set()
    lines = []
    for c in chunks:
        if c.source_file in seen:
            continue
        seen.add(c.source_file)
        lines.append(f"- {c.source_file} ({c.source_url})")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def create_gemini_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env or run:\n"
            '  $env:GEMINI_API_KEY="your_key_here"'
        )
    return genai.Client(api_key=api_key)


def ask(
    user_question: str,
    *,
    top_k: int = TOP_K,
    verbose: bool = False,
) -> dict:
    """End-to-end RAG: retrieve, generate, attach programmatic source list."""
    chunks = retrieve_relevant_chunks(user_question, top_k=top_k)
    context = format_context(chunks)
    sources_block = format_sources(chunks)

    user_message = f"CONTEXT:\n{context}\n\nQUESTION:\n{user_question}"
    client = create_gemini_client()

    if verbose:
        print(f"Query: {user_question}")
        for c in chunks:
            print(f"  {c.source_file} dist={c.distance}")

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.0,
        ),
    )

    answer = response.text or "(No text returned by model.)"
    full_answer = f"{answer}\n\n---\nRetrieved from:\n{sources_block}"

    return {
        "question": user_question,
        "answer": full_answer,
        "answer_text": answer,
        "sources": [c.source_file for c in chunks],
        "sources_display": sources_block,
        "chunks": chunks,
    }


def ask_unofficial_guide(user_question: str, client: genai.Client, **kwargs) -> dict:
    """Backward-compatible wrapper used by evaluate.py."""
    del client
    return ask(user_question, **kwargs)
