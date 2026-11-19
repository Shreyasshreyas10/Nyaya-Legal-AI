# Nyaya — AI-Powered Indian Legal Advisory System

Multi-agent RAG pipeline · Sarvam LLM · LangGraph · Multilingual · Arize Phoenix

---

## Team
| Name | USN |
|---|---|
| Shreyas Savant | 02FE23BCS078 |
| Pooja Managuli | 02FE23BCS072 |
| Anusha Kattimani | 02FE23BCS016 |
| Kushal Itnal | 02FE23BCS015 |

---

## Setup (Day 1)

### Prerequisites
- Python 3.11
- [Ollama](https://ollama.com) installed
- NVIDIA GPU with 6+ GB VRAM recommended

### Install

```bash
# 1. Clone / create project folder
cd nyaya

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull Sarvam model via Ollama
ollama pull sarvam2b

# 5. Copy and edit environment file
cp .env .env.local               # edit if needed

# 6. Verify everything works
python verify_setup.py
```

### Run

```bash
# Start the FastAPI service from the nyaya folder
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Minimal UI: http://localhost:8000/

> For GPU acceleration, install PyTorch with CUDA support separately before running the index builder.

---

## Project Structure

```
nyaya/
├── data/
│   ├── raw/          # downloaded PDFs from legislative.gov.in
│   ├── processed/    # extracted clean text files
│   └── chroma_db/    # vector store (auto-created)
├── agents/          # future agent extensions
├── api/
│   └── main.py       # FastAPI app
├── core/
│   ├── ingest.py         # PDF ingestion
│   ├── chunk.py          # chunking + embeddings
│   ├── retrieve.py       # retrieval from ChromaDB
│   └── multilingual.py   # language detection + translation
├── ui/
│   └── index.html    # simple browser demo
├── tests/
│   ├── test_core.py
│   └── test_pipeline.py
├── config.py
├── download_corpus.py
├── verify_setup.py
├── run.sh
└── requirements.txt
```

---

## Dataset
Source: https://www.legislative.gov.in/documents

Documents: Constitution of India, Central Acts, CPA 2019, RERA, IPC, guidelines, orders.

---

## Supported Languages
English, Hindi, Kannada, Tamil, Telugu, Marathi, Bengali, Malayalam, Gujarati, Punjabi

---

## Architecture
See `docs/architecture.png` (sequence diagram exported from mermaid.live)
