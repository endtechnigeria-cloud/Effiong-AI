import os
import hashlib
from typing import List

import streamlit as st

try:
    from google import genai
except Exception:
    genai = None


class EmbeddingEngine:
    """
    ============================================================
    EFFIONG AI EMBEDDING ENGINE
    ============================================================

    Responsibilities

    - Generate semantic embeddings
    - Support Gemini Embeddings
    - Support local fallback embeddings
    - Support batch embedding generation
    - Feed Pinecone
    - Feed Supabase pgvector
    - Feed Research Engine
    - Feed Prediction Engine

    Future Expansion

    - HuggingFace Embeddings
    - Voyage AI Embeddings
    - BGE Embeddings
    - Instructor XL
    """

    def __init__(self):

        self.gemini_key = (
            st.secrets.get("GEMINI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )

        self.client = None

        if genai and self.gemini_key:
            try:
                self.client = genai.Client(
                    api_key=self.gemini_key
                )
            except Exception as e:
                print(
                    f"[Embedding Engine] Gemini unavailable: {e}"
                )

    # ========================================================
    # PRIMARY EMBEDDING METHOD
    # ========================================================

    def generate_embedding(
        self,
        text: str
    ) -> List[float]:

        if not text:
            return []

        try:

            if self.client:

                response = self.client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )

                return response.embeddings[0].values

        except Exception as e:

            print(
                f"[Embedding Engine] Gemini embedding failed: {e}"
            )

        return self._fallback_embedding(text)

    # ========================================================
    # BATCH EMBEDDINGS
    # ========================================================

    def generate_batch_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:

        vectors = []

        for text in texts:

            vectors.append(
                self.generate_embedding(text)
            )

        return vectors

    # ========================================================
    # HERITAGE EMBEDDINGS
    # ========================================================

    def generate_heritage_embedding(
        self,
        title: str,
        description: str
    ) -> List[float]:

        combined = f"""
TITLE:
{title}

DESCRIPTION:
{description}
"""

        return self.generate_embedding(combined)

    # ========================================================
    # RESEARCH EMBEDDINGS
    # ========================================================

    def generate_research_embedding(
        self,
        source_text: str
    ) -> List[float]:

        return self.generate_embedding(
            source_text
        )

    # ========================================================
    # PREDICTION EMBEDDINGS
    # ========================================================

    def generate_prediction_embedding(
        self,
        prediction_text: str
    ) -> List[float]:

        return self.generate_embedding(
            prediction_text
        )

    # ========================================================
    # LOCAL FALLBACK
    # ========================================================

    def _fallback_embedding(
        self,
        text: str
    ) -> List[float]:
        """
        Local deterministic vector.

        Not semantically intelligent.

        Prevents system crashes when
        embedding APIs are unavailable.
        """

        digest = hashlib.sha256(
            text.encode("utf-8")
        ).digest()

        vector = []

        for byte in digest:

            vector.append(
                float(byte) / 255.0
            )

        while len(vector) < 128:

            vector.extend(vector)

        return vector[:128]

    # ========================================================
    # VECTOR UTILITIES
    # ========================================================

    def cosine_similarity(
        self,
        vector_a: List[float],
        vector_b: List[float]
    ) -> float:

        if not vector_a or not vector_b:
            return 0.0

        length = min(
            len(vector_a),
            len(vector_b)
        )

        dot = sum(
            vector_a[i] * vector_b[i]
            for i in range(length)
        )

        mag_a = (
            sum(x * x for x in vector_a[:length])
        ) ** 0.5

        mag_b = (
            sum(x * x for x in vector_b[:length])
        ) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot / (mag_a * mag_b)