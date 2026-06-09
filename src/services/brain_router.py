import asyncio
from datetime import datetime
from typing import Dict, Any

from src.brain.context_manager import ContextManager

from src.database.archive import ArchiveDatabase
from src.database.vector_mesh import VectorMesh
from src.database.heritage_store import HeritageStore

from src.services.repository_service import RepositoryService
from src.services.research_service import ResearchService
from src.services.evidence_service import EvidenceService
from src.services.prediction_service import PredictionService
from src.services.model_service import ModelService
from src.services.document_service import DocumentService
from src.services.operator_service import OperatorService


EFFIONG_SYSTEM_PROMPT = """
You are Effiong AI.

MISSION

1. Preserve African heritage.
2. Pursue evidence-based truth.
3. Separate fact from speculation.
4. Explain reasoning clearly.
5. Support forecasting using evidence.
6. Never present forecasts as facts.
7. Future-discerning of events.

TRUTH MATRIX RULES

Always separate:

FACTS
INFERENCES
PREDICTIONS
UNCERTAINTIES

When evidence is weak,
explicitly state uncertainty.

When evidence is strong,
state confidence level.

When discussing history,
separate:

Verified Evidence
Oral Tradition
Speculation

from each other.
"""


class BrainRouter:

    """
    ==========================================================
    EFFIONG AI BRAIN ROUTER V3
    ==========================================================

    MASTER ORCHESTRATOR

    Problem #1
    Conversation Memory

    Problem #2
    Persistent Knowledge

    Problem #3
    Problem Solving

    Problem #4
    Prediction Engine

    Problem #5
    Truth Matrix

    Problem #6
    Document Generation

    Problem #7
    Multimedia Layer

    Problem #8
    Verification Engine

    Problem #9
    Knowledge Graph

    Problem #10
    Operator Control Center

    Problem #12
    Research & Evidence Engine
    """

    def __init__(self):

        self.context_manager = ContextManager()

        self.archive = ArchiveDatabase()

        self.vector_mesh = VectorMesh()

        self.heritage_store = HeritageStore()

        self.repository_service = RepositoryService()

        self.research_service = ResearchService()

        self.evidence_service = EvidenceService()

        self.prediction_service = PredictionService()

        self.model_service = ModelService()

        self.document_service = DocumentService()

        self.operator_service = OperatorService()

    # =====================================================
    # MEMORY
    # =====================================================

    async def build_memory_context(
        self,
        prompt: str,
        chat_history
    ) -> str:

        conversation_context = (
            self.context_manager.build_context(
                current_prompt=prompt,
                chat_history=chat_history
            )
        )

        retrieval_context = await (
            self.vector_mesh.build_retrieval_context(
                prompt
            )
        )

        return f"""
CONVERSATION MEMORY

{conversation_context}

VECTOR MEMORY

{retrieval_context}
"""

    # =====================================================
    # RESEARCH
    # =====================================================

    async def build_research_package(
        self,
        prompt: str
    ) -> Dict:

        report = (
            self.research_service
            .generate_research_report(
                prompt
            )
        )

        return report

    # =====================================================
    # EVIDENCE
    # =====================================================

    def build_truth_matrix(
        self,
        report: Dict
    ) -> Dict:

        sources = report.get(
            "sources",
            []
        )

        matrix = (
            self.evidence_service
            .build_truth_matrix(
                source_count=len(sources),
                evidence_count=len(sources)
            )
        )

        return matrix

    # =====================================================
    # PREDICTION
    # =====================================================

    def build_prediction(
        self,
        prompt: str,
        report: Dict
    ) -> Dict:

        evidence_items = []

        for source in report.get(
            "sources",
            []
        ):

            evidence_items.append(
                source.get(
                    "summary",
                    ""
                )
            )

        prediction = (
            self.prediction_service
            .forecast_event(
                topic=prompt,
                evidence_items=evidence_items,
                source_count=len(
                    report.get(
                        "sources",
                        []
                    )
                )
            )
        )

        return prediction

    # =====================================================
    # MODEL PROMPT
    # =====================================================

    def build_model_prompt(
        self,
        user_prompt: str,
        memory_context: str,
        research_report: Dict,
        truth_matrix: Dict,
        prediction: Dict
    ) -> str:

        return f"""
USER REQUEST

{user_prompt}

================================================

MEMORY CONTEXT

{memory_context}

================================================

RESEARCH CONTEXT

{research_report.get('research_context','')}

================================================

TRUTH MATRIX

{truth_matrix}

================================================

PREDICTION FRAMEWORK

{prediction}

================================================

INSTRUCTIONS

Answer comprehensively.

Separate:

FACTS
INFERENCES
PREDICTIONS
UNCERTAINTIES

when applicable.
"""

    # =====================================================
    # CORE EXECUTION
    # =====================================================

    async def process_prompt(
        self,
        prompt: str,
        chat_history
    ) -> Dict[str, Any]:

        started_at = datetime.utcnow()

        # ----------------------------------
        # MEMORY
        # ----------------------------------

        memory_context = (
            await self.build_memory_context(
                prompt,
                chat_history
            )
        )

        # ----------------------------------
        # RESEARCH
        # ----------------------------------

        research_report = (
            await self.build_research_package(
                prompt
            )
        )

        # ----------------------------------
        # EVIDENCE
        # ----------------------------------

        truth_matrix = (
            self.build_truth_matrix(
                research_report
            )
        )

        # ----------------------------------
        # PREDICTION
        # ----------------------------------

        prediction = (
            self.build_prediction(
                prompt,
                research_report
            )
        )

        # ----------------------------------
        # MODEL INPUT
        # ----------------------------------

        model_prompt = (
            self.build_model_prompt(
                prompt,
                memory_context,
                research_report,
                truth_matrix,
                prediction
            )
        )

        # ----------------------------------
        # LLM ROUTING
        # ----------------------------------

        model_response = (
            await self.model_service
            .execute_failover_chain(
                prompt=model_prompt,
                system_instruction=
                EFFIONG_SYSTEM_PROMPT
            )
        )

        final_output = (
            model_response.get(
                "output",
                ""
            )
        )

        engine = (
            model_response.get(
                "engine",
                "Unknown"
            )
        )

        # ----------------------------------
        # ARCHIVE CHAT
        # ----------------------------------

        try:

            self.archive.save_chat_exchange(
                user_prompt=prompt,
                assistant_response=final_output,
                engine=engine
            )

        except Exception as e:

            print(
                f"[Archive Error] {e}"
            )

        # ----------------------------------
        # VECTOR MEMORY
        # ----------------------------------

        try:

            await self.vector_mesh.index_chat_exchange(
                prompt,
                final_output
            )

        except Exception as e:

            print(
                f"[Vector Error] {e}"
            )

        # ----------------------------------
        # STORE PREDICTION
        # ----------------------------------

        try:

            self.archive.save_prediction(
                prediction
            )

        except Exception as e:

            print(
                f"[Prediction Save Error] {e}"
            )

        # ----------------------------------
        # OPERATOR METRICS
        # ----------------------------------

        try:

            self.operator_service.log_event({

                "timestamp":
                    datetime.utcnow().isoformat(),

                "engine":
                    engine,

                "prompt":
                    prompt[:100],

                "status":
                    "success"
            })

        except Exception as e:

            print(
                f"[Operator Error] {e}"
            )

        completed_at = datetime.utcnow()

        # ----------------------------------
        # RESPONSE
        # ----------------------------------

        return {

            "success": True,

            "engine":
                engine,

            "response":
                final_output,

            "research_report":
                research_report,

            "truth_matrix":
                truth_matrix,

            "prediction":
                prediction,

            "started_at":
                started_at.isoformat(),

            "completed_at":
                completed_at.isoformat()
        }

    # =====================================================
    # DOCUMENT GENERATION
    # =====================================================

    def generate_research_document(
        self,
        title: str,
        report: Dict
    ):

        return (
            self.document_service
            .create_research_report(
                title=title,

                summary=
                report.get(
                    "research_context",
                    ""
                ),

                evidence=
                report.get(
                    "sources",
                    []
                ),

                sources=
                report.get(
                    "sources",
                    []
                )
            )
        )

    # =====================================================
    # HEALTH
    # =====================================================

    def health_status(self):

        return {

            "archive":
                True,

            "vector_mesh":
                True,

            "heritage_store":
                True,

            "repository":
                self.repository_service
                .repository_health(),

            "models":
                self.model_service
                .model_availability()
        }


# ==========================================================
# PUBLIC WRAPPER
# ==========================================================

async def execute_effiong_cycle(
    prompt: str,
    chat_history
):

    router = BrainRouter()

    return await router.process_prompt(
        prompt,
        chat_history
    )


def execute_effiong_sync(
    prompt: str,
    chat_history
):

    return asyncio.run(
        execute_effiong_cycle(
            prompt,
            chat_history
        )
    )