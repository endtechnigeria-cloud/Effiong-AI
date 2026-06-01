from google import genai
from google.genai import types
import base64
import logging

logger = logging.getLogger(__name__)

class MediaGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def generate_image(self, prompt: str):
        try:
            response = self.client.models.generate_content(
                model="gemini-3.1-flash-image",  # Native image generation model
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                )
            )
            
            for part in response.parts:
                if part.inline_data:
                    # Return base64 image
                    return f"data:image/png;base64,{part.inline_data.data}"
            return None
        except Exception as e:
            logger.error(f"Gemini Image Gen failed: {e}")
            # Fallback to Pollinations
            return f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '_')}?width=1024&height=576"
