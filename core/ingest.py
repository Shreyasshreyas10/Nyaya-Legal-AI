"""
core/ingest.py
Day 2 — PDF ingestion pipeline for Indian legal documents.

Usage:
    python -m core.ingest                        # process all PDFs in data/raw/
    python -m core.ingest --file data/raw/cpa.pdf  # process one file
"""
"""
core/ingest.py
Day 2 — PDF ingestion pipeline for Indian legal documents.
"""

import re
import json
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box

import pymupdf
import pdfplumber

console = Console()

RAW_DIR       = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
MANIFEST_PATH = Path("data/processed/manifest.json")


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    text = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u0900-\u097F\u0C00-\u0C7F\u0B80-\u0BFF\u0C80-\u0CFF\u0980-\u09FF]', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def detect_sections(text: str) -> list:
    patterns = [
        r'(?m)^(CHAPTER\s+[IVXLC\d]+[.\s]*.{0,80})$',
        r'(?m)^(Section\s+\d+[A-Z]?\s*[.:\-].{0,80})$',
        r'(?m)^(\d+[A-Z]?\.\s+[A-Z][^.]{10,80})$',
        r'(?m)^(Article\s+\d+[A-Z]?\s*[.:\-].{0,80})$',
        r'(?m)^(PART\s+[IVXLC\d]+[.\s]*.{0,80})$',
        r'(?m)^(Schedule\s+[IVXLC\d]+.{0,80})$',
    ]
    boundaries = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            boundaries.append((match.start(), match.group(1).strip()))

    if not boundaries:
        return [{"section_id": "full_doc", "heading": "Full Document", "content": text}]

    boundaries.sort(key=lambda x: x[0])
    sections = []
    for i, (start, heading) in enumerate(boundaries):
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
        sections.append({
            "section_id": f"sec_{i+1:04d}",
            "heading": heading[:120],
            "content": text[start:end].strip(),
        })
    return sections


def extract_with_pymupdf(pdf_path: Path) -> str:
    try:
        doc = pymupdf.open(str(pdf_path))
        pages = []
        for page in doc:
            try:
                pages.append(page.get_text("text"))
            except Exception:
                continue
        doc.close()
        return "\n".join(pages)
    except Exception:
        return ""


def extract_with_pdfplumber(pdf_path: Path) -> str:
    try:
        pages = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                try:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                except Exception:
                    continue
        return "\n".join(pages)
    except Exception:
        return ""


def is_good_extraction(text: str) -> bool:
    if not text or len(text.strip()) < 100:
        return False
    readable = sum(1 for c in text if c.isalpha() or c.isspace())
    return (readable / len(text)) > 0.6


def extract_with_ocr(pdf_path: Path) -> str:
    """Fallback parallel OCR using PyMuPDF to extract page images and Tesseract OCR."""
    console.print(f"  [yellow]PyMuPDF & pdfplumber failed/scanned, falling back to parallel OCR...[/yellow]")
    try:
        import concurrent.futures
        import pymupdf
        from core.scan import ocr_image_bytes

        doc = pymupdf.open(str(pdf_path))
        num_pages = len(doc)
        if num_pages == 0:
            return ""

        console.print(f"  [yellow]OCR-ing {num_pages} pages in parallel...[/yellow]")
        
        futures = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for idx, page in enumerate(doc):
                pix = page.get_pixmap(dpi=110)
                png_bytes = pix.tobytes("png")
                fut = executor.submit(ocr_image_bytes, png_bytes)
                futures[fut] = idx
                
            results = []
            completed = 0
            for fut in concurrent.futures.as_completed(futures):
                idx = futures[fut]
                try:
                    res = fut.result()
                    results.append((idx, res.get("text", "")))
                except Exception as e:
                    console.print(f"    [red]Error OCR-ing page {idx + 1}: {e}[/red]")
                    results.append((idx, ""))
                completed += 1
                if completed % 5 == 0 or completed == num_pages:
                    console.print(f"    Processed {completed}/{num_pages} pages...")

        # Sort results by page index to preserve reading order
        results.sort(key=lambda x: x[0])
        
        full_text = "\n\n".join(text for idx, text in results)
        doc.close()
        return full_text
    except Exception as exc:
        console.print(f"  [red]OCR pipeline failure: {exc}[/red]")
        return ""


