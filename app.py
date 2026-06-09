"""
CodePath AI201 — Project 1: The Unofficial Guide (TXST)
End-to-end RAG: ingest → vector search → grounded Gemini generation.
"""

import sys

from ingest import ingest_documents
from rag import ask_unofficial_guide, create_gemini_client


def main() -> None:
    try:
        chunks, _ = ingest_documents()
        print(f"Loaded {len(chunks)} document chunks into ChromaDB.\n")
        client = create_gemini_client()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except EnvironmentError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR during ingestion: {exc}", file=sys.stderr)
        sys.exit(1)

    ask_unofficial_guide(
        "Who is better for CS 1428, Prof. Jones or Prof. Smith?",
        client,
    )


if __name__ == "__main__":
    main()
