# Nyaya Legal AI — AI Continuation Handoff

**Purpose of this document:** Give another AI (or developer) everything needed to continue building **Nyaya** — an Indian legal assistant that behaves like a **lawyer explaining advice in simple words**, not a law textbook.

**Project root:** `d:\nyaya_day1\nyaya`  
**Run all commands from that folder.**

---

## 1. Product vision (current)

| Goal | Implementation |
|------|----------------|
| Act like a lawyer for the user | Answers use **“Legal advice in simple words”** framing, step-by-step options, practical next steps |
| Plain language | `core/knowledge.py` + `core/plain_language.py` replace jargon (allottee → home buyer, etc.) |
| Indian law focus | RERA delay/possession, Consumer Protection, legal notices |
| Multilingual queries | Hindi, Kannada, Tamil, Telugu, etc. via `deep-translator` + `langdetect` |
| Scan notices | Camera/upload → OCR → analyze as legal query |
| Draft documents | Legal notices/complaints + **how to serve** under Indian procedure |

**Disclaimer (always shown):** Informational guidance, not a substitute for a licensed advocate.

---

## 2. Architecture

```mermaid
graph TD
    UI[index.html - 3 tabs] --> API[FastAPI api/main.py]
    API --> Q[/query]
    API --> S[/scan]
    API --> D[/draft]
    API --> F[/feedback]
    Q --> P[core/pipeline.py]
    P --> ML[core/multilingual.py]
    P --> AB[core/answer_builder.py]
    P --> PL[core/plain_language.py]
    P --> KN[core/knowledge.py]
    AB --> HR[core/retrieve.py hybrid]
    HR --> EM[core/embeddings.py]
    HR --> CH[(ChromaDB nyaya_children)]
    S --> SC[core/scan.py]
    SC --> TESS[D:/Student Register/tesseract.exe]
    D --> LD[core/legal_draft.py]
    P --> CV[agents/citation_verifier.py]
    PL -.optional.-> OLL[Ollama local]
```

---

## 3. Tech stack

| Layer | Technology |
|-------|------------|
| API | FastAPI 0.136, Uvicorn |
| UI | Single `ui/index.html` (glassmorphic, vanilla JS) |
| Vector DB | ChromaDB 0.5.5, collection `nyaya_children` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (must match index + query) |
| LLM (optional) | Ollama — default `gaganyatri/sarvam-2b-v0.5` (weak; plain answers mostly rule-based) |
| OCR | Portable Tesseract 5.5 from `D:\Student Register` |
| Translation | Google via `deep-translator` |
| PDF ingest | PyMuPDF, pdfplumber |

---

## 4. How to run

