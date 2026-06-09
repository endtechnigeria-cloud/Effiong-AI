```python
import os
import json
import uuid

from datetime import datetime
from typing import List, Dict, Any

import streamlit as st

from src.brain.embeddings import EmbeddingEngine

try:
    from pinecone import Pinecone
except Exception:
    Pinecone = None

try:
    from supabase import create_client
except Exception:
    create_client = None


class VectorMesh:
    """
    ============================================================
    EFFIONG AI VECTOR MESH V2
    ============================================================

    HYBRID MEMORY SYSTEM

    Layer 1:
        Pinecone

    Layer 2:
        Supabase pgvector

    Layer 3:
        Local JSON Memory

    Supports

    Problem #1
    Persistent Memory

    Problem #3
    Retrieval Layer

    Problem #4
    Prediction Memory

    Problem #8
    Evidence Memory

    Problem #9
    Knowledge Graph Memory

    Problem #12
    Research Engine Memory
    """

    def __init__(self):

        self.embedding_engine = (
            EmbeddingEngine()
        )

        self.local_memory_path = (
            "vector_memory"
        )

        os.makedirs(
            self.local_memory_path,
            exist_ok=True
        )

        self.pinecone_index = None

        self.supabase = None

        self._initialize_pinecone()

        self._initialize_supabase()

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def _initialize_pinecone(self):

        try:

            pinecone_key = (
                st.secrets.get(
                    "PINECONE_API_KEY"
                )
                or os.getenv(
                    "PINECONE_API_KEY"
                )
            )

            pinecone_index = (
                st.secrets.get(
                    "PINECONE_INDEX"
                )
                or os.getenv(
                    "PINECONE_INDEX",
                    "effiong-memory"
                )
            )

            if (
                Pinecone
                and pinecone_key
            ):

                pc = Pinecone(
                    api_key=pinecone_key
                )

                self.pinecone_index = (
                    pc.Index(
                        pinecone_index
                    )
                )

        except Exception as e:

            print(
                f"[VectorMesh] Pinecone unavailable: {e}"
            )

    def _initialize_supabase(self):

        try:

            url = (
                st.secrets.get(
                    "SUPABASE_URL"
                )
                or os.getenv(
                    "SUPABASE_URL"
                )
            )

            key = (
                st.secrets.get(
                    "SUPABASE_KEY"
                )
                or os.getenv(
                    "SUPABASE_KEY"
                )
            )

            if (
                create_client
                and url
                and key
            ):

                self.supabase = (
                    create_client(
                        url,
                        key
                    )
                )

        except Exception as e:

            print(
                f"[VectorMesh] Supabase unavailable: {e}"
            )

    # =====================================================
    # MASTER STORE
    # =====================================================

    async def store_vector(
        self,
        text: str,
        metadata: Dict[str, Any]
    ):

        vector = (
            self.embedding_engine
            .generate_embedding(text)
        )

        vector_id = str(
            uuid.uuid4()
        )

        metadata["content"] = text

        metadata["vector_id"] = vector_id

        metadata["stored_at"] = (
            datetime.utcnow().isoformat()
        )

        # --------------------------------
        # Pinecone
        # --------------------------------

        try:

            if self.pinecone_index:

                self.pinecone_index.upsert(
                    vectors=[
                        (
                            vector_id,
                            vector,
                            metadata
                        )
                    ]
                )

        except Exception as e:

            print(
                f"[VectorMesh] Pinecone store failed: {e}"
            )

        # --------------------------------
        # Supabase
        # --------------------------------

        try:

            if self.supabase:

                self.supabase.table(
                    "vector_memory"
                ).insert({

                    "vector_id":
                        vector_id,

                    "content":
                        text,

                    "metadata":
                        metadata

                }).execute()

        except Exception as e:

            print(
                f"[VectorMesh] Supabase store failed: {e}"
            )

        # --------------------------------
        # Local
        # --------------------------------

        self._store_local_memory(
            vector_id,
            text,
            vector,
            metadata
        )

    # =====================================================
    # CHAT MEMORY
    # =====================================================

    async def index_chat_exchange(
        self,
        user_prompt: str,
        assistant_response: str
    ):

        text = f"""

USER

{user_prompt}

ASSISTANT

{assistant_response}

"""

        await self.store_vector(

            text=text,

            metadata={

                "type":
                    "chat",

                "timestamp":
                    datetime.utcnow().isoformat()
            }
        )

    # =====================================================
    # RESEARCH MEMORY
    # =====================================================

    async def store_research(
        self,
        query: str,
        research_context: str
    ):

        await self.store_vector(

            text=research_context,

            metadata={

                "type":
                    "research",

                "query":
                    query
            }
        )

    # =====================================================
    # TRUTH MATRIX MEMORY
    # =====================================================

    async def store_truth_matrix(
        self,
        truth_matrix: Dict
    ):

        await self.store_vector(

            text=json.dumps(
                truth_matrix,
                indent=2
            ),

            metadata={

                "type":
                    "truth_matrix"
            }
        )

    # =====================================================
    # PREDICTION MEMORY
    # =====================================================

    async def store_prediction(
        self,
        topic: str,
        prediction_text: str
    ):

        await self.store_vector(

            text=prediction_text,

            metadata={

                "type":
                    "prediction",

                "topic":
                    topic
            }
        )

    # =====================================================
    # EVIDENCE MEMORY
    # =====================================================

    async def store_evidence(
        self,
        source: str,
        evidence: str
    ):

        await self.store_vector(

            text=evidence,

            metadata={

                "type":
                    "evidence",

                "source":
                    source
            }
        )

    # =====================================================
    # KNOWLEDGE GRAPH MEMORY
    # =====================================================

    async def store_entity(
        self,
        entity_name: str,
        entity_type: str,
        description: str
    ):

        await self.store_vector(

            text=description,

            metadata={

                "type":
                    "entity",

                "entity_name":
                    entity_name,

                "entity_type":
                    entity_type
            }
        )

    # =====================================================
    # SEARCH API
    # =====================================================

    async def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:

        return await self.retrieve_context(
            query,
            top_k
        )

    # =====================================================
    # RETRIEVAL
    # =====================================================

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:

        query_vector = (

            self.embedding_engine
            .generate_embedding(
                query
            )
        )

        try:

            if self.pinecone_index:

                results = (
                    self.pinecone_index.query(
                        vector=query_vector,
                        top_k=top_k,
                        include_metadata=True
                    )
                )

                matches = []

                for match in results.matches:

                    matches.append({

                        "score":
                            match.score,

                        "metadata":
                            match.metadata
                    })

                return matches

        except Exception as e:

            print(
                f"[VectorMesh] Retrieval failed: {e}"
            )

        return self._local_similarity_search(
            query_vector,
            top_k
        )

    # =====================================================
    # BUILD CONTEXT
    # =====================================================

    async def build_retrieval_context(
        self,
        query: str
    ) -> str:

        results = await self.search(
            query,
            top_k=10
        )

        blocks = []

        for item in results:

            metadata = (
                item.get(
                    "metadata",
                    {}
                )
            )

            content = (
                metadata.get(
                    "content",
                    ""
                )
            )

            if content:

                blocks.append(
                    content
                )

        return "\n\n".join(
            blocks
        )

    # =====================================================
    # LOCAL STORE
    # =====================================================

    def _store_local_memory(
        self,
        vector_id,
        text,
        vector,
        metadata
    ):

        filepath = os.path.join(

            self.local_memory_path,

            "memory.json"
        )

        records = []

        if os.path.exists(
            filepath
        ):

            try:

                with open(
                    filepath,
                    "r",
                    encoding="utf-8"
                ) as f:

                    records = json.load(f)

            except Exception:

                records = []

        records.append({

            "vector_id":
                vector_id,

            "content":
                text,

            "vector":
                vector,

            "metadata":
                metadata
        })

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(

                records,

                f,

                ensure_ascii=False,

                indent=2
            )

    # =====================================================
    # LOCAL SEARCH
    # =====================================================

    def _local_similarity_search(
        self,
        query_vector,
        top_k
    ):

        filepath = os.path.join(

            self.local_memory_path,

            "memory.json"
        )

        if not os.path.exists(
            filepath
        ):
            return []

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as f:

                records = json.load(f)

        except Exception:

            return []

        scored = []

        for item in records:

            similarity = (

                self.embedding_engine
                .cosine_similarity(

                    query_vector,

                    item["vector"]
                )
            )

            scored.append({

                "score":
                    similarity,

                "metadata": {

                    **item["metadata"],

                    "content":
                        item["content"]
                }
            })

        scored.sort(

            key=lambda x: x["score"],

            reverse=True
        )

        return scored[:top_k]
```
