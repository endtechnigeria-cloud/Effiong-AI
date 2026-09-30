"""
EFFIONG AI - Document Service (Sovereign Knowledge Document Channel)
====================================================================
Decides WHAT document the user wants, has the multi-brain write it (default writer: Claude when a key exists,
otherwise Gemini and the free tiers), then compiles native PDF / Word / PowerPoint files.

Covers: academic documents, theses, research papers, dissertations, government & official records, legal
documents, certificates, licences, patents, trademarks, proposals, business & corporate documents, business plans,
company profiles, personal documents, memoirs, CVs / resumes, cover letters, letters, memos, reports, presentations.

Not covered on purpose: .cdr (CorelDRAW's closed format) cannot be written by open tools - Effiong AI produces
SVG vector graphics instead, which CorelDRAW opens directly.
"""
from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.guard import ExecutionBudget
from src.core.health import HEALTH
from src.services.llm_providers import BRAIN, AllProvidersFailed, LLMResponse
from src.utilities import doc_engine
from src.utilities.text_utils import extract_json, truncate

DOC_TYPES: Dict[str, Dict[str, Any]] = {
    "cover_letter": {"label": "Cover Letter", "kw": ["cover letter", "application letter", "motivation letter"],
                     "guide": "One page. Sender block, date, recipient, subject line, 3-4 tight paragraphs (hook, evidence of fit with quantified achievements, motivation, close), formal sign-off. Use [placeholders] for unknown personal details."},
    "resume": {"label": "Resume / CV", "kw": ["resume", "résumé", "curriculum vitae", " cv ", "my cv", "a cv", "write cv", "create cv", "make cv", "make a cv"],
               "guide": "Header with contact placeholders, professional summary, skills table, experience (reverse chronological, action verbs, measurable results), education, certifications, languages, referees. ATS-friendly; no fabricated employers - use [placeholders]."},
    "proposal": {"label": "Proposal", "kw": ["proposal", "tender", "bid document", "grant application", "funding request"],
                 "guide": "Executive summary, problem/need, objectives, scope of work, methodology, timeline table, budget table with line items, team, risk table (High/Medium/Low), expected outcomes, terms, conclusion."},
    "business_plan": {"label": "Business Plan", "kw": ["business plan", "startup plan", "lean canvas", "go-to-market"], "long": True,
                      "guide": "Executive summary, company description, market analysis, competition table, products/services, marketing & sales, operations, management, financial projections (tables), funding request, risks, milestones."},
    "company_profile": {"label": "Company Profile", "kw": ["company profile", "corporate profile", "business profile", "capability statement"],
                        "guide": "Overview, vision/mission/values, services table, track record, team, clients/partners placeholders, certifications, contact block."},
    "thesis": {"label": "Thesis / Dissertation", "kw": ["thesis", "dissertation", "research project", "capstone"], "long": True,
               "guide": "Title page block, abstract, table of contents list, introduction (background, problem, objectives, questions, significance, scope), literature review, methodology, results/analysis, discussion, conclusion & recommendations, references (ONLY from supplied sources), appendices."},
    "research_paper": {"label": "Research Paper", "kw": ["research paper", "academic paper", "journal article", "scientific paper", "term paper", "essay", "literature review", "case study"], "long": True,
                       "guide": "Abstract, keywords, introduction, related work, method, findings (with tables), discussion, limitations, conclusion, references (ONLY from supplied sources)."},
    "legal": {"label": "Legal Document", "kw": ["agreement", "contract", "memorandum of understanding", "mou", "nda", "non-disclosure", "affidavit", "power of attorney", "lease", "tenancy", "deed", "terms and conditions", "privacy policy", "legal notice", "will and testament", "letter of intent"],
              "guide": "Formal legal structure: title, parties, recitals, definitions, numbered operative clauses, term & termination, liability, governing law/jurisdiction (use [placeholder] if unknown), dispute resolution, signature blocks with witness lines. Add a short note that this is a draft template, not legal advice."},
    "certificate": {"label": "Certificate", "kw": ["certificate", "certification of", "award of", "diploma"], "guide": "Short formal certificate text."},
    "licence": {"label": "Licence / Permit", "kw": ["licence", "license", "permit", "authorization letter", "authorisation"],
                "guide": "Issuer, licensee, scope, conditions, validity period, revocation terms, serial [placeholder], signature block."},
    "patent": {"label": "Patent Application Draft", "kw": ["patent"],
               "guide": "Title, abstract, technical field, background, summary, brief description of drawings, detailed description, numbered claims (independent then dependent). Add note: must be reviewed by a registered patent attorney."},
    "trademark": {"label": "Trademark Application Draft", "kw": ["trademark", "trade mark", "brand registration"],
                  "guide": "Mark description, owner details, classes of goods/services (Nice classification), specimen description, statement of use, priority claims. Note: confirm with the national registry."},
    "memoir": {"label": "Memoir / Personal Story", "kw": ["memoir", "autobiography", "life story", "personal story", "biography"], "long": True,
               "guide": "Warm first-person narrative with chapters, sensory detail, dialogue, reflection; preserve cultural context and names given by the user."},
    "government": {"label": "Official Record", "kw": ["official record", "government record", "birth record", "civil record", "gazette", "press release", "policy brief", "white paper", "official report"],
                   "guide": "Formal official-record layout: reference number placeholder, issuing authority, subject, body in numbered paragraphs, certification block, date and seal placeholder."},
    "memo": {"label": "Memo", "kw": ["memo", "memorandum", "internal note"], "guide": "TO / FROM / DATE / SUBJECT header table, purpose, key points, action items table with owners and deadlines."},
    "letter": {"label": "Letter", "kw": ["letter", "recommendation", "reference letter", "resignation", "complaint letter", "invitation letter", "appointment letter", "offer letter", "demand letter"],
               "guide": "Formal letter: sender block, date, recipient, salutation, subject, body, close, signature."},
    "presentation": {"label": "Presentation", "kw": ["presentation", "slides", "slide deck", "powerpoint", "pptx", "pitch deck", "deck"], "formats": ["pptx", "pdf"],
                     "guide": "DECK FORMAT: '# Deck title', then one subtitle paragraph, then '## Slide title' per slide with 3-5 bullets (max 14 words each), optional table, and a 'Notes:' paragraph with speaker notes. 8-14 slides: title, agenda, content slides, summary, next steps."},
    "report": {"label": "Report", "kw": ["report", "briefing", "brief", "analysis document", "whitepaper", "minutes of meeting", "minutes"], "long": False,
               "guide": "Executive summary, background, findings with tables (colour-codable status words such as Verified / Pending / High / Low), analysis, recommendations, conclusion."},
    "document": {"label": "Document", "kw": [], "guide": "Clear professional structure with headings, short paragraphs and tables where useful."},
}

