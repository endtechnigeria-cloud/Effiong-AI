"""
EFFIONG AI - Prediction Engine
==============================
Structured forecasting for events, outcomes, markets and human / animal behaviour.

Principles (printed into every forecast):  FACT . INFERENCE . FORECAST . UNCERTAINTY  -  a prediction is never a fact.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.services.evidence_service import EvidenceService
from src.services.predictive_service import PredictiveEngine, extract_series, format_forecast


class PredictionService:
    def __init__(self) -> None:
        self.version = "3.0"
        self.evidence_service = EvidenceService()
        self.quant = PredictiveEngine()

    # -- calibration helpers --------------------------------------------------------
    def calculate_confidence(self, evidence_count: int, source_count: int, evidence_score: float = 0) -> float:
        raw = evidence_count * 4 + source_count * 5 + evidence_score * 0.35
        return round(max(5.0, min(raw, 88.0)), 2)           # never claim certainty

    def classify_uncertainty(self, confidence: float) -> str:
        if confidence >= 80:
            return "LOW UNCERTAINTY"
        if confidence >= 65:
            return "MODERATE UNCERTAINTY"
        if confidence >= 45:
            return "HIGH UNCERTAINTY"
        return "EXTREME UNCERTAINTY"

    def determine_horizon(self, topic: str) -> str:
        t = topic.lower()
        if any(x in t for x in ("today", "tonight", "tomorrow", "this week", "next week", "days")):
            return "SHORT TERM"
        if any(x in t for x in ("month", "quarter", "this year", "next year", "2027", "2028")):
            return "MEDIUM TERM"
        return "LONG TERM"

    def analyze_trend_strength(self, evidence_count: int, source_count: int) -> str:
        score = evidence_count + source_count
        return "STRONG TREND" if score >= 20 else "MODERATE TREND" if score >= 10 else "WEAK TREND"

    def build_risk_matrix(self, confidence: float) -> Dict[str, str]:
        if confidence >= 75:
            prob, vol = "HIGH", "LOW"
        elif confidence >= 55:
            prob, vol = "MODERATE", "MODERATE"
        else:
            prob, vol = "LOW", "HIGH"
        return {"probability": prob, "volatility": vol, "uncertainty": self.classify_uncertainty(confidence)}

    def generate_scenarios(self, topic: str) -> Dict[str, str]:
        return {"best_case": f"Positive developments around {topic} continue.",
                "base_case": f"Current trends around {topic} continue.",
                "worst_case": f"Negative variables emerge and change the trajectory of {topic}."}

    def analyze_behavior(self, scenario: str) -> Dict[str, Any]:
        return {"scenario": scenario,
                "behavioral_drivers": ["Incentives", "Risk aversion", "Social influence", "Resource constraints", "Habit and routine", "Decision pressure"],
                "analysis": "Behaviour of people and animals follows strong patterns but is shaped by many interacting variables, so forecasts are probabilistic.",
                "predictability": "PARTIAL"}

    # -- deterministic forecast card (used with or without an AI writer) -------------
    def build_forecast(self, topic: str, evidence_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        evidence_count = len(evidence_items)
        source_count = len({i.get("source", "?") for i in evidence_items})
        matrix = self.evidence_service.build_truth_matrix(evidence_items)
        confidence = self.calculate_confidence(evidence_count, source_count, matrix["evidence_score"])
        return {
            "topic": topic, "generated_at": datetime.now(timezone.utc).isoformat(), "forecast_horizon": self.determine_horizon(topic),
            "confidence": confidence, "trend_strength": self.analyze_trend_strength(evidence_count, source_count),
            "risk_matrix": self.build_risk_matrix(confidence), "scenarios": self.generate_scenarios(topic),
            "evidence_count": evidence_count, "source_count": source_count, "truth_matrix": matrix,
            "disclaimer": "Forecasts are probabilistic estimates, not guarantees.",
        }

    forecast_event = build_forecast

    def evidence_footer_markdown(self, forecast: Dict[str, Any], series_result: Optional[Dict[str, Any]] = None) -> str:
        """Deterministic 'how sure are we' block appended to every prediction."""
        rm = forecast["risk_matrix"]
        parts = [
            "## Evidence & confidence",
            "| Measure | Value |", "|---|---|",
            f"| Horizon | {forecast['forecast_horizon']} |",
            f"| Evidence base | {forecast['evidence_count']} item(s) from {forecast['source_count']} source(s) |",
            f"| Evidence quality | {forecast['truth_matrix']['classification']} |",
            f"| Data-driven confidence | {forecast['confidence']}% ({rm['uncertainty']}) |",
            f"| Volatility | {rm['volatility']} |",
        ]
        if series_result and "error" not in series_result:
            parts += ["", "## Quantitative projection", format_forecast(series_result)]
        parts += ["", f"_{forecast['disclaimer']} A prediction is never a fact - treat it as one input to your own judgement._"]
        return "\n".join(parts)

    @staticmethod
    def detect_series(text: str) -> Optional[List[float]]:
        return extract_series(text)


prediction_service = PredictionService()
