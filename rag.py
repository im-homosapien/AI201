"""
RAG core: semantic retrieval from ChromaDB + grounded Gemini generation with citations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from google import genai
from google.genai import types

from ingest import CHROMA_DIR, COLLECTION_NAME, get_chroma_collection

MODEL_ID = "gemini-2.5-flash"
TOP_K = 3

SYSTEM_INSTRUCTION = """You are 'The Unofficial Guide' for Texas State University.

RULES:
- Answer ONLY using the numbered CONTEXT sources below.
- Cite sources inline using [chunk_XXX] tags (e.g. [chunk_001]) whenever you state a fact.
- If the context does not contain enough information, say "I don't know" and explain what is missing.
- Do not use outside knowledge. Do not invent professors, ratings, or housing details.
- For comparisons, only compare facts present in the context."""


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source_tag: str
    distance: float | None


def get_collection():
    return get_chroma_collection(CHROMA_DIR)


def retrieve_relevant_chunks(user_query: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
    """Semantic search over the vector store — returns top-k chunks by embedding similarity."""
    collection = get_collection()
    results = collection.query(query_texts=[user_query], n_results=top_k)

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results.get("distances", [[]])[0]

    retrieved: list[RetrievedChunk] = []
    for i, chunk_id in enumerate(ids):
        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                text=documents[i],
                source_tag=metadatas[i].get("source_tag", "unknown"),
                distance=distances[i] if distances else None,
            )
        )
    return retrieved


def format_context(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for c in chunks:
        dist = f" (distance={c.distance:.4f})" if c.distance is not None else ""
        lines.append(
            f"[{c.chunk_id}] ({c.source_tag}){dist}\n{c.text}"
        )
    return "\n\n".join(lines)


def ask_unofficial_guide(
    user_question: str,
    client: genai.Client,
    *,
    top_k: int = TOP_K,
    verbose: bool = True,
) -> dict:
    """Run full RAG: retrieve → prompt → generate. Returns structured result dict."""
    chunks = retrieve_relevant_chunks(user_question, top_k=top_k)
    context = format_context(chunks)

    user_message = f"CONTEXT:\n{context}\n\nQUESTION:\n{user_question}"

    if verbose:
        print("=" * 60)
        print("TXST UNOFFICIAL GUIDE — RAG PIPELINE")
        print("=" * 60)
        print(f"\n[1] USER QUERY:\n    {user_question}\n")
        print("[2] RETRIEVED CHUNKS (vector search):")
        for c in chunks:
            dist = f"{c.distance:.4f}" if c.distance is not None else "n/a"
            print(f"    • {c.chunk_id} [{c.source_tag}] dist={dist}")
            print(f"      {c.text[:100]}{'...' if len(c.text) > 100 else ''}")
        print(f"\n[3] PROMPT → {MODEL_ID} (temperature=0.0)\n")

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.0,
        ),
    )

    answer = response.text or "(No text returned by model.)"

    if verbose:
        print(f"[4] GEMINI RESPONSE:\n    {answer}\n")
        print("=" * 60)

    return {
        "question": user_question,
        "chunks": chunks,
        "answer": answer,
        "context": context,
    }


def create_gemini_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            'PowerShell: $env:GEMINI_API_KEY="your_key_here"'
        )
    return genai.Client(api_key=api_key)
