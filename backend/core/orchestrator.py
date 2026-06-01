from .memory import VectorMemory
from .media import MediaGenerator
from .prediction import PredictionEngine
import httpx
import logging

class AIModelOrchestrator:
    def __init__(self, gemini_key: str, tavily_key: str = None, groq_key: str = None):
        self.gemini_key = gemini_key
        self.tavily_key = tavily_key
        self.groq_key = groq_key
        self.memory = VectorMemory()
        self.media_gen = MediaGenerator(gemini_key)

    async def process(self, prompt: str, user_id: str = "default"):
        # Retrieve long-term memory
        context = self.memory.query(prompt)
        context_str = "\n".join(context) if context else ""

        system_prompt = f"""You are EFFIONG AI... [same high-quality prediction DNA as before]"""

        try:
            client = genai.Client(api_key=self.gemini_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[f"Context from memory: {context_str}\n\nUser: {prompt}"],
                config=types.GenerateContentConfig(system_instruction=system_prompt)
            )
            
            text = response.text
            enhanced = PredictionEngine.enhance(text)

            # Store in vector DB
            self.memory.add(f"Q: {prompt}\nA: {text}", {"user_id": user_id})

            return {
                "response": enhanced,
                "core": "Gemini 2.5 Flash + Chroma RAG",
                "image_url": await self._try_generate_image(prompt)
            }
        except Exception:
            # Fallback logic...
            return {"response": "Edge intelligence active.", "core": "Fallback"}
    
    async def _try_generate_image(self, prompt: str):
        if any(word in prompt.lower() for word in ["image", "picture", "draw", "generate visual"]):
            return await self.media_gen.generate_image(prompt)
        return None
