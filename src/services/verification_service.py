"""
EFFIONG AI - Verification Engine (truth-seeking core)
=====================================================
Decides whether a heritage / historical / current-events claim is a FACT, a PROBABLE fact, an ORAL TRADITION, an
OPINION, a SPECULATION or DISPUTED - from evidence, not from the submitter's say-so.

Pipeline
  1. Read every link in the submission (safe fetch) and check the page really discusses the claim
  2. Look up each link on the Wayback Machine (is it already preserved?)
  3. Corroborate against open knowledge repositories and live web search
  4. Ask the multi-brain to judge support / contradiction (strictly from the evidence, never from memory alone)
  5. Combine into a truth-matrix classification + a UI status (Verified / Pending Verification / Disputed / Opinion / Speculation)

If the network or every AI tier is down the claim is simply kept as "Pending Verification" - it is never
auto-promoted to a fact.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Dict, List, Optional

import requests

from src.core.guard import ExecutionBudget
from src.core.health import HEALTH
from src.services import search_service
from src.services.evidence_service import EvidenceService, classify_url
from src.services.llm_providers import BRAIN, AllProvidersFailed
from src.services.repository_service import RepositoryService
from src.utilities.text_utils import extract_json, extract_urls, truncate, utc_now_iso

_STOP = set("the a an and or of to in on at by for with from as is are was were be been it its this that these those he she they "
            "their his her our your you we i not no but if then than into about over under after before between during also "
            "have has had which who whom when where why how what there here said says one two three".split())


def _keywords(text: str, limit: int = 14) -> List[str]:
    words = re.findall(r"[^\W\d_]{4,}", (text or "").lower(), re.UNICODE)
    seen: List[str] = []
    for w in words:
        if w not in _STOP and w not in seen:
            seen.append(w)
    return seen[:limit]


def relevance(claim_keywords: List[str], text: str) -> float:
    if not claim_keywords or not text:
        return 0.0
    low = text.lower()
    hits = sum(1 for k in claim_keywords if k in low)
    return round(hits / min(len(claim_keywords), 10), 2)


class VerificationService:
    def __init__(self) -> None:
        self.evidence_service = EvidenceService()
        self.repos = RepositoryService()

    # ------------------------------------------------------------------ helpers
    def wayback_lookup(self, url: str) -> Optional[Dict[str, str]]:
        try:
            r = requests.get("https://archive.org/wayback/available", params={"url": url}, timeout=10,
                             headers={"User-Agent": "EffiongAI/3.0"})
            snap = ((r.json().get("archived_snapshots") or {}).get("closest")) if r.status_code == 200 else None
            if snap and snap.get("available"):
                return {"url": snap.get("url", ""), "timestamp": snap.get("timestamp", "")}
        except Exception as exc:
            HEALTH.flag("verify:wayback", exc.__class__.__name__)
        return None

    def check_url(self, url: str, claim_kw: List[str]) -> Dict[str, Any]:
        page = search_service.fetch_page_text(url, max_chars=5000)
        text = page.get("text", "")
        out = {"url": url, "reachable": bool(text) or not page.get("error"), "title": page.get("title", ""),
               "kind": classify_url(url), "relevance": relevance(claim_kw, f"{page.get('title', '')} {text}"),
               "error": page.get("error", ""), "excerpt": truncate(text, 400)}
        out["wayback"] = self.wayback_lookup(url)
        return out

    # ------------------------------------------------------------------ main
    def verify_claim(self, title: str, narrative: str, verification_class: str = "", evidence_urls: Optional[List[str]] = None,
                     evidence_files: Optional[List[Dict[str, Any]]] = None, use_network: bool = True,
                     use_llm: bool = True, budget: Optional[ExecutionBudget] = None) -> Dict[str, Any]:
        claim_text = f"{title}. {narrative}"
        claim_kw = _keywords(claim_text)
        urls = list(dict.fromkeys((evidence_urls or []) + extract_urls(narrative)))[:5]
        files = evidence_files or []
        url_checks: List[Dict[str, Any]] = []
        repo_hits: List[Dict[str, Any]] = []
        web_hits: List[Dict[str, Any]] = []

        if use_network:
            pool = ThreadPoolExecutor(max_workers=8)
            url_futs = [pool.submit(self.check_url, u, claim_kw) for u in urls]
            repo_fut = pool.submit(self.repos.aggregate_knowledge, truncate(title or narrative, 140), "standard", 3)
            web_fut = pool.submit(search_service.web_search, truncate(title or narrative, 140), 5)
            wait(url_futs + [repo_fut, web_fut], timeout=28)
            for f in url_futs:
                if f.done() and not f.exception():
                    url_checks.append(f.result())
            if repo_fut.done() and not repo_fut.exception():
                repo_hits = repo_fut.result()
            if web_fut.done() and not web_fut.exception():
                web_hits = web_fut.result()
            pool.shutdown(wait=False, cancel_futures=True)

        sources: List[Dict[str, Any]] = []
        for c in url_checks:
            if c["reachable"] and c["relevance"] >= 0.2:
                sources.append({"source": f"Submitted link ({c['kind'].title()})", "title": c["title"] or c["url"], "url": c["url"],
                                "source_type": c["kind"].lower(), "relevance": c["relevance"], "stance": "supports"})
        for h in repo_hits:
            rel = relevance(claim_kw, f"{h['title']} {h['summary']}")
            if rel >= 0.25:
                sources.append({"source": h["source"], "title": h["title"], "url": h["url"], "source_type": h.get("source_type", ""),
                                "relevance": rel, "stance": "supports"})
        for w in web_hits:
            rel = relevance(claim_kw, f"{w.get('title', '')} {w.get('snippet', '')}")
            if rel >= 0.3:
                sources.append({"source": f"Web ({w.get('engine', '')})", "title": w.get("title", ""), "url": w.get("url", ""),
                                "source_type": classify_url(w.get("url", "")).lower(), "relevance": rel, "stance": "supports"})
        for f in files:
            sources.append({"source": f"Uploaded {f.get('kind', 'file')} proof", "title": f.get("name", ""), "url": "",
                            "source_type": "general", "relevance": 0.4, "stance": "supports", "sha256": f.get("sha256", "")})

        llm = self._llm_assessment(title, narrative, verification_class, sources, url_checks, budget) if (use_llm and use_network) else None
        if llm:
            contradict = set(int(i) for i in llm.get("contradicts", []) if str(i).isdigit())
            for i, s in enumerate(sources):
                if i in contradict:
                    s["stance"] = "contradicts"

        matrix = self.evidence_service.build_truth_matrix(sources)
        classification = matrix["classification"]
        claim_type = (llm or {}).get("claim_type", "unassessed")
        oral_class = "oral" in (verification_class or "").lower()

        # final record class + UI status
        if claim_type == "opinion":
            record_class, status = "Opinion", "Opinion"
        elif claim_type == "speculation":
            record_class, status = "Speculation", "Speculation"
        elif claim_type == "disputed" or classification == "COMPETING CLAIM":
            record_class, status = "Disputed", "Disputed"
        elif classification in ("VERIFIED FACT", "EVIDENCE SUPPORTED") and not oral_class and len(sources) >= 2:
            record_class, status = "Verified fact" if classification == "VERIFIED FACT" else "Evidence-supported fact", "Verified"
        elif oral_class or claim_type == "oral_tradition":
            record_class, status = "Oral tradition", "Pending Verification"
        elif classification in ("PROBABLE", "EVIDENCE SUPPORTED", "VERIFIED FACT"):
            record_class, status = "Probable", "Pending Verification"
        else:
            record_class, status = "Unverified", "Pending Verification"

        return {
            "checked_at": utc_now_iso(),
            "classification": classification,
            "record_class": record_class,
            "status": status,
            "confidence": float((llm or {}).get("confidence", matrix["evidence_score"])),
            "claim_type": claim_type,
            "assessment": (llm or {}).get("assessment") or (
                "Automatic checks were limited (network or AI tiers unavailable); the record stays pending verification."
                if not sources else f"{len(sources)} corroborating source(s) found."),
            "sources": sources,
            "url_checks": url_checks,
            "truth_matrix": matrix,
        }

    def _llm_assessment(self, title: str, narrative: str, vclass: str, sources: List[Dict[str, Any]],
                        url_checks: List[Dict[str, Any]], budget: Optional[ExecutionBudget]) -> Optional[Dict[str, Any]]:
        ev = "\n".join(f"[{i}] {s['source']} — {s['title']} ({s['url']})" for i, s in enumerate(sources)) or "(no external evidence found)"
        excerpts = "\n".join(f"- {c['url']}: {c['excerpt']}" for c in url_checks if c.get("excerpt"))
        prompt = (
            "You are a strict fact-checking editor for an African heritage archive. Judge ONLY from the evidence below; "
            "if the evidence does not support the claim say so. Do not use unstated memory as proof.\n\n"
            f"CLAIM TITLE: {title}\nCLAIM: {truncate(narrative, 2500)}\nSUBMITTER'S CLASS: {vclass}\n\n"
            f"EVIDENCE LIST:\n{ev}\n\nLINK EXCERPTS:\n{truncate(excerpts, 2500)}\n\n"
            'Return ONLY JSON: {"claim_type": "fact|oral_tradition|opinion|speculation|disputed", "confidence": 0-100, '
            '"contradicts": [evidence indexes that contradict the claim], "assessment": "2-3 sentences, plain language"}'
        )
        try:
            resp = BRAIN.generate([{"role": "user", "content": prompt}], task="reasoning", json_mode=True, max_tokens=700,
                                  temperature=0.1, timeout=40, budget=budget)
            data = extract_json(resp.text)
            if isinstance(data, dict) and data.get("claim_type") in ("fact", "oral_tradition", "opinion", "speculation", "disputed"):
                return data
        except AllProvidersFailed as exc:
            HEALTH.flag("verify:llm", f"no AI tier answered: {exc}")
        except Exception as exc:
            HEALTH.flag("verify:llm", f"{exc.__class__.__name__}: {exc}")
        return None

    # legacy API ------------------------------------------------------------------
    def validate_sources(self, sources: List[Dict]) -> Dict[str, int]:
        counts = {"verified": 0, "probable": 0, "oral": 0, "unverified": 0}
        for s in sources:
            v = str(s.get("verification", "")).lower()
            key = "verified" if "verified" in v or "reference" in v else "probable" if "probable" in v or "archive" in v else "oral" if "oral" in v else "unverified"
            counts[key] += 1
        return counts

    def verify_research(self, sources: List[Dict]) -> Dict[str, Any]:
        return {"source_breakdown": self.validate_sources(sources), "truth_matrix": self.evidence_service.build_truth_matrix(sources)}

    def verify_heritage_node(self, title: str, evidence_present: bool) -> Dict[str, Any]:
        return self.verify_claim(title, "", "", use_network=False, evidence_files=[{"name": "evidence", "kind": "file"}] if evidence_present else [])
