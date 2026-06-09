from datetime import datetime


class ReportSections:

    @staticmethod
    def title_section(title: str):

        return {
            "type": "title",
            "title": title,
            "generated_at": datetime.utcnow().isoformat()
        }

    @staticmethod
    def executive_summary(summary: str):

        return {
            "type": "executive_summary",
            "content": summary
        }

    @staticmethod
    def evidence_section(evidence_items: list):

        return {
            "type": "evidence",
            "items": evidence_items
        }

    @staticmethod
    def source_section(sources: list):

        return {
            "type": "sources",
            "sources": sources
        }

    @staticmethod
    def truth_matrix(
        facts: list,
        probabilities: list,
        speculation: list
    ):

        return {
            "type": "truth_matrix",
            "facts": facts,
            "probabilities": probabilities,
            "speculation": speculation
        }

    @staticmethod
    def prediction_section(
        prediction: str,
        confidence: float
    ):

        return {
            "type": "prediction",
            "prediction": prediction,
            "confidence": confidence
        }

    @staticmethod
    def heritage_section(
        title: str,
        verification_status: str,
        narrative: str
    ):

        return {
            "type": "heritage",
            "title": title,
            "verification_status": verification_status,
            "narrative": narrative
        }

    @staticmethod
    def operator_section(metrics: dict):

        return {
            "type": "operator",
            "metrics": metrics
        }