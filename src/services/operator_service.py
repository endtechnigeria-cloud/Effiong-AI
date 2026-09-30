"""
EFFIONG AI - Operator Control Center
====================================
Reads the JSONL event log that every other module already writes to via
`src.core.health.write_operator_log`, plus the live component-health registry and the request-throttling
counters, and turns them into one dashboard snapshot for the sidebar's "Operator" panel.

No separate storage: this module is a read/aggregate layer over what already exists, so there is exactly one
source of truth for system events.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.core.guard import GUARD
from src.core.health import HEALTH, read_operator_log, write_operator_log


class OperatorService:
    def __init__(self) -> None:
        self.log_directory = "operator_logs"

    # -- write ---------------------------------------------------------------------
    def log_event(self, event: Dict[str, Any]) -> None:
        name = event.pop("event", "event")
        write_operator_log(name, event)

    def log_error(self, source: str, message: str) -> None:
        write_operator_log("error", {"source": source, "message": message})

    # -- read ------------------------------------------------------------------------
    def get_events(self, limit: int = 200) -> List[Dict[str, Any]]:
        return read_operator_log(limit)

    def get_errors(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [e for e in read_operator_log(2000) if e.get("event") in ("error", "component_flagged")][-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        events = self.get_events(2000)
        kinds = Counter(e.get("event", "unknown") for e in events)
        providers_used = Counter(e.get("component", "").split(":")[-1] for e in events if e.get("event") == "component_flagged")
        return {"total_events": len(events), "event_breakdown": dict(kinds), "components_flagged": dict(providers_used),
                "total_errors": len(self.get_errors())}

    def dashboard_snapshot(self) -> Dict[str, Any]:
        health = HEALTH.snapshot()
        degraded = HEALTH.degraded()
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "metrics": self.get_metrics(),
            "component_health": health,
            "degraded_components": degraded,
            "system_status": "DEGRADED" if degraded else "NOMINAL",
            "recent_events": self.get_events(20),
        }

    def usage_snapshot(self, user_id: str) -> Dict[str, Any]:
        return {"user": user_id, "today": GUARD.usage_for(user_id)}

    def reset_usage(self) -> None:
        GUARD.reset()
        write_operator_log("usage_reset", {})


operator_service = OperatorService()
