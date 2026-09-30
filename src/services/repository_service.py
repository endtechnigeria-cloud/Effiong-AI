"""
EFFIONG AI - Repository Service (multi-tier knowledge base)
===========================================================
Pulls from many open repositories of human knowledge at once (all free, no key needed):

    Wikipedia . Wikidata . Internet Archive . Library of Congress . Open Library . Project Gutenberg .
    Crossref (scholarly) . OpenAlex (scholarly) . arXiv (papers)

Every adapter is isolated: if one repository is slow or down it is skipped and flagged, and the
others still answer.  Results are plain dicts:
    {source, source_type, title, summary, url, verification}
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Callable, Dict, List

import requests

from src.core.health import HEALTH
from src.utilities.text_utils import truncate

UA = {"User-Agent": "EffiongAI/3.0 (heritage research; contact via project owner)"}
TIMEOUT = 9

Item = Dict[str, str]


def _item(source: str, source_type: str, title: str, summary: str, url: str, verification: str) -> Item:
    return {"source": source, "source_type": source_type, "title": (title or "").strip(),
            "summary": truncate((summary or "").strip(), 1800), "url": url or "", "verification": verification}


def _get(url: str, **params: Any) -> requests.Response:
    return requests.get(url, params=params or None, headers=UA, timeout=TIMEOUT)


def _clean_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


# ---------------------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------------------
def wikipedia(query: str, n: int = 3) -> List[Item]:
    r = _get("https://en.wikipedia.org/w/api.php", action="query", generator="search", gsrsearch=query,
             gsrlimit=n, prop="extracts|info", exintro=1, explaintext=1, exlimit=n, inprop="url", format="json")
    if r.status_code != 200:
        return []
    pages = (r.json().get("query") or {}).get("pages", {})
    ranked = sorted(pages.values(), key=lambda p: p.get("index", 99))
    return [_item("Wikipedia", "reference", p.get("title", ""), p.get("extract", ""), p.get("fullurl", ""), "reference")
            for p in ranked if p.get("extract")]


def wikidata(query: str, n: int = 3) -> List[Item]:
    r = _get("https://www.wikidata.org/w/api.php", action="wbsearchentities", search=query, language="en",
             format="json", limit=n)
    if r.status_code != 200:
        return []
    return [_item("Wikidata", "reference", i.get("label", ""), i.get("description", ""),
                  i.get("concepturi") or f"https://www.wikidata.org/wiki/{i.get('id', '')}", "reference")
            for i in r.json().get("search", [])]


def internet_archive(query: str, n: int = 4) -> List[Item]:
    r = _get("https://archive.org/advancedsearch.php", q=query, rows=n, output="json", **{"fl[]": ["identifier", "title", "description", "date"]})
    if r.status_code != 200:
        return []
    out = []
    for d in (r.json().get("response") or {}).get("docs", []):
        desc = d.get("description", "")
        if isinstance(desc, list):
            desc = " ".join(desc)
        out.append(_item("Internet Archive", "archive", d.get("title", ""), _clean_html(desc) or f"Archived item ({d.get('date', 'undated')})",
                         f"https://archive.org/details/{d.get('identifier', '')}", "archive"))
    return out


def library_of_congress(query: str, n: int = 3) -> List[Item]:
    r = _get("https://www.loc.gov/search/", q=query, fo="json", c=n)
    if r.status_code != 200:
        return []
    out = []
    for d in r.json().get("results", [])[:n]:
        desc = d.get("description") or d.get("subject") or ""
        if isinstance(desc, list):
            desc = "; ".join(map(str, desc))
        out.append(_item("Library of Congress", "government", d.get("title", ""), str(desc), d.get("url", "") or d.get("id", ""), "archive"))
    return out


def open_library(query: str, n: int = 3) -> List[Item]:
    r = _get("https://openlibrary.org/search.json", q=query, limit=n)
    if r.status_code != 200:
        return []
    out = []
    for d in r.json().get("docs", [])[:n]:
        authors = ", ".join(d.get("author_name", [])[:3])
        summary = f"By {authors or 'unknown author'}; first published {d.get('first_publish_year', 'n/a')}."
        out.append(_item("Open Library", "book", d.get("title", ""), summary, "https://openlibrary.org" + d.get("key", ""), "probable"))
    return out


def gutenberg(query: str, n: int = 3) -> List[Item]:
    r = _get("https://gutendex.com/books/", search=query)
    if r.status_code != 200:
        return []
    out = []
    for d in r.json().get("results", [])[:n]:
        authors = ", ".join(a.get("name", "") for a in d.get("authors", [])[:2])
        out.append(_item("Project Gutenberg", "book", d.get("title", ""), f"Public-domain book by {authors or 'unknown'}.",
                         f"https://www.gutenberg.org/ebooks/{d.get('id')}", "probable"))
    return out


def crossref(query: str, n: int = 3) -> List[Item]:
    r = _get("https://api.crossref.org/works", query=query, rows=n, select="DOI,title,author,issued,container-title,abstract,URL")
    if r.status_code != 200:
        return []
    out = []
    for d in r.json().get("message", {}).get("items", []):
        title = (d.get("title") or [""])[0]
        journal = (d.get("container-title") or [""])[0]
        year = ((d.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip() for a in d.get("author", [])[:3])
        summary = _clean_html(d.get("abstract", "")) or f"{journal} ({year}). {authors}"
        out.append(_item("Crossref (journal article)", "academic", title, summary, d.get("URL", ""), "probable"))
    return out


def openalex(query: str, n: int = 3) -> List[Item]:
    r = _get("https://api.openalex.org/works", search=query, **{"per-page": n})
    if r.status_code != 200:
        return []
    out = []
    for d in r.json().get("results", []):
        venue = ((d.get("primary_location") or {}).get("source") or {}).get("display_name", "")
        out.append(_item("OpenAlex (university & journal index)", "academic", d.get("display_name", ""),
                         f"{venue} ({d.get('publication_year', 'n/a')}); cited by {d.get('cited_by_count', 0)}.",
                         d.get("doi") or d.get("id", ""), "probable"))
    return out


def arxiv(query: str, n: int = 3) -> List[Item]:
    r = _get("https://export.arxiv.org/api/query", search_query=f"all:{query}", max_results=n)
    if r.status_code != 200:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    try:
        root = ET.fromstring(r.text)
    except ET.ParseError:
        return []
    for e in root.findall("a:entry", ns):
        out.append(_item("arXiv (preprint)", "academic", (e.findtext("a:title", "", ns) or "").strip(),
                         (e.findtext("a:summary", "", ns) or "").strip(), (e.findtext("a:id", "", ns) or "").strip(), "probable"))
    return out


ADAPTERS: Dict[str, Callable[..., List[Item]]] = {
    "wikipedia": wikipedia, "wikidata": wikidata, "internet_archive": internet_archive,
    "library_of_congress": library_of_congress, "open_library": open_library, "gutenberg": gutenberg,
    "crossref": crossref, "openalex": openalex, "arxiv": arxiv,
}

DEPTHS = {
    "quick": ["wikipedia", "wikidata"],
    "standard": ["wikipedia", "wikidata", "internet_archive", "library_of_congress", "open_library", "crossref", "openalex"],
    "deep": list(ADAPTERS.keys()),
}


class RepositoryService:
    """Unified knowledge retrieval layer."""

    def __init__(self) -> None:
        self.adapters = ADAPTERS

    def aggregate_knowledge(self, query: str, depth: str = "standard", per_source: int = 3,
                            total_timeout: float = 11.0) -> List[Item]:
        query = (query or "").strip()
        if not query:
            return []
        names = DEPTHS.get(depth, DEPTHS["standard"])
        results: List[Item] = []
        pool = ThreadPoolExecutor(max_workers=min(8, len(names)))
        futures = {pool.submit(self.adapters[n], query, per_source): n for n in names if n in self.adapters}
        done, pending = wait(list(futures), timeout=total_timeout)
        for fut in done:
            name = futures[fut]
            try:
                rows = fut.result()
                results.extend(rows)
                HEALTH.ok(f"repo:{name}", f"{len(rows)} hits")
            except Exception as exc:
                HEALTH.flag(f"repo:{name}", f"{exc.__class__.__name__}: {exc}")
        for fut in pending:
            HEALTH.flag(f"repo:{futures[fut]}", "timed out")
            fut.cancel()
        pool.shutdown(wait=False, cancel_futures=True)
        return results

    def build_context(self, query: str, depth: str = "standard", max_chars: int = 6000) -> str:
        blocks = []
        for i, s in enumerate(self.aggregate_knowledge(query, depth), 1):
            blocks.append(f"[{i}] {s['source']} — {s['title']} ({s['url']})\n{truncate(s['summary'], 700)}")
        return truncate("\n\n".join(blocks), max_chars)

    def repository_health(self) -> Dict[str, Any]:
        snap = HEALTH.snapshot()
        return {n: snap.get(f"repo:{n}", {"status": "untested"}).get("status", "untested") for n in self.adapters}
