import json
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.legal_draft import DOCUMENT_TYPES, draft_document
from core.scan import get_ocr_status, ocr_image_bytes

from config import APP_HOST, APP_PORT, CHROMA_PERSIST_DIR, OLLAMA_BASE_URL, OLLAMA_MODEL
from core.chunk import build_vector_store, get_embedding_device
from core.ingest import run as ingest_run
from core.retrieve import get_collection_stats

app = FastAPI(
    title="Nyaya Legal AI API",
    description="PDF ingestion, embeddings, and retrieval for Indian legal documents.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ui_path = Path("ui")
if ui_path.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_path), html=True), name="ui")


class IngestRequest(BaseModel):
    file: Optional[str] = Field(
        None,
        description="Optional file name in data/raw or absolute PDF path to ingest.",
    )


class BuildIndexRequest(BaseModel):
    refresh: bool = Field(False, description="Rebuild the ChromaDB index from scratch.")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = Field(3, ge=1, le=20)
    translate: bool = Field(True, description="Auto-translate non-English queries to English before retrieval.")
    target_lang: Optional[str] = Field("auto", description="Target language code (e.g. en, hi, kn) or 'auto'.")
    doc_id: Optional[str] = Field(None, description="Optional document id filter for retrieval.")


class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None


class DraftRequest(BaseModel):
    document_type: str = Field("rera_legal_notice", description="Type of legal document to generate.")
    sender_name: str = Field(..., min_length=2)
    sender_address: str = Field(..., min_length=5)
    recipient_name: str = Field(..., min_length=2)
    recipient_address: str = Field(..., min_length=5)
    subject: str = Field(..., min_length=3)
    facts: str = Field(..., min_length=10)
    relief_sought: str = Field(..., min_length=10)
    language: str = Field("en", description="en, hi, or kn for draft language note.")


def _ollama_status() -> dict:
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3.0)
        r.raise_for_status()
        models = [m.get("name", "") for m in r.json().get("models", [])]
        model_ready = any(OLLAMA_MODEL in name or name.startswith(OLLAMA_MODEL) for name in models)
        return {"reachable": True, "model": OLLAMA_MODEL, "model_ready": model_ready, "models": models}
    except Exception as exc:
        return {"reachable": False, "model": OLLAMA_MODEL, "model_ready": False, "error": str(exc)}


@app.on_event("startup")
def startup_checks():
    stats = get_collection_stats()
    if not stats["ready"] or stats["chunk_count"] == 0:
        print("[Nyaya] WARNING: ChromaDB index is empty. Run: python -m core.chunk --refresh")
    ollama = _ollama_status()
    if not ollama.get("model_ready"):
        print(f"[Nyaya] WARNING: Ollama model '{OLLAMA_MODEL}' not loaded. Run: ollama pull {OLLAMA_MODEL}")


@app.get("/health")
def health() -> dict:
    chroma = get_collection_stats()
    ollama = _ollama_status()
    ready = chroma["ready"] and chroma["chunk_count"] > 0 and ollama.get("model_ready", False)
    return {
        "status": "ok" if ready else "degraded",
        "ready": ready,
        "chroma": chroma,
        "chroma_persist_dir": str(Path(CHROMA_PERSIST_DIR).resolve()),
        "embedding_device": get_embedding_device(),
        "ollama": ollama,
        "ocr": get_ocr_status(),
    }


@app.get("/status")
def status() -> dict:
    return health()


@app.get("/", response_model=None)
def root():
    landing = Path("ui/index.html")
    if landing.exists():
        return FileResponse(landing)
    return {"message": "Nyaya API is running. Use /docs for API documentation."}


@app.post("/ingest")
def ingest(request: IngestRequest) -> dict:
    file_val = request.file
    if file_val:
        candidate = Path(file_val)
        if not candidate.is_absolute():
            candidate = Path("data/raw") / file_val
        if not candidate.exists():
            raise HTTPException(status_code=404, detail=f"PDF not found: {candidate}")
        file_val = str(candidate)

    results = ingest_run(target_file=file_val)
    if not results:
        raise HTTPException(status_code=404, detail="No PDFs were ingested.")

    return {"status": "ok", "documents": results}


@app.post("/index")
def build_index(request: BuildIndexRequest) -> dict:
    build_vector_store(refresh=request.refresh)
    chroma = get_collection_stats()
    return {"status": "ok", "refresh": request.refresh, "chroma": chroma}


@app.post("/query")
def search(request: QueryRequest) -> dict:
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    chroma = get_collection_stats()
    if not chroma["ready"] or chroma["chunk_count"] == 0:
        print("[Nyaya] WARNING: ChromaDB index is empty or not ready. Falling back to keyword-only retrieval.")

    try:
        from core.pipeline import run_pipeline

        return run_pipeline(
            query=query_text,
            target_lang=request.target_lang or "auto",
            top_k=request.top_k,
            translate=request.translate,
            doc_id=request.doc_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/document-types")
def document_types() -> dict:
    return {"types": DOCUMENT_TYPES}


@app.post("/scan")
async def scan_notice(file: UploadFile = File(...)) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload a JPG or PNG image of the notice.")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 10 MB.")
    result = ocr_image_bytes(data)
    return {
        "status": "ok" if result.get("success") else "partial",
        "filename": file.filename,
        **result,
    }


@app.post("/draft")
def generate_draft(request: DraftRequest) -> dict:
    try:
        return {"status": "ok", **draft_document(**request.model_dump())}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/feedback")
def submit_feedback(request: FeedbackRequest) -> dict:
    feedback_dir = Path("data/feedback")
    feedback_dir.mkdir(parents=True, exist_ok=True)
    feedback_file = feedback_dir / "user_feedback.jsonl"

    feedback_entry = {
        "query": request.query,
        "response": request.response,
        "rating": request.rating,
        "feedback_text": request.feedback_text,
    }

    try:
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")
        return {"status": "ok", "message": "Feedback submitted successfully."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {exc}") from exc
