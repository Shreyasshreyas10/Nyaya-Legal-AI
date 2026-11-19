"""
agents/citation_verifier.py
Verification agent to validate citations in LLM responses.
"""

import re
from typing import Dict, List, Tuple

class CitationVerifier:
    def __init__(self):
        # Regex patterns to find legal references in response
        self.section_pattern = re.compile(
            r'\b(?:Section|Sec\.?|S\.)\s*(\d+[A-Z]?)\b', re.IGNORECASE
        )
        self.article_pattern = re.compile(
            r'\b(?:Article|Art\.?)\s*(\d+[A-Z]?)\b', re.IGNORECASE
        )
        self.chapter_pattern = re.compile(
            r'\b(?:Chapter|Ch\.?)\s*([IVXLC\d]+)\b', re.IGNORECASE
        )
        # Match documents / acts mentioned (e.g. 023c05a84523bce30bca92bd293625c5)
        self.doc_hash_pattern = re.compile(
            r'\b([a-f0-9]{32})\b', re.IGNORECASE
        )

    def extract_citations(self, text: str) -> Dict[str, List[str]]:
        """Extract citations from LLM output text."""
        sections = self.section_pattern.findall(text)
        articles = self.article_pattern.findall(text)
        chapters = self.chapter_pattern.findall(text)
        docs = self.doc_hash_pattern.findall(text)

        # Normalize and deduplicate
        return {
            "sections": sorted(list(set(sections))),
            "articles": sorted(list(set(articles))),
            "chapters": sorted(list(set(chapters))),
            "docs": sorted(list(set(docs))),
        }

    def verify(self, response_text: str, retrieved_sections: List[dict]) -> dict:
        """
        Verify references in the response_text against retrieved parent sections.
        Returns a structured dictionary of verified and unverified citations.
        """
        citations_found = self.extract_citations(response_text)
        
        verified_citations = []
        unverified_citations = []

        # Map retrieved sections for fast lookup
        # We look for section numbers, article numbers, and document IDs
        retrieved_sec_ids = set()
        retrieved_headings = []
        retrieved_doc_ids = set()
        retrieved_contents = []

        for sec in retrieved_sections:
            doc_id = sec.get("doc_id", "")
            sec_id = sec.get("section_id", "")
            heading = sec.get("heading", "")
            content = sec.get("content", "")

            retrieved_doc_ids.add(doc_id)
            retrieved_sec_ids.add(sec_id)
            retrieved_headings.append(heading)
            retrieved_contents.append(content)

        # Process Section citations
        for sec_num in citations_found["sections"]:
            # Check if this section number appears in retrieved section_id, heading, or content
            matched_sec = None
            # Look for section matches in retrieved sections
            for sec in retrieved_sections:
                sec_id = sec.get("section_id", "")
                heading = sec.get("heading", "")
                
                # Check direct section_id match (e.g. sec_0012 matches 12) or inside heading
                if (sec_num.lower() in sec_id.lower() or 
                    f"section {sec_num.lower()}" in heading.lower() or 
                    re.search(fr'\bSection\s*{sec_num}\b', heading, re.IGNORECASE) or
                    re.search(fr'\bSection\s*{sec_num}\b', sec.get("content", ""), re.IGNORECASE)):
                    matched_sec = sec
                    break
            
            citation_label = f"Section {sec_num}"
            if matched_sec:
                verified_citations.append({
                    "citation": citation_label,
                    "type": "section",
                    "doc_id": matched_sec.get("doc_id"),
                    "section_id": matched_sec.get("section_id"),
                    "heading": matched_sec.get("heading"),
                    "snippet": matched_sec.get("content")[:200] + "..."
                })
            else:
                unverified_citations.append({
                    "citation": citation_label,
                    "type": "section",
                    "reason": "Cited section was not in the retrieved search context."
                })

        # Process Article citations
        for art_num in citations_found["articles"]:
            matched_sec = None
            for sec in retrieved_sections:
                heading = sec.get("heading", "")
                if (f"article {art_num.lower()}" in heading.lower() or
                    re.search(fr'\bArticle\s*{art_num}\b', heading, re.IGNORECASE) or
                    re.search(fr'\bArticle\s*{art_num}\b', sec.get("content", ""), re.IGNORECASE)):
                    matched_sec = sec
                    break
            
            citation_label = f"Article {art_num}"
            if matched_sec:
                verified_citations.append({
                    "citation": citation_label,
                    "type": "article",
                    "doc_id": matched_sec.get("doc_id"),
                    "section_id": matched_sec.get("section_id"),
                    "heading": matched_sec.get("heading"),
                    "snippet": matched_sec.get("content")[:200] + "..."
                })
            else:
                unverified_citations.append({
                    "citation": citation_label,
                    "type": "article",
                    "reason": "Cited article was not in the retrieved search context."
                })

        # Process Chapter citations
        for ch_num in citations_found["chapters"]:
            matched_sec = None
            for sec in retrieved_sections:
                heading = sec.get("heading", "")
                if (f"chapter {ch_num.lower()}" in heading.lower() or
                    re.search(fr'\bChapter\s*{ch_num}\b', heading, re.IGNORECASE) or
                    re.search(fr'\bChapter\s*{ch_num}\b', sec.get("content", ""), re.IGNORECASE)):
                    matched_sec = sec
                    break
            
            citation_label = f"Chapter {ch_num}"
            if matched_sec:
                verified_citations.append({
                    "citation": citation_label,
                    "type": "chapter",
                    "doc_id": matched_sec.get("doc_id"),
                    "section_id": matched_sec.get("section_id"),
                    "heading": matched_sec.get("heading"),
                    "snippet": matched_sec.get("content")[:200] + "..."
                })
            else:
                unverified_citations.append({
                    "citation": citation_label,
                    "type": "chapter",
                    "reason": "Cited chapter was not in the retrieved search context."
                })

        # Check for doc mentions
        for doc_hash in citations_found["docs"]:
            if doc_hash in retrieved_doc_ids:
                # Document hash is verified
                # Find matching section
                matched_sec = next((s for s in retrieved_sections if s.get("doc_id") == doc_hash), None)
                if matched_sec and not any(v["doc_id"] == doc_hash for v in verified_citations):
                    verified_citations.append({
                        "citation": f"Doc {doc_hash[:8]}",
                        "type": "document",
                        "doc_id": doc_hash,
                        "section_id": matched_sec.get("section_id"),
                        "heading": matched_sec.get("heading"),
                        "snippet": matched_sec.get("content")[:200] + "..."
                    })
            else:
                unverified_citations.append({
                    "citation": f"Doc {doc_hash[:8]}",
                    "type": "document",
                    "reason": "Document reference not present in retrieved context."
                })

        # If no explicit citations are found in response text, check context matching
        # Check if the response matches sections in retrieved context semantically/lexically
        if not verified_citations and not unverified_citations:
            # We will list all retrieved sections as "context_matched" if we detect overlap
            for sec in retrieved_sections:
                heading = sec.get("heading", "")
                doc_id = sec.get("doc_id", "")
                sec_id = sec.get("section_id", "")
                
                # Check simple keyword overlapping or if LLM talks about the topic of the heading
                words_in_heading = [w.lower() for w in heading.split() if len(w) > 3]
                overlap = sum(1 for w in words_in_heading if w in response_text.lower())
                
                if overlap >= min(2, len(words_in_heading)) or (len(words_in_heading) > 0 and heading.lower() in response_text.lower()):
                    verified_citations.append({
                        "citation": f"{heading[:30]}...",
                        "type": "context_match",
                        "doc_id": doc_id,
                        "section_id": sec_id,
                        "heading": heading,
                        "snippet": sec.get("content")[:200] + "..."
                    })
            
            # If still nothing, let's just surface the top retrieved section as potential reference
            if not verified_citations and retrieved_sections:
                top_sec = retrieved_sections[0]
                verified_citations.append({
                    "citation": f"{top_sec.get('heading')[:30]}...",
                    "type": "context_match",
                    "doc_id": top_sec.get("doc_id"),
                    "section_id": top_sec.get("section_id"),
                    "heading": top_sec.get("heading"),
                    "snippet": top_sec.get("content")[:200] + "..."
                })

        # Calculate status
        if not unverified_citations and verified_citations:
            status = "verified"
        elif verified_citations and unverified_citations:
            status = "partial"
        else:
            status = "unverified"

        return {
            "status": status,
            "verified": verified_citations,
            "unverified": unverified_citations,
            "citations_found": citations_found
        }
