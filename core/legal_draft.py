"""Generate Indian legal notices/documents with service-of-notice guidance."""

from __future__ import annotations

from datetime import date
from typing import Dict, List

DOCUMENT_TYPES = {
    "rera_legal_notice": "Legal Notice to Builder/Promoter (RERA)",
    "rera_authority_complaint": "Complaint Cover Letter to State RERA Authority",
    "consumer_legal_notice": "Legal Notice under Consumer Protection Act",
    "consumer_complaint": "Consumer Commission Complaint — Cover Page",
    "reply_to_notice": "Reply to Legal Notice",
    "demand_notice": "Demand Notice (General Civil)",
}

SERVICE_GUIDES: Dict[str, List[str]] = {
    "rera_legal_notice": [
        "Send by **Registered Post AD / Speed Post** to the promoter’s registered office and project address.",
        "Send a copy to the **concerned State RERA Authority** (as per project registration state).",
        "Retain postal receipts, tracking, copy of notice, and annexures for evidence.",
        "Allow **15–30 days** (as stated in your notice) for compliance before escalation.",
        "If no remedy, file complaint on the **state RERA portal** and attach this notice with proof of service.",
    ],
    "rera_authority_complaint": [
        "File online on your **State RERA website** (Maharashtra MahaRERA, Karnataka K-RERA, etc.).",
        "Upload: agreement for sale, payment proofs, allotment letter, delay evidence, and this cover letter.",
        "Keep the **complaint reference number** and email/SMS acknowledgements.",
        "The authority may seek promoter reply; respond within given timelines.",
    ],
    "consumer_legal_notice": [
        "Serve on the **opposite party** (builder/company) at registered/corporate address by **Registered AD post**.",
        "Keep **postal proof**, copy of notice, and invoices/agreements as annexures.",
        "Wait for the notice period (commonly **15 to 30 days**) before filing complaint.",
        "Jurisdiction: file before **District Consumer Commission** (or State/National based on claim value).",
    ],
    "consumer_complaint": [
        "File through **edaakhil.nic.in** (National Consumer Helpline / commission portals) or state commission portal.",
        "Attach: notice copy, proof of service, agreement, payment receipts, correspondence.",
        "Pay prescribed fee; serve commission notice on opposite party when directed.",
    ],
    "reply_to_notice": [
        "Send reply within the **time limit stated in the incoming notice** (usually 15–30 days).",
        "Use **Registered Post AD** with acknowledgment due to the sender’s address in the notice.",
        "Keep a signed copy, annexures, and dispatch proof.",
        "Do not admit liability unless legally advised; state your version precisely.",
    ],
    "demand_notice": [
        "Serve by **Registered Post AD** on the debtor/defaulter at last known address.",
        "Mention clear **amount, basis, and time limit** for compliance (commonly 15–30 days).",
        "Preserve proof of service before filing civil suit or other proceedings.",
    ],
}


def _today() -> str:
    return date.today().strftime("%d %B %Y")


