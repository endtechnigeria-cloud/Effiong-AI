from src.utilities.pdf_engine import PDFEngine
from src.utilities.report_templates import ReportTemplates

from src.database.archive import ArchiveDatabase


class DocumentService:

    def __init__(self):

        self.pdf_engine = PDFEngine()

        self.archive = ArchiveDatabase()

    # ==================================================
    # RESEARCH REPORT
    # ==================================================

    def create_research_report(

        self,

        title,

        summary,

        evidence,

        sources

    ):

        sections = ReportTemplates.research_report(

            title,

            summary,

            evidence,

            sources
        )

        pdf = self.pdf_engine.render_report(
            sections
        )

        return {

            "type": "document",

            "filename":
                f"{title}.pdf",

            "content": pdf
        }

    # ==================================================
    # EVIDENCE REPORT
    # ==================================================

    def create_evidence_report(

        self,

        title,

        summary,

        evidence,

        sources,

        facts,

        probabilities,

        speculation

    ):

        sections = ReportTemplates.evidence_report(

            title,

            summary,

            evidence,

            sources,

            facts,

            probabilities,

            speculation
        )

        pdf = self.pdf_engine.render_report(
            sections
        )

        return {

            "type": "document",

            "filename":
                f"{title}.pdf",

            "content": pdf
        }

    # ==================================================
    # PREDICTION REPORT
    # ==================================================

    def create_prediction_report(

        self,

        title,

        prediction,

        confidence,

        evidence

    ):

        sections = ReportTemplates.prediction_report(

            title,

            prediction,

            confidence,

            evidence
        )

        pdf = self.pdf_engine.render_report(
            sections
        )

        return {

            "type": "document",

            "filename":
                f"{title}.pdf",

            "content": pdf
        }

    # ==================================================
    # HERITAGE REPORT
    # ==================================================

    def create_heritage_report(

        self,

        title,

        narrative,

        verification_status

    ):

        sections = ReportTemplates.heritage_report(

            title,

            narrative,

            verification_status
        )

        pdf = self.pdf_engine.render_report(
            sections
        )

        return {

            "type": "document",

            "filename":
                f"{title}.pdf",

            "content": pdf
        }