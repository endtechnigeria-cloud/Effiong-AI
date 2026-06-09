from typing import Dict
from typing import List

from src.database.archive import ArchiveDatabase
from src.database.heritage_store import HeritageStore
from src.database.vector_mesh import VectorMesh


import wikipediaapi
import internetarchive


class RepositoryService:

    """
    ==========================================================
    EFFIONG AI REPOSITORY SERVICE V2
    ==========================================================

    Unified Knowledge Retrieval Layer

    Sources

    1. Wikipedia
    2. Internet Archive
    3. Heritage Ledger
    4. Archive Database
    5. Vector Mesh

    Supports

    Problem #1
    Problem #2
    Problem #3
    Problem #8
    Problem #9
    Problem #12
    """

    def __init__(self):

        self.archive = ArchiveDatabase()

        self.heritage_store = HeritageStore()

        self.vector_mesh = VectorMesh()

        self.wikipedia = wikipediaapi.Wikipedia(
            language="en",
            user_agent="EffiongAI/3.0"
        )

    # =====================================================
    # WIKIPEDIA
    # =====================================================

    def search_wikipedia(
        self,
        query: str
    ) -> List[Dict]:

        results = []

        try:

            page = self.wikipedia.page(query)

            if page.exists():

                results.append({

                    "source":
                        "Wikipedia",

                    "title":
                        page.title,

                    "summary":
                        page.summary[:2500],

                    "verification":
                        "verified"
                })

        except Exception as e:

            print(
                f"[Wikipedia Error] {e}"
            )

        return results

    # =====================================================
    # INTERNET ARCHIVE
    # =====================================================

    def search_archive_org(
        self,
        query: str
    ) -> List[Dict]:

        results = []

        try:

            search = internetarchive.search_items(
                query
            )

            counter = 0

            for item in search:

                if counter >= 5:
                    break

                results.append({

                    "source":
                        "Internet Archive",

                    "title":
                        item.get(
                            "title",
                            "Unknown"
                        ),

                    "summary":
                        item.get(
                            "description",
                            ""
                        ),

                    "verification":
                        "probable"
                })

                counter += 1

        except Exception as e:

            print(
                f"[Archive Error] {e}"
            )

        return results

    # =====================================================
    # HERITAGE STORE
    # =====================================================

    def search_heritage(
        self,
        query: str
    ) -> List[Dict]:

        results = []

        try:

            nodes = (
                self.heritage_store
                .search_nodes(query)
            )

            for node in nodes:

                results.append({

                    "source":
                        "Heritage Ledger",

                    "title":
                        node["title"],

                    "summary":
                        node["description"],

                    "verification":
                        node[
                            "truth_classification"
                        ]
                })

        except Exception as e:

            print(
                f"[Heritage Error] {e}"
            )

        return results

    # =====================================================
    # ARCHIVE DATABASE
    # =====================================================

    def search_archive_database(
        self,
        query: str
    ) -> List[Dict]:

        results = []

        try:

            archive_hits = (
                self.archive
                .search_chat_history(query)
            )

            for hit in archive_hits:

                results.append({

                    "source":
                        "Archive Memory",

                    "title":
                        "Chat Memory",

                    "summary":
                        hit.get(
                            "assistant_response",
                            ""
                        ),

                    "verification":
                        "historical"
                })

        except Exception as e:

            print(
                f"[Archive DB Error] {e}"
            )

        return results

    # =====================================================
    # VECTOR MEMORY
    # =====================================================

    async def search_vector_memory(
        self,
        query: str
    ) -> List[Dict]:

        results = []

        try:

            vector_hits = await (
                self.vector_mesh
                .retrieve_context(
                    query=query,
                    top_k=5
                )
            )

            for hit in vector_hits:

                metadata = hit.get(
                    "metadata",
                    {}
                )

                results.append({

                    "source":
                        "Vector Mesh",

                    "title":
                        metadata.get(
                            "type",
                            "memory"
                        ),

                    "summary":
                        metadata.get(
                            "content",
                            ""
                        ),

                    "verification":
                        "memory"
                })

        except Exception as e:

            print(
                f"[Vector Error] {e}"
            )

        return results

    # =====================================================
    # MASTER AGGREGATOR
    # =====================================================

    async def aggregate_knowledge(
        self,
        query: str
    ) -> List[Dict]:

        results = []

        results.extend(
            self.search_wikipedia(query)
        )

        results.extend(
            self.search_archive_org(query)
        )

        results.extend(
            self.search_heritage(query)
        )

        results.extend(
            self.search_archive_database(query)
        )

        vector_results = await (
            self.search_vector_memory(
                query
            )
        )

        results.extend(
            vector_results
        )

        return results

    # =====================================================
    # BUILD CONTEXT
    # =====================================================

    async def build_context(
        self,
        query: str
    ) -> str:

        sources = await (
            self.aggregate_knowledge(
                query
            )
        )

        blocks = []

        for source in sources:

            blocks.append(
                f"""
SOURCE:
{source['source']}

TITLE:
{source['title']}

CONTENT:
{source['summary']}
"""
            )

        return "\n".join(blocks)

    # =====================================================
    # HEALTH
    # =====================================================

    def repository_health(self):

        return {

            "wikipedia":
                True,

            "internet_archive":
                True,

            "heritage_store":
                True,

            "archive":
                True,

            "vector_mesh":
                True
        }