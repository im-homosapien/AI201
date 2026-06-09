"""
Document ingestion: load TXST text, clean, chunk, embed, and store in ChromaDB.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

DATA_FILE = Path(__file__).parent / "txst_data.txt"
CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "txst_unofficial_guide"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    source_tag: str
    category: str


def load_raw_text(filepath: Path = DATA_FILE) -> str:
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    return filepath.read_text(encoding="utf-8")


def clean_and_chunk(raw_text: str) -> list[DocumentChunk]:
    """Strip comments/blank lines and split into one chunk per content line."""
    chunks: list[DocumentChunk] = []
    index = 0

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        source_tag = "unknown"
        category = "general"
        body = stripped

        tag_match = re.match(r"^\[([^\]]+)\]\s*(.*)$", stripped)
        if tag_match:
            source_tag = tag_match.group(1)
            body = tag_match.group(2).strip()
            category = source_tag.split("/")[0].lower()

        chunk_id = f"chunk_{index:03d}"
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                text=body,
                source_tag=source_tag,
                category=category,
            )
        )
        index += 1

    if not chunks:
        raise ValueError("No valid document chunks found after cleaning.")

    return chunks


def get_chroma_collection(persist_dir: Path = CHROMA_DIR):
    persist_dir.mkdir(parents=True, exist_ok=True)
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=str(persist_dir))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"project": "txst_unofficial_guide"},
    )


def ingest_documents(
    filepath: Path = DATA_FILE,
    persist_dir: Path = CHROMA_DIR,
    reset: bool = True,
) -> tuple[list[DocumentChunk], chromadb.Collection]:
    """Full ingestion pipeline: clean → chunk → embed → store."""
    raw = load_raw_text(filepath)
    chunks = clean_and_chunk(raw)

    if reset and persist_dir.exists():
        import shutil

        shutil.rmtree(persist_dir)

    collection = get_chroma_collection(persist_dir)

    collection.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {"source_tag": c.source_tag, "category": c.category}
            for c in chunks
        ],
    )

    return chunks, collection


if __name__ == "__main__":
    docs, col = ingest_documents()
    print(f"Ingested {len(docs)} chunks into '{COLLECTION_NAME}' ({col.count()} in store).")
