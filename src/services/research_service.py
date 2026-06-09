import asyncio

from datetime import datetime
from typing import Dict, List, Any

from src.services.repository_service import RepositoryService
from src.services.evidence_service import EvidenceService

from src.database.archive import ArchiveDatabase
from src.database.vector_mesh import VectorMesh


class ResearchService:
    """
    ============================================================
    EFFIONG AI RESEARCH ENGINE V3
    ============================================================

    Master Research Layer

    Responsibilities

    - Evidence Collection
    - Source Ranking
    - Truth Matrix Generation
    - Research Reports
    - Prediction Context
    - Vector Indexing
    - Archive Persistence
    - Knowledge Extraction

    Supports

    Problem #1 Memory
    Problem #2 Persistence
    Problem #3 Reasoning
    Problem #4 Prediction
    Problem #8 Verification
    Problem #9 Knowledge Graph
    Problem #10 Operator Center
    Problem #11 Agents
    Problem #12 Research Engine
    ============================================================
    """

    def __init__(self):

        self.repository_service = (
            RepositoryService()
        )

        self.evidence_service = (
            EvidenceService()
        )

        self.archive = (
            ArchiveDatabase()
        )

        self.vector_mesh = (
            VectorMesh()
        )

    # =========================================================
    # COLLECT EVIDENCE
    # =========================================================

    async def collect_evidence(
        self,
        query: str
    ) -> List[Dict]:

        return await (
            self.repository_service
            .aggregate_knowledge(query)
        )

    # =========================================================
    # RANK SOURCES
    # =========================================================

    def rank_sources(
        self,
        sources: List[Dict]
    ) -> List[Dict]:

        return sorted(

            sources,

            key=lambda x:
                x.get(
                    "confidence",
                    0
                ),

            reverse=True
        )

    # =========================================================
    # BUILD TRUTH MATRIX
    # =========================================================

    def build_truth_matrix(
        self,
        sources: List[Dict]
    ) -> Dict:

        return (
            self.evidence_service
            .build_truth_matrix_from_sources(
                sources
            )
        )

    # =========================================================
    # RESEARCH CONTEXT
    # =========================================================

    async def build_research_context(
        self,
        query: str,
        max_items: int = 10
    ) -> str:

        sources = await (
            self.collect_evidence(
                query
            )
        )

        sources = self.rank_sources(
            sources
        )

        blocks = []

        for source in sources[:max_items]:

            blocks.append(

                f"""
SOURCE:
{source.get('source')}

TITLE:
{source.get('title')}

CONTENT:
{source.get('content')}

CONFIDENCE:
{source.get('confidence')}
"""
            )

        return "\n".join(blocks)

    # =========================================================
    # EVIDENCE SUMMARY
    # =========================================================

    async def generate_evidence_summary(
        self,
        query: str
    ) -> str:

        report = await (
            self.generate_research_report(
                query
            )
        )

        tm = report["truth_matrix"]

        return f"""
TRUTH MATRIX

Classification:
{tm.get('classification')}

Confidence:
{tm.get('score')}%

Evidence Sources:
{len(report['sources'])}

FACT LAYER
{tm.get('fact_layer')}

SPECULATION LAYER
{tm.get('speculation_layer')}
"""

    # =========================================================
    # RESEARCH REPORT
    # =========================================================

    async def generate_research_report(
        self,
        query: str
    ) -> Dict[str, Any]:

        sources = await (
            self.collect_evidence(
                query
            )
        )

        ranked_sources = (
            self.rank_sources(
                sources
            )
        )

        truth_matrix = (
            self.build_truth_matrix(
                ranked_sources
            )
        )

        research_context = await (
            self.build_research_context(
                query
            )
        )

        report = {

            "query":
                query,

            "generated_at":
                datetime.utcnow().isoformat(),

            "sources":
                ranked_sources,

            "source_count":
                len(ranked_sources),

            "truth_matrix":
                truth_matrix,

            "research_context":
                research_context
        }

        return report

    # =========================================================
    # STORE RESEARCH REPORT
    # =========================================================

    async def persist_research_report(
        self,
        report: Dict
    ):

        try:

            self.archive.save_research_report(

                query=report["query"],

                report=report
            )

        except Exception as e:

            print(
                f"[Research Archive Error] {e}"
            )

    # =========================================================
    # VECTOR INDEX RESEARCH
    # =========================================================

    async def index_research_report(
        self,
        report: Dict
    ):

        try:

            text = f"""
QUERY

{report['query']}

RESEARCH

{report['research_context']}
"""

            await self.vector_mesh.store_vector(

                text=text,

                metadata={

                    "type":
                        "research",

                    "query":
                        report["query"],

                    "timestamp":
                        report[
                            "generated_at"
                        ]
                }
            )

        except Exception as e:

            print(
                f"[Research Index Error] {e}"
            )

    # =========================================================
    # COMPLETE RESEARCH PIPELINE
    # =========================================================

    async def execute_research_pipeline(
        self,
        query: str
    ) -> Dict:

        report = await (
            self.generate_research_report(
                query
            )
        )

        await self.persist_research_report(
            report
        )

        await self.index_research_report(
            report
        )

        return report

    # =========================================================
    # PREDICTION CONTEXT
    # =========================================================

    async def build_prediction_context(
        self,
        query: str
    ) -> Dict:

        report = await (
            self.execute_research_pipeline(
                query
            )
        )

        return {

            "prediction_ready":
                True,

            "confidence":
                report["truth_matrix"].get(
                    "score",
                    0
                ),

            "classification":
                report["truth_matrix"].get(
                    "classification",
                    "Unknown"
                ),

            "context":
                report[
                    "research_context"
                ],

            "sources":
                report[
                    "source_count"
                ]
        }

    # =========================================================
    # ENTITY EXTRACTION
    # =========================================================

    async def extract_entity_candidates(
        self,
        query: str
    ) -> List[str]:

        report = await (
            self.generate_research_report(
                query
            )
        )

        entities = set()

        for source in report["sources"]:

            title = source.get(
                "title",
                ""
            )

            if title:

                entities.add(title)

        return list(entities)

    # =========================================================
    # KNOWLEDGE GRAPH PACKAGE
    # =========================================================

    async def build_knowledge_graph_package(
        self,
        query: str
    ) -> Dict:

        entities = await (
            self.extract_entity_candidates(
                query
            )
        )

        return {

            "query":
                query,

            "entities":
                entities,

            "entity_count":
                len(entities),

            "generated_at":
                datetime.utcnow().isoformat()
        }

    # =========================================================
    # OPERATOR SUMMARY
    # =========================================================

    async def operator_summary(
        self,
        query: str
    ) -> Dict:

        report = await (
            self.generate_research_report(
                query
            )
        )

        return {

            "query":
                query,

            "source_count":
                report[
                    "source_count"
                ],

            "truth_classification":
                report[
                    "truth_matrix"
                ].get(
                    "classification"
                ),

            "confidence":
                report[
                    "truth_matrix"
                ].get(
                    "score"
                ),

            "generated_at":
                report[
                    "generated_at"
                ]
        }

    # =========================================================
    # AGENT RESEARCH PACKAGE
    # =========================================================

    async def build_agent_research_package(
        self,
        query: str
    ) -> Dict:

        report = await (
            self.generate_research_report(
                query
            )
        )

        return {

            "query":
                query,

            "research_context":
                report[
                    "research_context"
                ],

            "truth_matrix":
                report[
                    "truth_matrix"
                ],

            "sources":
                report[
                    "sources"
                ]
        }

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    def health_check(
        self
    ) -> Dict:

        return {

            "repository_service":
                True,

            "evidence_service":
                True,

            "archive":
                True,

            "vector_mesh":
                True,

            "status":
                "online"
        }