_FORMAT_WORDS = {
    "pdf": ["pdf"], "docx": ["docx", "word", ".doc", "ms word", "microsoft word"], "pptx": ["pptx", "powerpoint", "power point", "slides", "slide deck", "presentation", "deck"],
}
_LONG_HINT = re.compile(r"\b(detailed|comprehensive|full|complete|long|in[- ]depth|extensive|chapter|chapters|thesis|dissertation)\b", re.I)


def detect_doc_type(text: str) -> str:
    t = f" {text.lower()} "
    order = ["certificate", "cover_letter", "resume", "presentation", "patent", "trademark", "business_plan", "thesis",
             "research_paper", "company_profile", "proposal", "licence", "legal", "memoir", "government", "memo",
             "letter", "report"]
    for key in order:
        if any(k in t for k in DOC_TYPES[key]["kw"]):
            return key
    return "document"


def detect_formats(text: str, doc_type: str) -> List[str]:
    t = text.lower()
    wanted = [f for f, words in _FORMAT_WORDS.items() if any(w in t for w in words)]
    if doc_type == "presentation":
        return ["pptx", "pdf"] + (["docx"] if "docx" in wanted or "word" in t else [])
    if not wanted:
        return ["pdf", "docx"]
    # always keep a PDF alongside unless they explicitly want only Word/PowerPoint
    return wanted if len(wanted) > 1 or wanted == ["pdf"] else wanted + ["pdf"]


