# 🐆 Effiong AI — Sovereign Wisdom Engine

A truth-seeking, future-discerning research and African heritage preservation platform, built as a
Streamlit app with a multi-tier, failover-first AI backend. Every engine — chat, images, video,
documents, math, prediction, live research, and heritage verification — is designed so that a busy or
missing provider degrades gracefully instead of breaking the app, and the **free tier is the default
path**: Effiong AI works with **zero API keys**.

## What's inside

| Capability | How it works |
|---|---|
| **Chat** | Multi-tier LLM failover (Gemini → Groq → Cerebras → GitHub Models → Mistral → SambaNova → OpenRouter → Together → NVIDIA → Cloudflare → Hugging Face → DeepSeek → Grok → Perplexity → OpenAI → Claude → local Ollama). Automatic key rotation and cooldowns when a provider runs out of free quota. |
| **File uploads (＋ button)** | Images, video, PDF, Word, PowerPoint, Excel/CSV, audio, code, text, and **zip folders** (opened and read file-by-file, zip-bomb safe). |
| **Image generation** | Pollinations (free, no key) → Hugging Face FLUX → Cloudflare FLUX → Together FLUX → Leonardo AI → Gemini image model → local poster canvas (always works, even fully offline). |
| **Video generation** | Google Veo (optional) → Pollinations video → PixVerse → Kling AI → **local Ken-Burns motion render** built from AI keyframes (always available, free). |
| **Documents** | Native Markdown → PDF / Word / PowerPoint compiler (no LibreOffice needed): résumés, cover letters, proposals, business plans, theses, research papers, legal drafts, certificates, licences, patents, memos, letters, reports, presentations. Long documents (thesis, business plan) are outlined then written section-by-section in parallel. |
| **Math** | SymPy-backed symbolic engine (algebra, calculus, equations) with a strict, sandboxed parser — brain explains, engine verifies. |
| **Prediction** | Deterministic evidence/confidence scoring + a NumPy quantitative forecaster (Holt damped-trend / linear regression with confidence bands) for any numeric series in the question. |
| **Research** | Parallel search across live web (Tavily/SerpAPI/Brave/DuckDuckGo/Wikipedia) + open knowledge repositories (Wikipedia, Wikidata, Internet Archive, Library of Congress, Open Library, Project Gutenberg, Crossref, OpenAlex, arXiv), with citations. |
| **Self-learning memory** | Every research answer's public sources are embedded (local hashing embedder by default, or Gemini embeddings) and stored in a local SQLite vector store — optionally mirrored to Pinecone/Supabase — so later questions get smarter automatically. |
| **Heritage ledger** | Log a historical/oral claim → automatic evidence check (links, Wayback, repositories, web, AI fact-check) → truth classification (Verified / Pending / Disputed / Opinion / Speculation) → one-click publish to Wayback Machine, Internet Archive, Zenodo, OSF, Figshare, Wikimedia Commons, Wikidata. |
| **Voice** | Browser dictation + speech synthesis (free, built-in), with Groq Whisper / Gemini transcription for uploaded audio, and optional ElevenLabs TTS. |
| **Security shield** | Per-user rate limiting & daily quotas, a per-request time/call budget (kills runaway loops), SSRF-safe fetching, and a component health registry so one broken piece never takes the whole app down. |

The **UI is unchanged** from the original design (dark "sovereign" theme, segmented chat blocks,
sidebar heritage ledger + chat history) — the only addition is the **➕ button** beside the chat box for
attaching files, images, videos and documents.

## Quick start (zero configuration)

```bash
pip install -r requirements.txt
streamlit run app.py
```

That's it — the app runs immediately using free, keyless tiers (Pollinations for images, DuckDuckGo for
search, the local math/document/vector engines, and a local motion-render for video). Add API keys (see
below) to unlock more chat tiers, higher rate limits, and the optional paid providers.

## Adding API keys (all optional)

