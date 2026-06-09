from typing import List, Dict


class ContextManager:
    """
    Effiong AI Memory Layer v1

    Handles:
    - Conversation Memory
    - Session Summaries
    - Context Injection
    """

    def __init__(self):
        self.max_history = 10

    def build_context(
        self,
        current_prompt: str,
        chat_history: List[Dict]
    ) -> str:
        """
        Inject recent conversation context.
        """

        recent_messages = chat_history[-self.max_history:]

        context_blocks = []

        for msg in recent_messages:

            if msg["role"] == "user":
                context_blocks.append(
                    f"USER: {msg['content']}"
                )

            elif msg["role"] == "assistant":

                if "content" in msg:
                    context_blocks.append(
                        f"ASSISTANT: {msg['content']}"
                    )

                elif "segments" in msg:

                    combined = " ".join(
                        seg["content"]
                        for seg in msg["segments"]
                        if seg["type"] == "text"
                    )

                    context_blocks.append(
                        f"ASSISTANT: {combined}"
                    )

        memory_context = "\n".join(context_blocks)

        return f"""
CONVERSATION MEMORY

{memory_context}

CURRENT USER REQUEST

{current_prompt}
"""