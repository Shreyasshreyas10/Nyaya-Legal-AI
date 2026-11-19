# Nyaya — Quick Start (Windows)

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) running locally
- Model: `ollama pull gaganyatri/sarvam-2b-v0.5`

## One-command start

```powershell
cd d:\nyaya_day1\nyaya
pip install -r requirements.txt
.\run.ps1
```

Open **http://localhost:8000** in your browser.

## Features

| Tab | What it does |
|-----|----------------|
| **Ask Nyaya** | Type or **voice** your legal question (mic button; Chrome/Edge) |
| **Scan Notice** | Camera/upload image → OCR → **Analyze This Notice** |
| **Draft Document** | Generate legal notice/complaint + **how to serve** under Indian law |

### OCR (Scan tab)

Uses portable **Tesseract 5.5** from `D:\Student Register` (`tesseract.exe` + `tessdata\`).

Ensure `.env` contains:

```
STUDENT_REGISTER_OCR_DIR=D:\Student Register
```

Optional: add `hin.traineddata` / `kan.traineddata` into that `tessdata` folder for better Hindi/Kannada scans.

```powershell
pip install pillow pytesseract
```

## Manual start

```powershell
cd d:\nyaya_day1\nyaya
pip install -r requirements.txt
ollama serve
python -X utf8 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Build / refresh search index

```powershell
python -X utf8 -m core.chunk --refresh
```

Or: `POST http://localhost:8000/index` with body `{"refresh": true}`

## Health check

`GET http://localhost:8000/health` — reports Chroma chunk count, Ollama model, and `ready` status.
