"""
EFFIONG AI - Heritage Ledger
============================
The African Heritage record keeper.  Each record ("node") stores WHAT was claimed, HOW it was checked, WHO logged
it and WHEN, plus a SHA-256 fingerprint so the record can be cited and later proven unchanged.

Node types:  Fact Node . Oral Track Node . Opinion Node . Speculation Node . Disputed Node . Claim Node (pending)
Statuses  :  Verified . Pending Verification . Disputed . Opinion . Speculation

This class is plain Python (no Streamlit): the sidebar hands it the list stored in the session, the FastAPI
backend hands it a list loaded from Supabase.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.utilities.text_utils import sha256_text

NODE_TYPES = {"Verified": "Fact Node", "Opinion": "Opinion Node", "Speculation": "Speculation Node", "Disputed": "Disputed Node"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class HeritageStore:
    def __init__(self, records: Optional[List[Dict[str, Any]]] = None) -> None:
        self.records: List[Dict[str, Any]] = records if records is not None else []

    # ------------------------------------------------------------------ create
    def create_node(self, title: str, description: str, verification_class: str, evidence_url: str = "",
                    contributor: str = "Anonymous", verification: Optional[Dict[str, Any]] = None,
                    evidence_files: Optional[List[Dict[str, Any]]] = None, contributor_id: str = "",
                    contributor_profile: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        verification = verification or {}
        status = verification.get("status")
        oral = "oral" in (verification_class or "").lower()
        if not status:                                    # no verification ran: never auto-promote to "Verified"
            status = "Pending Verification"
        if status == "Pending Verification" and (oral or verification.get("record_class") == "Oral tradition"):
            node_type, truth = "Oral Track Node", "Oral Tradition"
        else:
            node_type = NODE_TYPES.get(status, "Claim Node")
            truth = verification.get("record_class") or ("Evidence Supported" if status == "Verified" else "Unverified")
        ts = _now()
        node = {
            "id": f"HER-{uuid.uuid4().hex[:8].upper()}",
            "title": title.strip(),
            "description": description.strip(),
            "node_type": node_type,
            "type": node_type,                           # kept for the sidebar card
            "verification_class": verification_class,
            "truth_classification": truth,
            "status": status,
            "confidence": verification.get("confidence"),
            "assessment": verification.get("assessment", ""),
            "evidence_url": evidence_url,
            "evidence_sources": [{k: s.get(k) for k in ("source", "title", "url", "stance")} for s in verification.get("sources", [])][:15],
            "evidence_files": evidence_files or [],
            "truth_matrix": {k: verification.get("truth_matrix", {}).get(k) for k in ("classification", "evidence_score", "consensus_score", "sources_reviewed")} if verification else {},
            "contributor": contributor,
            "contributor_id": contributor_id,
            "contributor_nationality": (contributor_profile or {}).get("nationality", ""),
            "contributor_tribe": (contributor_profile or {}).get("tribe", ""),
            "created_at": ts,
            "updated_at": ts,
            "checked_at": verification.get("checked_at", ""),
            "archives": [],
        }
        node["record_sha256"] = self.fingerprint(node)
        self.records.append(node)
        return node

    @staticmethod
    def fingerprint(node: Dict[str, Any]) -> str:
        """SHA-256 over the canonical, immutable part of the record (not archive receipts / edits)."""
        core = {k: node.get(k) for k in ("id", "title", "description", "verification_class", "evidence_url", "evidence_files",
                                          "contributor", "contributor_id", "created_at")}
        return sha256_text(json.dumps(core, sort_keys=True, ensure_ascii=False, default=str))

    # ------------------------------------------------------------------ read
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        return self.records

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return next((n for n in self.records if n["id"] == node_id), None)

    def search_nodes(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [n for n in self.records if q in f"{n['title']} {n['description']} {n['truth_classification']} {n['verification_class']}".lower()]

    def get_verified_nodes(self) -> List[Dict[str, Any]]:
        return [n for n in self.records if n["status"] == "Verified"]

    def get_pending_nodes(self) -> List[Dict[str, Any]]:
        return [n for n in self.records if n["status"] == "Pending Verification"]

    def get_fact_nodes(self) -> List[Dict[str, Any]]:
        return [n for n in self.records if n["node_type"] == "Fact Node"]

    def get_oral_nodes(self) -> List[Dict[str, Any]]:
        return [n for n in self.records if n["node_type"] == "Oral Track Node"]

    # ------------------------------------------------------------------ update
    def update_status(self, node_id: str, new_status: str) -> Optional[Dict[str, Any]]:
        n = self.get_node(node_id)
        if n:
            n["status"] = new_status
            n["updated_at"] = _now()
        return n

    def update_truth_classification(self, node_id: str, truth: str) -> Optional[Dict[str, Any]]:
        n = self.get_node(node_id)
        if n:
            n["truth_classification"] = truth
            n["updated_at"] = _now()
        return n

    def add_archive_receipts(self, node_id: str, receipts: List[Dict[str, Any]]) -> None:
        n = self.get_node(node_id)
        if n is not None:
            n.setdefault("archives", []).extend(receipts)
            n["updated_at"] = _now()

    def delete_node(self, node_id: str) -> bool:
        for i, n in enumerate(self.records):
            if n["id"] == node_id:
                del self.records[i]
                return True
        return False

    # ------------------------------------------------------------------ reporting
    def get_statistics(self) -> Dict[str, int]:
        return {"total_nodes": len(self.records), "verified_nodes": len(self.get_verified_nodes()),
                "pending_nodes": len(self.get_pending_nodes()), "fact_nodes": len(self.get_fact_nodes()),
                "oral_nodes": len(self.get_oral_nodes())}

    def export_ledger(self) -> Dict[str, Any]:
        return {"ledger_name": "Effiong AI Sovereign Heritage Ledger", "generated_at": _now(),
                "total_records": len(self.records), "records": self.records}

    @staticmethod
    def record_markdown(node: Dict[str, Any]) -> str:
        """Human-readable report for one record (rendered to PDF for archiving)."""
        tm = node.get("truth_matrix") or {}
        lines = [
            f"# Heritage Record {node['id']}: {node['title']}",
            "",
            "A record logged on **Effiong AI**, the African heritage preservation platform. Classification below is "
            "an automated evidence assessment - it is not proof, and it can change as new evidence arrives.",
            "",
            "## Record summary",
            "| Field | Value |", "|---|---|",
            f"| Record ID | {node['id']} |",
            f"| Status | {node['status']} |",
            f"| Classification | {node.get('truth_classification', '')} |",
            f"| Node type | {node.get('node_type', '')} |",
            f"| Submitted class | {node.get('verification_class', '')} |",
            f"| Logged (UTC) | {node.get('created_at', '')} |",
            f"| Last evidence check (UTC) | {node.get('checked_at') or 'not yet checked'} |",
            f"| Contributor | {node.get('contributor', 'Anonymous')} |",
            f"| SHA-256 fingerprint | {node.get('record_sha256', '')} |",
            "",
            "## Narrative",
            node.get("description", ""),
            "",
        ]
        if node.get("assessment"):
            lines += ["## Verification assessment", node["assessment"], ""]
        if tm:
            lines += ["## Truth matrix", "| Measure | Value |", "|---|---|",
                      f"| Classification | {tm.get('classification', '')} |", f"| Evidence score | {tm.get('evidence_score', '')}% |",
                      f"| Consensus score | {tm.get('consensus_score', '')}% |", f"| Sources reviewed | {tm.get('sources_reviewed', '')} |", ""]
        srcs = node.get("evidence_sources") or []
        if srcs:
            lines += ["## Evidence sources", "| # | Source | Title | Link | Stance |", "|---|---|---|---|---|"]
            for i, s in enumerate(srcs, 1):
                lines.append(f"| {i} | {s.get('source', '')} | {(s.get('title') or '')[:80]} | {s.get('url') or '-'} | {s.get('stance', '')} |")
            lines.append("")
        files = node.get("evidence_files") or []
        if files:
            lines += ["## Attached evidence files", "| File | Type | SHA-256 |", "|---|---|---|"]
            lines += [f"| {f.get('name', '')} | {f.get('kind', '')} | {f.get('sha256', '')[:24]}... |" for f in files]
            lines.append("")
        lines += ["---", "Cite as: Effiong AI Heritage Ledger, record " + node["id"] + ", fingerprint " + node.get("record_sha256", "")[:16] + "."]
        return "\n".join(lines)

    @staticmethod
    def record_json(node: Dict[str, Any]) -> str:
        return json.dumps({"@context": "https://schema.org", "@type": "CreativeWork", "identifier": node["id"], "name": node["title"],
                           "description": node["description"], "dateCreated": node["created_at"], "author": node.get("contributor"),
                           "additionalProperty": [{"name": "status", "value": node["status"]},
                                                  {"name": "classification", "value": node.get("truth_classification")},
                                                  {"name": "sha256", "value": node.get("record_sha256")}],
                           "citation": [s.get("url") for s in node.get("evidence_sources", []) if s.get("url")],
                           "record": node}, ensure_ascii=False, indent=2, default=str)
