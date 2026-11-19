"""Lawyer-style plain language for Nyaya answers."""

from __future__ import annotations

import re
from typing import Optional

from config import OLLAMA_BASE_URL, OLLAMA_MODEL

TERM_REPLACEMENTS = [
    (r"\ballottee\b", "home buyer"),
    (r"\bpromoter\b", "builder"),
    (r"\bstatutory\b", "fixed by law"),
    (r"\bregulatory complaint\b", "official complaint"),
    (r"\bdeficiency of service\b", "poor or incomplete service"),
    (r"\bcompetent forums\b", "proper courts or complaint bodies"),
    (r"\bSBI highest marginal cost of lending rate \+ 2%", "bank lending rate plus 2% extra"),
    (r"\bagreement for sale\b", "flat booking agreement"),
]


def simplify_with_rules(text: str) -> str:
    for pattern, replacement in TERM_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
        elif lines and lines[-1]:
            lines.append("")
    return "\n".join(lines).strip()


def _with_disclaimer(text: str) -> str:
    note = (
        "\n\n---\n*General legal information only — not a formal opinion from a licensed advocate. "
        "For court filings or serious disputes, meet a lawyer in person.*"
    )
    if "licensed advocate" in text.lower() or "not a formal opinion" in text.lower():
        return text
    return text + note


def to_plain_language(question: str, legal_answer: str, use_ai: bool = False) -> str:
    """Format answer in simple lawyer voice. AI off by default (weak local models)."""
    text = simplify_with_rules(legal_answer)
    if "**legal advice in simple words**" not in text.lower()[:200]:
        q = question.strip()[:100]
        text = (
            f"**Legal advice in simple words**\n\n"
            f"**Your question:** {q}\n\n"
            f"{text}"
        )
    return _with_disclaimer(text)
