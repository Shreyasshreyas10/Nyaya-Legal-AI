"""
verify_setup.py
Run this after pip install to confirm every Day 1 dependency works.
Usage: python verify_setup.py
"""

import sys
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

results = []

def check(label, fn):
    try:
        fn()
        results.append((label, "ok", ""))
    except Exception as e:
        results.append((label, "fail", str(e)[:80]))


# --- import checks ---
def chk_langchain():
    import langchain
    import langgraph

def chk_ollama():
    from langchain_ollama import OllamaLLM
    import httpx
    from config import OLLAMA_BASE_URL, OLLAMA_MODEL
    r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    assert r.status_code == 200, f"Ollama not reachable at {OLLAMA_BASE_URL}"
    models = [m["name"] for m in r.json().get("models", [])]
    if not any(OLLAMA_MODEL in m for m in models):
        raise RuntimeError(
            f"Model '{OLLAMA_MODEL}' not found in Ollama. "
            f"Run: ollama pull {OLLAMA_MODEL}\nAvailable: {models}"
        )

def chk_sarvam_inference():
    from langchain_ollama import OllamaLLM
    from config import OLLAMA_BASE_URL, OLLAMA_MODEL
    llm = OllamaLLM(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
    out = llm.invoke("Say 'Nyaya system ready' in one line.")
    assert len(out) > 3, "Sarvam returned empty response"
    console.print(f"  [dim]Sarvam says: {out[:120]}[/dim]")

def chk_chromadb():
    import chromadb
    client = chromadb.Client()
    col = client.get_or_create_collection("test_col")
    col.add(documents=["test document"], ids=["id1"])
    res = col.query(query_texts=["test"], n_results=1)
    assert len(res["documents"]) > 0

def chk_embeddings():
    from sentence_transformers import SentenceTransformer
    from config import EMBEDDING_MODEL
    model = SentenceTransformer(EMBEDDING_MODEL)
    vec = model.encode("Indian Constitution Article 21")
    assert len(vec) > 0

def chk_pdf():
    import pymupdf
    import pdfplumber

def chk_multilingual():
    from langdetect import detect
    from deep_translator import GoogleTranslator
    lang = detect("मेरे बिल्डर ने फ्लैट में देरी की")
    assert lang == "hi", f"Expected 'hi', got '{lang}'"
    translated = GoogleTranslator(source="hi", target="en").translate(
        "मेरे बिल्डर ने फ्लैट में देरी की"
    )
    assert "builder" in translated.lower() or "delay" in translated.lower(), \
        f"Translation unexpected: {translated}"
    console.print(f"  [dim]Hindi → English: {translated}[/dim]")

def chk_phoenix():
    import phoenix as px
    import opentelemetry

def chk_fastapi():
    import fastapi
    import uvicorn

def chk_folders():
    import os
    required = [
        "data/raw", "data/processed", "data/chroma_db",
        "agents", "core", "api", "ui", "tests", "logs"
    ]
    for folder in required:
        os.makedirs(folder, exist_ok=True)
    assert all(os.path.isdir(f) for f in required)


# --- run all checks ---
console.print("\n[bold]Nyaya — Day 1 setup verification[/bold]\n")

check("LangChain + LangGraph",        chk_langchain)
check("Ollama reachable",              chk_ollama)
check("Sarvam model inference",        chk_sarvam_inference)
check("ChromaDB",                      chk_chromadb)
check("Sentence embeddings",           chk_embeddings)
check("PDF libraries (pymupdf + pdfplumber)", chk_pdf)
check("Multilingual (langdetect + deep-translator)", chk_multilingual)
check("Arize Phoenix + OpenTelemetry", chk_phoenix)
check("FastAPI + Uvicorn",             chk_fastapi)
check("Project folder structure",      chk_folders)


# --- print results table ---
table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
table.add_column("Check", style="", min_width=38)
table.add_column("Status", min_width=6)
table.add_column("Note", style="dim")

all_ok = True
for label, status, note in results:
    if status == "ok":
        table.add_row(label, "[green]PASS[/green]", note)
    else:
        table.add_row(label, "[red]FAIL[/red]", note)
        all_ok = False

console.print(table)

if all_ok:
    console.print("[bold green]All checks passed. You're ready for Day 2.[/bold green]\n")
else:
    console.print("[bold red]Some checks failed. Fix the errors above before proceeding.[/bold red]\n")
    console.print("Common fixes:")
    console.print("  Ollama not running  →  run [bold]ollama serve[/bold] in a separate terminal")
    console.print(f"  Model missing       →  run [bold]ollama pull sarvam2b[/bold]")
    console.print("  Import error        →  run [bold]pip install -r requirements.txt[/bold]\n")
    sys.exit(1)
