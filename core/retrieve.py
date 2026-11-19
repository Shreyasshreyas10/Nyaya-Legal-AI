import json
from pathlib import Path
from typing import Dict, List, Optional

from rich import box
from rich.console import Console
from rich.table import Table

import chromadb

from config import CHROMA_PERSIST_DIR, TOP_K_RETRIEVAL
from core.embeddings import encode_query

console = Console()
COLLECTION_NAME = "nyaya_children"
PROCESSED_DIR = Path("data/processed")
MAX_DISTANCE = 1.25


def get_collection_stats() -> dict:
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        return {"collection": COLLECTION_NAME, "chunk_count": collection.count(), "ready": True}
    except Exception:
        return {"collection": COLLECTION_NAME, "chunk_count": 0, "ready": False}


def load_parent_sections() -> Dict[str, dict]:
    parents = {}
    for source_path in sorted(PROCESSED_DIR.glob("*_sections.json")):
        try:
            doc = json.loads(source_path.read_text(encoding="utf-8"))
        except Exception as exc:
            console.print(f"[red]Failed to read {source_path}: {exc}[/red]")
            continue

        doc_id = doc.get("doc_id") or source_path.stem.replace("_sections", "")
        for section in doc.get("sections", []):
            parent_id = f"{doc_id}__{section.get('section_id', 'unknown')}"
            parents[parent_id] = {
                "doc_id": doc_id,
                "section_id": section.get("section_id", "unknown"),
                "heading": section.get("heading", ""),
                "content": section.get("content", ""),
            }
    return parents


def retrieve(
    query: str,
    top_k: int = TOP_K_RETRIEVAL,
    doc_id: Optional[str] = None,
) -> List[dict]:
    stats = get_collection_stats()
    if not stats["ready"] or stats["chunk_count"] == 0:
        console.print(f"[red]Collection '{COLLECTION_NAME}' not found or empty in {Path(CHROMA_PERSIST_DIR).resolve()}[/red]")
        return []

    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)

    where = {"doc_id": doc_id} if doc_id else None
    query_kwargs = {
        "query_embeddings": [encode_query(query)],
        "n_results": top_k,
        "include": ["metadatas", "documents", "distances"],
    }
    if where:
        query_kwargs["where"] = where

    query_result = collection.query(**query_kwargs)

    if not query_result or not query_result.get("metadatas"):
        return []

    metadatas = query_result["metadatas"][0]
    documents = query_result["documents"][0]
    distances = query_result["distances"][0]

    parent_sections = load_parent_sections()
    unique_parents: Dict[str, dict] = {}

    for metadata, chunk_text, distance in zip(metadatas, documents, distances):
        if distance is not None and distance > MAX_DISTANCE:
            continue
        parent_id = metadata.get("parent_id")
        if not parent_id:
            continue
        section = parent_sections.get(parent_id, {})
        if parent_id not in unique_parents:
            unique_parents[parent_id] = {
                "parent_id": parent_id,
                "doc_id": metadata.get("doc_id", section.get("doc_id", "unknown")),
                "section_id": metadata.get("section_id", section.get("section_id", "unknown")),
                "heading": metadata.get("heading", section.get("heading", "")),
                "content": section.get("content", ""),
                "top_chunks": [],
            }
        unique_parents[parent_id]["top_chunks"].append({
            "chunk": chunk_text,
            "distance": distance,
        })

    return list(unique_parents.values())


def run(query: str, top_k: int = TOP_K_RETRIEVAL):
    if not query:
        console.print("[yellow]Provide a --query string to search the ChromaDB index.[/yellow]")
        return

    results = retrieve(query, top_k=top_k)
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Rank", justify="right")
    table.add_column("Doc ID", min_width=20)
    table.add_column("Section", min_width=12)
    table.add_column("Heading", min_width=40)
    table.add_column("Chunks", justify="right")

    for idx, section in enumerate(results, start=1):
        table.add_row(
            str(idx),
            section["doc_id"],
            section["section_id"],
            section["heading"][:60].replace("\n", " "),
            str(len(section["top_chunks"])),
        )

    console.print(table)
    console.print()

    for idx, section in enumerate(results, start=1):
        console.print(f"[bold]{idx}. {section['heading']}[/bold] ({section['doc_id']}, {section['section_id']})")
        preview = section["content"][:800].replace("\n", " ")
        console.print(f"[dim]{preview}...[/dim]\n")
        for chunk in section["top_chunks"]:
            chunk_preview = chunk["chunk"][:200].replace("\n", " ")
            console.print(f"  • [italic]chunk distance={chunk['distance']:.4f}[/italic] {chunk_preview}")
        console.print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--top-k", type=int, default=TOP_K_RETRIEVAL)
    parser.add_argument("--doc-id", type=str, default=None)
    args = parser.parse_args()
    run(query=args.query, top_k=args.top_k)
