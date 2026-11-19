"""OCR for legal notices — uses portable Tesseract from Student Register."""

from __future__ import annotations

import io
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from config import STUDENT_REGISTER_OCR_DIR, TESSERACT_EXE, TESSDATA_DIR

TESSERACT_PATHS = [
    str(TESSERACT_EXE),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


def _student_register_ocr_ready() -> bool:
    return TESSERACT_EXE.is_file() and TESSDATA_DIR.is_dir() and (TESSDATA_DIR / "eng.traineddata").is_file()


def _configure_pytesseract() -> Optional[str]:
    try:
        import pytesseract
    except ImportError:
        return None

    for path in TESSERACT_PATHS:
        if path and os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return path
    return None


def clean_ocr_text(text: str) -> str:
    text = re.sub(
        r"[^\x09\x0A\x0D\x20-\x7E\u0900-\u097F\u0C80-\u0CFF\u0B80-\u0BFF\u0C00-\u0C7F\u0980-\u09FF]",
        " ",
        text,
    )
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _preprocess_image(data: bytes):
    from PIL import Image, ImageEnhance, ImageOps

    image = Image.open(io.BytesIO(data))
    if image.mode not in ("L", "RGB"):
        image = image.convert("RGB")
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Sharpness(gray).enhance(1.4)
    return gray


def _ocr_lang() -> str:
    langs = ["eng"]
    if (TESSDATA_DIR / "hin.traineddata").is_file():
        langs.append("hin")
    if (TESSDATA_DIR / "kan.traineddata").is_file():
        langs.append("kan")
    return "+".join(langs)


def ocr_via_student_register_tesseract(image_bytes: bytes) -> dict:
    """Run bundled tesseract.exe from D:\\Student Register."""
    if not _student_register_ocr_ready():
        return {
            "text": "",
            "success": False,
            "engine": "none",
            "message": f"Tesseract not found at {STUDENT_REGISTER_OCR_DIR}. Check STUDENT_REGISTER_OCR_DIR in .env",
        }

    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        return {"text": "", "success": False, "engine": "none", "message": "Install pillow: pip install pillow"}

    try:
        processed = _preprocess_image(image_bytes)
        with tempfile.TemporaryDirectory() as tmp:
            img_path = Path(tmp) / "notice.png"
            out_base = Path(tmp) / "out"
            processed.save(img_path, format="PNG")

            env = os.environ.copy()
            env.pop("TESSDATA_PREFIX", None)
            cmd = [
                str(TESSERACT_EXE),
                str(img_path),
                str(out_base),
                "-l",
                _ocr_lang(),
                "--psm",
                "6",
                "--oem",
                "1",
                "--tessdata-dir",
                str(TESSDATA_DIR),
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=120,
                cwd=str(STUDENT_REGISTER_OCR_DIR),
            )
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "Unknown tesseract error").strip()
                return {"text": "", "success": False, "engine": "student_register", "message": err[:500]}

            txt_path = Path(f"{out_base}.txt")
            raw = txt_path.read_text(encoding="utf-8", errors="replace") if txt_path.exists() else ""
            text = clean_ocr_text(raw)
            if len(text) < 15:
                return {
                    "text": text,
                    "success": False,
                    "engine": "student_register",
                    "message": "Very little text detected. Retake in good light with the full notice visible.",
                }
            return {
                "text": text,
                "success": True,
                "engine": "student_register",
                "message": "Scanned with Student Register Tesseract OCR.",
            }
    except subprocess.TimeoutExpired:
        return {"text": "", "success": False, "engine": "student_register", "message": "OCR timed out."}
    except Exception as exc:
        return {"text": "", "success": False, "engine": "student_register", "message": f"OCR failed: {exc}"}


def ocr_via_pytesseract(image_bytes: bytes) -> dict:
    import pytesseract
    from PIL import Image

    if not _configure_pytesseract():
        return {"text": "", "success": False, "engine": "pytesseract", "message": "Tesseract executable not configured."}

    os.environ.pop("TESSDATA_PREFIX", None)
    image = _preprocess_image(image_bytes)
    raw = pytesseract.image_to_string(
        image,
        lang=_ocr_lang(),
        config=f"--psm 6 --oem 1 --tessdata-dir {TESSDATA_DIR}",
    )
    text = clean_ocr_text(raw)
    if len(text) < 15:
        return {
            "text": text,
            "success": False,
            "engine": "pytesseract",
            "message": "Very little text detected.",
        }
    return {
        "text": text,
        "success": True,
        "engine": "pytesseract",
        "message": "Scanned with Tesseract (pytesseract).",
    }


def ocr_image_bytes(data: bytes, lang: str = "eng+hin") -> dict:
    """Primary OCR entry — prefers Student Register portable Tesseract."""
    del lang  # languages resolved from tessdata folder

    if _student_register_ocr_ready():
        result = ocr_via_student_register_tesseract(data)
        if result.get("success"):
            return result
        fallback = ocr_via_pytesseract(data)
        if fallback.get("success"):
            fallback["message"] = f"{result.get('message', '')} Used pytesseract fallback."
            return fallback
        return result

    exe = _configure_pytesseract()
    if exe:
        return ocr_via_pytesseract(data)

    return {
        "text": "",
        "success": False,
        "engine": "none",
        "message": (
            f"No OCR engine found. Set Student Register path (current: {STUDENT_REGISTER_OCR_DIR}) "
            "or install Tesseract system-wide."
        ),
    }


def get_ocr_status() -> dict:
    return {
        "student_register_dir": str(STUDENT_REGISTER_OCR_DIR),
        "tesseract_exe": str(TESSERACT_EXE),
        "tesseract_ready": _student_register_ocr_ready(),
        "languages": _ocr_lang(),
        "tessdata": str(TESSDATA_DIR),
    }