@dataclass
class DocResult:
    title: str
    markdown: str
    doc_type: str
    label: str
    formats: List[str]
    images: Dict[str, bytes] = field(default_factory=dict)
    certificate: Optional[Dict[str, str]] = None
    provider: str = ""
    warnings: List[str] = field(default_factory=list)

    def spec(self) -> Dict[str, Any]:
        """JSON-safe form stored in chat history (files are rebuilt on demand)."""
        import base64

        return {"title": self.title, "markdown": self.markdown, "doc_type": self.doc_type, "label": self.label,
                "formats": self.formats, "certificate": self.certificate, "provider": self.provider,
                "images": {k: base64.b64encode(v).decode("ascii") for k, v in self.images.items()}}


_CHART_BLOCK = re.compile(r"```chart\s*([\s\S]*?)```", re.IGNORECASE)


def extract_charts(markdown: str) -> Tuple[str, Dict[str, bytes]]:
    """Replace ```chart {json}``` blocks with rendered PNG images referenced as ![caption](chart_n)."""
    images: Dict[str, bytes] = {}

    def repl(m: re.Match) -> str:
        spec = extract_json(m.group(1))
        if not isinstance(spec, dict):
            return ""
        try:
            name = f"chart_{len(images) + 1}"
            images[name] = doc_engine.render_chart(spec, theme="light")
            return f"![{spec.get('title', 'Chart')}]({name})"
        except Exception as exc:
            HEALTH.flag("charts", f"{exc.__class__.__name__}: {exc}")
            return ""

    return _CHART_BLOCK.sub(repl, markdown), images


