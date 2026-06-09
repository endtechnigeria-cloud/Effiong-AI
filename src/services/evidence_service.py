```python
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter


class EvidenceService:
    """
    ============================================================
    EFFIONG AI EVIDENCE ENGINE V2
    ============================================================

    Purpose

    - Evidence Classification
    - Source Reliability Analysis
    - Truth Matrix Construction
    - Heritage Verification
    - Prediction Confidence Support
    - Knowledge Graph Validation

    Supports

    Problem #8
    Knowledge Verification Engine

    Problem #9
    Sovereign Knowledge Graph

    Problem #12
    Research & Evidence Engine
    """

    def __init__(self):

        self.version = "2.0"

    # =========================================================
    # SOURCE CLASSIFICATION
    # =========================================================

    def classify_source(
        self,
        source_name: str
    ) -> str:

        source_name = source_name.lower()

        # Highest reliability

        if "journal" in source_name:
            return "ACADEMIC"

        if "university" in source_name:
            return "ACADEMIC"

        if "government" in source_name:
            return "GOVERNMENT"

        # Archive sources

        if "archive" in source_name:
            return "ARCHIVE"

        # Reference sources

        if "wikipedia" in source_name:
            return "REFERENCE"

        # Heritage sources

        if "oral" in source_name:
            return "ORAL"

        return "GENERAL"

    # =========================================================
    # SOURCE RELIABILITY SCORE
    # =========================================================

    def source_reliability_score(
        self,
        source_name: str
    ) -> float:

        source_type = self.classify_source(
            source_name
        )

        scores = {

            "ACADEMIC": 1.00,

            "GOVERNMENT": 0.95,

            "ARCHIVE": 0.90,

            "REFERENCE": 0.75,

            "GENERAL": 0.60,

            "ORAL": 0.50
        }

        return scores.get(
            source_type,
            0.50
        )

    # =========================================================
    # EVIDENCE SCORE
    # =========================================================

    def calculate_evidence_score(
        self,
        sources: List[Dict]
    ) -> float:

        if not sources:
            return 0.0

        total = 0

        for source in sources:

            source_name = source.get(
                "source",
                "unknown"
            )

            total += (
                self.source_reliability_score(
                    source_name
                )
            )

        score = (
            total / len(sources)
        ) * 100

        return round(
            score,
            2
        )

    # =========================================================
    # CLAIM CONSISTENCY
    # =========================================================

    def calculate_consensus_score(
        self,
        sources: List[Dict]
    ) -> float:

        if len(sources) <= 1:

            return 50.0

        titles = []

        for item in sources:

            title = item.get(
                "title",
                ""
            )

            if title:

                titles.append(
                    title.lower()
                )

        if not titles:

            return 0.0

        counts = Counter(
            titles
        )

        highest = max(
            counts.values()
        )

        score = (
            highest / len(titles)
        ) * 100

        return round(
            score,
            2
        )

    # =========================================================
    # TRUTH CLASSIFICATION
    # =========================================================

    def classify_truth_status(
        self,
        evidence_score: float,
        consensus_score: float
    ) -> str:

        combined = (
            evidence_score * 0.7
            +
            consensus_score * 0.3
        )

        if combined >= 90:

            return "VERIFIED FACT"

        if combined >= 75:

            return "EVIDENCE SUPPORTED"

        if combined >= 60:

            return "PROBABLE"

        if combined >= 45:

            return "ORAL TRADITION"

        if combined >= 30:

            return "COMPETING CLAIM"

        if combined >= 15:

            return "SPECULATIVE"

        return "UNVERIFIED"

    # =========================================================
    # BUILD TRUTH MATRIX
    # =========================================================

    def build_truth_matrix(
        self,
        sources: List[Dict]
    ) -> Dict[str, Any]:

        evidence_score = (
            self.calculate_evidence_score(
                sources
            )
        )

        consensus_score = (
            self.calculate_consensus_score(
                sources
            )
        )

        classification = (
            self.classify_truth_status(
                evidence_score,
                consensus_score
            )
        )

        return {

            "generated_at":
                datetime.utcnow().isoformat(),

            "classification":
                classification,

            "evidence_score":
                evidence_score,

            "consensus_score":
                consensus_score,

            "sources_reviewed":
                len(sources),

            "fact_layer":

                "Claims supported by available evidence.",

            "inference_layer":

                "Reasonable conclusions drawn from evidence.",

            "probability_layer":

                "Likelihood estimates based on evidence patterns.",

            "speculation_layer":

                "Claims requiring additional verification.",

            "warning":

                (
                    "Confidence is not proof. "
                    "Future evidence may strengthen "
                    "or weaken current conclusions."
                )
        }

    # =========================================================
    # HERITAGE REVIEW
    # =========================================================

    def evaluate_heritage_submission(
        self,
        title: str,
        evidence_present: bool,
        source_count: int = 0
    ) -> Dict:

        if evidence_present:

            if source_count >= 3:

                status = "FACT NODE"

                truth_status = (
                    "EVIDENCE SUPPORTED"
                )

            else:

                status = "FACT NODE"

                truth_status = (
                    "PROBABLE"
                )

        else:

            status = (
                "ORAL TRACK NODE"
            )

            truth_status = (
                "ORAL TRADITION"
            )

        return {

            "title":
                title,

            "status":
                status,

            "truth_status":
                truth_status,

            "reviewed_at":
                datetime.utcnow().isoformat()
        }

    # =========================================================
    # SOURCE BREAKDOWN
    # =========================================================

    def source_breakdown(
        self,
        sources: List[Dict]
    ) -> Dict:

        breakdown = Counter()

        for source in sources:

            source_name = source.get(
                "source",
                ""
            )

            source_type = (
                self.classify_source(
                    source_name
                )
            )

            breakdown[
                source_type
            ] += 1

        return dict(
            breakdown
        )

    # =========================================================
    # EVIDENCE SUMMARY
    # =========================================================

    def generate_evidence_summary(
        self,
        sources: List[Dict]
    ) -> str:

        truth_matrix = (
            self.build_truth_matrix(
                sources
            )
        )

        breakdown = (
            self.source_breakdown(
                sources
            )
        )

        return f"""
TRUTH MATRIX ANALYSIS

Classification:
{truth_matrix['classification']}

Evidence Score:
{truth_matrix['evidence_score']}%

Consensus Score:
{truth_matrix['consensus_score']}%

Sources Reviewed:
{truth_matrix['sources_reviewed']}

Source Breakdown:
{breakdown}

FACT LAYER
Claims supported by available evidence.

INFERENCE LAYER
Reasonable conclusions from evidence.

PROBABILITY LAYER
Likelihood estimates from observed patterns.

SPECULATION LAYER
Claims requiring further verification.
"""

    # =========================================================
    # PREDICTION SUPPORT
    # =========================================================

    def prediction_confidence_input(
        self,
        sources: List[Dict]
    ) -> Dict:

        truth_matrix = (
            self.build_truth_matrix(
                sources
            )
        )

        return {

            "classification":
                truth_matrix["classification"],

            "confidence":
                truth_matrix["evidence_score"],

            "consensus":
                truth_matrix["consensus_score"]
        }
```
