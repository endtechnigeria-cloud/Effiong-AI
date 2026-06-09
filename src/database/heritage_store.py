from datetime import datetime
from typing import Dict, List, Optional
import uuid

import streamlit as st


class HeritageStore:
    """
    ============================================================
    EFFIONG AI HERITAGE LEDGER
    ============================================================

    Purpose:
        Permanent heritage preservation layer.

    Handles:
        - Fact Nodes
        - Oral Tradition Nodes
        - Evidence Nodes
        - Historical Records
        - Truth Classification

    Future Integrations:
        - Supabase
        - Pinecone
        - Vector Mesh
        - Verification Engine
        - Sovereign Knowledge Graph
        - Public Timeline API
    ============================================================
    """

    def __init__(self):
        self._initialize_store()

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def _initialize_store(self):

        if "heritage_store" not in st.session_state:

            st.session_state.heritage_store = []

    # ============================================================
    # CREATE NODE
    # ============================================================

    def create_node(
        self,
        title: str,
        description: str,
        verification_class: str,
        evidence_url: str = "",
        contributor: str = "Anonymous"
    ) -> Dict:

        node_id = f"HER-{uuid.uuid4().hex[:8].upper()}"

        if "Oral" in verification_class:

            node_type = "Oral Track Node"

            status = "Pending Verification"

            truth_classification = "Oral Tradition"

        else:

            node_type = "Fact Node"

            status = "Verified"

            truth_classification = "Evidence Supported"

        timestamp = datetime.utcnow().isoformat()

        node = {

            # Core Identity
            "id": node_id,

            # Content
            "title": title,
            "description": description,

            # Classification
            "node_type": node_type,
            "verification_class": verification_class,
            "truth_classification": truth_classification,

            # Status
            "status": status,

            # Evidence
            "evidence_url": evidence_url,

            # Metadata
            "contributor": contributor,
            "created_at": timestamp,
            "updated_at": timestamp
        }

        st.session_state.heritage_store.append(node)

        return node

    # ============================================================
    # READ OPERATIONS
    # ============================================================

    def get_all_nodes(self) -> List[Dict]:

        return st.session_state.heritage_store

    def get_node(
        self,
        node_id: str
    ) -> Optional[Dict]:

        for node in st.session_state.heritage_store:

            if node["id"] == node_id:

                return node

        return None

    # ============================================================
    # UPDATE STATUS
    # ============================================================

    def update_status(
        self,
        node_id: str,
        new_status: str
    ) -> Optional[Dict]:

        for node in st.session_state.heritage_store:

            if node["id"] == node_id:

                node["status"] = new_status

                node["updated_at"] = (
                    datetime.utcnow().isoformat()
                )

                return node

        return None

    # ============================================================
    # UPDATE TRUTH CLASSIFICATION
    # ============================================================

    def update_truth_classification(
        self,
        node_id: str,
        truth_classification: str
    ) -> Optional[Dict]:

        """
        Supported Values:

        Verified Fact
        Evidence Supported
        Oral Tradition
        Developing Report
        Disputed Claim
        Unverified Claim
        """

        for node in st.session_state.heritage_store:

            if node["id"] == node_id:

                node["truth_classification"] = (
                    truth_classification
                )

                node["updated_at"] = (
                    datetime.utcnow().isoformat()
                )

                return node

        return None

    # ============================================================
    # SEARCH
    # ============================================================

    def search_nodes(
        self,
        query: str
    ) -> List[Dict]:

        query = query.lower()

        results = []

        for node in st.session_state.heritage_store:

            searchable_text = f"""
            {node['title']}
            {node['description']}
            {node['truth_classification']}
            {node['verification_class']}
            """

            if query in searchable_text.lower():

                results.append(node)

        return results

    # ============================================================
    # FILTERS
    # ============================================================

    def get_verified_nodes(self) -> List[Dict]:

        return [

            node

            for node in st.session_state.heritage_store

            if node["status"] == "Verified"
        ]

    def get_pending_nodes(self) -> List[Dict]:

        return [

            node

            for node in st.session_state.heritage_store

            if node["status"] == "Pending Verification"
        ]

    def get_fact_nodes(self) -> List[Dict]:

        return [

            node

            for node in st.session_state.heritage_store

            if node["node_type"] == "Fact Node"
        ]

    def get_oral_nodes(self) -> List[Dict]:

        return [

            node

            for node in st.session_state.heritage_store

            if node["node_type"] == "Oral Track Node"
        ]

    # ============================================================
    # DELETE
    # ============================================================

    def delete_node(
        self,
        node_id: str
    ) -> bool:

        store = st.session_state.heritage_store

        for index, node in enumerate(store):

            if node["id"] == node_id:

                del store[index]

                return True

        return False

    # ============================================================
    # LEDGER STATISTICS
    # ============================================================

    def get_statistics(self) -> Dict:

        nodes = st.session_state.heritage_store

        total_nodes = len(nodes)

        verified_nodes = len(
            [
                n
                for n in nodes
                if n["status"] == "Verified"
            ]
        )

        pending_nodes = len(
            [
                n
                for n in nodes
                if n["status"] == "Pending Verification"
            ]
        )

        fact_nodes = len(
            [
                n
                for n in nodes
                if n["node_type"] == "Fact Node"
            ]
        )

        oral_nodes = len(
            [
                n
                for n in nodes
                if n["node_type"] == "Oral Track Node"
            ]
        )

        return {

            "total_nodes": total_nodes,

            "verified_nodes": verified_nodes,

            "pending_nodes": pending_nodes,

            "fact_nodes": fact_nodes,

            "oral_nodes": oral_nodes
        }

    # ============================================================
    # EXPORT
    # ============================================================

    def export_ledger(self) -> Dict:

        return {

            "ledger_name":
                "Effiong AI Sovereign Heritage Ledger",

            "generated_at":
                datetime.utcnow().isoformat(),

            "total_records":
                len(st.session_state.heritage_store),

            "records":
                st.session_state.heritage_store
        }

    # ============================================================
    # FUTURE SUPABASE SYNC
    # ============================================================

    async def sync_to_supabase(self):

        """
        Problem #2 Future Upgrade

        Push heritage nodes
        into Supabase permanent storage.

        Future implementation.
        """

        pass

    # ============================================================
    # FUTURE VECTOR INDEXING
    # ============================================================

    async def index_into_vector_mesh(self):

        """
        Problem #3 Future Upgrade

        Send heritage records
        into Pinecone/Supabase pgvector.

        Future implementation.
        """

        pass

    # ============================================================
    # FUTURE VERIFICATION ENGINE
    # ============================================================

    async def verify_node_evidence(
        self,
        node_id: str
    ):

        """
        Problem #8 Future Upgrade

        Automated evidence validation.

        Future implementation.
        """

        pass