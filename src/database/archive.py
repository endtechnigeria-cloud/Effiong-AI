from datetime import datetime
from typing import Dict, List, Optional
import json
import os

import streamlit as st

try:
    from supabase import create_client
except Exception:
    create_client = None


class ArchiveDatabase:

    """
    ==========================================================
    EFFIONG AI ARCHIVE DATABASE V2
    ==========================================================

    Persistent Storage Layer

    Stores

    - Chat History
    - Heritage Ledger
    - Predictions
    - Research Reports
    - Generated Assets

    Supports

    Problem #1
    Problem #2
    Problem #3
    Problem #4
    Problem #6
    Problem #7
    Problem #10
    """

    def __init__(self):

        self.local_storage_path = "archive_storage"

        os.makedirs(
            self.local_storage_path,
            exist_ok=True
        )

        self.supabase = None

        try:

            url = (
                st.secrets.get("SUPABASE_URL")
                or os.getenv("SUPABASE_URL")
            )

            key = (
                st.secrets.get("SUPABASE_KEY")
                or os.getenv("SUPABASE_KEY")
            )

            if create_client and url and key:

                self.supabase = create_client(
                    url,
                    key
                )

        except Exception as e:

            print(
                f"[Archive] Supabase unavailable: {e}"
            )

    # =====================================================
    # LOCAL HELPERS
    # =====================================================

    def _file_path(
        self,
        filename: str
    ):

        return os.path.join(
            self.local_storage_path,
            filename
        )

    def _read_file(
        self,
        filename: str
    ) -> List[Dict]:

        path = self._file_path(filename)

        if not os.path.exists(path):
            return []

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception:

            return []

    def _append_record(
        self,
        filename: str,
        record: Dict
    ):

        records = self._read_file(
            filename
        )

        records.append(record)

        with open(
            self._file_path(filename),
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                records,
                f,
                indent=2,
                ensure_ascii=False
            )

    # =====================================================
    # CHAT STORAGE
    # =====================================================

    def save_chat_exchange(
        self,
        user_prompt: str,
        assistant_response: str,
        engine: str
    ):

        record = {

            "timestamp":
                datetime.utcnow().isoformat(),

            "user_prompt":
                user_prompt,

            "assistant_response":
                assistant_response,

            "engine":
                engine
        }

        self._append_record(
            "chat_history.json",
            record
        )

        return record

    # =====================================================
    # HERITAGE STORAGE
    # =====================================================

    def save_heritage_node(
        self,
        node: Dict
    ):

        self._append_record(
            "heritage_nodes.json",
            node
        )

    # =====================================================
    # PREDICTION STORAGE
    # =====================================================

    def save_prediction(
        self,
        prediction: Dict
    ):

        self._append_record(
            "prediction_logs.json",
            prediction
        )

    # =====================================================
    # ASSET STORAGE
    # =====================================================

    def save_asset(
        self,
        asset: Dict
    ):

        self._append_record(
            "generated_assets.json",
            asset
        )

    # =====================================================
    # SEARCH CHAT HISTORY
    # =====================================================

    def search_chat_history(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict]:

        results = []

        query = query.lower()

        records = self._read_file(
            "chat_history.json"
        )

        for item in records:

            text = f"""
            {item.get('user_prompt','')}
            {item.get('assistant_response','')}
            """

            if query in text.lower():

                results.append(item)

        return results[:limit]

    # =====================================================
    # SEARCH HERITAGE
    # =====================================================

    def search_heritage_nodes(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict]:

        results = []

        query = query.lower()

        records = self._read_file(
            "heritage_nodes.json"
        )

        for node in records:

            text = f"""
            {node.get('title','')}
            {node.get('description','')}
            """

            if query in text.lower():

                results.append(node)

        return results[:limit]

    # =====================================================
    # SEARCH PREDICTIONS
    # =====================================================

    def search_predictions(
        self,
        query: str,
        limit: int = 50
    ):

        results = []

        query = query.lower()

        records = self._read_file(
            "prediction_logs.json"
        )

        for item in records:

            text = str(item)

            if query in text.lower():

                results.append(item)

        return results[:limit]

    # =====================================================
    # SEARCH ASSETS
    # =====================================================

    def search_assets(
        self,
        query: str,
        limit: int = 50
    ):

        results = []

        query = query.lower()

        records = self._read_file(
            "generated_assets.json"
        )

        for item in records:

            text = str(item)

            if query in text.lower():

                results.append(item)

        return results[:limit]

    # =====================================================
    # GLOBAL SEARCH
    # =====================================================

    def search_all(
        self,
        query: str
    ):

        return {

            "chat_history":
                self.search_chat_history(query),

            "heritage":
                self.search_heritage_nodes(query),

            "predictions":
                self.search_predictions(query),

            "assets":
                self.search_assets(query)
        }

    # =====================================================
    # STATS
    # =====================================================

    def statistics(self):

        return {

            "chat_records":
                len(
                    self._read_file(
                        "chat_history.json"
                    )
                ),

            "heritage_records":
                len(
                    self._read_file(
                        "heritage_nodes.json"
                    )
                ),

            "prediction_records":
                len(
                    self._read_file(
                        "prediction_logs.json"
                    )
                ),

            "asset_records":
                len(
                    self._read_file(
                        "generated_assets.json"
                    )
                )
        }