"""
EFFIONG AI - Audio service
==========================
Speech-to-text  : Groq Whisper (free)  ->  Gemini audio understanding  (browser dictation is handled in the page)
Text-to-speech  : browser speech (default, free)  ->  ElevenLabs (optional free tier, when a key is set)
"""
from __future__ import annotations

from typing import Dict, Optional

import requests

from src import config
from src.core.health import HEALTH

SUPPORTED_LANGUAGES = {
    "English (US)": "en-US", "English (Nigeria)": "en-NG", "English (UK)": "en-GB", "French": "fr-FR",
    "Arabic": "ar-SA", "Swahili": "sw-KE", "Yoruba": "yo-NG", "Igbo": "ig-NG", "Hausa": "ha-NG",
    "Zulu": "zu-ZA", "Amharic": "am-ET", "Portuguese": "pt-PT",
}

# profile language name -> BCP-47 tag for browser speech APIs
_LANG_HINTS = {"english": "en-NG", "yoruba": "yo-NG", "igbo": "ig-NG", "hausa": "ha-NG", "swahili": "sw-KE",
               "zulu": "zu-ZA", "amharic": "am-ET", "french": "fr-FR", "arabic": "ar-SA", "portuguese": "pt-PT"}


def speech_language(profile: Optional[Dict] = None) -> str:
    forced = config.get("SPEECH_LANG")
    if forced:
        return forced
    langs = (profile or {}).get("languages") or ""
    first = str(langs).split(",")[0].strip().lower() if langs else ""
    return _LANG_HINTS.get(first, "en-US")


class AudioService:
    def transcribe(self, data: bytes, filename: str = "audio.wav", mime: str = "audio/wav") -> str:
        """Return a transcript ('' if every tier fails)."""
        for key in config.get_keys("GROQ_API_KEY"):
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {key}"},
                    files={"file": (filename, data, mime)},
                    data={"model": config.get("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo"), "response_format": "json"},
                    timeout=60,
                )
                if r.status_code == 200 and r.json().get("text"):
                    HEALTH.ok("stt:groq", "transcribed")
                    return r.json()["text"].strip()
                if r.status_code in (401, 403):
                    HEALTH.flag("stt:groq", "key rejected")
            except requests.RequestException as exc:
                HEALTH.flag("stt:groq", f"{exc.__class__.__name__}")
        if config.get_keys("GEMINI_API_KEY") and len(data) <= 18_000_000:
            try:
                from src.services.llm_providers import BRAIN

                resp = BRAIN.generate([{"role": "user", "content": "Transcribe this audio exactly. Output only the transcript."}],
                                      task="chat", docs=[(mime or "audio/wav", data)], max_tokens=4096, temperature=0.0)
                return resp.text.strip()
            except Exception as exc:
                HEALTH.flag("stt:gemini", f"{exc.__class__.__name__}: {exc}")
        return ""

    def synthesize(self, text: str) -> Optional[bytes]:
        """MP3 bytes from ElevenLabs when configured; None means 'let the browser speak'."""
        key = config.get("ELEVENLABS_API_KEY")
        if not key or config.get("TTS_PROVIDER", "browser").lower() != "elevenlabs":
            return None
        voice = config.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        try:
            r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                              headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
                              json={"text": text[:2500], "model_id": config.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")},
                              timeout=45)
            if r.status_code == 200 and r.content:
                return r.content
            HEALTH.flag("tts:elevenlabs", f"HTTP {r.status_code}")
        except requests.RequestException as exc:
            HEALTH.flag("tts:elevenlabs", exc.__class__.__name__)
        return None

    def health_check(self) -> Dict:
        return {"stt": "groq" if config.get_keys("GROQ_API_KEY") else ("gemini" if config.get_keys("GEMINI_API_KEY") else "browser-only"),
                "tts": config.get("TTS_PROVIDER", "browser")}


audio_service = AudioService()
