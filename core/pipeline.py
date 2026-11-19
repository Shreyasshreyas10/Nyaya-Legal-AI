"""
core/pipeline.py — Nyaya RAG: lawyer-style guidance in simple words.
"""

from typing import Any, Dict

from rich.console import Console

from config import SUPPORTED_LANGUAGES, TOP_K_RETRIEVAL, USE_PLAIN_LANGUAGE_AI
from core.answer_builder import build_answer, hybrid_retrieve
from core.plain_language import to_plain_language
from core.multilingual import detect_language, translate_to_english
from agents.citation_verifier import CitationVerifier

console = Console()
citation_verifier = CitationVerifier()


def translate_from_english(text: str, target_lang: str) -> str:
    if not target_lang or target_lang in ("en", "unknown"):
        return text
    if target_lang not in SUPPORTED_LANGUAGES:
        return text
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="en", target=target_lang).translate(text)
    except Exception as exc:
        console.print(f"[red]Translation back to {target_lang} failed: {exc}[/red]")
        return text


def _empty_response(query: str, detected_lang: str, target_lang: str, translate: bool) -> Dict[str, Any]:
    built = build_answer(query, [])
    answer_en = to_plain_language(query, built["body"], use_ai=USE_PLAIN_LANGUAGE_AI)
    final = translate_from_english(answer_en, target_lang) if translate and target_lang not in ("en", "unknown") else answer_en
    return {
        "query": query,
        "detected_language": detected_lang,
        "target_language": target_lang,
        "answer": final,
        "answer_en": answer_en,
        "topic_id": built.get("topic_id"),
        "next_steps": built.get("next_steps", []),
        "citations": {
            "status": "unverified",
            "verified": [],
            "unverified": [],
            "citations_found": {"sections": [], "articles": [], "chapters": [], "docs": []},
        },
        "source_sections": [],
    }


def run_pipeline(
    query: str,
    target_lang: str = "auto",
    top_k: int = TOP_K_RETRIEVAL,
    translate: bool = True,
    doc_id: str | None = None,
) -> Dict[str, Any]:
    console.print(f"\n[bold blue]Nyaya pipeline:[/bold blue] '{query}'")

    detected_lang = detect_language(query)
    if target_lang == "auto":
        target_lang = detected_lang if detected_lang in SUPPORTED_LANGUAGES else "en"

    if translate and detected_lang not in ("en", "unknown"):
        english_query = translate_to_english(query, source_lang=detected_lang)
    else:
        english_query = query

    if doc_id:
        from core.retrieve import retrieve
        retrieved_sections = retrieve(english_query, top_k=top_k, doc_id=doc_id)
    else:
        retrieved_sections = hybrid_retrieve(english_query, top_k=top_k)

    console.print(f"  Retrieved {len(retrieved_sections)} section(s)")

    if not retrieved_sections:
        return _empty_response(query, detected_lang, target_lang, translate)

    built = build_answer(english_query, retrieved_sections)
    answer_en = to_plain_language(english_query, built["body"], use_ai=USE_PLAIN_LANGUAGE_AI)
    verification_report = citation_verifier.verify(answer_en, retrieved_sections)

    final_answer = (
        translate_from_english(answer_en, target_lang)
        if translate and target_lang not in ("en", "unknown")
        else answer_en
    )

    if target_lang != "en":
        for citation in verification_report.get("verified", []):
            if "snippet" in citation:
                citation["snippet_translated"] = translate_from_english(citation["snippet"], target_lang)
            if "heading" in citation:
                citation["heading_translated"] = translate_from_english(citation["heading"], target_lang)

    return {
        "query": query,
        "detected_language": detected_lang,
        "target_language": target_lang,
        "answer": final_answer,
        "answer_en": answer_en,
        "topic_id": built.get("topic_id"),
        "next_steps": built.get("next_steps", []),
        "citations": verification_report,
        "source_sections": retrieved_sections,
    }
