"""Curated lawyer-style guidance in simple language (informational only)."""

from __future__ import annotations

import re
from typing import List, Optional

TOPICS = [
    {
        "id": "rera_delay",
        "terms": (
            "rera", "delay", "possession", "flat", "buyer", "allottee", "builder",
            "apartment", "project", "handover", "compensation", "real estate",
        ),
        "min_hits": 2,
        "summary": "Your builder is late with the flat. RERA law protects you.",
        "answer": """**Quick answer:** You can claim a refund with interest, OR stay in the deal and get monthly compensation until possession.

**Your legal rights (RERA):**

1. **Full refund** — If possession is late beyond your agreement date (including allowed extension), you may cancel and get all money back **with interest**.

2. **Monthly compensation** — If you stay, the builder must pay **interest every month** until handover (usually bank rate + 2%).

3. **RERA complaint** — File on your **state RERA website**; they can order compensation and penalties.

4. **Consumer court** — You may also complain for poor service by the builder.

**Documents to keep ready:** flat agreement, payment receipts, allotment letter, RERA project number, emails/SMS about possession dates.
""",
        "next_steps": [
            "Send a legal notice to the builder by registered post (use Draft Document tab).",
            "File a complaint on your state RERA portal with all payment proofs.",
            "If no reply in 30 days, consult a lawyer for consumer court or RERA hearing.",
        ],
    },
    {
        "id": "consumer_deficiency",
        "terms": ("consumer", "deficiency", "service", "refund", "compensation", "forum", "commission"),
        "min_hits": 2,
        "summary": "A company or builder failed to deliver what was promised.",
        "answer": """**Quick answer:** You can complain as a **consumer** and ask for refund, repair, or compensation.

**Your legal rights:**

1. **Bad service** — Delay, poor quality, or broken promises = deficiency of service.

2. **Relief you can ask for** — Refund, replacement, compensation, and costs in fit cases.

3. **Where to file** — District Consumer Court (smaller claims) or State/National Commission (bigger claims).

4. **Time limit** — Act within about **two years** from when the problem started (unless extended for good reason).

**Documents to keep ready:** bills, agreement, photos, emails, warranty cards, and proof of payments.
""",
        "next_steps": [
            "Send a legal notice asking for refund/fix within 15 days (registered post).",
            "File complaint on edaakhil.nic.in or your state consumer commission portal.",
            "Attach notice, proofs of service, and all payment/receipt documents.",
        ],
    },
    {
        "id": "cheque_bounce",
        "terms": ("cheque", "check", "bounce", "dishonour", "dishonor", "138", "negotiable"),
        "min_hits": 2,
        "summary": "A cheque you received has bounced (not paid by the bank).",
        "answer": """**Quick answer:** Cheque bounce is a serious offence in India. You can send a legal notice and then file a criminal complaint.

**Your legal rights (Section 138, Negotiable Instruments Act):**

1. **Legal notice first** — Within **30 days** of bank dishonour memo, send notice to the person who gave the cheque demanding payment within **15 days**.

2. **Criminal complaint** — If they still do not pay, you may file a complaint in court within **one month** after the 15-day notice period ends.

3. **Civil recovery** — You can also file a civil suit to recover the money separately.

**Documents to keep ready:** original cheque, bank dishonour memo, copy of legal notice, postal proof, and any loan/agreement showing why they owed you money.
""",
        "next_steps": [
            "Collect the bank dishonour memo from your bank immediately.",
            "Send legal notice within 30 days of dishonour (registered AD post).",
            "If unpaid after 15 days from notice, consult a lawyer to file Section 138 complaint.",
        ],
    },
    {
        "id": "reply_notice",
        "terms": ("reply", "legal notice", "notice received", "respond", "response"),
        "min_hits": 2,
        "summary": "You received a legal notice and need to reply properly.",
        "answer": """**Quick answer:** Read the notice carefully, reply within the time given (usually 15–30 days), and do not admit fault unless your lawyer agrees.

**What you should do:**

1. **Check the deadline** — The notice will state how many days you have. Missing it can harm your case.

2. **Reply in writing** — Send a **registered post (AD)** reply to the address in the notice. Keep a copy and postal receipt.

3. **State your version** — Explain your facts calmly. Deny wrong claims without prejudice.

4. **Get a lawyer if serious** — Property, money, or criminal allegations need professional review.

**Documents to keep ready:** the notice, your reply copy, dispatch proof, and supporting papers (agreements, payments, messages).
""",
        "next_steps": [
            "Note the reply deadline on your calendar today.",
            "Draft reply using the Draft Document tab (Reply to Legal Notice).",
            "Send by registered post AD and keep tracking receipt.",
        ],
    },
]


def match_topic(query: str) -> Optional[dict]:
    q = query.lower()
    words = set(re.findall(r"[a-z0-9]+", q))
    best = None
    best_score = 0
    for topic in TOPICS:
        hits = sum(1 for term in topic["terms"] if term in words or term in q)
        if hits >= topic["min_hits"] and hits > best_score:
            best_score = hits
            best = topic
    return best


def get_next_steps(topic: Optional[dict]) -> List[str]:
    if not topic:
        return [
            "Write down dates, payments, and promises in one page.",
            "Collect agreements, receipts, and messages with the other party.",
            "Consider sending a legal notice before going to court (Draft Document tab).",
            "Consult a licensed advocate for your exact situation.",
        ]
    return list(topic.get("next_steps", []))
