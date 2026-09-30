"""
EFFIONG AI - Autonomous research agents
=======================================
Real agents (not simulations): each one gathers evidence from the web + repositories and stores what it learned in
the shared public-knowledge memory.  They return honest metrics (how many sources were actually found / stored).
"""
from __future__ import annotations

import time
from typing import Any, Dict

from src.core.health import HEALTH


class AgentService:
    def run_research_agent(self, topic: str, depth: str = "deep") -> Dict[str, Any]:
        from src.services.research_service import ResearchService

        start = time.time()
        try:
            pkg = ResearchService().gather(topic, depth=depth, live=True, repositories=True, memory=False, learn=False, pasted_links=False)
            stored = ResearchService()._learn(pkg)
            return {"status": "COMPLETED", "target_subject": topic, "sources_found": len(pkg.sources),
                    "snippets_learned": stored, "classification": (pkg.truth_matrix or {}).get("classification", "n/a"),
                    "seconds": round(time.time() - start, 1)}
        except Exception as exc:
            HEALTH.flag("agents", f"{exc.__class__.__name__}: {exc}")
            return {"status": "FAILED", "target_subject": topic, "error": str(exc)}

    def execute_agent(self, agent_type: str, objective: str) -> Dict[str, Any]:
        if agent_type in ("historical_deepdive", "heritage_scan", "repository_sync", "research"):
            return self.run_research_agent(objective, depth="deep" if agent_type == "historical_deepdive" else "standard")
        return {"status": "UNKNOWN_AGENT", "agent": agent_type}


agent_service = AgentService()
