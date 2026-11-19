import json
from pathlib import Path
from typing import Iterable, List

from rich import box
from rich.console import Console
from rich.table import Table

import chromadb

from config import CHROMA_PERSIST_DIR, CHUNK_CHILD_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL
from core.embeddings import encode_texts, get_embedding_device

console = Console()
COLLECTION_NAME = "nyaya_children"
PROCESSED_DIR = Path("data/processed")
MIN_SECTION_CHARS = 80


def ensure_dirs():
    Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def split_text_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    words = text.split()
    if len(words) <= chunk_size:
        return [text.strip()]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def iter_batches(items: List, batch_size: int) -> Iterable[List]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def load_sections() -> List[dict]:
    sections = []
    loaded_docs_count = 0

    for source_path in sorted(PROCESSED_DIR.glob("*_sections.json")):
        try:
            data = json.loads(source_path.read_text(encoding="utf-8"))
        except Exception as exc:
            console.print(f"[red]Failed to read {source_path}: {exc}[/red]")
            continue

        doc_id = data.get("doc_id") or source_path.stem.replace("_sections", "")
        doc_sections = 0
        for section in data.get("sections", []):
            content = (section.get("content") or "").strip()
            if len(content) < MIN_SECTION_CHARS:
                continue
            parent_id = f"{doc_id}__{section.get('section_id', 'unknown')}"
            sections.append({
                "parent_id": parent_id,
                "doc_id": doc_id,
                "section_id": section.get("section_id", "unknown"),
                "heading": section.get("heading", ""),
                "content": content,
            })
            doc_sections += 1
        if doc_sections:
            loaded_docs_count += 1

    console.print(f"[green]Loaded {len(sections):,} sections from {loaded_docs_count} documents[/green]")
    return sections


def build_vector_store(refresh: bool = False):
    ensure_dirs()

    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    existing_collections = {c.name for c in client.list_collections()}
    if COLLECTION_NAME in existing_collections:
        if refresh:
            client.delete_collection(name=COLLECTION_NAME)
            existing_collections.remove(COLLECTION_NAME)
        else:
            console.print(f"[yellow]Collection '{COLLECTION_NAME}' already exists. Use --refresh to rebuild.[/yellow]")
            return

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    sections = load_sections()
    if not sections:
        console.print(f"[yellow]No section JSON files found in {PROCESSED_DIR.resolve()}[/yellow]")
        return

    rows = []
    for section in sections:
        content = section["content"].strip()
        if not content:
            continue
        child_chunks = split_text_into_chunks(content, CHUNK_CHILD_SIZE, CHUNK_OVERLAP)
        for idx, chunk in enumerate(child_chunks, start=1):
            rows.append({
                "id": f"{section['parent_id']}_chunk_{idx:04d}",
                "document": chunk,
                "metadata": {
                    "parent_id": section["parent_id"],
                    "doc_id": section["doc_id"],
                    "section_id": section["section_id"],
                    "heading": section["heading"],
                },
            })

    if not rows:
        console.print("[yellow]No child chunks were generated.[/yellow]")
        return

    console.print(f"[bold]Using embedding device:[/bold] {get_embedding_device()}")

    ids = [row["id"] for row in rows]
    documents = [row["document"] for row in rows]
    metadatas = [row["metadata"] for row in rows]
    console.print(f"[bold]Embedding {len(documents):,} child chunks with {EMBEDDING_MODEL}[/bold]")
    embeddings = encode_texts(documents, batch_size=256, show_progress_bar=True)

    console.print(f"[bold]Adding {len(ids):,} child chunks in batches to ChromaDB collection '{COLLECTION_NAME}'[/bold]")
    db_batch_size = 2000
    for i in range(0, len(ids), db_batch_size):
        end_idx = i + db_batch_size
        collection.add(
            ids=ids[i:end_idx],
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            embeddings=embeddings[i:end_idx],
        )

    console.print(f"[green]Stored {len(ids):,} child chunks in ChromaDB collection '{COLLECTION_NAME}'[/green]")

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Parent ID", min_width=36)
    table.add_column("Section", min_width=10)
    table.add_column("Chunks", justify="right")

    parent_counts = {}
    for metadata in metadatas:
        parent_counts[metadata["parent_id"]] = parent_counts.get(metadata["parent_id"], 0) + 1

    for parent_id, count in list(parent_counts.items())[:20]:
        table.add_row(parent_id, "", str(count))

    console.print(table)


def run(refresh: bool = False):
    build_vector_store(refresh=refresh)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Rebuild the ChromaDB collection from scratch")
    args = parser.parse_args()
    run(refresh=args.refresh)