def draft_document(
    document_type: str,
    sender_name: str,
    sender_address: str,
    recipient_name: str,
    recipient_address: str,
    subject: str,
    facts: str,
    relief_sought: str,
    language: str = "en",
) -> dict:
    if document_type not in DOCUMENT_TYPES:
        document_type = "rera_legal_notice"

    sender_name = sender_name.strip() or "[Your Full Name]"
    sender_address = sender_address.strip() or "[Your Complete Address with PIN]"
    recipient_name = recipient_name.strip() or "[Recipient Name / Company]"
    recipient_address = recipient_address.strip() or "[Registered Office / Correspondence Address]"
    subject = subject.strip() or "Legal Notice regarding deficiency/delay"
    facts = facts.strip() or "[Describe chronology: booking date, payments, promised possession, actual delay, correspondence]"
    relief_sought = relief_sought.strip() or "[State refund with interest / possession with compensation / compliance within 30 days]"

    templates = {
        "rera_legal_notice": f"""LEGAL NOTICE
(Under Real Estate (Regulation and Development) Act, 2016)

Date: {_today()}

To,
{recipient_name}
{recipient_address}

From,
{sender_name}
{sender_address}

Subject: {subject}

Sir/Madam,

Under instruction and authority of my client/undersigned allottee, I/we issue this legal notice as follows:

1. **Agreement & Project**: {facts}

2. **Default**: The promoter has failed to hand over possession within the agreed/conforming timeline and has caused deficiency in service to the allottee in violation of RERA, 2016 and the agreement for sale.

3. **Relief Demanded**: {relief_sought}

4. **Compliance Period**: You are called upon to remedy the breach within **30 days** from receipt of this notice, failing which the allottee shall be constrained to initiate complaint before the **State Real Estate Regulatory Authority**, consumer forum, and other competent forums without further reference.

5. **Reservation of Rights**: All rights and remedies available in law are expressly reserved.

Yours faithfully,
{sender_name}
""",
        "rera_authority_complaint": f"""BEFORE THE REAL ESTATE REGULATORY AUTHORITY
[State — as per project registration]

Complaint Reference: _____________
Date: {_today()}

Complainant: {sender_name}
Address: {sender_address}

Opposite Party: {recipient_name}
Address: {recipient_address}

Subject: {subject}

**Brief Facts**
{facts}

**Relief Sought**
{relief_sought}

**List of Annexures**
1. Agreement for Sale / Allotment Letter
2. Payment receipts / bank statements
3. RERA registration details of project
4. Correspondence with promoter
5. Proof of delay / possession status

Place: _____________
Signature of Complainant: _____________
""",
        "consumer_legal_notice": f"""LEGAL NOTICE
(Consumer Protection Act, 2019)

Date: {_today()}

To,
{recipient_name}
{recipient_address}

From,
{sender_name}
{sender_address}

Subject: {subject}

Dear Sir/Madam,

The above-named consumer hereby serves this legal notice:

**Facts**
{facts}

**Deficiency / Unfair Trade Practice**
The opposite party has committed deficiency in service and failed to provide the agreed standard/timeline.

**Relief Demanded within 15 days**
{relief_sought}

Failure to comply shall compel the consumer to file a complaint before the appropriate **Consumer Disputes Redressal Commission** with costs.

Yours faithfully,
{sender_name}
""",
        "consumer_complaint": f"""BEFORE THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION
[Insert District]

Consumer Complaint No.: _____ of {_today().split()[-1]}

Complainant: {sender_name}, {sender_address}

Opposite Party: {recipient_name}, {recipient_address}

Subject: {subject}

**Facts of the Case**
{facts}

**Prayer**
{relief_sought}

**Verification**
I verify that contents of this complaint are true to my knowledge.

Filed at: _____________ on {_today()}
""",
        "reply_to_notice": f"""REPLY TO LEGAL NOTICE

Date: {_today()}

To,
{recipient_name}
{recipient_address}

From,
{sender_name}
{sender_address}

Subject: {subject} — Reply to your notice dated _______

Dear Sir/Madam,

I/We reply to your notice as under:

**Our Version**
{facts}

**Stand**
Without prejudice to rights, the contents of your notice are denied where disputed. {relief_sought}

This reply is issued without admission of liability.

Yours faithfully,
{sender_name}
""",
        "demand_notice": f"""DEMAND NOTICE

Date: {_today()}

To,
{recipient_name}
{recipient_address}

From,
{sender_name}
{sender_address}

Subject: {subject}

You are hereby called upon to:

{relief_sought}

**Background**
{facts}

Comply within **15 days** of receipt, failing which civil and other remedies shall be pursued at your risk as to costs and consequences.

Yours faithfully,
{sender_name}
""",
    }

    body = templates.get(document_type, templates["rera_legal_notice"])
    service = SERVICE_GUIDES.get(document_type, SERVICE_GUIDES["demand_notice"])

    if language == "hi":
        body += "\n\n[हिंदी अनुवाद हेतु: इस पाठ को Google Translate या अधिवक्ता से सत्यापित कराएँ।]\n"
    elif language == "kn":
        body += "\n\n[ಕನ್ನಡ ಅನುವಾದಕ್ಕಾಗಿ: ಈ ಪತ್ರವನ್ನು ಅಧಿವಕ್ತರ ಮೂಲಕ ಸ್ಥಳೀಯ ಭಾಷೆಗೆ ಪ್ರಮಾಣೀಕರಿಸಿ.]\n"

    return {
        "document_type": document_type,
        "document_title": DOCUMENT_TYPES[document_type],
        "document": body.strip(),
        "service_instructions": service,
        "language": language,
        "generated_on": _today(),
    }
