from typing import Dict, List

from src.services.evidence_service import EvidenceService


class VerificationService:

    """
    ============================================================
    EFFIONG AI VERIFICATION ENGINE
    ============================================================

    Problem #8

    Responsibilities

    - Source Validation
    - Evidence Scoring
    - Truth Classification
    - Heritage Validation
    """

    def __init__(self):

        self.evidence_service = (
            EvidenceService()
        )

    # =====================================================
    # SOURCE VALIDATION
    # =====================================================

    def validate_sources(
        self,
        sources: List[Dict]
    ):

        verified = 0

        probable = 0

        oral = 0

        unverified = 0

        for source in sources:

            status = source.get(
                "verification",
                ""
            ).lower()

            if "verified" in status:
                verified += 1

            elif "probable" in status:
                probable += 1

            elif "oral" in status:
                oral += 1

            else:
                unverified += 1

        return {

            "verified":
                verified,

            "probable":
                probable,

            "oral":
                oral,

            "unverified":
                unverified
        }

    # =====================================================
    # VERIFY RESEARCH
    # =====================================================

    def verify_research(
        self,
        sources: List[Dict]
    ):

        breakdown = self.validate_sources(
            sources
        )

        matrix = (
            self.evidence_service
            .build_truth_matrix(
                source_count=len(sources),
                evidence_count=len(sources)
            )
        )

        return {

            "source_breakdown":
                breakdown,

            "truth_matrix":
                matrix
        }

    # =====================================================
    # HERITAGE REVIEW
    # =====================================================

    def verify_heritage_node(
        self,
        title,
        evidence_present
    ):

        return (

            self.evidence_service
            .evaluate_heritage_submission(

                title,

                evidence_present
            )
        )