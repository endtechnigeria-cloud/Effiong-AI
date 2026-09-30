"""Registry of the autonomous agents Effiong AI can dispatch."""
from __future__ import annotations

from typing import Any, Dict, List

from src.services.agent_service import agent_service


class AgentRegistry:
    def __init__(self) -> None:
        self.agent_executor = agent_service
        self.registered_agents = {
            "historical_deepdive": {"description": "Deep multi-repository sweep of a historical topic; stores public sources it finds.", "status": "ACTIVE"},
            "heritage_scan": {"description": "Scans the web for new African heritage / history developments and learns them.", "status": "ACTIVE"},
            "repository_sync": {"description": "Refreshes long-term memory from open repositories for a subject.", "status": "ACTIVE"},
        }

    def dispatch_agent_task(self, agent_type: str, conceptual_topic: str) -> Dict[str, Any]:
        if agent_type not in self.registered_agents:
            return {"error": f"Agent '{agent_type}' is not registered."}
        return {"registry_status": "DISPATCHED", "execution_metrics": self.agent_executor.execute_agent(agent_type, conceptual_topic)}

    def get_all_manifests(self) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in self.registered_agents.items()]
