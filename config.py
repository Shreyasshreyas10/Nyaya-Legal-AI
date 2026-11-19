from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "gaganyatri/sarvam-2b-v0.5")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

PHOENIX_HOST = os.getenv("PHOENIX_HOST", "localhost")
PHOENIX_PORT = int(os.getenv("PHOENIX_PORT", 6006))

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "bn": "Bengali",
    "ml": "Malayalam",
    "gu": "Gujarati",
    "pa": "Punjabi",
}

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_PARENT_SIZE = 1000
CHUNK_CHILD_SIZE  = 150
CHUNK_OVERLAP     = 20

TOP_K_RETRIEVAL = 3

# Portable Tesseract from Student Register project
STUDENT_REGISTER_OCR_DIR = Path(os.getenv("STUDENT_REGISTER_OCR_DIR", r"D:\Student Register"))
TESSERACT_EXE = Path(os.getenv("TESSERACT_EXE", str(STUDENT_REGISTER_OCR_DIR / "tesseract.exe")))
TESSDATA_DIR = Path(os.getenv("TESSDATA_DIR", str(STUDENT_REGISTER_OCR_DIR / "tessdata")))

# Rewrite answers in simple words using Ollama (falls back to rules if model fails)
USE_PLAIN_LANGUAGE_AI = os.getenv("USE_PLAIN_LANGUAGE_AI", "false").lower() in ("1", "true", "yes")
