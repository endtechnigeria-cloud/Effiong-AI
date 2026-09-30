"""
EFFIONG AI - Research Engine (self-learning)
============================================
One call gathers everything Effiong AI can learn about a question, in parallel:

    * its own long-term knowledge memory (things it learned earlier)
    * live web search / pages the user pasted
    * the open knowledge repositories (Wikipedia, Wikidata, Internet Archive, LoC, scholarly indexes ...)

...and then LEARNS from what it found: public snippets are stored in the vector memory so the next question about
the same subject is answered faster and with more context.  Private chat text is never stored.
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.core.health import HEALTH
from src.database.vector_mesh import get_mesh
from src.services import search_service
from src.services.evidence_service import EvidenceService
from src.services.repository_service import RepositoryService
from src.utilities.text_utils import truncate


@dataclass
class ResearchPackage:
    query: str
    context: str = ""
    sources: List[Dict[str, Any]] = field(default_factory=list)   # normalised evidence items (for scoring / citing)
    live_results: List[Dict[str, str]] = field(default_factory=list)
    repo_hits: List[Dict[str, str]] = field(default_factory=list)
    memory_hits: List[Dict[str, Any]] = field(default_factory=list)
    truth_matrix: Dict[str, Any] = field(default_factory=dict)


class ResearchService:
    def __init__(self) -> None:
        self.repos = RepositoryService()
        self.evidence = EvidenceService()

    def gather(self, query: str, depth: str = "standard", live: bool = True, repositories: bool = True,
               memory: bool = True, learn: bool = True, pasted_links: bool = True) -> ResearchPackage:
        pkg = ResearchPackage(query=query)
        pool = ThreadPoolExecutor(max_workers=5)
        futs: Dict[str, Any] = {}
        if memory:
            futs["memory"] = pool.submit(lambda: get_mesh().query_similarity(query, limit=3, min_score=0.22))
        if live:
            futs["live"] = pool.submit(search_service.get_live_context, query)
        if repositories:
            futs["repos"] = pool.submit(self.repos.aggregate_knowledge, query, depth, 3)
        if pasted_links:
            futs["links"] = pool.submit(search_service.read_links_in, query)
        wait(list(futs.values()), timeout=24)
        blocks: List[str] = []

        def result(name: str, default: Any) -> Any:
            f = futs.get(name)
            if f is not None and f.done() and not f.exception():
                return f.result()
            if f is not None and f.done() and f.exception():
                HEALTH.flag(f"research:{name}", f"{f.exception().__class__.__name__}: {f.exception()}")
            return default

        pkg.memory_hits = result("memory", [])
        if pkg.memory_hits:
            blocks.append("[Effiong long-term memory (previously learned public sources)]\n" + "\n".join(
                f"- {truncate(h['text'], 500)} (source: {h['metadata'].get('url') or h['metadata'].get('source', 'memory')})" for h in pkg.memory_hits))
        link_text = result("links", "")
        if link_text:
            blocks.append("[Pages the user linked]\n" + link_text)
        live_ctx, pkg.live_results = result("live", ("", []))
        if live_ctx:
            blocks.append(live_ctx)
        pkg.repo_hits = result("repos", [])
        if pkg.repo_hits:
            lines = [f"[R{i}] {h['source']} — {h['title']} ({h['url']})\n    {truncate(h['summary'], 600)}" for i, h in enumerate(pkg.repo_hits[:9], 1)]
            blocks.append("[Open knowledge repositories]\n" + "\n".join(lines))
        pool.shutdown(wait=False, cancel_futures=True)

        pkg.sources = [{"source": h["source"], "source_type": h.get("source_type", ""), "title": h["title"], "url": h["url"]} for h in pkg.repo_hits]
        pkg.sources += [{"source": f"Web ({r.get('engine', '')})", "title": r.get("title", ""), "url": r.get("url", "")} for r in pkg.live_results]
        pkg.truth_matrix = self.evidence.build_truth_matrix(pkg.sources) if pkg.sources else {}
        pkg.context = truncate("\n\n".join(blocks), 14000)
        if learn and (pkg.repo_hits or pkg.live_results):
            threading.Thread(target=self._learn, args=(pkg,), daemon=True).start()
        return pkg

    def _learn(self, pkg: ResearchPackage) -> int:
        """Store public knowledge only (never the user's own words)."""
        mesh = get_mesh()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        stored = 0
        try:
            for h in pkg.repo_hits[:8]:
                if mesh.learn(f"{h['title']}. {h['summary']}", {"source": h["source"], "url": h["url"], "kind": "repository", "learned_at": now}):
                    stored += 1
            for r in pkg.live_results[:6]:
                if r.get("snippet") and mesh.learn(f"{r.get('title', '')}. {r['snippet']}", {"source": r.get("engine", "web"), "url": r.get("url", ""), "kind": "web", "learned_at": now}):
                    stored += 1
            HEALTH.ok("self-learning", f"stored {stored} public snippet(s)")
        except Exception as exc:
            HEALTH.flag("self-learning", f"{exc.__class__.__name__}: {exc}")
        return stored

    def health_check(self) -> Dict[str, Any]:
        return {"status": "online", "memory_items": get_mesh().count(), "repositories": self.repos.repository_health()}
