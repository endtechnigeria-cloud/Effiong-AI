from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

from reportlab.lib.enums import TA_CENTER


class PDFEngine:

    def __init__(self):

        self.styles = getSampleStyleSheet()

        self.styles.add(
            ParagraphStyle(
                name="EffiongTitle",
                parent=self.styles["Title"],
                alignment=TA_CENTER,
                textColor=colors.HexColor("#D27D2D")
            )
        )

    def render_report(
        self,
        sections
    ):

        buffer = BytesIO()

        doc = SimpleDocTemplate(buffer)

        story = []

        for section in sections:

            section_type = section["type"]

            if section_type == "title":

                story.append(
                    Paragraph(
                        "EFFIONG AI",
                        self.styles["EffiongTitle"]
                    )
                )

                story.append(
                    Spacer(1, 12)
                )

                story.append(
                    Paragraph(
                        section["title"],
                        self.styles["Heading1"]
                    )
                )

                story.append(
                    Paragraph(
                        section["generated_at"],
                        self.styles["BodyText"]
                    )
                )

            elif section_type == "executive_summary":

                story.append(
                    Spacer(1, 12)
                )

                story.append(
                    Paragraph(
                        "Executive Summary",
                        self.styles["Heading2"]
                    )
                )

                story.append(
                    Paragraph(
                        section["content"],
                        self.styles["BodyText"]
                    )
                )

            elif section_type == "prediction":

                story.append(
                    Spacer(1, 12)
                )

                story.append(
                    Paragraph(
                        "Prediction",
                        self.styles["Heading2"]
                    )
                )

                story.append(
                    Paragraph(
                        section["prediction"],
                        self.styles["BodyText"]
                    )
                )

                story.append(
                    Paragraph(
                        f"Confidence: {section['confidence']}%",
                        self.styles["BodyText"]
                    )
                )

            elif section_type == "truth_matrix":

                story.append(
                    PageBreak()
                )

                story.append(
                    Paragraph(
                        "Truth Matrix",
                        self.styles["Heading1"]
                    )
                )

                story.append(
                    Paragraph(
                        "<b>Facts</b>",
                        self.styles["BodyText"]
                    )
                )

                for item in section["facts"]:
                    story.append(
                        Paragraph(
                            f"• {item}",
                            self.styles["BodyText"]
                        )
                    )

                story.append(
                    Paragraph(
                        "<b>Probabilities</b>",
                        self.styles["BodyText"]
                    )
                )

                for item in section["probabilities"]:
                    story.append(
                        Paragraph(
                            f"• {item}",
                            self.styles["BodyText"]
                        )
                    )

                story.append(
                    Paragraph(
                        "<b>Speculation</b>",
                        self.styles["BodyText"]
                    )
                )

                for item in section["speculation"]:
                    story.append(
                        Paragraph(
                            f"• {item}",
                            self.styles["BodyText"]
                        )
                    )

            elif section_type == "evidence":

                story.append(
                    Paragraph(
                        "Evidence",
                        self.styles["Heading2"]
                    )
                )

                for item in section["items"]:
                    story.append(
                        Paragraph(
                            f"• {item}",
                            self.styles["BodyText"]
                        )
                    )

            elif section_type == "sources":

                story.append(
                    Paragraph(
                        "Sources",
                        self.styles["Heading2"]
                    )
                )

                for source in section["sources"]:
                    story.append(
                        Paragraph(
                            f"• {source}",
                            self.styles["BodyText"]
                        )
                    )

            elif section_type == "heritage":

                story.append(
                    Paragraph(
                        "Heritage Record",
                        self.styles["Heading1"]
                    )
                )

                story.append(
                    Paragraph(
                        f"Verification Status: {section['verification_status']}",
                        self.styles["BodyText"]
                    )
                )

                story.append(
                    Paragraph(
                        section["narrative"],
                        self.styles["BodyText"]
                    )
                )

            elif section_type == "operator":

                story.append(
                    Paragraph(
                        "System Metrics",
                        self.styles["Heading1"]
                    )
                )

                for key, value in section["metrics"].items():

                    story.append(
                        Paragraph(
                            f"{key}: {value}",
                            self.styles["BodyText"]
                        )
                    )

            story.append(
                Spacer(1, 12)
            )

        doc.build(story)

        pdf = buffer.getvalue()

        buffer.close()

        return pdf