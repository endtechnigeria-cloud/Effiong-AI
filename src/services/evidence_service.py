"""
EFFIONG AI - Evidence Engine
============================
Scores sources and turns evidence into a truth classification.

Truth ladder (highest -> lowest):
    VERIFIED FACT . EVIDENCE SUPPORTED . PROBABLE . ORAL TRADITION . COMPETING CLAIM . SPECULATIVE . UNVERIFIED
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urlparse

TRUSTED_SUFFIXES = (".gov", ".gov.ng", ".gov.za", ".gov.uk", ".edu", ".ac.uk", ".ac.za", ".edu.ng", ".int", ".mil")
TRUSTED_DOMAINS = {
    "archive.org": "ARCHIVE", "web.archive.org": "ARCHIVE", "wikipedia.org": "REFERENCE", "wikidata.org": "REFERENCE",
    "loc.gov": "GOVERNMENT", "unesco.org": "GOVERNMENT", "who.int": "GOVERNMENT", "worldbank.org": "GOVERNMENT",
    "britishmuseum.org": "ACADEMIC", "si.edu": "ACADEMIC", "jstor.org": "ACADEMIC", "nature.com": "ACADEMIC",
    "sciencedirect.com": "ACADEMIC", "springer.com": "ACADEMIC", "doi.org": "ACADEMIC", "zenodo.org": "ARCHIVE",
    "osf.io": "ARCHIVE", "figshare.com": "ARCHIVE", "reuters.com": "NEWS", "apnews.com": "NEWS", "bbc.com": "NEWS",
    "bbc.co.uk": "NEWS", "aljazeera.com": "NEWS", "theguardian.com": "NEWS", "africanews.com": "NEWS",
    "punchng.com": "NEWS", "premiumtimesng.com": "NEWS", "channelstv.com": "NEWS",
}

SCORES = {"ACADEMIC": 1.00, "GOVERNMENT": 0.95, "ARCHIVE": 0.90, "NEWS": 0.80, "REFERENCE": 0.75, "BOOK": 0.70,
          "GENERAL": 0.60, "ORAL": 0.50}


def classify_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if not host:
        return "GENERAL"
    for dom, kind in TRUSTED_DOMAINS.items():
        if host == dom or host.endswith("." + dom):
            return kind
    if host.endswith(TRUSTED_SUFFIXES):
        return "GOVERNMENT" if ".gov" in host or host.endswith((".int", ".mil")) else "ACADEMIC"
    return "GENERAL"


class EvidenceService:
    def __init__(self) -> None:
        self.version = "3.0"

    def classify_source(self, source: Any) -> str:
        """Accepts a source name/string or a repository result dict."""
        if isinstance(source, dict):
            stype = str(source.get("source_type", "")).upper()
            mapping = {"ACADEMIC": "ACADEMIC", "GOVERNMENT": "GOVERNMENT", "ARCHIVE": "ARCHIVE", "REFERENCE": "REFERENCE", "BOOK": "BOOK"}
            if stype in mapping:
                return mapping[stype]
            if source.get("url"):
                return classify_url(source["url"])
            source = source.get("source", "")
        name = str(source).lower()
        if "journal" in name or "university" in name or "academic" in name:
            return "ACADEMIC"
        if "government" in name:
            return "GOVERNMENT"
        if "archive" in name:
            return "ARCHIVE"
        if "wikipedia" in name or "wikidata" in name:
            return "REFERENCE"
        if "oral" in name:
            return "ORAL"
        return "GENERAL"

    def source_reliability_score(self, source: Any) -> float:
        return SCORES.get(self.classify_source(source), 0.5)

    def calculate_evidence_score(self, sources: List[Dict]) -> float:
        if not sources:
            return 0.0
        total = sum(self.source_reliability_score(s) for s in sources)
        # more independent sources raise confidence (diminishing returns)
        breadth = min(1.0, 0.55 + 0.15 * len({s.get("source", "") for s in sources}))
        return round((total / len(sources)) * breadth * 100, 2)

    def calculate_consensus_score(self, sources: List[Dict]) -> float:
        if len(sources) <= 1:
            return 50.0
        supportive = sum(1 for s in sources if str(s.get("stance", "supports")).lower() != "contradicts")
        return round(100.0 * supportive / len(sources), 2)

    def classify_truth_status(self, evidence_score: float, consensus_score: float) -> str:
        combined = evidence_score * 0.7 + consensus_score * 0.3
        for limit, label in ((88, "VERIFIED FACT"), (72, "EVIDENCE SUPPORTED"), (58, "PROBABLE"), (44, "ORAL TRADITION"),
                             (30, "COMPETING CLAIM"), (15, "SPECULATIVE")):
            if combined >= limit:
                return label
        return "UNVERIFIED"

    def build_truth_matrix(self, sources: List[Dict]) -> Dict[str, Any]:
        ev = self.calculate_evidence_score(sources)
        cons = self.calculate_consensus_score(sources)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "classification": self.classify_truth_status(ev, cons),
            "evidence_score": ev,
            "consensus_score": cons,
            "sources_reviewed": len(sources),
            "source_breakdown": self.source_breakdown(sources),
            "fact_layer": "Claims supported by available evidence.",
            "inference_layer": "Reasonable conclusions drawn from evidence.",
            "probability_layer": "Likelihood estimates based on evidence patterns.",
            "speculation_layer": "Claims requiring additional verification.",
            "warning": "Confidence is not proof. Future evidence may change conclusions.",
        }

    build_truth_matrix_from_sources = build_truth_matrix  # older modules used this name

    def source_breakdown(self, sources: List[Dict]) -> Dict[str, int]:
        return dict(Counter(self.classify_source(s) for s in sources))

    def generate_evidence_summary(self, sources: List[Dict]) -> str:
        m = self.build_truth_matrix(sources)
        return (f"TRUTH MATRIX ANALYSIS\nClassification: {m['classification']}\nEvidence Score: {m['evidence_score']}%\n"
                f"Consensus Score: {m['consensus_score']}%\nSources Reviewed: {m['sources_reviewed']}\n"
                f"Source Breakdown: {m['source_breakdown']}")

    def prediction_confidence_input(self, sources: List[Dict]) -> Dict:
        m = self.build_truth_matrix(sources)
        return {"classification": m["classification"], "confidence": m["evidence_score"], "consensus": m["consensus_score"]}
