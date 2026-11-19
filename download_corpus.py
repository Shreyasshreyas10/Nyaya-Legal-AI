"""
download_corpus.py
Downloads key Indian legal PDFs from legislative.gov.in
Run this first before ingest.py

Usage: python download_corpus.py
"""

import os
import time
import httpx
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn

console = Console()

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Key Indian legal documents — direct PDF links from legislative.gov.in
# Add more URLs here as needed
DOCUMENTS = [
    {
        "name": "Consumer_Protection_Act_2019.pdf",
        "url": "https://www.legislative.gov.in/sites/default/files/A2019-35.pdf",
        "desc": "Consumer Protection Act, 2019",
    },
    {
        "name": "Constitution_of_India.pdf",
        "url": "https://www.legislative.gov.in/sites/default/files/COI...pdf",
        "desc": "Constitution of India",
    },
    {
        "name": "RERA_2016.pdf",
        "url": "https://www.legislative.gov.in/sites/default/files/A2016-16.pdf",
        "desc": "Real Estate (Regulation and Development) Act, 2016",
    },
    {
        "name": "IPC_1860.pdf",
        "url": "https://www.legislative.gov.in/sites/default/files/A1860-45.pdf",
        "desc": "Indian Penal Code, 1860",
    },
    {
        "name": "RTI_Act_2005.pdf",
        "url": "https://www.legislative.gov.in/sites/default/files/A2005-22.pdf",
        "desc": "Right to Information Act, 2005",
    },
]


def download_file(url: str, dest: Path, desc: str) -> bool:
    """Download a single file with progress display."""
    if dest.exists():
        console.print(f"  [dim]Already exists: {dest.name} — skipping[/dim]")
        return True

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        with httpx.stream("GET", url, headers=headers, timeout=30, follow_redirects=True) as r:
            if r.status_code != 200:
                console.print(f"  [red]HTTP {r.status_code} for {desc}[/red]")
                return False

            total = int(r.headers.get("content-length", 0))
            with open(dest, "wb") as f:
                downloaded = 0
                for chunk in r.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

        size_kb = dest.stat().st_size // 1024
        console.print(f"  [green]Downloaded {desc} ({size_kb} KB)[/green]")
        return True

    except Exception as e:
        console.print(f"  [red]Failed: {desc} — {e}[/red]")
        if dest.exists():
            dest.unlink()
        return False


def run():
    console.print("\n[bold]Nyaya — Corpus Downloader[/bold]")
    console.print("Source: legislative.gov.in\n")
    console.print("[yellow]Note: If any download fails, go to https://www.legislative.gov.in/documents")
    console.print("and manually download PDFs into the data/raw/ folder.[/yellow]\n")

    ok = 0
    for doc in DOCUMENTS:
        dest = RAW_DIR / doc["name"]
        console.print(f"[bold]{doc['desc']}[/bold]")
        if download_file(doc["url"], dest, doc["desc"]):
            ok += 1
        time.sleep(1)  # be polite to the server

    console.print(f"\n[bold]{ok}/{len(DOCUMENTS)} documents downloaded to {RAW_DIR.resolve()}[/bold]")
    console.print("\nIf some failed, manually download from:")
    console.print("[bold]https://www.legislative.gov.in/documents?page=1[/bold]")
    console.print(f"and save PDFs to: [bold]{RAW_DIR.resolve()}[/bold]\n")
    console.print("Then run: [bold]python -m core.ingest[/bold]\n")


if __name__ == "__main__":
    run()
