"""
EFFIONG AI - Multi-Tier Brain (LLM providers)
=============================================
Default brain : Google Gemini (AI Studio free tier).
Other tiers   : Groq, Cerebras, GitHub Models (free GPT-class access), Mistral, SambaNova, OpenRouter (free
                models, incl. DeepSeek), Together, NVIDIA NIM, Cloudflare Workers AI, Hugging Face, xAI Grok,
                Perplexity (optional), OpenAI (optional), Anthropic Claude (optional), local Ollama.

How the "switch to the next free token when one is exhausted" rule works
------------------------------------------------------------------------
* Every provider can hold several keys (NAME, NAME_2 ... NAME_9, NAMES="a,b").
* A key that answers 429 / quota-exhausted is put on cooldown; the next key is used; when all keys of a
  provider are cooling the next provider in the task profile answers.
* A key that answers 401/403 is cooled for an hour and the operator is flagged (wrong / revoked key).
* Any exception is isolated - one broken provider never stops the others.

Model names change often on free tiers: every provider's models can be overridden with
    <PROVIDER>_MODEL = "model-a,model-b"        e.g.  GEMINI_MODEL, GROQ_MODEL, OPENROUTER_MODEL
"""
from __future__ import annotations

import base64
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

from src import config
from src.core.guard import BudgetExceeded, ExecutionBudget
from src.core.health import HEALTH, write_operator_log

Message = Dict[str, str]
Blob = Tuple[str, bytes]  # (mime_type, raw_bytes)