```powershell
cd d:\nyaya_day1\nyaya
pip install -r requirements.txt
ollama serve
ollama pull gaganyatri/sarvam-2b-v0.5
python -X utf8 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Or: `.\run.ps1`

**Open:** http://127.0.0.1:8000

**Health check:** `GET /health` → `ready`, `chroma.chunk_count`, `ocr.tesseract_ready`, `ollama`

---

## 5. UI tabs

| Tab | Features |
|-----|----------|
| **Ask Nyaya** | Text query, **voice input** (Web Speech API, Chrome/Edge), language select, suggestion pills, results + citations + feedback stars |
| **Scan Notice** | Camera or upload image → `POST /scan` → OCR text → **Analyze This Notice** fills query and runs `/query` |
| **Draft Document** | Form → `POST /draft` → legal notice/complaint + service instructions (registered post, RERA portal, consumer court) |

---

## 6. API endpoints

| Method | Path | Body / notes |
|--------|------|----------------|
| GET | `/` | Serves `ui/index.html` |
| GET | `/health` | Status, Chroma count, Ollama, OCR |
| POST | `/query` | `{ query, top_k, translate, target_lang, doc_id? }` → full RAG response |
| POST | `/scan` | `multipart/form-data` file (image) → `{ text, success, engine, message }` |
| POST | `/draft` | `{ document_type, sender_name, sender_address, recipient_name, recipient_address, subject, facts, relief_sought, language }` |
| GET | `/document-types` | List of draft templates |
| POST | `/feedback` | `{ query, response, rating, feedback_text }` → appends `data/feedback/user_feedback.jsonl` |
| POST | `/ingest` | PDF ingestion |
| POST | `/index` | `{ refresh: true }` rebuild Chroma |

---

## 7. Core modules (what each file does)

| File | Role |
|------|------|
| `config.py` | Ollama, Chroma paths, OCR paths, `USE_PLAIN_LANGUAGE_AI` |
| `api/main.py` | FastAPI routes, CORS, startup warnings |
| `core/pipeline.py` | End-to-end `/query`: detect lang → translate → retrieve → build answer → plain language → translate back → citation verify |
| `core/answer_builder.py` | `hybrid_retrieve()` (vector + keyword), `build_answer()` |
| `core/knowledge.py` | Curated **simple lawyer-style** answers for RERA delay + consumer topics |
| `core/plain_language.py` | Jargon replacement, strip bad corpus excerpts, optional Ollama simplify |
| `core/retrieve.py` | Chroma query with **shared embeddings** (`query_embeddings`) |
| `core/embeddings.py` | Cached SentenceTransformer encode |
| `core/chunk.py` | Build index from `data/processed/*_sections.json` (min 80 chars/section) |
| `core/ingest.py` | PDF → processed JSON + txt |
| `core/scan.py` | OCR via `D:\Student Register\tesseract.exe` + image preprocess |
| `core/legal_draft.py` | 6 document types + `SERVICE_GUIDES` for Indian service of notice |
| `core/multilingual.py` | `detect_language`, `translate_to_english` |
| `agents/citation_verifier.py` | Regex citation extract + verify against retrieved sections |
| `ui/index.html` | Full frontend (tabs, voice, scan, draft) |

---

## 8. Query pipeline (detailed)

1. **Language:** `langdetect` on user query; optional translate to English.
2. **Retrieval:** `hybrid_retrieve()` — Chroma semantic (top 10) + keyword scan over parent sections; rerank; penalize auction/railway junk.
3. **Answer build:** If query matches `knowledge.py` topic (RERA delay, consumer) → use curated simple legal advice. Else short corpus extracts only (max 2 lines).
4. **Plain language:** `to_plain_language()` — term replacements, lawyer intro, disclaimer. AI rewrite via Ollama only if `USE_PLAIN_LANGUAGE_AI=true` (default **false** — Sarvam 2B echoes prompts).
5. **Citations:** `CitationVerifier.verify()` on final text.
6. **Translate back** to `target_lang` if requested.

---

## 9. Data state (typical)

| Path | Content |
|------|---------|
| `data/raw/` | Source PDFs |
| `data/processed/` | `*_sections.json` + `.txt` (~1500+ docs; manifest shows many ingest failures) |
| `data/chroma_db/` | Indexed child chunks (~22,074 when built with older keyword filter; rebuild with `python -m core.chunk --refresh` indexes all sections ≥80 chars) |
| `data/feedback/` | `user_feedback.jsonl` |

---

## 10. Environment (`.env`)

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gaganyatri/sarvam-2b-v0.5
CHROMA_PERSIST_DIR=./data/chroma_db
APP_PORT=8000
STUDENT_REGISTER_OCR_DIR=D:\Student Register
USE_PLAIN_LANGUAGE_AI=false
```

---

## 11. Work completed (changelog for continuation AI)

### RAG & answers
- Fixed **embedding mismatch** (index used manual vectors; queries now use `core/embeddings.py`).
- Replaced broken Sarvam-only generation with **curated + hybrid retrieval** answers.
- Added **simple lawyer-style** wording (`knowledge.py`, `plain_language.py`).
- Query expansion + reranking for RERA/consumer queries.
- Filtered dictionary/gazette garbage from displayed corpus lines.

### API & UX
- Enhanced `/health` (Chroma, Ollama, OCR).
- Removed hard Ollama requirement on `/query` (answers work without LLM).
- **3 tabs:** Ask (voice), Scan, Draft.
- Feedback binding fixed on first page load.
- 120s fetch timeout on queries.

### OCR
- Integrated **`D:\Student Register`** portable Tesseract (`tesseract.exe` + `tessdata\eng.traineddata`).
- `POST /scan` with PIL preprocess (grayscale, autocontrast, sharpen).

### Legal drafts
- `POST /draft` — 6 types: RERA notice, RERA complaint cover, consumer notice, consumer complaint, reply to notice, demand notice.
- Each includes **service instructions** (registered AD post, RERA portal, consumer commission, timelines).

### Ops
- `run.ps1`, `START.md`, `requirements.txt` updated.

### Tests
- `pytest tests/` — 4 tests passing (chunking, lang detect).

---

## 12. Known limitations

| Issue | Detail |
|-------|--------|
| Ollama Sarvam 2B | Poor instruction following; do not rely on it for main answers unless upgraded to llama3/mistral etc. |
| Retrieval quality | Corpus has dictionaries/acts tables; semantic search can return irrelevant sections (auction, etc.). |
| Ingest | ~60% PDF failures in manifest; scanned PDFs need OCR in ingest (not wired). |
| OCR languages | Only `eng` in Student Register tessdata; add `hin.traineddata` / `kan.traineddata` for better Indian language scans. |
| Not a real lawyer | Templates and curated text are informational; advocate review required before filing. |
| Chroma telemetry | Harmless `capture() takes 1 positional argument` warnings in logs. |

---

## 13. Recommended next steps (for next AI)

### High priority
1. **Stronger LLM** — Set `OLLAMA_MODEL=llama3.2` (or similar), enable `USE_PLAIN_LANGUAGE_AI=true` with strict output validation in `plain_language.py`.
2. **Expand `knowledge.py`** — More topics: eviction, cheque bounce (NI Act), divorce maintenance, labour rights — all in simple lawyer voice.
3. **Improve retrieval** — Metadata filters (`doc_type`, `act_name`), exclude dictionary docs from index rebuild.
4. **Hindi/Kannada OCR** — Copy traineddata into `D:\Student Register\tessdata`.

### Medium priority
5. Wire `core/ocr_ingest.py` into PDF ingest for scanned documents.
6. Draft tab: preview PDF, email/WhatsApp share link.
7. User session history (SQLite) for past queries and drafts.
8. Separate `ui/app.js` + component split (index.html is ~1500 lines).

### Low priority
9. Phoenix / LangGraph (mentioned in old README, not implemented).
10. Production deploy (Docker, nginx, HTTPS).

---

## 14. Key commands reference

```powershell
# Rebuild search index (full corpus, no old keyword filter)
python -X utf8 -m core.chunk --refresh

# Test query in terminal
python -X utf8 -c "from core.pipeline import run_pipeline; print(run_pipeline('RERA delay flat refund', target_lang='en')['answer'])"

# Test OCR
python -X utf8 -c "from core.scan import get_ocr_status; print(get_ocr_status())"

# Run tests
python -X utf8 -m pytest tests/ -q
```

---

## 15. Response JSON shape (`POST /query`)

```json
{
  "query": "user text",
  "detected_language": "en",
  "target_language": "en",
  "answer": "Legal advice in simple words...",
  "answer_en": "English version",
  "citations": {
    "status": "verified|partial|unverified",
    "verified": [],
    "unverified": [],
    "citations_found": { "sections": [], "articles": [], "chapters": [], "docs": [] }
  },
  "source_sections": []
}
```

---

## 16. Persona guidelines (for any new prompt engineering)

When modifying answers, the assistant should:

- Speak as a **patient Indian lawyer** explaining to a first-time client.
- Use **short sentences** and **numbered steps**.
- Explain any legal term in brackets the first time.
- Give **practical next steps** (which office, which documents, what deadline).
- End with a **soft disclaimer** (consult advocate for your exact case).
- **Never** dump raw statute text or dictionary entries to the user.

---

*Handoff generated for continuation by other AI tools. Update this file when major features land.*
