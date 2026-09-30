"""
EFFIONG AI - Quantitative forecasting engine (numbers -> projections)
====================================================================
Pure NumPy (no scikit-learn needed).  Picks the better of a linear trend and Holt's damped-trend smoothing by
back-testing on the last points of the series, then returns projections with honest uncertainty bands.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import numpy as np


def extract_series(text: str, min_points: int = 4) -> Optional[List[float]]:
    """Find a run of numbers such as '10, 12, 15, 19, 24' inside a question."""
    num = r"-?\d+(?:,\d{3})*(?:\.\d+)?"
    m = re.search(r"(%s(?:\s*(?:,|;|->|→|then|and)\s*%s){%d,})" % (num, num, min_points - 1), text or "")
    if not m:
        return None
    nums = re.findall(num, m.group(1))
    try:
        vals = [float(n.replace(",", "")) for n in nums]
    except ValueError:
        return None
    return vals if len(vals) >= min_points else None


def _holt(y: np.ndarray, alpha: float, beta: float, phi: float = 0.92) -> tuple[np.ndarray, float, float]:
    level, trend = y[0], (y[1] - y[0])
    fitted = [y[0]]
    for t in range(1, len(y)):
        fitted.append(level + phi * trend)
        prev = level
        level = alpha * y[t] + (1 - alpha) * (level + phi * trend)
        trend = beta * (level - prev) + (1 - beta) * phi * trend
    return np.asarray(fitted), level, trend


class PredictiveEngine:
    @staticmethod
    def forecast_series(values: List[float], steps: int = 3) -> Dict[str, Any]:
        y = np.asarray(values, dtype=float)
        n = len(y)
        if n < 3:
            return {"error": "Insufficient data points for predictive modeling. Minimum 3 points required."}
        x = np.arange(n)
        hold = max(2, n // 5) if n >= 8 else 1
        train, test = y[:-hold], y[-hold:]

        def linear_fc(tr: np.ndarray, k: int) -> np.ndarray:
            b, a = np.polyfit(np.arange(len(tr)), tr, 1)
            return a + b * np.arange(len(tr), len(tr) + k)

        best_holt, best_err = (0.5, 0.3), float("inf")
        for a in (0.2, 0.5, 0.8):
            for b in (0.1, 0.3):
                _, lvl, trd = _holt(train, a, b)
                fc = np.array([lvl + sum(0.92 ** i for i in range(1, h + 1)) * trd for h in range(1, hold + 1)])
                err = float(np.mean(np.abs(fc - test)))
                if err < best_err:
                    best_holt, best_err = (a, b), err
        lin_err = float(np.mean(np.abs(linear_fc(train, hold) - test)))
        use_holt = best_err < lin_err and n >= 5

        if use_holt:
            fitted, lvl, trd = _holt(y, *best_holt)
            proj = np.array([lvl + sum(0.92 ** i for i in range(1, h + 1)) * trd for h in range(1, steps + 1)])
            resid = y - fitted
            model = f"Holt damped-trend smoothing (alpha={best_holt[0]}, beta={best_holt[1]})"
        else:
            b, a = np.polyfit(x, y, 1)
            proj = a + b * np.arange(n, n + steps)
            resid = y - (a + b * x)
            model = "Linear trend (least squares)"
        sigma = float(np.std(resid, ddof=1)) if n > 2 else float(np.std(y))
        widen = np.sqrt(np.arange(1, steps + 1))
        upper, lower = proj + 1.96 * sigma * widen, proj - 1.96 * sigma * widen
        ss_tot = float(np.sum((y - y.mean()) ** 2)) or 1.0
        r2 = max(0.0, 1 - float(np.sum(resid ** 2)) / ss_tot)
        slope = float(np.polyfit(x, y, 1)[0])
        return {
            "model": model,
            "historical_baseline": [float(v) for v in y],
            "projected_steps": [round(float(v), 4) for v in proj],
            "upper_confidence_bound": [round(float(v), 4) for v in upper],
            "lower_confidence_bound": [round(float(v), 4) for v in lower],
            "trend_direction": "UPWARD" if slope > 1e-9 else "DOWNWARD" if slope < -1e-9 else "FLAT",
            "model_confidence_score": round(r2 * 100, 2),
            "backtest_mean_abs_error": round(min(best_err, lin_err), 4),
            "rate_of_change": round(slope, 4),
            "note": "Bands are 95% ranges assuming past volatility continues; structural breaks are not modelled.",
        }

    forecast_linear_trend = forecast_series  # older name
    

def format_forecast(result: Dict[str, Any]) -> str:
    if "error" in result:
        return result["error"]
    steps = "\n".join(f"| +{i + 1} | {p} | {lo} – {hi} |" for i, (p, lo, hi) in enumerate(zip(
        result["projected_steps"], result["lower_confidence_bound"], result["upper_confidence_bound"])))
    return (f"**Quantitative model:** {result['model']}\n\n| Step | Projection | 95% range |\n|---|---|---|\n{steps}\n\n"
            f"Trend: **{result['trend_direction']}** (rate {result['rate_of_change']} per step) . fit {result['model_confidence_score']}% . "
            f"back-test error {result['backtest_mean_abs_error']}\n\n_{result['note']}_")
