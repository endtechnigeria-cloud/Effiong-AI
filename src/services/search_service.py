"""
EFFIONG AI - Real-time browsing
===============================
Search chain (first engine that answers wins):
    Tavily  ->  SerpAPI  ->  Brave Search  ->  DuckDuckGo (free, no key)  ->  Wikipedia search
Page reader: fetches a URL the user pasted (or a search hit), strips it to readable text, refuses
private/internal addresses.
"""
from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from src import config
from src.core.guard import UnsafeURL, safe_get
from src.core.health import HEALTH, safe_import
from src.utilities.text_utils import extract_urls, truncate

Result = Dict[str, str]

_LIVE_PATTERNS = [
    r"\b(latest|breaking|current(?:ly)?|right now|today|tonight|yesterday|this (?:week|month|year)|recent(?:ly)?)\b",
    r"\b(news|headline|update|trending|trends|score|scores|results?|fixtures?|standings|weather|forecast for)\b",
    r"\b(price|prices|exchange rate|stock|share price|market cap|inflation|interest rate|petrol|fuel|naira|dollar rate)\b",
    r"\b(who is|who's) (?:the )?(?:current |new |present )?(?:president|prime minister|ceo|governor|minister|king|queen|leader|chairman)\b",
    r"\b(search|browse|look ?up|google|find online|on the internet|on the web|web search)\b",
    r"\b20(2[4-9]|3\d)\b",
    r"\b(election|poll|referendum|coup|protest|summit)\b",
]
_LIVE_RE = re.compile("|".join(_LIVE_PATTERNS), re.IGNORECASE)


def needs_live_data(query: str) -> bool:
    if extract_urls(query or ""):
        return True
    return bool(_LIVE_RE.search(query or ""))


# ------------------------------------------------------------------------------------------
# Engines
# ------------------------------------------------------------------------------------------
def _tavily(query: str, n: int, news: bool) -> List[Result]:
    key = config.get("TAVILY_API_KEY")
    if not key:
        return []
    payload = {"query": query, "max_results": n, "search_depth": "basic", "topic": "news" if news else "general"}
    r = requests.post("https://api.tavily.com/search", json=payload,
                      headers={"Authorization": f"Bearer {key}"}, timeout=20)
    if r.status_code != 200:
        HEALTH.flag("search:tavily", f"HTTP {r.status_code}")
        return []
    return [{"title": i.get("title", ""), "url": i.get("url", ""), "snippet": i.get("content", ""), "engine": "Tavily"}
            for i in r.json().get("results", [])]


def _serpapi(query: str, n: int, news: bool) -> List[Result]:
    key = config.get("SERPAPI_KEY") or config.get("SERPAPI_API_KEY")
    if not key:
        return []
    params = {"q": query, "api_key": key, "num": n}
    if news:
        params["tbm"] = "nws"
    r = requests.get("https://serpapi.com/search.json", params=params, timeout=20)
    if r.status_code != 200:
        HEALTH.flag("search:serpapi", f"HTTP {r.status_code}")
        return []
    data = r.json()
    rows = data.get("organic_results") or data.get("news_results") or []
    return [{"title": i.get("title", ""), "url": i.get("link", ""), "snippet": i.get("snippet", ""), "engine": "SerpAPI"}
            for i in rows[:n]]


def _brave(query: str, n: int, news: bool) -> List[Result]:
    key = config.get("BRAVE_API_KEY")
    if not key:
        return []
    r = requests.get("https://api.search.brave.com/res/v1/web/search", params={"q": query, "count": n},
                     headers={"X-Subscription-Token": key, "Accept": "application/json"}, timeout=20)
    if r.status_code != 200:
        HEALTH.flag("search:brave", f"HTTP {r.status_code}")
        return []
    rows = (r.json().get("web") or {}).get("results", [])
    return [{"title": i.get("title", ""), "url": i.get("url", ""), "snippet": i.get("description", ""), "engine": "Brave"}
            for i in rows[:n]]


def _ddg(query: str, n: int, news: bool) -> List[Result]:
    DDGS = safe_import("ddgs", "search:ddg", "DDGS") or safe_import("duckduckgo_search", "search:ddg", "DDGS")
    if DDGS is None:
        return []
    with DDGS() as ddg:
        rows = list(ddg.news(query, max_results=n)) if news else list(ddg.text(query, max_results=n))
    out = []
    for i in rows:
        out.append({"title": i.get("title", ""), "url": i.get("href") or i.get("url", ""),
                    "snippet": i.get("body") or i.get("excerpt", ""), "engine": "DuckDuckGo"})
    return out