def ingest_pdf(pdf_path: Path) -> dict:
    out_name = pdf_path.stem
    sections_json_path = PROCESSED_DIR / f"{out_name}_sections.json"
    txt_path = PROCESSED_DIR / f"{out_name}.txt"
    if sections_json_path.exists() and txt_path.exists():
        try:
            with open(sections_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            console.print(f"  [blue]Skipping {pdf_path.name} (already processed)[/blue]")
            return {
                "file": pdf_path.name,
                "doc_id": out_name,
                "chars": data.get("total_chars", 0),
                "sections": data.get("section_count", 0),
                "status": "ok",
            }
        except Exception:
            pass

    console.print(f"\n[bold]Processing:[/bold] {pdf_path.name}")
    text = extract_with_pymupdf(pdf_path)

    if not is_good_extraction(text):
        if len(text.strip()) < 50:
            # Completely scanned PDF with no text layer. Bypassing pdfplumber.
            pass
        else:
            try:
                doc = pymupdf.open(str(pdf_path))
                page_count = len(doc)
                doc.close()
            except Exception:
                page_count = 0
            
            if page_count > 30:
                console.print(f"  [yellow]PyMuPDF poor, but PDF has {page_count} pages. Bypassing pdfplumber fallback.[/yellow]")
            else:
                console.print(f"  [yellow]PyMuPDF poor, trying pdfplumber on {page_count} pages...[/yellow]")
                text = extract_with_pdfplumber(pdf_path)

    if not is_good_extraction(text):
        text = extract_with_ocr(pdf_path)

    if not is_good_extraction(text):
        console.print(f"  [red]Skipping (corrupted or scanned)[/red]")
        return {"file": pdf_path.name, "status": "failed", "chars": 0, "sections": 0}

    console.print(f"  [green]Extracted {len(text):,} characters[/green]")
    text = clean_text(text)
    sections = detect_sections(text)
    console.print(f"  [green]Detected {len(sections)} sections[/green]")

    out_name = pdf_path.stem
    (PROCESSED_DIR / f"{out_name}.txt").write_text(text, encoding="utf-8")
    (PROCESSED_DIR / f"{out_name}_sections.json").write_text(
        json.dumps({
            "source_file": pdf_path.name,
            "doc_id": out_name,
            "total_chars": len(text),
            "section_count": len(sections),
            "sections": sections,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    preview = text[:300].replace('\n', ' ')
    console.print(f"  [dim]Preview: {preview}...[/dim]")

    return {
        "file": pdf_path.name,
        "doc_id": out_name,
        "chars": len(text),
        "sections": len(sections),
        "status": "ok",
    }


def run(target_file: str = None):
    ensure_dirs()
    pdf_files = []

    if target_file:
        candidate = Path(target_file)
        if not candidate.is_absolute():
            candidate = RAW_DIR / target_file
        if not candidate.exists():
            console.print(f"\n[red]File not found:[/red] {candidate}")
            return []
        pdf_files = [candidate]
    else:
        pdf_files = sorted(RAW_DIR.glob("*.pdf"))

    if not pdf_files:
        console.print(f"\n[yellow]No PDFs found in {RAW_DIR}/[/yellow]")
        console.print(f"Place PDFs in: [bold]{RAW_DIR.resolve()}[/bold]\n")
        return []

    console.print(f"\n[bold]Nyaya - PDF Ingestion Pipeline[/bold]")
    console.print(f"Found [bold]{len(pdf_files)}[/bold] PDF(s)\n")

    results = [ingest_pdf(p) for p in pdf_files]

    MANIFEST_PATH.write_text(
        json.dumps({"total": len(results), "documents": results}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    console.print("\n")
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("File", min_width=30)
    table.add_column("Status", min_width=8)
    table.add_column("Characters", min_width=12)
    table.add_column("Sections", min_width=10)

    for r in results:
        table.add_row(
            r["file"],
            "[green]OK[/green]" if r["status"] == "ok" else "[red]FAILED[/red]",
            f"{r.get('chars', 0):,}",
            str(r.get('sections', 0)),
        )

    console.print(table)
    ok = sum(1 for r in results if r["status"] == "ok")
    console.print(f"[bold green]{ok}/{len(results)} PDFs processed successfully.[/bold green]")
    console.print(f"Output: [bold]{PROCESSED_DIR.resolve()}[/bold]\n")
    if ok > 0:
        console.print("[bold]Day 2 complete. Ready for Day 3.[/bold]\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default=None)
    args = parser.parse_args()
    run(target_file=args.file)