class DocumentService:
    def __init__(self) -> None:
        self.output_dir = "generated_documents"

    # ------------------------------------------------------------------ authoring
    def _system(self, doc_type: str, allow_charts: bool = True) -> str:
        info = DOC_TYPES[doc_type]
        rules = [
            "You are the Effiong AI Document Channel: you write finished, professional, ready-to-use documents.",
            f"Document type: {info['label']}. Structure: {info['guide']}",
            "Output ONLY the document in Markdown - no preface, no closing remarks, no code fences around it.",
            "Start with a single '# Title' line. Use '##' for sections and '###' for sub-sections.",
            "Use pipe tables where data is tabular; use status words such as Verified / Pending / High / Medium / Low in status columns.",
            "NEVER invent real people, registration or licence numbers, statistics, quotations or references. Where a fact is unknown use a clear [Placeholder]. Cite only sources supplied in the context.",
            "Write full, substantive content of the length and depth the request implies - do not summarise or write meta-comments about the document.",
        ]
        if allow_charts:
            rules.append("If a chart would help, include a fenced block ```chart {\"type\":\"bar|line|pie|area\",\"title\":\"...\",\"labels\":[...],\"series\":[{\"name\":\"...\",\"values\":[...]}]} ``` using ONLY numbers supplied by the user or context.")
        return "\n".join(rules)

    def write(self, request: str, doc_type: Optional[str] = None, context: str = "", history_text: str = "",
              budget: Optional[ExecutionBudget] = None, on_status: Optional[Callable[[str], None]] = None,
              user: Optional[Dict[str, Any]] = None) -> DocResult:
        doc_type = doc_type or detect_doc_type(request)
        info = DOC_TYPES[doc_type]
        formats = detect_formats(request, doc_type)
        if doc_type == "certificate":
            return self._certificate(request, formats, budget, user)

        user_note = ""
        if user and user.get("name"):
            user_note = f"\nThe requester's name is {user['name']}; use it only where a personal document needs the author's name."
        prompt = f"REQUEST:\n{request}\n{user_note}"
        if history_text:
            prompt += f"\n\nCONVERSATION CONTEXT (for details the user already gave):\n{truncate(history_text, 3000)}"
        if context:
            prompt += f"\n\nSUPPLIED SOURCES / FILE CONTENT (the only facts you may cite):\n{truncate(context, 12000)}"

        long_form = bool(info.get("long")) and bool(_LONG_HINT.search(request) or doc_type in ("thesis", "business_plan"))
        provider = ""
        try:
            if long_form:
                if on_status:
                    on_status("📚 Planning chapters, then writing them in parallel...")
                markdown, provider = self._write_long(prompt, doc_type, budget, on_status)
            else:
                if on_status:
                    on_status("✍️ Drafting the document...")
                resp = BRAIN.generate([{"role": "user", "content": prompt}], system=self._system(doc_type), task="docs",
                                      max_tokens=8192, temperature=0.5, timeout=70, budget=budget)
                markdown, provider = resp.text, f"{resp.provider}/{resp.model}"
        except AllProvidersFailed as exc:
            markdown = self._offline_template(request, doc_type)
            provider = "offline template"
            HEALTH.flag("documents", f"all writers failed: {exc}")
        markdown = self._strip_fences(markdown)
        markdown, images = extract_charts(markdown)
        title, _ = doc_engine.extract_title(doc_engine.parse_markdown(markdown), info["label"])
        res = DocResult(title=title, markdown=markdown, doc_type=doc_type, label=info["label"], formats=formats,
                        images=images, provider=provider)
        if provider == "offline template":
            res.warnings.append("All AI writers were unavailable, so a fill-in template was produced instead.")
        return res

    def _write_long(self, prompt: str, doc_type: str, budget: Optional[ExecutionBudget],
                    on_status: Optional[Callable[[str], None]]) -> Tuple[str, str]:
        outline_resp = BRAIN.generate(
            [{"role": "user", "content": prompt + "\n\nReturn ONLY JSON: {\"title\": str, \"subtitle\": str, \"sections\": [{\"heading\": str, \"brief\": str}]} with 6-8 sections in logical order."}],
            system=self._system(doc_type, False), task="docs", json_mode=True, max_tokens=1500, temperature=0.3, timeout=40, budget=budget)
        plan = extract_json(outline_resp.text) or {}
        sections = [s for s in (plan.get("sections") or []) if isinstance(s, dict) and s.get("heading")][:8]
        title = plan.get("title") or "Document"
        if len(sections) < 2:
            resp = BRAIN.generate([{"role": "user", "content": prompt}], system=self._system(doc_type), task="docs", max_tokens=8192,
                                  temperature=0.5, timeout=70, budget=budget)
            return resp.text, f"{resp.provider}/{resp.model}"
        groups = [sections[i:i + 2] for i in range(0, len(sections), 2)]
        outline_text = "\n".join(f"{i + 1}. {s['heading']} - {s.get('brief', '')}" for i, s in enumerate(sections))

        def write_group(group: List[Dict[str, str]]) -> Tuple[str, str]:
            names = "; ".join(g["heading"] for g in group)
            gp = (f"{prompt}\n\nFULL OUTLINE:\n{outline_text}\n\nWrite ONLY these sections now, in depth (each 500-900 words, "
                  f"with '## ' headings exactly as named): {names}\nDo not write a title line or other sections.")
            r = BRAIN.generate([{"role": "user", "content": gp}], system=self._system(doc_type, False), task="docs",
                               max_tokens=6000, temperature=0.5, timeout=70, budget=None)
            return r.text, f"{r.provider}/{r.model}"

        with ThreadPoolExecutor(max_workers=min(4, len(groups))) as pool:
            results = list(pool.map(lambda g: self._safe_group(write_group, g), groups))
        parts = [f"# {title}"]
        if plan.get("subtitle"):
            parts.append(str(plan["subtitle"]))
        prov = ""
        for text, p in results:
            parts.append(self._strip_fences(text).strip())
            prov = prov or p
        return "\n\n".join(parts), prov or "multi-brain"

    @staticmethod
    def _safe_group(fn: Callable, group: List[Dict[str, str]]) -> Tuple[str, str]:
        try:
            return fn(group)
        except Exception as exc:
            HEALTH.flag("documents", f"section group failed: {exc.__class__.__name__}")
            return "\n\n".join(f"## {g['heading']}\n[Section could not be generated - please retry.]" for g in group), ""

    @staticmethod
    def _strip_fences(text: str) -> str:
        t = text.strip()
        t = re.sub(r"^```(?:markdown|md)?\s*\n", "", t)
        t = re.sub(r"\n```\s*$", "", t)
        return t.strip()

    def _certificate(self, request: str, formats: List[str], budget: Optional[ExecutionBudget],
                     user: Optional[Dict[str, Any]]) -> DocResult:
        cert = {"title": "Certificate of Achievement", "recipient": (user or {}).get("name") or "[Recipient Name]",
                "body": "has successfully met the requirements set out for this recognition.", "issuer": "Effiong AI", "serial": ""}
        provider = "template"
        try:
            resp = BRAIN.generate(
                [{"role": "user", "content": f"Request: {request}\nReturn ONLY JSON with keys title, recipient, body (2-3 sentences), issuer, serial. Use [Placeholder] for unknown names."}],
                system="You draft the wording for formal certificates. Never invent official registration numbers.", task="docs",
                json_mode=True, max_tokens=600, temperature=0.4, timeout=30, budget=budget)
            data = extract_json(resp.text)
            if isinstance(data, dict):
                cert.update({k: str(v) for k, v in data.items() if k in cert and v})
                provider = f"{resp.provider}/{resp.model}"
        except Exception as exc:
            HEALTH.flag("documents", f"certificate wording fallback: {exc.__class__.__name__}")
        md = f"# {cert['title']}\n\nThis is to certify that **{cert['recipient']}** {cert['body']}\n\nIssued by {cert['issuer']}."
        return DocResult(title=cert["title"], markdown=md, doc_type="certificate", label="Certificate", formats=["pdf", "docx"],
                         certificate=cert, provider=provider)

    @staticmethod
    def _offline_template(request: str, doc_type: str) -> str:
        label = DOC_TYPES[doc_type]["label"]
        guide = DOC_TYPES[doc_type]["guide"]
        lines = [f"# {label} - Draft Template", "", f"Request: {truncate(request, 300)}", "",
                 "## Notice", "The AI writing tiers are temporarily unavailable, so this is a fill-in structure. Re-send the request in a minute for a full draft.",
                 "", "## Suggested structure"]
        lines += [f"- {part.strip()}" for part in re.split(r"[,.;]\s*", guide) if part.strip()][:12]
        return "\n".join(lines)

    # ------------------------------------------------------------------ compiling
    def build_file(self, spec: Dict[str, Any], fmt: str) -> Tuple[bytes, str, str]:
        """Return (bytes, filename, mime) for pdf | docx | pptx from a stored/fresh doc spec."""
        import base64

        images = {k: base64.b64decode(v) if isinstance(v, str) else v for k, v in (spec.get("images") or {}).items()}
        title = spec.get("title") or "Effiong AI Document"
        safe = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")[:50] or "Effiong_AI_Document"
        md, label = spec.get("markdown", ""), spec.get("label", "Document")
        if fmt == "pdf":
            cert = spec.get("certificate")
            if cert:
                data = doc_engine.compile_certificate_pdf(cert.get("title", title), cert.get("recipient", ""), cert.get("body", ""),
                                                          cert.get("issuer", "Effiong AI"), serial=cert.get("serial", ""))
            else:
                data = doc_engine.compile_pdf_bytes(md, doc_type=label, images=images)
            return data, f"{safe}.pdf", "application/pdf"
        if fmt == "docx":
            return (doc_engine.compile_word_bytes(md, doc_type=label, images=images), f"{safe}.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if fmt == "pptx":
            return (doc_engine.compile_pptx_bytes(md, images=images), f"{safe}.pptx",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        raise ValueError(f"unsupported format {fmt}")

    # ------------------------------------------------------------------ legacy API (app_core.py)
    def generate_research_document(self, title: str, raw_intel: str) -> List[str]:
        """Write a PDF + Markdown pair to disk and return their paths."""
        os.makedirs(self.output_dir, exist_ok=True)
        stamp = int(time.time())
        base = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "document"
        md_path = os.path.join(self.output_dir, f"{base}_{stamp}.md")
        pdf_path = os.path.join(self.output_dir, f"{base}_{stamp}.pdf")
        md = raw_intel if raw_intel.lstrip().startswith("# ") else f"# {title}\n\n{raw_intel}"
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(pdf_path, "wb") as fh:
            fh.write(doc_engine.compile_pdf_bytes(md, doc_type="Research Briefing"))
        return [pdf_path, md_path]


document_service = DocumentService()
