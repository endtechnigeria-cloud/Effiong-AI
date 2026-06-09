import re
from collections import defaultdict
from typing import Dict, List


class KnowledgeGraphService:

    """
    ============================================================
    EFFIONG AI KNOWLEDGE GRAPH
    ============================================================

    Problem #9

    Responsibilities

    - Entity Extraction
    - Relationship Mapping
    - Heritage Graph
    - Research Graph
    - Prediction Graph

    Future

    - Neo4j
    - GraphRAG
    """

    def __init__(self):

        self.graph = {

            "nodes": [],

            "edges": []
        }

    # =====================================================
    # ENTITY EXTRACTION
    # =====================================================

    def extract_entities(
        self,
        text: str
    ) -> List[str]:

        candidates = re.findall(
            r"\b[A-Z][a-zA-Z]+\b",
            text
        )

        return list(
            set(candidates)
        )

    # =====================================================
    # BUILD GRAPH
    # =====================================================

    def build_graph(
        self,
        documents: List[str]
    ):

        node_set = set()

        edge_set = set()

        for document in documents:

            entities = (
                self.extract_entities(
                    document
                )
            )

            for entity in entities:

                node_set.add(entity)

            for i in range(
                len(entities)
            ):

                for j in range(
                    i + 1,
                    len(entities)
                ):

                    edge_set.add(

                        (
                            entities[i],
                            entities[j]
                        )
                    )

        self.graph["nodes"] = [

            {

                "id": n,

                "label": n
            }

            for n in node_set
        ]

        self.graph["edges"] = [

            {

                "source": e[0],

                "target": e[1]
            }

            for e in edge_set
        ]

        return self.graph

    # =====================================================
    # HERITAGE GRAPH
    # =====================================================

    def build_heritage_graph(
        self,
        heritage_nodes
    ):

        docs = []

        for node in heritage_nodes:

            docs.append(

                f"""
                {node.get('title','')}
                {node.get('description','')}
                """
            )

        return self.build_graph(
            docs
        )

    # =====================================================
    # RESEARCH GRAPH
    # =====================================================

    def build_research_graph(
        self,
        sources
    ):

        docs = []

        for source in sources:

            docs.append(

                source.get(
                    "summary",
                    ""
                )
            )

        return self.build_graph(
            docs
        )

    # =====================================================
    # GRAPH STATISTICS
    # =====================================================

    def graph_statistics(self):

        return {

            "nodes":
                len(
                    self.graph["nodes"]
                ),

            "edges":
                len(
                    self.graph["edges"]
                )
        }

    # =====================================================
    # EXPORT
    # =====================================================

    def export_graph(self):

        return self.graph