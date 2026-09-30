"""
EFFIONG AI - Global Archive Publisher
=====================================
Sends a heritage record (PDF report + machine-readable JSON + evidence files) to the world's open archives at the
same time, each with timestamp, fingerprint and citation metadata, and returns one receipt per service.

    Wayback Machine ..... saves every evidence link (keyless).  Uses SPN2 keys when IA_ACCESS_KEY/IA_SECRET_KEY exist
    Internet Archive .... uploads the record as a permanent item      (IA_ACCESS_KEY + IA_SECRET_KEY)
    Zenodo .............. deposition with DOI on publish              (ZENODO_TOKEN)
    OSF ................. project + files                             (OSF_TOKEN)
    Figshare ............ article + files                             (FIGSHARE_TOKEN)
    Wikimedia Commons ... file page for the report PDF               (WIKIMEDIA_BOT_USER + WIKIMEDIA_BOT_PASSWORD)
    Wikidata ............ item describing the record                  (same bot credentials)

ARCHIVE_PUBLISH_MODE (secret, default "draft")
    off   - nothing leaves the app
    draft - SAFE TEST MODE: Zenodo *sandbox* / unpublished draft, OSF private project, Figshare private draft, the
            Wikimedia test wikis; Wayback saves only public links; Internet Archive is skipped (it has no draft state)
    live  - real, permanent, public records (Zenodo DOI is minted and cannot be deleted)

Wikimedia Commons and Wikidata have licensing / notability rules; automatic submission there also needs
WIKI_AUTO_SUBMIT=true, otherwise an upload-ready kit is prepared instead.
Services without credentials return status "skipped" with the exact secret name to add - they never raise.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from src import config
from src.core.health import HEALTH
from src.database.heritage_store import HeritageStore
from src.utilities import doc_engine

UA = {"User-Agent": "EffiongAI/3.0 (heritage archiving; contact project owner)"}
Receipt = Dict[str, Any]
Evidence = List[Tuple[str, bytes, str]]  # (filename, bytes, mime)


def _receipt(service: str, status: str, detail: str = "", url: str = "", ident: str = "") -> Receipt:
    return {"service": service, "status": status, "detail": detail[:300], "url": url, "id": ident,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def publish_mode() -> str:
    mode = config.get("ARCHIVE_PUBLISH_MODE", "draft").lower()
    return mode if mode in ("off", "draft", "live") else "draft"


def _slug(node: Dict[str, Any]) -> str:
    return re.sub(r"[^a-z0-9]+", "-", node["id"].lower()).strip("-")


def _description(node: Dict[str, Any]) -> str:
    return (f"{node['description']}\n\nClassification: {node.get('truth_classification')} (status: {node['status']}). "
            f"Logged {node['created_at']} UTC on Effiong AI. SHA-256: {node.get('record_sha256')}.")


class ArchivePublisher:
    def __init__(self) -> None:
        self.adapters: List[Tuple[str, Callable[..., Receipt]]] = [
            ("Wayback Machine", self._wayback), ("Internet Archive", self._internet_archive), ("Zenodo", self._zenodo),
            ("OSF", self._osf), ("Figshare", self._figshare), ("Wikimedia Commons", self._commons), ("Wikidata", self._wikidata),
        ]

    # ------------------------------------------------------------------ main
    def publish(self, node: Dict[str, Any], evidence: Optional[Evidence] = None, timeout: float = 90.0) -> List[Receipt]:
        mode = publish_mode()
        if mode == "off":
            return [_receipt(name, "skipped", "ARCHIVE_PUBLISH_MODE is off") for name, _ in self.adapters]
        pdf = doc_engine.compile_pdf_bytes(HeritageStore.record_markdown(node), doc_type="African Heritage Record")
        js = HeritageStore.record_json(node).encode("utf-8")
        bundle = {"pdf": pdf, "json": js, "evidence": evidence or []}
        pool = ThreadPoolExecutor(max_workers=len(self.adapters))
        futs = {pool.submit(self._safe, name, fn, node, bundle, mode): name for name, fn in self.adapters}
        done, pending = wait(list(futs), timeout=timeout)
        receipts: List[Receipt] = []
        order = [n for n, _ in self.adapters]
        by_name: Dict[str, Receipt] = {futs[f]: f.result() for f in done}
        for f in pending:
            by_name[futs[f]] = _receipt(futs[f], "error", "timed out - retry later")
        pool.shutdown(wait=False, cancel_futures=True)
        for name in order:
            receipts.append(by_name[name])
        return receipts

    @staticmethod
    def _safe(name: str, fn: Callable[..., Receipt], node: Dict[str, Any], bundle: Dict[str, Any], mode: str) -> Receipt:
        try:
            r = fn(node, bundle, mode)
            HEALTH.ok(f"archive:{name}", r["status"])
            return r
        except requests.RequestException as exc:
            HEALTH.flag(f"archive:{name}", f"network: {exc.__class__.__name__}")
            return _receipt(name, "error", f"network error: {exc.__class__.__name__}")
        except Exception as exc:
            HEALTH.flag(f"archive:{name}", f"{exc.__class__.__name__}: {exc}")
            return _receipt(name, "error", f"{exc.__class__.__name__}: {exc}")

    # ------------------------------------------------------------------ Wayback
    def _wayback(self, node: Dict[str, Any], bundle: Dict[str, Any], mode: str) -> Receipt:
        urls = [s["url"] for s in node.get("evidence_sources", []) if s.get("url", "").startswith("http")]
        if node.get("evidence_url", "").startswith("http"):
            urls.insert(0, node["evidence_url"])
        urls = list(dict.fromkeys(urls))[:6]
        if not urls:
            return _receipt("Wayback Machine", "skipped", "no evidence links to preserve")
        ia_a, ia_s = config.get("IA_ACCESS_KEY"), config.get("IA_SECRET_KEY")
        saved = []
        for u in urls:
            try:
                if ia_a and ia_s:
                    r = requests.post("https://web.archive.org/save", headers={**UA, "Accept": "application/json",
                                      "Authorization": f"LOW {ia_a}:{ia_s}"}, data={"url": u, "capture_all": "1"}, timeout=40)
                    ok = r.status_code in (200, 202)
                else:
                    r = requests.get("https://web.archive.org/save/" + u, headers=UA, timeout=45, allow_redirects=True)
                    ok = r.status_code == 200
                if ok:
                    saved.append(u)
            except requests.RequestException:
                continue
        if saved:
            return _receipt("Wayback Machine", "published", f"{len(saved)}/{len(urls)} evidence link(s) saved",
                            url="https://web.archive.org/web/*/" + saved[0])
        return _receipt("Wayback Machine", "error", "Wayback Machine did not accept the links right now (rate limit) - retry later")

    # ------------------------------------------------------------------ Internet Archive
    def _internet_archive(self, node: Dict[str, Any], bundle: Dict[str, Any], mode: str) -> Receipt:
        a, s = config.get("IA_ACCESS_KEY"), config.get("IA_SECRET_KEY")
        if not (a and s):
            return _receipt("Internet Archive", "skipped", "add IA_ACCESS_KEY and IA_SECRET_KEY (free at archive.org/account/s3.php)")
        if mode != "live":
            return _receipt("Internet Archive", "skipped", "Internet Archive items are public immediately - upload happens only in ARCHIVE_PUBLISH_MODE=live")
        import internetarchive as ia

        ident = f"effiong-heritage-{_slug(node)}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        files: Dict[str, Any] = {f"{_slug(node)}.pdf": io.BytesIO(bundle["pdf"]), f"{_slug(node)}.json": io.BytesIO(bundle["json"])}
        for name, data, _ in bundle["evidence"][:5]:
            files[re.sub(r"[^\w.\-]+", "_", name)] = io.BytesIO(data)
        meta = {"title": f"{node['title']} (Effiong AI heritage record {node['id']})", "description": _description(node),
                "creator": node.get("contributor", "Effiong AI"), "mediatype": "texts", "collection": "opensource",
                "subject": ["African heritage", "oral history", node.get("truth_classification", "")], "date": node["created_at"][:10]}
        res = ia.upload(ident, files=files, metadata=meta, access_key=a, secret_key=s, retries=3, retries_sleep=5)
        ok = all(getattr(r, "status_code", 200) == 200 for r in res)
        return _receipt("Internet Archive", "published" if ok else "error", "uploaded" if ok else "upload incomplete",
                        url=f"https://archive.org/details/{ident}", ident=ident)

    # ------------------------------------------------------------------ Zenodo
    def _zenodo(self, node: Dict[str, Any], bundle: Dict[str, Any], mode: str) -> Receipt:
        tok = config.get("ZENODO_TOKEN")
        if not tok:
            return _receipt("Zenodo", "skipped", "add ZENODO_TOKEN (free at zenodo.org/account/settings/applications)")
        sandbox = mode != "live" or config.get_bool("ZENODO_SANDBOX", False)
        base = "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
        hdr = {"Authorization": f"Bearer {tok}"}
        dep = requests.post(f"{base}/deposit/depositions", headers=hdr, json={}, timeout=40)
        if dep.status_code not in (200, 201):
            return _receipt("Zenodo", "error", f"HTTP {dep.status_code}: {dep.text[:120]}")
        d = dep.json()
        bucket, dep_id = d["links"]["bucket"], d["id"]
        for fname, data in [(f"{_slug(node)}.pdf", bundle["pdf"]), (f"{_slug(node)}.json", bundle["json"])] + \
                           [(re.sub(r"[^\w.\-]+", "_", n), b) for n, b, _ in bundle["evidence"][:5]]:
            up = requests.put(f"{bucket}/{fname}", data=data, headers=hdr, timeout=120)
            if up.status_code not in (200, 201):
                return _receipt("Zenodo", "error", f"file upload HTTP {up.status_code}")
        meta = {"metadata": {"title": f"{node['title']} — Effiong AI heritage record {node['id']}", "upload_type": "publication",
                             "publication_type": "other", "description": _description(node).replace("\n", "<br>"),
                             "creators": [{"name": node.get("contributor") or "Effiong AI Contributor"}],
                             "keywords": ["African heritage", "oral history", node.get("node_type", ""), "Effiong AI"],
                             "access_right": "open", "license": "cc-by-4.0", "publication_date": node["created_at"][:10]}}
        m = requests.put(f"{base}/deposit/depositions/{dep_id}", headers=hdr, json=meta, timeout=40)
        if m.status_code != 200:
            return _receipt("Zenodo", "error", f"metadata HTTP {m.status_code}: {m.text[:120]}")
        host = "https://sandbox.zenodo.org" if sandbox else "https://zenodo.org"
        if mode == "live":
            pub = requests.post(f"{base}/deposit/depositions/{dep_id}/actions/publish", headers=hdr, timeout=60)
            if pub.status_code in (200, 201, 202):
                j = pub.json()
                return _receipt("Zenodo", "published", f"DOI {j.get('doi', '')}", url=j.get("links", {}).get("record_html") or f"{host}/records/{dep_id}", ident=str(j.get("doi", dep_id)))
            return _receipt("Zenodo", "error", f"publish HTTP {pub.status_code}: {pub.text[:120]}")
        return _receipt("Zenodo", "draft", "saved as unpublished draft on the Zenodo SANDBOX (test mode)", url=f"{host}/deposit/{dep_id}", ident=str(dep_id))

    # ------------------------------------------------------------------ OSF
    def _osf(self, node: Dict[str, Any], bundle: Dict[str, Any], mode: str) -> Receipt:
        tok = config.get("OSF_TOKEN")
        if not tok:
            return _receipt("OSF", "skipped", "add OSF_TOKEN (free at osf.io/settings/tokens)")
        hdr = {"Authorization": f"Bearer {tok}", "Content-Type": "application/vnd.api+json"}
        body = {"data": {"type": "nodes", "attributes": {"title": f"{node['title']} — {node['id']}", "category": "project",
                                                          "description": _description(node)[:900], "public": mode == "live"}}}
        r = requests.post("https://api.osf.io/v2/nodes/", headers=hdr, json=body, timeout=40)
        if r.status_code not in (200, 201):
            return _receipt("OSF", "error", f"HTTP {r.status_code}: {r.text[:120]}")
        nid = r.json()["data"]["id"]
        for fname, data in [(f"{_slug(node)}.pdf", bundle["pdf"]), (f"{_slug(node)}.json", bundle["json"])]:
            up = requests.put(f"https://files.osf.io/v1/resources/{nid}/providers/osfstorage/", params={"kind": "file", "name": fname},
                              headers={"Authorization": f"Bearer {tok}"}, data=data, timeout=90)
            if up.status_code not in (200, 201):
                return _receipt("OSF", "error", f"file upload HTTP {up.status_code}")
        return _receipt("OSF", "published" if mode == "live" else "draft", "project created" + ("" if mode == "live" else " (private)"),
                        url=f"https://osf.io/{nid}/", ident=nid)

    # ------------------------------------------------------------------ Figshare
    def _figshare(self, node: Dict[str, Any], bundle: Dict[str, Any], mode: str) -> Receipt:
        tok = config.get("FIGSHARE_TOKEN")
        if not tok:
            return _receipt("Figshare", "skipped", "add FIGSHARE_TOKEN (free at figshare.com/account/applications)")
        api = "https://api.figshare.com/v2"
        hdr = {"Authorization": f"token {tok}"}
        art = requests.post(f"{api}/account/articles", headers=hdr, timeout=40, json={
            "title": f"{node['title']} — Effiong AI heritage record {node['id']}", "description": _description(node),
            "tags": ["African heritage", "oral history", "Effiong AI"], "defined_type": "journal contribution"})
        if art.status_code not in (200, 201):
            return _receipt("Figshare", "error", f"HTTP {art.status_code}: {art.text[:120]}")
        art_id = requests.get(art.json()["location"], headers=hdr, timeout=30).json()["id"]
        for fname, data in [(f"{_slug(node)}.pdf", bundle["pdf"])]:
            init = requests.post(f"{api}/account/articles/{art_id}/files", headers=hdr, timeout=40,
                                 json={"name": fname, "md5": hashlib.md5(data).hexdigest(), "size": len(data)})
            file_info = requests.get(init.json()["location"], headers=hdr, timeout=30).json()
            parts = requests.get(file_info["upload_url"], headers=hdr, timeout=30).json().get("parts", [])
            for p in parts:
                chunk = data[p["startOffset"]: p["endOffset"] + 1]
                requests.put(f"{file_info['upload_url']}/{p['partNo']}", data=chunk, headers=hdr, timeout=90)
            requests.post(f"{api}/account/articles/{art_id}/files/{file_info['id']}", headers=hdr, timeout=30)
        if mode == "live":
            pub = requests.post(f"{api}/account/articles/{art_id}/publish", headers=hdr, timeout=40)
            if pub.status_code in (200, 201):
                return _receipt("Figshare", "published", "published", url=f"https://figshare.com/articles/{art_id}", ident=str(art_id))
            return _receipt("Figshare", "error", f"publish HTTP {pub.status_code}")
        return _receipt("Figshare", "draft", "private draft article created", url=f"https://figshare.com/account/articles/{art_id}", ident=str(art_id))

    # ------------------------------------------------------------------ MediaWiki helpers
    def _mw_login(self, api: str) -> Optional[requests.Session]:
        user, pw = config.get("WIKIMEDIA_BOT_USER"), config.get("WIKIMEDIA_BOT_PASSWORD")
        if not (user and pw):
            return None
        s = requests.Session()
        s.headers.update(UA)
        t = s.get(api, params={"action": "query", "meta": "tokens", "type": "login", "format": "json"}, timeout=25).json()
        token = t["query"]["tokens"]["logintoken"]
        r = s.post(api, data={"action": "login", "lgname": user, "lgpassword": pw, "lgtoken": token, "format": "json"}, timeout=25).json()
        if r.get("login", {}).get("result") != "Success":
            raise RuntimeError(f"login failed: {r.get('login', {}).get('reason', 'unknown')}")
        return s

    def _mw_csrf(self, s: requests.Session, api: str) -> str:
        return s.get(api, params={"action": "query", "meta": "tokens", "format": "json"}, timeout=25).json()["query"]["tokens"]["csrftoken"]

    def _commons(self, node: Dict[str, Any], bundle: Dict[str, Any], mode: str) -> Receipt:
        fname = f"Effiong_AI_Heritage_Record_{node['id']}.pdf"
        wikitext = (f"== {{{{int:filedesc}}}} ==\n{{{{Information\n|description={{{{en|1={node['title']} — heritage record {node['id']} (status: {node['status']})}}}}\n"
                    f"|date={node['created_at'][:10]}\n|source=Effiong AI heritage ledger\n|author={node.get('contributor', 'Effiong AI')}\n"
                    f"|permission=CC BY 4.0 granted by the contributor\n}}}}\n\n== {{{{int:license-header}}}} ==\n{{{{cc-by-4.0}}}}\n\n[[Category:African heritage]]")
        if not config.get_bool("WIKI_AUTO_SUBMIT", False):
            return _receipt("Wikimedia Commons", "queued",
                            f"upload kit prepared for '{fname}' - Commons needs a human to confirm the licence (set WIKIMEDIA_BOT_USER/PASSWORD and WIKI_AUTO_SUBMIT=true to automate)")
        api = "https://commons.wikimedia.org/w/api.php" if mode == "live" else "https://test-commons.wikimedia.org/w/api.php"
        s = self._mw_login(api)
        if s is None:
            return _receipt("Wikimedia Commons", "skipped", "add WIKIMEDIA_BOT_USER and WIKIMEDIA_BOT_PASSWORD (Special:BotPasswords)")
        r = s.post(api, data={"action": "upload", "filename": fname, "comment": "Heritage record via Effiong AI", "text": wikitext,
                              "token": self._mw_csrf(s, api), "format": "json"}, files={"file": (fname, bundle["pdf"], "application/pdf")}, timeout=90).json()
        if r.get("upload", {}).get("result") == "Success":
            host = "commons.wikimedia.org" if mode == "live" else "test-commons.wikimedia.org"
            return _receipt("Wikimedia Commons", "published" if mode == "live" else "draft", "uploaded", url=f"https://{host}/wiki/File:{fname}", ident=fname)
        return _receipt("Wikimedia Commons", "error", json.dumps(r)[:200])

    def _wikidata(self, node: Dict[str, Any], bundle: Dict[str, Any], mode: str) -> Receipt:
        if not config.get_bool("WIKI_AUTO_SUBMIT", False):
            return _receipt("Wikidata", "queued", "item statements prepared - Wikidata has notability rules, so a human editor should review (set WIKI_AUTO_SUBMIT=true with bot credentials to automate)")
        api = "https://www.wikidata.org/w/api.php" if mode == "live" else "https://test.wikidata.org/w/api.php"
        s = self._mw_login(api)
        if s is None:
            return _receipt("Wikidata", "skipped", "add WIKIMEDIA_BOT_USER and WIKIMEDIA_BOT_PASSWORD (Special:BotPasswords)")
        data = {"labels": {"en": {"language": "en", "value": node["title"][:250]}},
                "descriptions": {"en": {"language": "en", "value": f"African heritage record {node['id']} ({node['status']})"}}}
        r = s.post(api, data={"action": "wbeditentity", "new": "item", "data": json.dumps(data), "token": self._mw_csrf(s, api), "format": "json",
                              "summary": "Heritage record via Effiong AI"}, timeout=60).json()
        if r.get("success"):
            qid = r["entity"]["id"]
            host = "www.wikidata.org" if mode == "live" else "test.wikidata.org"
            return _receipt("Wikidata", "published" if mode == "live" else "draft", "item created", url=f"https://{host}/wiki/{qid}", ident=qid)
        return _receipt("Wikidata", "error", json.dumps(r)[:200])


archive_publisher = ArchivePublisher()
