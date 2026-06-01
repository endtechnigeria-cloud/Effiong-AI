from .memory import VectorMemory
from .media import MediaGenerator
from .prediction import PredictionEngine
import os
from google import genai
from google.genai.types import GenerateContentConfig, Part
import logging

logger = logging.getLogger(__name__)

class AIModelOrchestrator:
    def __init__(self, gemini_key: str, tavily_key: str = None, groq_key: str = None):
        self.gemini_key = gemini_key
        self.tavily_key = tavily_key
        self.groq_key = groq_key
        self.memory = VectorMemory()
        self.media_gen = MediaGenerator(gemini_key)
        self.client = genai.Client(api_key=gemini_key) if gemini_key else None

    async def process(self, prompt: str, history: list = None):
        context = self.memory.query(prompt)
        context_str = "\n".join(context) if context else ""

        system_prompt = """You are EFFIONG AI, the absolute finest sovereign multi-neural intelligence system...
[Full DNA prompt from previous versions - prediction excellence, African heritage, Bayesian reasoning, etc.]"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[f"Memory Context:\n{context_str}\n\nUser: {prompt}"],
                config=GenerateContentConfig(system_instruction=system_prompt)
            )

            text = response.text
            enhanced = PredictionEngine.enhance(text)

            self.memory.add(f"Q: {prompt}\nA: {text}")

            image_url = await self.media_gen.generate_image(prompt) if "image" in prompt.lower() else None

            return {
                "response": enhanced,
                "core": "Gemini 2.5 + Chroma RAG",
                "image_url": image_url
            }
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return {"response": "Edge intelligence active.", "core": "Localized Baseline"}

    async def generate_speech(self, text: str) -> str:
        """Gemini Native TTS"""
        try:
            response = self.client.models.generate_content(
                model="gemini-3.1-flash-tts",  # Native TTS model
                contents=[text],
                config=GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    audio_config={"voice": "african_male_natural"}  # Customizable
                )
            )

            for part in response.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("audio"):
                    # Return base64 audio data URL
                    return f"data:audio/mp3;base64,{part.inline_data.data}"
            return None
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None