class ProviderError(Exception):
    """kind: quota | auth | transient | notfound | blocked | other"""

    def __init__(self, message: str, kind: str = "other", retry_after: Optional[float] = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.retry_after = retry_after


class AllProvidersFailed(Exception):
    def __init__(self, errors: List[str]) -> None:
        super().__init__("; ".join(errors[-6:]) or "no provider configured")
        self.errors = errors


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    sources: List[Dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------------------
# Cooldown book (per provider + key)
# ---------------------------------------------------------------------------------------
class _Cooldowns:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._until: Dict[Tuple[str, str], float] = {}
        self._reason: Dict[Tuple[str, str], str] = {}

    def is_cooling(self, provider: str, key: str) -> bool:
        with self._lock:
            return self._until.get((provider, key), 0) > time.time()

    def cool(self, provider: str, key: str, seconds: float, reason: str = "") -> None:
        with self._lock:
            self._until[(provider, key)] = time.time() + max(5.0, seconds)
            self._reason[(provider, key)] = reason

    def clear(self, provider: str, key: str) -> None:
        with self._lock:
            self._until.pop((provider, key), None)
            self._reason.pop((provider, key), None)

    def summary(self) -> Dict[str, Dict[str, Any]]:
        now = time.time()
        out: Dict[str, Dict[str, Any]] = {}
        with self._lock:
            for (prov, key), until in self._until.items():
                if until > now:
                    out.setdefault(prov, {"cooling_keys": 0, "seconds_left": 0, "reason": ""})
                    out[prov]["cooling_keys"] += 1
                    out[prov]["seconds_left"] = max(out[prov]["seconds_left"], int(until - now))
                    out[prov]["reason"] = self._reason.get((prov, key), "")
        return out


COOLDOWNS = _Cooldowns()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _error_from_response(resp: requests.Response) -> ProviderError:
    status = resp.status_code
    body = (resp.text or "")[:400]
    low = body.lower()
    retry_after: Optional[float] = None
    try:
        if resp.headers.get("retry-after"):
            retry_after = float(resp.headers["retry-after"])
    except (TypeError, ValueError):
        retry_after = None
    if "api key" in low and ("invalid" in low or "not valid" in low or "expired" in low):
        return ProviderError(f"{status} invalid api key", "auth")
    if status == 429 or "resource_exhausted" in low or "quota" in low or "rate limit" in low or "rate_limit" in low:
        if retry_after is None:
            retry_after = 3600 if ("per day" in low or "daily" in low) else 65
        return ProviderError(f"{status} quota/rate limit", "quota", retry_after)
    if status in (401, 403):
        return ProviderError(f"{status} unauthorized: {body[:120]}", "auth")
    if status == 404:
        return ProviderError(f"404 not found: {body[:120]}", "notfound")
    if status == 400 and ("safety" in low or "blocked" in low or "content_filter" in low or "policy" in low):
        return ProviderError("content blocked by provider safety filter", "blocked")
    if status >= 500 or status in (408, 409, 425):
        return ProviderError(f"{status} provider unavailable", "transient")
    return ProviderError(f"{status}: {body[:160]}", "other")


def _merge_same_role(messages: Sequence[Message]) -> List[Message]:
    merged: List[Message] = []
    for m in messages:
        role = "assistant" if m.get("role") in ("assistant", "model") else "user"
        content = str(m.get("content", "")).strip()
        if not content:
            continue
        if merged and merged[-1]["role"] == role:
            merged[-1]["content"] += "\n\n" + content
        else:
            merged.append({"role": role, "content": content})
    if merged and merged[0]["role"] != "user":
        merged.insert(0, {"role": "user", "content": "(conversation start)"})
    return merged


# ---------------------------------------------------------------------------------------
# Provider base
# ---------------------------------------------------------------------------------------
class Provider:
    name = "base"
    label = "Base"
    key_base = ""                       # config name of the (first) key
    default_models: List[str] = []
    vision_models: List[str] = []
    supports_vision = False
    supports_files = False              # can accept PDFs/audio/video inline (Gemini)
    free_note = ""

    # -- configuration ---------------------------------------------------------------
    def keys(self) -> List[str]:
        return config.get_keys(self.key_base) if self.key_base else []

    def configured(self) -> bool:
        return bool(self.keys())

    def model_list(self, need_vision: bool = False) -> List[str]:
        override = config.get(f"{self.name.upper()}_MODEL")
        if override:
            return [m.strip() for m in override.split(",") if m.strip()]
        if need_vision and self.vision_models:
            return list(self.vision_models)
        return list(self.default_models)

    # -- to implement ------------------------------------------------------------------
    def _request(self, key: str, model: str, messages: List[Message], system: str, images: List[Blob],
                 docs: List[Blob], max_tokens: int, temperature: float, timeout: float, json_mode: bool,
                 grounding: bool) -> Tuple[str, List[Dict[str, str]]]:
        raise NotImplementedError

    # -- shared loop -------------------------------------------------------------------
    def complete(self, messages: Sequence[Message], *, system: str = "", images: Optional[List[Blob]] = None,
                 docs: Optional[List[Blob]] = None, max_tokens: int = 2048, temperature: float = 0.7,
                 timeout: float = 40, need_vision: bool = False, json_mode: bool = False,
                 grounding: bool = False, budget: Optional[ExecutionBudget] = None) -> LLMResponse:
        images = images or []
        docs = docs or []
        msgs = _merge_same_role(messages)
        if not msgs:
            raise ProviderError("empty prompt", "other")
        keys = [k for k in self.keys() if not COOLDOWNS.is_cooling(self.name, k)]
        if not keys:
            raise ProviderError(f"{self.label}: all keys are cooling down", "quota")
        models = self.model_list(need_vision)[:3]
        last: Optional[Exception] = None
        for key in keys:
            for model in models:
                if budget:
                    budget.spend()
                t_out = budget.timeout_for(timeout) if budget else timeout
                try:
                    text, sources = self._request(key, model, msgs, system, images, docs, max_tokens, temperature,
                                                  t_out, json_mode, grounding)
                    if text and text.strip():
                        COOLDOWNS.clear(self.name, key)
                        HEALTH.ok(f"llm:{self.name}", f"answered with {model}")
                        return LLMResponse(text.strip(), self.name, model, sources)
                    last = ProviderError("empty response", "transient")
                except ProviderError as exc:
                    last = exc
                    if exc.kind == "quota":
                        COOLDOWNS.cool(self.name, key, exc.retry_after or 65, "quota/rate-limit")
                        write_operator_log("token_exhausted", {"provider": self.name, "model": model})
                        break  # switch to the next key
                    if exc.kind == "auth":
                        COOLDOWNS.cool(self.name, key, 3600, "auth failed")
                        HEALTH.flag(f"llm:{self.name}", f"key rejected ({exc}) - check the secret")
                        break
                    if exc.kind == "blocked":
                        raise
                    continue  # notfound / transient / other -> next model
                except requests.Timeout as exc:
                    last = ProviderError(f"timeout after {t_out:.0f}s", "transient")
                    HEALTH.flag(f"llm:{self.name}", "timeout")
                    break
                except requests.RequestException as exc:
                    last = ProviderError(f"network: {exc.__class__.__name__}", "transient")
                    continue
                except (KeyError, IndexError, TypeError, ValueError) as exc:
                    last = ProviderError(f"unexpected response shape: {exc}", "other")
                    continue
        if isinstance(last, ProviderError):
            raise last
        raise ProviderError("provider exhausted", "other")


# ---------------------------------------------------------------------------------------
# Google Gemini (default brain)
# ---------------------------------------------------------------------------------------
class GeminiProvider(Provider):
    name = "gemini"
    label = "Gemini (Google AI Studio)"
    key_base = "GEMINI_API_KEY"
    default_models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]
    vision_models = default_models
    supports_vision = True
    supports_files = True
    free_note = "Google AI Studio free tier"

    def _request(self, key, model, messages, system, images, docs, max_tokens, temperature, timeout, json_mode, grounding):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        contents: List[Dict[str, Any]] = []
        last_user = max((i for i, m in enumerate(messages) if m["role"] == "user"), default=-1)
        for i, m in enumerate(messages):
            parts: List[Dict[str, Any]] = [{"text": m["content"]}]
            if i == last_user:
                for mime, data in list(images) + list(docs):
                    parts.append({"inlineData": {"mimeType": mime, "data": _b64(data)}})
            contents.append({"role": "model" if m["role"] == "assistant" else "user", "parts": parts})
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if json_mode and not grounding:
            body["generationConfig"]["responseMimeType"] = "application/json"
        if grounding:
            body["tools"] = [{"google_search": {}}]
        r = requests.post(url, headers={"Content-Type": "application/json", "x-goog-api-key": key}, json=body,
                          timeout=timeout)
        if r.status_code != 200:
            raise _error_from_response(r)
        data = r.json()
        if data.get("promptFeedback", {}).get("blockReason"):
            raise ProviderError("prompt blocked by Gemini safety filter", "blocked")
        cand = (data.get("candidates") or [{}])[0]
        if cand.get("finishReason") in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST") and not cand.get("content"):
            raise ProviderError("answer blocked by Gemini safety filter", "blocked")
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        sources: List[Dict[str, str]] = []
        for chunk in (cand.get("groundingMetadata") or {}).get("groundingChunks", []) or []:
            web = chunk.get("web") or {}
            if web.get("uri"):
                sources.append({"title": web.get("title", web["uri"]), "url": web["uri"]})
        return text, sources


# ---------------------------------------------------------------------------------------
# Anthropic Claude (optional - no free API exists; used only when a key is supplied)
# ---------------------------------------------------------------------------------------
class AnthropicProvider(Provider):
    name = "anthropic"
    label = "Claude (Anthropic) - optional, paid API"
    key_base = "ANTHROPIC_API_KEY"
    default_models = ["claude-sonnet-5", "claude-haiku-4-5-20251001"]
    vision_models = default_models
    supports_vision = True
    free_note = "no free API - only used if you add a key"

    def _request(self, key, model, messages, system, images, docs, max_tokens, temperature, timeout, json_mode, grounding):
        last_user = max((i for i, m in enumerate(messages) if m["role"] == "user"), default=-1)
        out = []
        for i, m in enumerate(messages):
            content: Any = m["content"]
            if i == last_user and images:
                content = [{"type": "text", "text": m["content"]}]
                for mime, data in images:
                    content.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": _b64(data)}})
            out.append({"role": m["role"], "content": content})
        body = {"model": model, "max_tokens": max_tokens, "temperature": min(1.0, temperature), "messages": out}
        if system:
            body["system"] = system
        r = requests.post("https://api.anthropic.com/v1/messages",
                          headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                          json=body, timeout=timeout)
        if r.status_code != 200:
            raise _error_from_response(r)
        blocks = r.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text"), []


# ---------------------------------------------------------------------------------------
# Generic OpenAI-compatible providers (one class, many tiers)
# ---------------------------------------------------------------------------------------
class OpenAICompatProvider(Provider):
    def __init__(self, name: str, label: str, key_base: str, url: str, models: List[str],
                 vision_models: Optional[List[str]] = None, extra_headers: Optional[Dict[str, str]] = None,
                 free_note: str = "", token_param: str = "max_tokens", enabled_flag: str = "") -> None:
        self.name = name
        self.label = label
        self.key_base = key_base
        self._url = url
        self.default_models = models
        self.vision_models = vision_models or []
        self.supports_vision = bool(vision_models)
        self.extra_headers = extra_headers or {}
        self.free_note = free_note
        self.token_param = token_param
        self.enabled_flag = enabled_flag

    def url(self) -> str:
        return self._url

    def configured(self) -> bool:
        if self.enabled_flag and not config.get_bool(self.enabled_flag, False):
            return False
        return super().configured()

    def _request(self, key, model, messages, system, images, docs, max_tokens, temperature, timeout, json_mode, grounding):
        msgs: List[Dict[str, Any]] = []
        if system:
            msgs.append({"role": "system", "content": system})
        last_user = max((i for i, m in enumerate(messages) if m["role"] == "user"), default=-1)
        for i, m in enumerate(messages):
            content: Any = m["content"]
            if i == last_user and images and self.supports_vision:
                content = [{"type": "text", "text": m["content"]}]
                for mime, data in images:
                    content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{_b64(data)}"}})
            msgs.append({"role": m["role"], "content": content})
        payload = {"model": model, "messages": msgs, self.token_param: max_tokens, "temperature": temperature}
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
        headers.update(self.extra_headers)
        r = requests.post(self.url(), headers=headers, json=payload, timeout=timeout)
        if r.status_code != 200:
            raise _error_from_response(r)
        data = r.json()
        choice = data["choices"][0]
        if choice.get("finish_reason") == "content_filter":
            raise ProviderError("blocked by provider content filter", "blocked")
        content = choice["message"]["content"]
        if isinstance(content, list):
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
        content = re.sub(r"<think>[\s\S]*?</think>", "", content or "").strip()  # hide reasoning traces
        return content, []


class CloudflareProvider(OpenAICompatProvider):
    def configured(self) -> bool:
        return bool(config.get("CLOUDFLARE_ACCOUNT_ID")) and super().configured()

    def url(self) -> str:
        acct = config.get("CLOUDFLARE_ACCOUNT_ID")
        return f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/v1/chat/completions"


class OllamaProvider(OpenAICompatProvider):
    """Local model for developers running Effiong AI on their own machine."""

    def keys(self) -> List[str]:
        return ["local"] if config.get_bool("ENABLE_OLLAMA", False) or config.get("OLLAMA_URL") else []

    def url(self) -> str:
        return config.get("OLLAMA_URL", "http://localhost:11434/v1/chat/completions")

    def model_list(self, need_vision: bool = False) -> List[str]:
        return [config.get("OLLAMA_MODEL", "llama3")]


def _build_registry() -> Dict[str, Provider]:
    reg: Dict[str, Provider] = {}

    def add(p: Provider) -> None:
        reg[p.name] = p

    add(GeminiProvider())
    add(OpenAICompatProvider(
        "groq", "Groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        vision_models=["meta-llama/llama-4-scout-17b-16e-instruct"], free_note="Groq free tier"))
    add(OpenAICompatProvider(
        "cerebras", "Cerebras", "CEREBRAS_API_KEY", "https://api.cerebras.ai/v1/chat/completions",
        ["llama-3.3-70b", "llama3.1-8b"], free_note="Cerebras free tier"))
    add(OpenAICompatProvider(
        "github", "GitHub Models (GPT-class)", "GITHUB_TOKEN", "https://models.github.ai/inference/chat/completions",
        ["openai/gpt-4o-mini", "meta/Llama-3.3-70B-Instruct"], vision_models=["openai/gpt-4o-mini"],
        free_note="free with any GitHub token that has 'models: read'"))
    add(OpenAICompatProvider(
        "mistral", "Mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1/chat/completions",
        ["mistral-small-latest"], vision_models=["mistral-small-latest"], free_note="Mistral free experiment tier"))
    add(OpenAICompatProvider(
        "sambanova", "SambaNova", "SAMBANOVA_API_KEY", "https://api.sambanova.ai/v1/chat/completions",
        ["Meta-Llama-3.3-70B-Instruct"], free_note="SambaNova free tier"))
    add(OpenAICompatProvider(
        "openrouter", "OpenRouter (free models incl. DeepSeek)", "OPENROUTER_API_KEY",
        "https://openrouter.ai/api/v1/chat/completions",
        ["meta-llama/llama-3.3-70b-instruct:free", "deepseek/deepseek-chat-v3-0324:free",
         "google/gemma-3-27b-it:free", "mistralai/mistral-small-3.1-24b-instruct:free"],
        vision_models=["google/gemma-3-27b-it:free", "mistralai/mistral-small-3.1-24b-instruct:free"],
        extra_headers={"HTTP-Referer": "https://effiong-ai.streamlit.app", "X-Title": "Effiong AI"},
        free_note="':free' models"))
    add(OpenAICompatProvider(
        "together", "Together AI", "TOGETHER_API_KEY", "https://api.together.xyz/v1/chat/completions",
        ["meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"], free_note="free Llama endpoint"))
    add(OpenAICompatProvider(
        "nvidia", "NVIDIA NIM", "NVIDIA_API_KEY", "https://integrate.api.nvidia.com/v1/chat/completions",
        ["meta/llama-3.3-70b-instruct"], free_note="NVIDIA developer free credits"))
    add(CloudflareProvider(
        "cloudflare", "Cloudflare Workers AI", "CLOUDFLARE_API_TOKEN", "",
        ["@cf/meta/llama-3.3-70b-instruct-fp8-fast"], free_note="Cloudflare free daily allowance"))
    add(OpenAICompatProvider(
        "huggingface", "Hugging Face Inference", "HF_TOKEN", "https://router.huggingface.co/v1/chat/completions",
        ["meta-llama/Llama-3.3-70B-Instruct", "Qwen/Qwen2.5-72B-Instruct"],
        vision_models=["Qwen/Qwen2.5-VL-72B-Instruct"], free_note="HF free monthly credits"))
    add(OpenAICompatProvider(
        "deepseek", "DeepSeek", "DEEPSEEK_API_KEY", "https://api.deepseek.com/chat/completions",
        ["deepseek-chat"], free_note="optional - low cost, not free"))
    add(OpenAICompatProvider(
        "xai", "xAI Grok", "XAI_API_KEY", "https://api.x.ai/v1/chat/completions",
        ["grok-4.1-fast-non-reasoning"], free_note="uses your existing xAI credits"))
    add(OpenAICompatProvider(
        "perplexity", "Perplexity Sonar (search-grounded)", "PERPLEXITY_API_KEY",
        "https://api.perplexity.ai/chat/completions", ["sonar"], free_note="optional - paid API"))
    add(OpenAICompatProvider(
        "openai", "OpenAI", "OPENAI_API_KEY", "https://api.openai.com/v1/chat/completions",
        ["gpt-4o-mini"], vision_models=["gpt-4o-mini"], free_note="optional - paid API"))
    add(AnthropicProvider())
    add(OllamaProvider("ollama", "Local Ollama", "", "", ["llama3"], free_note="only on your own machine"))
    return reg


REGISTRY: Dict[str, Provider] = _build_registry()

# Which providers answer which kind of work, in priority order.
PROFILES: Dict[str, List[str]] = {
    "chat": ["gemini", "groq", "cerebras", "github", "mistral", "sambanova", "openrouter", "together", "nvidia",
             "cloudflare", "huggingface", "deepseek", "xai", "perplexity", "openai", "anthropic", "ollama"],
    "docs": ["anthropic", "gemini", "github", "openrouter", "mistral", "groq", "cerebras", "sambanova", "together",
             "nvidia", "huggingface", "deepseek", "cloudflare", "xai", "openai", "ollama"],
    "reasoning": ["gemini", "deepseek", "openrouter", "github", "groq", "cerebras", "sambanova", "mistral",
                  "together", "nvidia", "huggingface", "xai", "openai", "anthropic", "ollama"],
    "live": ["perplexity", "gemini", "groq", "cerebras", "github", "mistral", "openrouter", "sambanova", "together",
             "nvidia", "cloudflare", "huggingface", "xai", "openai", "ollama"],
    "vision": ["gemini", "groq", "github", "openrouter", "mistral", "huggingface", "openai", "anthropic"],
    "code": ["gemini", "mistral", "groq", "github", "cerebras", "openrouter", "sambanova", "together", "nvidia",
             "huggingface", "deepseek", "xai", "openai", "anthropic", "ollama"],
}


def configured_providers() -> List[str]:
    return [n for n, p in REGISTRY.items() if p.configured()]


class Brain:
    """The tier-walker: try providers in profile order until one answers."""

    def generate(self, messages: Sequence[Message], *, system: str = "", task: str = "chat",
                 images: Optional[List[Blob]] = None, docs: Optional[List[Blob]] = None, max_tokens: int = 2048,
                 temperature: float = 0.7, timeout: float = 40, json_mode: bool = False, grounding: bool = False,
                 prefer: Optional[str] = None, budget: Optional[ExecutionBudget] = None,
                 on_provider: Optional[Any] = None) -> LLMResponse:
        images = images or []
        docs = docs or []
        need_vision = bool(images)
        order = list(PROFILES.get(task, PROFILES["chat"]))
        if need_vision:
            order = list(PROFILES["vision"])
        if docs:  # inline documents / audio / video are only understood by Gemini
            order = [n for n in order if REGISTRY[n].supports_files] or order
        if prefer and prefer in REGISTRY:
            order = [prefer] + [n for n in order if n != prefer]

        errors: List[str] = []
        for name in order:
            prov = REGISTRY.get(name)
            if prov is None or not prov.configured():
                continue
            if need_vision and not prov.supports_vision:
                continue
            try:
                if on_provider:
                    on_provider(prov)
                return prov.complete(messages, system=system, images=images, docs=docs if prov.supports_files else [],
                                     max_tokens=max_tokens, temperature=temperature, timeout=timeout,
                                     need_vision=need_vision, json_mode=json_mode,
                                     grounding=grounding and name == "gemini", budget=budget)
            except BudgetExceeded as exc:
                errors.append(f"budget: {exc}")
                break
            except ProviderError as exc:
                errors.append(f"{name}: {exc}")
                continue
            except Exception as exc:  # never let one provider crash the cycle
                HEALTH.flag(f"llm:{name}", f"{exc.__class__.__name__}: {exc}")
                errors.append(f"{name}: {exc.__class__.__name__}")
                continue
        raise AllProvidersFailed(errors)

    def status(self) -> List[Dict[str, Any]]:
        cool = COOLDOWNS.summary()
        rows = []
        for name, prov in REGISTRY.items():
            rows.append({
                "provider": name,
                "label": prov.label,
                "configured": prov.configured(),
                "keys": len(prov.keys()),
                "cooling": cool.get(name),
                "note": prov.free_note,
            })
        return rows


BRAIN = Brain()
