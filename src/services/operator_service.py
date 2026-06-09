import json
import os
from datetime import datetime
from collections import Counter
from typing import Dict, List


class OperatorService:

    """
    ============================================================
    EFFIONG AI OPERATOR CONTROL CENTER
    ============================================================

    Responsibilities

    - System Metrics
    - Usage Analytics
    - Model Analytics
    - Error Monitoring
    - Agent Monitoring
    - Research Monitoring
    - Prediction Monitoring

    Problem #10
    """

    def __init__(self):

        self.log_directory = "operator_logs"

        os.makedirs(
            self.log_directory,
            exist_ok=True
        )

        self.event_file = os.path.join(
            self.log_directory,
            "events.json"
        )

        self.error_file = os.path.join(
            self.log_directory,
            "errors.json"
        )

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================

    def _append(
        self,
        filepath,
        payload
    ):

        records = []

        if os.path.exists(filepath):

            try:

                with open(filepath, "r") as f:
                    records = json.load(f)

            except Exception:
                records = []

        records.append(payload)

        with open(filepath, "w") as f:
            json.dump(
                records,
                f,
                indent=2
            )

    # =====================================================
    # EVENTS
    # =====================================================

    def log_event(
        self,
        event: Dict
    ):

        self._append(
            self.event_file,
            event
        )

    # =====================================================
    # ERRORS
    # =====================================================

    def log_error(
        self,
        source: str,
        message: str
    ):

        self._append(

            self.error_file,

            {

                "timestamp":
                    datetime.utcnow().isoformat(),

                "source":
                    source,

                "message":
                    message
            }
        )

    # =====================================================
    # METRICS
    # =====================================================

    def get_metrics(self):

        events = self.get_events()

        engines = Counter()

        for e in events:

            if "engine" in e:

                engines[e["engine"]] += 1

        return {

            "total_events":
                len(events),

            "engine_usage":
                dict(engines),

            "total_errors":
                len(self.get_errors())
        }

    # =====================================================
    # READ
    # =====================================================

    def get_events(self):

        if not os.path.exists(
            self.event_file
        ):
            return []

        try:

            with open(
                self.event_file,
                "r"
            ) as f:

                return json.load(f)

        except Exception:

            return []

    def get_errors(self):

        if not os.path.exists(
            self.error_file
        ):
            return []

        try:

            with open(
                self.error_file,
                "r"
            ) as f:

                return json.load(f)

        except Exception:

            return []

    # =====================================================
    # DASHBOARD
    # =====================================================

    def dashboard_snapshot(self):

        metrics = self.get_metrics()

        return {

            "generated_at":
                datetime.utcnow().isoformat(),

            "metrics":
                metrics
        }