# src/services/agent_registry.py

from typing import Dict, List, Callable, Optional, Any
from datetime import datetime

from src.services.agent_service import agent_service


class AgentRegistry:
    """
    ============================================================
    EFFIONG AI AGENT REGISTRY
    ============================================================

    Problem #11

    PURPOSE
    -------
    Central discovery and registration layer
    for all autonomous agents.

    BENEFITS
    --------

    Instead of hardcoding agents throughout
    the platform, every agent is registered here.

    This allows:

    - Dynamic agent discovery
    - Agent versioning
    - Agent permissions
    - Agent health tracking
    - Agent categories
    - Future plugin architecture
    - Future marketplace architecture

    FUTURE AGENTS
    -------------

    Core Intelligence
    - Research Agent
    - Prediction Agent
    - Evidence Agent
    - Heritage Agent

    Future Expansion
    - Verification Agent
    - Knowledge Graph Agent
    - Timeline Agent
    - Repository Agent
    - Image Agent
    - Video Agent
    - Document Agent
    - Forecast Agent
    - Monitoring Agent
    - Operator Agent
    """

    def __init__(self):

        self.registry = {}

        self.categories = {}

        self.load_core_agents()

    # =========================================================
    # REGISTER AGENT
    # =========================================================

    def register_agent(
        self,
        name: str,
        description: str,
        category: str,
        version: str,
        handler: Callable,
        permissions: Optional[List[str]] = None
    ) -> bool:

        self.registry[name] = {

            "name":
                name,

            "description":
                description,

            "category":
                category,

            "version":
                version,

            "handler":
                handler,

            "permissions":
                permissions or [],

            "registered_at":
                datetime.utcnow().isoformat(),

            "enabled":
                True
        }

        if category not in self.categories:
            self.categories[category] = []

        self.categories[category].append(name)

        return True

    # =========================================================
    # UNREGISTER AGENT
    # =========================================================

    def unregister_agent(
        self,
        name: str
    ) -> bool:

        if name not in self.registry:
            return False

        category = self.registry[name]["category"]

        if category in self.categories:

            self.categories[category] = [

                agent
                for agent in self.categories[category]
                if agent != name
            ]

        del self.registry[name]

        return True

    # =========================================================
    # ENABLE AGENT
    # =========================================================

    def enable_agent(
        self,
        name: str
    ) -> bool:

        if name not in self.registry:
            return False

        self.registry[name]["enabled"] = True

        return True

    # =========================================================
    # DISABLE AGENT
    # =========================================================

    def disable_agent(
        self,
        name: str
    ) -> bool:

        if name not in self.registry:
            return False

        self.registry[name]["enabled"] = False

        return True

    # =========================================================
    # GET AGENT
    # =========================================================

    def get_agent(
        self,
        name: str
    ) -> Optional[Dict]:

        return self.registry.get(name)

    # =========================================================
    # EXECUTE AGENT
    # =========================================================

    def execute_agent(
        self,
        name: str,
        objective: str
    ) -> Dict:

        agent = self.get_agent(name)

        if not agent:

            return {
                "status": "error",
                "message": "Agent not found"
            }

        if not agent["enabled"]:

            return {
                "status": "error",
                "message": "Agent disabled"
            }

        try:

            result = agent["handler"](
                objective
            )

            return {
                "status": "success",
                "agent": name,
                "result": result
            }

        except Exception as e:

            return {
                "status": "error",
                "agent": name,
                "message": str(e)
            }

    # =========================================================
    # CATEGORY LOOKUP
    # =========================================================

    def get_agents_by_category(
        self,
        category: str
    ) -> List[Dict]:

        names = self.categories.get(
            category,
            []
        )

        return [

            self.registry[name]

            for name in names

            if name in self.registry
        ]

    # =========================================================
    # LIST AGENTS
    # =========================================================

    def list_agents(
        self
    ) -> List[Dict]:

        return list(
            self.registry.values()
        )

    # =========================================================
    # AGENT COUNT
    # =========================================================

    def count_agents(
        self
    ) -> int:

        return len(
            self.registry
        )

    # =========================================================
    # LOAD CORE AGENTS
    # =========================================================

    def load_core_agents(
        self
    ):

        self.register_agent(

            name="research_agent",

            description=
                "Performs repository-backed research and analysis.",

            category="intelligence",

            version="1.0.0",

            handler=
                agent_service.run_research_agent,

            permissions=[
                "repository_access",
                "research_generation"
            ]
        )

        self.register_agent(

            name="prediction_agent",

            description=
                "Produces probabilistic forecasts and predictions.",

            category="prediction",

            version="1.0.0",

            handler=
                agent_service.run_prediction_agent,

            permissions=[
                "prediction_engine"
            ]
        )

        self.register_agent(

            name="evidence_agent",

            description=
                "Builds evidence packages and source bundles.",

            category="verification",

            version="1.0.0",

            handler=
                agent_service.run_evidence_agent,

            permissions=[
                "repository_access",
                "evidence_generation"
            ]
        )

        self.register_agent(

            name="heritage_agent",

            description=
                "Researches and preserves African heritage records.",

            category="heritage",

            version="1.0.0",

            handler=
                agent_service.run_heritage_agent,

            permissions=[
                "heritage_access",
                "research_generation"
            ]
        )

    # =========================================================
    # REGISTRY SNAPSHOT
    # =========================================================

    def registry_snapshot(
        self
    ) -> Dict:

        category_counts = {}

        for category, agents in self.categories.items():

            category_counts[category] = len(
                agents
            )

        return {

            "total_agents":
                self.count_agents(),

            "categories":
                category_counts,

            "registered_agents":
                list(self.registry.keys()),

            "generated_at":
                datetime.utcnow().isoformat()
        }

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    def health_check(
        self
    ) -> Dict:

        return {

            "service":
                "agent_registry",

            "status":
                "online",

            "registered_agents":
                self.count_agents(),

            "categories":
                len(self.categories)
        }


# ============================================================
# GLOBAL REGISTRY INSTANCE
# ============================================================

agent_registry = AgentRegistry()
