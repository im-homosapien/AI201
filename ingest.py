"""
Document ingestion: load TXST documents, clean, chunk, embed, store in ChromaDB.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

DOCUMENTS_DIR = Path(__file__).parent / "documents"
CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "txst_unofficial_guide"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 80


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    source_file: str
    source_url: str
    chunk_index: int


def clean_text(raw: str) -> str:
    """Remove source headers and normalize whitespace."""
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("source:"):
            continue
        if stripped.lower().startswith("collected:"):
            continue
        lines.append(stripped)
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_source_url(raw: str) -> str:
    for line in raw.splitlines():
        if line.strip().lower().startswith("source:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, source_file: str, source_url: str) -> list[DocumentChunk]:
    """Chunk by document boundary for short reviews; sentence splits with overlap for long text."""
    if len(text) <= CHUNK_SIZE:
        return [
            DocumentChunk(
                chunk_id=f"{source_file}::0",
                text=text,
                source_file=source_file,
                source_url=source_url,
                chunk_index=0,
            )
        ]

    sentences = split_sentences(text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= CHUNK_SIZE:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)

    # Apply character overlap between adjacent chunks
    overlapped: list[str] = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            overlapped.append(chunk)
            continue
        prev_tail = overlapped[-1][-CHUNK_OVERLAP:] if len(overlapped[-1]) > CHUNK_OVERLAP else overlapped[-1]
        overlapped.append(f"{prev_tail} {chunk}".strip())

    return [
        DocumentChunk(
            chunk_id=f"{source_file}::{i}",
            text=body,
            source_file=source_file,
            source_url=source_url,
            chunk_index=i,
        )
        for i, body in enumerate(overlapped)
        if body
    ]


def load_documents(documents_dir: Path = DOCUMENTS_DIR) -> list[DocumentChunk]:
    if not documents_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {documents_dir}")

    files = sorted(documents_dir.glob("*.txt"))
    if len(files) < 10:
        raise ValueError(f"Need at least 10 documents; found {len(files)} in {documents_dir}")

    all_chunks: list[DocumentChunk] = []
    for path in files:
        raw = path.read_text(encoding="utf-8")
        body = clean_text(raw)
        if not body:
            continue
        source_url = extract_source_url(raw)
        all_chunks.extend(chunk_text(body, path.name, source_url))

    if not all_chunks:
        raise ValueError("No valid chunks produced from documents.")

    return all_chunks


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
    documents_dir: Path = DOCUMENTS_DIR,
    persist_dir: Path = CHROMA_DIR,
    reset: bool = True,
) -> tuple[list[DocumentChunk], chromadb.Collection]:
    """Full pipeline: load -> clean -> chunk -> embed -> store."""
    chunks = load_documents(documents_dir)

    if reset and persist_dir.exists():
        shutil.rmtree(persist_dir)

    collection = get_chroma_collection(persist_dir)
    collection.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "source_file": c.source_file,
                "source_url": c.source_url,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ],
    )
    return chunks, collection


if __name__ == "__main__":
    docs, col = ingest_documents()
    print(f"Ingested {len(docs)} chunks from {len(list(DOCUMENTS_DIR.glob('*.txt')))} documents.")
    print(f"ChromaDB collection '{COLLECTION_NAME}' count: {col.count()}")
    print("\nSample chunks:")
    for c in docs[:5]:
        print(f"  [{c.chunk_id}] {c.text[:90]}...")
