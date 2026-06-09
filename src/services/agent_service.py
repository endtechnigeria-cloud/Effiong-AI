# src/services/agent_service.py

from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from src.services.repository_service import repository_service
from src.services.research_service import research_service
from src.services.prediction_service import prediction_service
from src.services.evidence_service import evidence_service
from src.services.operator_service import operator_service


class AgentService:
    """
    ============================================================
    EFFIONG AI AUTONOMOUS AGENT FRAMEWORK
    ============================================================

    Problem #11

    PURPOSE
    -------
    Provides autonomous research capabilities.

    Agents can:

    - Investigate topics
    - Gather evidence
    - Search repositories
    - Build reports
    - Generate predictions
    - Feed Heritage Ledger
    - Support Knowledge Verification

    FUTURE AGENTS
    -------------

    1. Heritage Agent
    2. Research Agent
    3. Prediction Agent
    4. Verification Agent
    5. Repository Agent
    6. Timeline Agent
    7. Knowledge Graph Agent
    8. Media Agent
    """

    def __init__(self):

        self.active_agents = {}

        self.completed_jobs = []

        self.agent_registry = {

            "research_agent":
                self.run_research_agent,

            "prediction_agent":
                self.run_prediction_agent,

            "evidence_agent":
                self.run_evidence_agent,

            "heritage_agent":
                self.run_heritage_agent
        }

    # =========================================================
    # AGENT CREATION
    # =========================================================

    def create_agent_job(
        self,
        agent_type: str,
        objective: str
    ) -> str:

        job_id = str(uuid.uuid4())

        self.active_agents[job_id] = {

            "job_id":
                job_id,

            "agent_type":
                agent_type,

            "objective":
                objective,

            "status":
                "running",

            "created_at":
                datetime.utcnow().isoformat(),

            "result":
                None
        }

        operator_service.register_agent_task(
            agent_type,
            objective
        )

        return job_id

    # =========================================================
    # AGENT EXECUTION
    # =========================================================

    def execute_agent(
        self,
        agent_type: str,
        objective: str
    ) -> Dict:

        if agent_type not in self.agent_registry:

            return {

                "status": "error",

                "message":
                    f"Unknown agent: {agent_type}"
            }

        job_id = self.create_agent_job(
            agent_type,
            objective
        )

        try:

            result = self.agent_registry[
                agent_type
            ](objective)

            self.active_agents[
                job_id
            ]["status"] = "completed"

            self.active_agents[
                job_id
            ]["result"] = result

            self.completed_jobs.append(
                self.active_agents[job_id]
            )

            return {

                "status":
                    "success",

                "job_id":
                    job_id,

                "result":
                    result
            }

        except Exception as e:

            self.active_agents[
                job_id
            ]["status"] = "failed"

            self.active_agents[
                job_id
            ]["error"] = str(e)

            return {

                "status":
                    "error",

                "job_id":
                    job_id,

                "message":
                    str(e)
            }

    # =========================================================
    # RESEARCH AGENT
    # =========================================================

    def run_research_agent(
        self,
        topic: str
    ) -> Dict:

        research_report = (
            research_service.perform_research(
                topic
            )
        )

        return {

            "agent":
                "research_agent",

            "topic":
                topic,

            "report":
                research_report
        }

    # =========================================================
    # PREDICTION AGENT
    # =========================================================

    def run_prediction_agent(
        self,
        topic: str
    ) -> Dict:

        prediction = (
            prediction_service.generate_prediction(
                topic
            )
        )

        return {

            "agent":
                "prediction_agent",

            "topic":
                topic,

            "prediction":
                prediction
        }

    # =========================================================
    # EVIDENCE AGENT
    # =========================================================

    def run_evidence_agent(
        self,
        topic: str
    ) -> Dict:

        repository_results = (
            repository_service.search_all_sources(
                topic
            )
        )

        evidence = (
            evidence_service.build_evidence_package(
                topic,
                repository_results
            )
        )

        return {

            "agent":
                "evidence_agent",

            "topic":
                topic,

            "evidence":
                evidence
        }

    # =========================================================
    # HERITAGE AGENT
    # =========================================================

    def run_heritage_agent(
        self,
        topic: str
    ) -> Dict:

        research_report = (
            research_service.perform_research(
                topic
            )
        )

        evidence = (
            evidence_service.build_evidence_package(
                topic,
                research_report.get(
                    "sources",
                    []
                )
            )
        )

        return {

            "agent":
                "heritage_agent",

            "topic":
                topic,

            "heritage_package": {

                "research":
                    research_report,

                "evidence":
                    evidence
            }
        }

    # =========================================================
    # MULTI-AGENT RESEARCH PIPELINE
    # =========================================================

    def execute_full_analysis(
        self,
        topic: str
    ) -> Dict:

        research = (
            self.run_research_agent(
                topic
            )
        )

        evidence = (
            self.run_evidence_agent(
                topic
            )
        )

        prediction = (
            self.run_prediction_agent(
                topic
            )
        )

        return {

            "topic":
                topic,

            "research":
                research,

            "evidence":
                evidence,

            "prediction":
                prediction,

            "generated_at":
                datetime.utcnow().isoformat()
        }

    # =========================================================
    # ACTIVE AGENTS
    # =========================================================

    def get_active_agents(
        self
    ) -> List[Dict]:

        return list(
            self.active_agents.values()
        )

    # =========================================================
    # COMPLETED JOBS
    # =========================================================

    def get_completed_jobs(
        self
    ) -> List[Dict]:

        return self.completed_jobs

    # =========================================================
    # AGENT REGISTRY
    # =========================================================

    def get_available_agents(
        self
    ) -> List[str]:

        return list(
            self.agent_registry.keys()
        )

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    def health_check(
        self
    ) -> Dict:

        return {

            "service":
                "agent_service",

            "status":
                "online",

            "available_agents":
                self.get_available_agents(),

            "active_jobs":
                len(
                    self.active_agents
                ),

            "completed_jobs":
                len(
                    self.completed_jobs
                )
        }


# ============================================================
# GLOBAL INSTANCE
# ============================================================

agent_service = AgentService()