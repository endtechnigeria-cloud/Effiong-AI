from datetime import datetime
from typing import Dict, List, Any

from src.services.evidence_service import EvidenceService


class PredictionService:
    """
    ============================================================
    EFFIONG AI PREDICTION ENGINE V2
    ============================================================

    Purpose

    - Structured forecasting
    - Historical trend analysis
    - Human behavior analysis
    - Risk assessment
    - Scenario generation
    - Confidence estimation
    - Truth Matrix separation

    Principles

    FACT
    INFERENCE
    FORECAST
    UNCERTAINTY

    Predictions are NEVER facts.
    """

    def __init__(self):

        self.version = "2.0"

        self.evidence_service = EvidenceService()

    # =========================================================
    # CONFIDENCE CALCULATOR
    # =========================================================

    def calculate_confidence(
        self,
        evidence_count: int,
        source_count: int,
        evidence_score: float = 0
    ) -> float:

        confidence = (
            (evidence_count * 6)
            +
            (source_count * 4)
            +
            (evidence_score * 0.3)
        )

        confidence = max(
            0,
            min(confidence, 95)
        )

        return round(confidence, 2)

    # =========================================================
    # UNCERTAINTY CLASSIFIER
    # =========================================================

    def classify_uncertainty(
        self,
        confidence: float
    ) -> str:

        if confidence >= 85:
            return "LOW UNCERTAINTY"

        if confidence >= 70:
            return "MODERATE UNCERTAINTY"

        if confidence >= 50:
            return "HIGH UNCERTAINTY"

        return "EXTREME UNCERTAINTY"

    # =========================================================
    # FORECAST HORIZON
    # =========================================================

    def determine_horizon(
        self,
        topic: str
    ) -> str:

        topic = topic.lower()

        if any(
            x in topic
            for x in [
                "today",
                "tomorrow",
                "week",
                "days"
            ]
        ):
            return "SHORT TERM"

        if any(
            x in topic
            for x in [
                "month",
                "year"
            ]
        ):
            return "MEDIUM TERM"

        return "LONG TERM"

    # =========================================================
    # TREND ANALYSIS
    # =========================================================

    def analyze_trend_strength(
        self,
        evidence_count: int,
        source_count: int
    ) -> str:

        score = evidence_count + source_count

        if score >= 20:
            return "STRONG TREND"

        if score >= 10:
            return "MODERATE TREND"

        return "WEAK TREND"

    # =========================================================
    # SCENARIO GENERATOR
    # =========================================================

    def generate_scenarios(
        self,
        topic: str
    ) -> Dict:

        return {

            "best_case": (
                f"Positive developments surrounding "
                f"{topic} continue."
            ),

            "base_case": (
                f"Current trends involving "
                f"{topic} continue."
            ),

            "worst_case": (
                f"Negative variables emerge and "
                f"change the trajectory of {topic}."
            )
        }

    # =========================================================
    # HUMAN BEHAVIOR ANALYSIS
    # =========================================================

    def analyze_behavior(
        self,
        scenario: str
    ) -> Dict:

        return {

            "scenario": scenario,

            "behavioral_drivers": [

                "Incentives",
                "Risk Avoidance",
                "Social Influence",
                "Resource Constraints",
                "Decision Pressure"
            ],

            "analysis":

                "Human behavior is influenced by "
                "multiple interacting variables and "
                "cannot be predicted with certainty.",

            "predictability":

                "PARTIAL"
        }

    # =========================================================
    # RISK MATRIX
    # =========================================================

    def build_risk_matrix(
        self,
        confidence: float
    ) -> Dict:

        if confidence >= 80:

            probability = "HIGH"

            volatility = "LOW"

        elif confidence >= 60:

            probability = "MODERATE"

            volatility = "MODERATE"

        else:

            probability = "LOW"

            volatility = "HIGH"

        return {

            "probability":
                probability,

            "volatility":
                volatility,

            "uncertainty":
                self.classify_uncertainty(
                    confidence
                )
        }

    # =========================================================
    # FORECAST GENERATOR
    # =========================================================

    def build_forecast(
        self,
        topic: str,
        evidence_items: List[Dict]
    ) -> Dict:

        evidence_count = len(
            evidence_items
        )

        source_count = len({

            item.get(
                "source",
                "Unknown"
            )

            for item in evidence_items
        })

        truth_matrix = (
            self.evidence_service
            .build_truth_matrix_from_sources(
                evidence_items
            )
        )

        confidence = self.calculate_confidence(

            evidence_count=
                evidence_count,

            source_count=
                source_count,

            evidence_score=
                truth_matrix["score"]
        )

        forecast_horizon = (
            self.determine_horizon(
                topic
            )
        )

        scenarios = (
            self.generate_scenarios(
                topic
            )
        )

        risk_matrix = (
            self.build_risk_matrix(
                confidence
            )
        )

        trend_strength = (
            self.analyze_trend_strength(
                evidence_count,
                source_count
            )
        )

        return {

            "topic":
                topic,

            "generated_at":
                datetime.utcnow().isoformat(),

            "forecast_horizon":
                forecast_horizon,

            "confidence":
                confidence,

            "trend_strength":
                trend_strength,

            "risk_matrix":
                risk_matrix,

            "scenarios":
                scenarios,

            "evidence_count":
                evidence_count,

            "source_count":
                source_count,

            "truth_matrix":
                truth_matrix,

            "forecast":
                (
                    "Forecast generated using "
                    "historical evidence, "
                    "retrieved sources, "
                    "trend analysis and "
                    "probabilistic reasoning."
                ),

            "disclaimer":
                (
                    "Forecasts are probabilistic "
                    "estimates and not guarantees."
                )
        }

    # =========================================================
    # EVENT FORECAST
    # =========================================================

    def forecast_event(
        self,
        topic: str,
        evidence_items: List[Dict]
    ) -> Dict:

        return self.build_forecast(
            topic,
            evidence_items
        )

    # =========================================================
    # GEOPOLITICAL ANALYSIS
    # =========================================================

    def analyze_geopolitical_event(
        self,
        topic: str,
        evidence_items: List[Dict]
    ) -> Dict:

        forecast = self.build_forecast(
            topic,
            evidence_items
        )

        forecast["analysis_type"] = (
            "GEOPOLITICAL"
        )

        forecast["variables"] = [

            "Political Stability",
            "Economic Conditions",
            "Military Factors",
            "International Relations",
            "Resource Availability"
        ]

        return forecast

    # =========================================================
    # ECONOMIC FORECAST
    # =========================================================

    def analyze_economic_event(
        self,
        topic: str,
        evidence_items: List[Dict]
    ) -> Dict:

        forecast = self.build_forecast(
            topic,
            evidence_items
        )

        forecast["analysis_type"] = (
            "ECONOMIC"
        )

        forecast["variables"] = [

            "Inflation",
            "Employment",
            "Interest Rates",
            "Consumer Demand",
            "Trade Activity"
        ]

        return forecast

    # =========================================================
    # OPERATOR DASHBOARD DATA
    # =========================================================

    def operator_summary(
        self,
        forecast: Dict
    ) -> Dict:

        return {

            "topic":
                forecast["topic"],

            "confidence":
                forecast["confidence"],

            "uncertainty":
                forecast["risk_matrix"]["uncertainty"],

            "trend_strength":
                forecast["trend_strength"],

            "generated_at":
                forecast["generated_at"]
        }