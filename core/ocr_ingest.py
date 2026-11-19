"""
core/ocr_ingest.py
Day 3 — OCR Fallback for scanned PDF documents.
Usage:
    python -m core.ocr_ingest
"""

import json
import os
import sys
from pathlib import Path
from rich.console import Console

# Import helper functions from core.ingest
try:
    from core.ingest import clean_text, detect_sections
except ImportError:
    # Fallback in case of execution context issues
    import re
    def clean_text(text: str) -> str:
        text = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u0900-\u097F\u0C00-\u0C7F\u0B80-\u0BFF\u0C80-\u0CFF\u0980-\u09FF]', ' ', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def detect_sections(text: str) -> list:
        return [{"section_id": "full_doc", "heading": "Full Document", "content": text}]

console = Console()

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
MANIFEST_PATH = Path("data/processed/manifest.json")

# Configure OCR tool paths (Tesseract and Poppler)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler\Library\bin"  # Adjust depending on where poppler is extracted

def configure_ocr_paths():
    # If the default paths exist, register them
    if os.path.exists(TESSERACT_CMD):
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
            console.print(f"[green]Registered Tesseract from {TESSERACT_CMD}[/green]")
        except ImportError:
            pass
    else:
        console.print(f"[yellow]Tesseract executable not found at '{TESSERACT_CMD}'[/yellow]")

    if os.path.exists(POPPLER_PATH):
        console.print(f"[green]Poppler found at {POPPLER_PATH}[/green]")
    else:
        console.print(f"[yellow]Poppler bin folder not found at '{POPPLER_PATH}'[/yellow]")


def ocr_pdf(pdf_path: Path) -> str:
    try:
        import pytesseract
        from pdf2image import convert_from_path
        from PIL import Image
    except ImportError as e:
        console.print(f"[red]Missing Python OCR dependencies: {e}[/red]")
        console.print("Please install: pip install pytesseract pdf2image pillow")
        return ""

    if not os.path.exists(TESSERACT_CMD) and not any(os.path.exists(os.path.join(p, "tesseract.exe")) for p in os.environ.get("PATH", "").split(os.pathsep)):
        console.print("[red]Tesseract OCR is not installed or not in PATH.[/red]")
        return ""

    console.print(f"  [yellow]Running OCR on {pdf_path.name}...[/yellow]")
    try:
        # Convert PDF pages to images
        poppler_param = POPPLER_PATH if os.path.exists(POPPLER_PATH) else None
        pages = convert_from_path(str(pdf_path), dpi=150, poppler_path=poppler_param)
        
        extracted_text_list = []
        for i, page in enumerate(pages, start=1):
            console.print(f"    OCR-ing page {i}/{len(pages)}...")
            text = pytesseract.image_to_string(page)
            extracted_text_list.append(text)
        
        full_text = "\n".join(extracted_text_list)
        return full_text
    except Exception as exc:
        console.print(f"  [red]OCR processing failed for {pdf_path.name}: {exc}[/red]")
        return ""


def run_ocr_ingestion():
    configure_ocr_paths()
    
    if not MANIFEST_PATH.exists():
        console.print(f"[red]Manifest file not found at {MANIFEST_PATH}. Run ingestion first.[/red]")
        return

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        console.print(f"[red]Failed to read manifest file: {exc}[/red]")
        return

    documents = manifest.get("documents", [])
    failed_docs = [doc for doc in documents if doc.get("status") == "failed"]
    
    if not failed_docs:
        console.print("[green]No failed documents in manifest to OCR.[/green]")
        return

    console.print(f"[bold]Found {len(failed_docs)} failed document(s) for OCR fallback.[/bold]")

    updated_count = 0
    for doc_entry in documents:
        if doc_entry.get("status") == "failed":
            file_name = doc_entry["file"]
            pdf_path = RAW_DIR / file_name
            if not pdf_path.exists():
                console.print(f"[red]File {file_name} not found in raw directory.[/red]")
                continue

            text = ocr_pdf(pdf_path)
            if text and len(text.strip()) > 100:
                text = clean_text(text)
                sections = detect_sections(text)
                out_name = pdf_path.stem
                
                # Save extracted text and sections
                (PROCESSED_DIR / f"{out_name}.txt").write_text(text, encoding="utf-8")
                (PROCESSED_DIR / f"{out_name}_sections.json").write_text(
                    json.dumps({
                        "source_file": file_name,
                        "doc_id": out_name,
                        "total_chars": len(text),
                        "section_count": len(sections),
                        "sections": sections,
                    }, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )

                # Update manifest entry
                doc_entry["doc_id"] = out_name
                doc_entry["chars"] = len(text)
                doc_entry["sections"] = len(sections)
                doc_entry["status"] = "ok"
                updated_count += 1
                console.print(f"  [green]Successfully OCR'd and saved {file_name}[/green]")
            else:
                console.print(f"  [red]OCR extracted insufficient text from {file_name}. Stays failed.[/red]")

    if updated_count > 0:
        # Save updated manifest
        MANIFEST_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        console.print(f"[green]Manifest updated: {updated_count} documents recovered via OCR.[/green]")
    else:
        console.print("[yellow]No documents were successfully updated via OCR.[/yellow]")


if __name__ == "__main__":
    run_ocr_ingestion()
