"""
EFFIONG AI - Brain Router (central orchestrator)
=================================================
Single entry point the UI calls for every chat turn. Decides what kind of request this is and dispatches to the
right engine(s), always through the multi-tier failover Brain and always wrapped in an ExecutionBudget so one
request can never hang the whole app.

Intents
  math        -> src.services.math_utils (verified symbolic result) + a short brain explanation
  image       -> src.services.image_service
  video       -> src.services.video_service
  document    -> src.services.document_service (compiles PDF/DOCX/PPTX for download)
  prediction  -> src.services.prediction_service + predictive_service (+ live evidence)
  research    -> src.services.research_service (repositories + web) feeding the brain, with citations
  chat        -> the multi-tier Brain directly, with conversation context and any file attachments
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.brain.context_manager import ContextManager
from src.brain.identity_directives import build_system_prompt
from src.core.guard import BudgetExceeded, ExecutionBudget, sanitize_text
from src.core.health import HEALTH
from src.services import search_service
from src.services.document_service import document_service
from src.services.evidence_service import EvidenceService
from src.services.file_service import Attachment, build_model_inputs
from src.services.image_service import ImageService
from src.services.llm_providers import BRAIN, AllProvidersFailed
from src.services.math_utils import try_symbolic
from src.services.prediction_service import prediction_service
from src.services.predictive_service import PredictiveEngine, extract_series
from src.services.research_service import ResearchService
from src.services.video_service import VideoService
from src.utilities.text_utils import truncate

_CTX = ContextManager()
_RESEARCH = ResearchService()
_IMAGES = ImageService()
_VIDEOS = VideoService()
_EVIDENCE = EvidenceService()

Intent = str

_IMAGE_RE = re.compile(r"\b(draw|paint|sketch|render|generate|create|make|design)\b.{0,40}\b(image|picture|photo|photograph|illustration|artwork|poster|logo|drawing|painting|portrait|avatar|icon|graphic|art)\b|"
                      r"\b(image|picture|photo|illustration|artwork)\s+of\b", re.IGNORECASE)
_VIDEO_RE = re.compile(r"\b(make|create|generate|render|produce|animate)\b.{0,30}\b(video|animation|clip|footage|motion\s*graphic)\b|\bvideo of\b", re.IGNORECASE)
_DOC_RE = re.compile(r"\b(write|draft|create|generate|prepare|compile|produce)\b.{0,40}\b(document|report|resume|résumé|cv\b|cover letter|proposal|business plan|thesis|"
                     r"dissertation|research paper|essay|contract|agreement|nda|memo|memorandum|certificate|licence|license|patent|trademark|"
                     r"presentation|slides|slide deck|powerpoint|pptx|company profile|memoir|policy brief|white ?paper|letter\b)", re.IGNORECASE)
_PREDICT_RE = re.compile(r"\b(predict|forecast|projection|will\s+\w+\s+(happen|occur|win|rise|fall|increase|decrease)|"
                         r"chances of|likelihood of|what.{0,15}happen (to|in|with)|next \d+ (days|weeks|months|years)|"
                         r"outlook for|trend for)\b", re.IGNORECASE)
_RESEARCH_HINT_RE = re.compile(r"\b(research|find out|investigate|dig into|sources on|evidence for|verify|fact.?check|"
                               r"history of|origin of|who (founded|built|discovered)|when did|what happened)\b", re.IGNORECASE)


@dataclass
class Segment:
    type: str                      # text | image | video | document | chart
    content: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteResult:
    intent: Intent
    segments: List[Segment]
    provider: str = ""
    sources: List[Dict[str, Any]] = field(default_factory=list)
    truth_matrix: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def classify_intent(text: str, has_images: bool = False) -> Intent:
    t = (text or "").strip()
    if not t and has_images:
        return "chat"
    if _DOC_RE.search(t):
        return "document"
    if _VIDEO_RE.search(t):
        return "video"
    if _IMAGE_RE.search(t) and not has_images:
        return "image"
    if extract_series(t) or _PREDICT_RE.search(t):
        return "prediction"
    if try_symbolic(t) is not None:
        return "math"
    if _RESEARCH_HINT_RE.search(t) or search_service.needs_live_data(t):
        return "research"
    return "chat"


class BrainRouter:
    def route(self, message: str, *, attachments: Optional[List[Attachment]] = None, chat_history: Optional[List[Dict[str, Any]]] = None,
              user: Optional[Dict[str, Any]] = None, budget: Optional[ExecutionBudget] = None,
              on_status: Optional[Callable[[str], None]] = None, force_intent: Optional[Intent] = None) -> RouteResult:
        attachments = attachments or []
        chat_history = chat_history or []
        budget = budget or ExecutionBudget()
        message = sanitize_text(message)
        att_text, att_images, att_docs = build_model_inputs(attachments)
        has_images = bool(att_images)
        intent = force_intent or classify_intent(message, has_images)

        try:
            if intent == "math":
                return self._math(message, budget, on_status)
            if intent == "image":
                return self._image(message, budget, on_status)
            if intent == "video":
                return self._video(message, budget, on_status)
            if intent == "document":
                return self._document(message, chat_history, att_text, budget, on_status, user)
            if intent == "prediction":
                return self._prediction(message, budget, on_status)
            if intent == "research":
                return self._research(message, chat_history, att_text, att_images, att_docs, budget, on_status, user)
            return self._chat(message, chat_history, att_text, att_images, att_docs, budget, on_status, user)
        except BudgetExceeded:
            return RouteResult(intent, [Segment("text", "This request grew too large for one turn - I've stopped safely. "
                                                        "Please ask again in a narrower way (or split it into steps).")],
                               warnings=["budget exceeded"])
        except Exception as exc:
            HEALTH.flag("brain_router", f"{exc.__class__.__name__}: {exc}")
            return RouteResult(intent, [Segment("text", "Something went wrong on my end handling that. Please try again - "
                                                        "if it keeps happening, try rephrasing the request.")],
                               warnings=[f"{exc.__class__.__name__}: {exc}"])

    # ------------------------------------------------------------------ math
    def _math(self, message: str, budget: ExecutionBudget, on_status) -> RouteResult:
        result = try_symbolic(message)
        if not result:
            return self._chat(message, [], "", [], [], budget, on_status, None)
        if on_status:
            on_status("🧮 Verifying with the symbolic math engine...")
        prompt = (f"The exact computed result for this problem is already verified below. Explain the working clearly and "
                  f"concisely, step by step, and finish by stating the final answer plainly.\n\nProblem: {message}\n"
                  f"Operation: {result['operation']}\nParsed as: {result['input']}\nVERIFIED RESULT: {result['result']}")
        try:
            resp = BRAIN.generate([{"role": "user", "content": prompt}], system=build_system_prompt("math"), task="reasoning",
                                  max_tokens=1200, temperature=0.2, timeout=35, budget=budget)
            text = resp.text
            provider = f"{resp.provider}/{resp.model}"
        except AllProvidersFailed:
            text = f"**Verified result:** {result['input']} → **{result['result']}**\n\n(computed by the built-in symbolic math engine)"
            provider = "sympy (offline)"
        return RouteResult("math", [Segment("text", text)], provider=provider)

    # ------------------------------------------------------------------ image
    def _image(self, message: str, budget: ExecutionBudget, on_status) -> RouteResult:
        res = _IMAGES.generate(message, budget=budget, on_status=on_status)
        seg = Segment("image", res.prompt, res.to_attachment() if hasattr(res, "to_attachment") else {})
        text = f"Here's what I created for: *{truncate(res.prompt, 160)}*" if not res.is_placeholder else (
            "The live image engines were all busy just now, so here's a placeholder while you try again shortly.")
        warns = res.notes if res.is_placeholder else []
        return RouteResult("image", [Segment("text", text), seg], provider=res.provider, warnings=warns)

    # ------------------------------------------------------------------ video
    def _video(self, message: str, budget: ExecutionBudget, on_status) -> RouteResult:
        res = _VIDEOS.generate(message, budget=budget, on_status=on_status)
        seg = Segment("video", res.prompt, res.to_attachment())
        text = f"Here's your video for: *{truncate(res.prompt, 160)}*" if not res.is_placeholder else (
            "Every video engine was busy, so I built a local motion render from generated stills instead.")
        return RouteResult("video", [Segment("text", text), seg], provider=res.provider, warnings=res.notes)

    # ------------------------------------------------------------------ document
    def _document(self, message: str, history: List[Dict[str, Any]], att_text: str, budget: ExecutionBudget, on_status,
                 user: Optional[Dict[str, Any]]) -> RouteResult:
        history_text = _CTX.build_history_context(history, max_chars=2500)
        doc = document_service.write(message, context=att_text, history_text=history_text, budget=budget, on_status=on_status, user=user)
        seg = Segment("document", doc.title, doc.spec())
        fmt_list = ", ".join(f.upper() for f in doc.formats)
        text = f"I've drafted **{doc.title}** ({doc.label}). Download links below ({fmt_list})."
        return RouteResult("document", [Segment("text", text), seg], provider=doc.provider, warnings=doc.warnings)

    # ------------------------------------------------------------------ prediction
    def _prediction(self, message: str, budget: ExecutionBudget, on_status) -> RouteResult:
        if on_status:
            on_status("🔮 Gathering evidence for the forecast...")
        pkg = _RESEARCH.gather(message, depth="quick", live=True, repositories=True, memory=True)
        forecast = prediction_service.build_forecast(message, pkg.sources)
        series = extract_series(message)
        series_result = PredictiveEngine.forecast_series(series, 4) if series else None
        footer = prediction_service.evidence_footer_markdown(forecast, series_result)
        prompt = (f"{build_system_prompt('predict')}\n\nQuestion: {message}\n\nContext gathered:\n{truncate(pkg.context, 5000)}\n\n"
                  f"Deterministic evidence metrics (do not contradict these numbers): confidence {forecast['confidence']}%, "
                  f"horizon {forecast['forecast_horizon']}, trend strength {forecast['trend_strength']}.")
        try:
            resp = BRAIN.generate([{"role": "user", "content": prompt}], task="reasoning", max_tokens=1800, temperature=0.5,
                                  timeout=45, budget=budget, grounding=True)
            text, provider = resp.text, f"{resp.provider}/{resp.model}"
        except AllProvidersFailed:
            text = (f"## Forecast: {message}\n\nBaseline scenario: {forecast['scenarios']['base_case']}\n\n"
                    f"Optimistic: {forecast['scenarios']['best_case']}\n\nDownside: {forecast['scenarios']['worst_case']}")
            provider = "deterministic engine (offline)"
        return RouteResult("prediction", [Segment("text", text + "\n\n" + footer)], provider=provider, sources=pkg.sources,
                           truth_matrix=forecast.get("truth_matrix", {}))

    # ------------------------------------------------------------------ research
    def _research(self, message: str, history: List[Dict[str, Any]], att_text: str, att_images, att_docs,
                 budget: ExecutionBudget, on_status, user: Optional[Dict[str, Any]]) -> RouteResult:
        if on_status:
            on_status("🔎 Researching across live web + open repositories...")
        pkg = _RESEARCH.gather(message, depth="standard", live=True, repositories=True, memory=True)
        history_text = _CTX.build_history_context(history)
        extra = f"CONVERSATION SO FAR:\n{truncate(history_text, 3000)}"
        if att_text:
            extra += f"\n\nUSER-SUPPLIED FILE CONTENT:\n{truncate(att_text, 4000)}"
        if pkg.context:
            extra += f"\n\nRESEARCH CONTEXT (ground your answer in this; cite the URLs you actually use):\n{pkg.context}"
        system = build_system_prompt("chat", user=user, extra=extra)
        messages = _CTX.to_messages(history) + [{"role": "user", "content": message}]
        try:
            resp = BRAIN.generate(messages, system=system, task="live", images=att_images, docs=att_docs, max_tokens=2600,
                                  temperature=0.6, timeout=50, budget=budget, grounding=True)
            text, provider, extra_sources = resp.text, f"{resp.provider}/{resp.model}", resp.sources
        except AllProvidersFailed as exc:
            text = ("I couldn't reach any AI engine just now (every free tier is busy or unreachable). Here is what I found "
                    f"directly from research sources:\n\n{truncate(pkg.context, 3000) or 'No sources could be reached either - please try again shortly.'}")
            provider, extra_sources = "offline", []
            HEALTH.flag("brain_router", f"research chat: all providers failed: {exc}")
        sources = pkg.sources + [{"source": "model citation", "title": s.get("title", ""), "url": s.get("url", "")} for s in extra_sources]
        matrix = _EVIDENCE.build_truth_matrix(sources) if sources else {}
        return RouteResult("research", [Segment("text", text)], provider=provider, sources=sources, truth_matrix=matrix)

    # ------------------------------------------------------------------ chat
    def _chat(self, message: str, history: List[Dict[str, Any]], att_text: str, att_images, att_docs,
             budget: ExecutionBudget, on_status, user: Optional[Dict[str, Any]]) -> RouteResult:
        extra = ""
        if att_text:
            extra = f"ATTACHED FILE CONTENT:\n{truncate(att_text, 6000)}"
        needs_live = search_service.needs_live_data(message)
        pkg = None
        if needs_live:
            if on_status:
                on_status("🔎 Checking the live web for this...")
            pkg = _RESEARCH.gather(message, depth="quick", live=True, repositories=False, memory=True)
            if pkg.context:
                extra += ("\n\n" if extra else "") + f"LIVE CONTEXT (cite URLs you use):\n{pkg.context}"
        system = build_system_prompt("chat", user=user, extra=extra)
        messages = _CTX.to_messages(history) + [{"role": "user", "content": message or "(see attached files)"}]
        try:
            resp = BRAIN.generate(messages, system=system, task="chat", images=att_images, docs=att_docs, max_tokens=2200,
                                  temperature=0.7, timeout=45, budget=budget, grounding=needs_live)
            text, provider, extra_sources = resp.text, f"{resp.provider}/{resp.model}", resp.sources
        except AllProvidersFailed as exc:
            text = ("Every AI tier is currently unreachable or out of free quota. Please check the operator panel, add another "
                    "provider key, or try again in a minute.")
            provider, extra_sources = "offline", []
            HEALTH.flag("brain_router", f"chat: all providers failed: {exc}")
        sources = (pkg.sources if pkg else []) + [{"source": "model citation", "title": s.get("title", ""), "url": s.get("url", "")} for s in extra_sources]
        return RouteResult("chat", [Segment("text", text)], provider=provider, sources=sources,
                           truth_matrix=_EVIDENCE.build_truth_matrix(sources) if sources else {})


brain_router = BrainRouter()


# =========================================================================================
# Legacy-compatible entry points (used by src/components/chat_ui.py and app.py)
# =========================================================================================
import base64
import json as _json

from src.utilities import doc_engine as _doc_engine


def compile_pdf_bytes(markdown_text: str, **kw: Any) -> bytes:
    """Thin wrapper kept for older imports (`from src.services.brain_router import compile_pdf_bytes`)."""
    return _doc_engine.compile_pdf_bytes(markdown_text, **kw)


def compile_word_bytes(markdown_text: str, **kw: Any) -> bytes:
    return _doc_engine.compile_word_bytes(markdown_text, **kw)


def compile_pptx_bytes(markdown_text: str, **kw: Any) -> bytes:
    return _doc_engine.compile_pptx_bytes(markdown_text, **kw)


def _legacy_history(history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """The UI's master_messages entries may carry 'segments' instead of a flat 'content' - flatten them."""
    out: List[Dict[str, Any]] = []
    for m in history or []:
        role = m.get("role", "user")
        if role == "user":
            out.append({"role": "user", "content": m.get("content", "")})
        else:
            text = m.get("content") or " ".join(s.get("content", "") for s in (m.get("segments") or []))
            out.append({"role": "assistant", "content": text})
    return out


