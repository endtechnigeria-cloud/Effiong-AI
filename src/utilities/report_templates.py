from src.utilities.report_sections import ReportSections


class ReportTemplates:

    @staticmethod
    def research_report(
        title,
        summary,
        evidence,
        sources
    ):

        return [

            ReportSections.title_section(title),

            ReportSections.executive_summary(summary),

            ReportSections.evidence_section(
                evidence
            ),

            ReportSections.source_section(
                sources
            )
        ]

    @staticmethod
    def evidence_report(
        title,
        summary,
        evidence,
        sources,
        facts,
        probabilities,
        speculation
    ):

        return [

            ReportSections.title_section(title),

            ReportSections.executive_summary(
                summary
            ),

            ReportSections.evidence_section(
                evidence
            ),

            ReportSections.truth_matrix(
                facts,
                probabilities,
                speculation
            ),

            ReportSections.source_section(
                sources
            )
        ]

    @staticmethod
    def prediction_report(
        title,
        prediction,
        confidence,
        evidence
    ):

        return [

            ReportSections.title_section(
                title
            ),

            ReportSections.prediction_section(
                prediction,
                confidence
            ),

            ReportSections.evidence_section(
                evidence
            )
        ]

    @staticmethod
    def heritage_report(
        title,
        narrative,
        verification_status
    ):

        return [

            ReportSections.title_section(
                title
            ),

            ReportSections.heritage_section(
                title,
                verification_status,
                narrative
            )
        ]

    @staticmethod
    def operator_report(
        title,
        metrics
    ):

        return [

            ReportSections.title_section(
                title
            ),

            ReportSections.operator_section(
                metrics
            )
        ]