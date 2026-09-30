"""Turns stored conversation state into compact model-ready context."""
from __future__ import annotations

from typing import Any, Dict, List


def _assistant_text(msg: Dict[str, Any]) -> str:
    if msg.get("content"):
        return str(msg["content"])
    segs = msg.get("segments") or []
    return " ".join(str(s.get("content", "")) for s in segs if s.get("type") == "text")


class ContextManager:
    """Tracks thread history and keeps it inside a safe size for the multi-brain engines."""

    def build_history_context(self, chat_history: List[Dict[str, Any]], max_chars: int = 12000) -> str:
        if not chat_history:
            return "No previous exchange context recorded in this thread session."
        blocks = []
        for msg in chat_history:
            role = str(msg.get("role", "unknown")).upper()
            text = str(msg.get("content", "")) if role == "USER" else _assistant_text(msg)
            if text:
                blocks.append(f"{role}: {text}")
        raw = "\n\n".join(blocks)
        return raw if len(raw) <= max_chars else "..." + raw[-max_chars:]

    def compile_thread_context(self, chat_history: List[Dict[str, Any]]) -> str:
        return self.build_history_context(chat_history)

    def to_messages(self, chat_history: List[Dict[str, Any]], max_turns: int = 12, max_chars: int = 9000) -> List[Dict[str, str]]:
        """Last N turns as [{'role','content'}] with size cap (oldest dropped first)."""
        msgs: List[Dict[str, str]] = []
        for m in chat_history[-max_turns:]:
            role = "user" if m.get("role") == "user" else "assistant"
            text = str(m.get("content", "")) if role == "user" else _assistant_text(m)
            if text.strip():
                msgs.append({"role": role, "content": text.strip()[:3000]})
        total = sum(len(m["content"]) for m in msgs)
        while msgs and total > max_chars:
            total -= len(msgs.pop(0)["content"])
        return msgs