def execute_sovereign_intelligence_cycle(prompt: str, history: Optional[List[Dict[str, Any]]] = None,
                                         attachments: Optional[List[Any]] = None, user: Optional[Dict[str, Any]] = None,
                                         on_status: Optional[Callable[[str], None]] = None) -> str:
    """
    Stable string-returning entry point for the Streamlit UI (keeps the original tag protocol so the chat
    renderer does not need to change): embeds [EFFIONG_MEDIA_IMAGE::path_or_url], [EFFIONG_MEDIA_VIDEO::...],
    [EFFIONG_TRIGGER_DOCUMENT_ASSET]::<markdown> and, for documents, a companion
    [EFFIONG_DOC_SPEC::<base64 json>] tag the UI can decode to offer PDF/Word/PowerPoint downloads together.
    """
    result = brain_router.route(message=prompt, attachments=attachments, chat_history=_legacy_history(history),
                                user=user, on_status=on_status)
    if result.intent == "document":
        doc_seg = next((s for s in result.segments if s.type == "document"), None)
        if doc_seg is not None:
            spec_b64 = base64.b64encode(_json.dumps(doc_seg.data, ensure_ascii=False, default=str).encode("utf-8")).decode("ascii")
            markdown = doc_seg.data.get("markdown", doc_seg.content)
            out = f"[EFFIONG_TRIGGER_DOCUMENT_ASSET]::{markdown}\n[EFFIONG_DOC_SPEC::{spec_b64}]"
            if result.warnings:
                out += "\n\n_Note: " + "; ".join(result.warnings) + "_"
            return out

    text_parts, tags = [], []
    for seg in result.segments:
        if seg.type == "text":
            text_parts.append(seg.content)
        elif seg.type == "image":
            ref = (seg.data or {}).get("src") or (seg.data or {}).get("path")
            if ref:
                tags.append(f"[EFFIONG_MEDIA_IMAGE::{ref}]")
        elif seg.type == "video":
            ref = (seg.data or {}).get("src") or (seg.data or {}).get("path")
            if ref:
                tags.append(f"[EFFIONG_MEDIA_VIDEO::{ref}]")

    body = "\n\n".join(p for p in text_parts if p)
    if tags:
        body += ("\n\n" if body else "") + "[EFFIONG_TRIGGER_MEDIA_ASSET]\n" + "\n".join(tags)
    if result.warnings:
        body += "\n\n_Note: " + "; ".join(result.warnings) + "_"
    return body or "I couldn't put together a response for that just now - please try rephrasing."