def _wikipedia(query: str, n: int, news: bool) -> List[Result]:
    r = requests.get("https://en.wikipedia.org/w/api.php",
                     params={"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": n},
                     headers={"User-Agent": "EffiongAI/3.0"}, timeout=12)
    if r.status_code != 200:
        return []
    out = []
    for i in r.json().get("query", {}).get("search", []):
        title = i.get("title", "")
        snippet = re.sub(r"<[^>]+>", "", i.get("snippet", ""))
        out.append({"title": title, "url": "https://en.wikipedia.org/wiki/" + title.replace(" ", "_"),
                    "snippet": snippet, "engine": "Wikipedia"})
    return out


ENGINES = [("tavily", _tavily), ("serpapi", _serpapi), ("brave", _brave), ("duckduckgo", _ddg), ("wikipedia", _wikipedia)]


def web_search(query: str, max_results: int = 6, news: Optional[bool] = None) -> List[Result]:
    """Run the chain; never raises."""
    query = (query or "").strip()
    if not query:
        return []
    if news is None:
        news = bool(re.search(r"\b(news|headline|breaking|latest|today)\b", query, re.IGNORECASE))
    for name, fn in ENGINES:
        try:
            rows = [r for r in fn(query, max_results, news) if r.get("url") or r.get("snippet")]
            if rows:
                HEALTH.ok(f"search:{name}", "answered")
                return rows[:max_results]
        except Exception as exc:
            HEALTH.flag(f"search:{name}", f"{exc.__class__.__name__}: {exc}")
    return []


def format_results(results: List[Result], max_chars: int = 5000) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title', '').strip()} — {r.get('url', '')}\n    {truncate(r.get('snippet', '').strip(), 420)}")
    return truncate("\n".join(lines), max_chars)


def get_live_context(query: str, max_results: int = 6) -> Tuple[str, List[Result]]:
    results = web_search(query, max_results)
    if not results:
        return "", []
    engine = results[0].get("engine", "web")
    return f"[Live web results via {engine} — cite the URLs you use]\n{format_results(results)}", results


# ------------------------------------------------------------------------------------------
# Page reader
# ------------------------------------------------------------------------------------------
def fetch_page_text(url: str, max_chars: int = 12000) -> Dict[str, Any]:
    """Return {'url','title','text','content_type'} or {'url','error'}."""
    try:
        resp = safe_get(url, timeout=15, max_bytes=6_000_000)
    except UnsafeURL as exc:
        return {"url": url, "error": f"blocked: {exc}"}
    except Exception as exc:
        return {"url": url, "error": f"{exc.__class__.__name__}: {exc}"}
    if resp.status_code >= 400:
        return {"url": url, "error": f"HTTP {resp.status_code}"}
    ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    raw = resp.content
    title, text = "", ""
    if "pdf" in ctype or url.lower().split("?")[0].endswith(".pdf"):
        pypdf = safe_import("pypdf", "pdf-read")
        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(io.BytesIO(raw))
                text = "\n".join((p.extract_text() or "") for p in reader.pages[:25])
                title = url.rsplit("/", 1)[-1]
            except Exception as exc:
                return {"url": url, "error": f"pdf unreadable: {exc}"}
    elif "html" in ctype or not ctype:
        html_text = raw.decode(resp.encoding or "utf-8", errors="replace")
        bs4 = safe_import("bs4", "html-read")
        if bs4 is not None:
            soup = bs4.BeautifulSoup(html_text, "html.parser")
            for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "form", "svg", "iframe"]):
                tag.decompose()
            title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
            main = soup.find("article") or soup.find("main") or soup.body or soup
            text = main.get_text("\n", strip=True)
        else:
            title_m = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
            title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""
            text = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html_text, flags=re.I)
            text = re.sub(r"<[^>]+>", " ", text)
    else:
        text = raw.decode(resp.encoding or "utf-8", errors="replace") if ctype.startswith("text/") or "json" in ctype else ""
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return {"url": url, "title": title, "text": "", "content_type": ctype, "error": "no readable text"}
    return {"url": url, "title": title, "text": truncate(text, max_chars), "content_type": ctype}


def read_links_in(text: str, max_links: int = 3, max_chars_each: int = 6000) -> str:
    """If the user pasted links, read them so the brain can answer about them."""
    blocks = []
    for url in extract_urls(text, limit=max_links):
        page = fetch_page_text(url, max_chars_each)
        if page.get("text"):
            blocks.append(f"[Page: {page.get('title') or url}]({url})\n{page['text']}")
        else:
            blocks.append(f"[Could not read {url}: {page.get('error', 'unknown')}]")
    return "\n\n".join(blocks)
