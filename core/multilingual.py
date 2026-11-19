from langdetect import DetectorFactory, detect
from deep_translator import GoogleTranslator

from config import SUPPORTED_LANGUAGES

DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    try:
        language_code = detect(text)
        return language_code
    except Exception:
        return "unknown"


def translate_to_english(text: str, source_lang: str | None = None) -> str:
    source_lang = source_lang or detect_language(text)
    if source_lang == "en":
        return text

    if source_lang not in SUPPORTED_LANGUAGES:
        source_lang = "auto"

    try:
        translator = GoogleTranslator(source=source_lang, target="en")
        return translator.translate(text)
    except Exception:
        return text