Copy **`.streamlit/secrets.toml.example`** to `.streamlit/secrets.toml` (local development or when
pasting into Streamlit Community Cloud's *Settings → Secrets*), or copy **`.env.example`** to `.env` /
set the same names as real environment variables (Hugging Face Spaces, Docker, Render, etc.). Every
secret name is documented inline in those two files. Nothing is required to start the app.

Add multiple keys per provider for automatic "switch to the next free token when one runs dry" rotation:

```toml
GEMINI_API_KEY   = "key-one"
GEMINI_API_KEY_2 = "key-two"
GEMINI_API_KEY_3 = "key-three"
# or: GEMINI_API_KEYS = "key-a,key-b,key-c"
```

## Deploying

- **Streamlit Community Cloud**: push this folder to a GitHub repo, create a new app pointing at
  `app.py`, paste your secrets (optional) into *Settings → Secrets*.
- **Hugging Face Spaces / Docker / Render**: set the same names as environment variables (see
  `.env.example`); the app reads `os.environ` first and Streamlit secrets second.
- **Persistent disk**: chat threads and the heritage ledger are saved to `app_data/` as JSON by
  default; generated images/video/documents live in `generated_assets/` /
  `generated_documents/` and are auto-cleaned after 24h or 600MB. On an ephemeral host, set
  `SUPABASE_URL` + `SUPABASE_KEY` (see `supabase/schema.sql`) to persist chats and the heritage ledger
  in the cloud instead.

## Project layout

```
app.py                          Streamlit entrypoint (UI + startup wiring)
src/
  config.py                     Secrets/env loader, key rotation, resource limits
  core/
    health.py                   Component health registry + safe_import/guarded decorators
    guard.py                    Rate limiting, execution budget, SSRF-safe fetch
  brain/
    identity_directives.py      Effiong AI's system prompt / persona / response format rules
    context_manager.py          Conversation history -> model context
    embeddings.py                Local + Gemini embedding engine
    vision.py                   Image normalisation for multimodal calls
  services/
    llm_providers.py            The 17-provider multi-tier chat brain with failover
    brain_router.py             Intent classification + orchestration (the app's "main brain")
    image_service.py / video_service.py   Multi-tier media generation
    document_service.py / utilities/doc_engine.py   Document authoring + native PDF/Word/PPTX/SVG/chart engine
    math_utils.py               Sandboxed SymPy engine
    prediction_service.py / predictive_service.py   Forecasting
    research_service.py / repository_service.py / search_service.py   Research + live web + open repositories
    verification_service.py / evidence_service.py   Truth-checking pipeline
    archive_publisher.py        Publishes heritage records to 7 open archives
    file_service.py             Upload ingestion (images/video/pdf/office/audio/zip)
    audio_service.py            Speech-to-text / text-to-speech
    agent_*.py                  Autonomous background research agents + scheduler
    knowledge_graph_service.py  Lightweight entity/relationship graph
    operator_service.py         Reads the health/event logs for a status dashboard
  database/
    archive.py                  Local JSON (+ optional Supabase) persistence
    heritage_store.py           Heritage ledger data model
    vector_mesh.py              Self-learning knowledge memory (SQLite + optional Pinecone/Supabase)
  components/
    chat_ui.py                  Segmented chat UI, incl. the ➕ attachment button
    sidebar.py                  Heritage ledger + chat history sidebar
tests/test_smoke.py             Offline smoke tests (no keys/network needed) - `pytest tests/ -q`
supabase/schema.sql             Optional cloud persistence schema
```

## Notes

- **`.cdr` (CorelDRAW)** is a closed, proprietary format with no open writer library — Effiong AI
  produces **SVG** vector graphics instead, which CorelDRAW, Illustrator and Inkscape all open directly.
- Every AI-generated fact, prediction, and heritage classification carries an explicit confidence /
  evidence trail — the system is built to say "I don't know" or "pending verification" rather than
  invent certainty.
