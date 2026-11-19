"""Build clear legal answers from retrieved sections and topic knowledge."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from core.knowledge import get_next_steps, match_topic
from core.retrieve import load_parent_sections, retrieve

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "what", "how", "when", "where",
    "who", "why", "can", "could", "should", "would", "for", "and", "or", "to",
    "of", "in", "on", "at", "by", "with", "from", "my", "me", "i", "we", "you",
    "under", "about", "this", "that", "be", "been", "have", "has", "had", "do",
    "does", "did", "will", "shall", "may", "might", "must", "not", "no", "yes",
    "act", "law", "legal", "rights", "right", "claim", "india", "indian",
}


def _query_terms(query: str) -> List[str]:
    terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 2 and t not in STOPWORDS]
    if "rera" in query.lower() and "rera" not in terms:
        terms.append("rera")
    return terms


def _section_label(sec: dict) -> str:
    heading = (sec.get("heading") or "").strip()
    if heading and len(heading) < 120:
        return heading
    return sec.get("section_id", "Provision")


def _split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    parts = re.split(r"(?<=[.;!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 40]


def _sentence_score(sentence: str, terms: List[str]) -> int:
    lower = sentence.lower()
    score = sum(3 if term in lower else 0 for term in terms)
    if any(ch.isdigit() for ch in sentence) and re.search(r"\bsection\b", lower):
        score += 2
    if len(sentence) > 600:
        score -= 2
    garbage = (
        "auctioneer", "gazette of india extraordinary", "inspecting officer may, after",
        "english-hindi", "workmen's compensation", "workmen s compensation", "unit trust of india",
        "shore nuisances", "railway property", "plant disease", "flat surface [s",
    )
    if any(g in lower for g in garbage):
        score -= 12
    return score


def _pick_sentences(content: str, terms: List[str], limit: int = 2) -> List[str]:
    ranked = sorted(_split_sentences(content), key=lambda s: _sentence_score(s, terms), reverse=True)
    picked = []
    for sentence in ranked:
        if _sentence_score(sentence, terms) <= 0:
            continue
        if sentence in picked:
            continue
        picked.append(sentence[:500])
        if len(picked) >= limit:
            break
    return picked


@lru_cache(maxsize=1)
def _parent_index() -> Dict[str, dict]:
    return load_parent_sections()


def keyword_retrieve(query: str, top_k: int = 5) -> List[dict]:
    terms = _query_terms(query)
    if not terms:
        return []

    scored: List[Tuple[int, dict]] = []
    for parent_id, sec in _parent_index().items():
        text = f"{sec.get('heading', '')} {sec.get('content', '')}".lower()
        score = sum(text.count(term) * (4 if len(term) > 4 else 2) for term in terms)
        if "rera" in query.lower():
            if "rera" in text or "real estate (regulation" in text:
                score += 25
            if "allottee" in text or "promoter" in text:
                score += 10
        if score <= 0:
            continue
        item = {
            "parent_id": parent_id,
            "doc_id": sec.get("doc_id", "unknown"),
            "section_id": sec.get("section_id", "unknown"),
            "heading": sec.get("heading", ""),
            "content": sec.get("content", ""),
            "top_chunks": [],
            "keyword_score": score,
        }
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def hybrid_retrieve(query: str, top_k: int = 3) -> List[dict]:
    vector_hits = retrieve(query, top_k=max(top_k * 3, 10))
    keyword_hits = keyword_retrieve(query, top_k=max(top_k * 2, 6))

    merged: Dict[str, dict] = {}
    for sec in keyword_hits + vector_hits:
        pid = sec.get("parent_id")
        if not pid:
            continue
        if pid not in merged:
            merged[pid] = sec
        else:
            merged[pid]["keyword_score"] = max(
                merged[pid].get("keyword_score", 0),
                sec.get("keyword_score", 0),
            )

    terms = _query_terms(query)

    def rank(sec: dict) -> int:
        text = f"{sec.get('heading', '')} {sec.get('content', '')}".lower()
        kw = sec.get("keyword_score", 0)
        overlap = sum(1 for t in terms if t in text)
        penalty = 0
        if any(g in text for g in ("auctioneer", "railway property", "plant disease", "dictionary")):
            penalty += 15
        return kw + overlap * 3 - penalty

    ordered = sorted(merged.values(), key=rank, reverse=True)
    return ordered[:top_k]


def build_answer(query: str, sections: List[dict]) -> dict:
    topic = match_topic(query)
    terms = _query_terms(query)
    parts: List[str] = []

    if topic:
        parts.append(f"**Legal advice in simple words**\n\n**In one line:** {topic['summary']}\n")
        parts.append(topic["answer"].strip())
        steps = get_next_steps(topic)
        if steps:
            parts.append("**What to do next (practical steps):**")
            parts.extend(f"{i}. {step}" for i, step in enumerate(steps, start=1))
    else:
        parts.append("**Legal advice in simple words**\n\n")
        parts.append(
            "I found some related legal material in our library, but no exact ready-made guide for your question. "
            "Here is general direction:"
        )
        corpus_points: List[str] = []
        for sec in sections:
            heading_lower = (sec.get("heading") or "").lower()
            if any(skip in heading_lower for skip in ("english-hindi", "dictionary", "glossary", "full document")):
                continue
            label = _section_label(sec)
            sentences = _pick_sentences(sec.get("content", ""), terms, limit=1)
            for sentence in sentences:
                if _sentence_score(sentence, terms) < 4:
                    continue
                corpus_points.append(f"- {sentence}")
        if corpus_points:
            parts.extend(corpus_points[:2])
        steps = get_next_steps(None)
        parts.append("**What to do next (practical steps):**")
        parts.extend(f"{i}. {step}" for i, step in enumerate(steps, start=1))

    if not topic and not sections:
        body = (
            "**Legal advice in simple words**\n\n"
            "I could not find a clear match for your question in our legal library.\n\n"
            "Try asking with words like: **RERA**, **possession delay**, **refund**, **builder**, "
            "**consumer court**, **cheque bounce**, or **legal notice reply**.\n\n"
            "**What to do next:**\n"
            "1. Rephrase your question with more detail (dates, amounts, names).\n"
            "2. Use the **Scan Notice** tab if you have a paper notice.\n"
            "3. Use the **Draft Document** tab to send a formal legal notice.\n"
            "4. Speak to a licensed advocate for case-specific strategy."
        )
        return {"body": body, "topic_id": None, "next_steps": get_next_steps(None)}

    return {
        "body": "\n\n".join(parts),
        "topic_id": topic["id"] if topic else None,
        "next_steps": get_next_steps(topic),
    }
