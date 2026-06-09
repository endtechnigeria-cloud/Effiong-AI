import os
import httpx
import asyncio

from typing import Dict, Any


class ModelService:
    """
    ============================================================
    EFFIONG AI MODEL ABSTRACTION LAYER
    ============================================================

    Responsibilities

    - Gemini Access
    - Groq Access
    - OpenRouter Access
    - HuggingFace Access

    Future

    - Claude
    - DeepSeek
    - Mistral
    - Qwen
    - Local Ollama Models

    Supports

    Problem #1
    Problem #2
    Problem #3
    Problem #4
    Problem #6
    Problem #10
    Problem #11
    """

    def __init__(self):

        self.gemini_key = os.getenv(
            "GEMINI_API_KEY",
            ""
        )

        self.groq_key = os.getenv(
            "GROQ_API_KEY",
            ""
        )

        self.openrouter_key = os.getenv(
            "OPENROUTER_KEY",
            ""
        )

        self.hf_token = os.getenv(
            "HF_TOKEN",
            ""
        )

        self.client = httpx.AsyncClient(
            timeout=60
        )

    # =========================================================
    # GEMINI
    # =========================================================

    async def call_gemini(
        self,
        prompt: str,
        system_instruction: str
    ) -> str:

        if not self.gemini_key:

            raise Exception(
                "Gemini API key missing."
            )

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        )

        payload = {

            "contents": [

                {
                    "role": "user",

                    "parts": [
                        {
                            "text":
                            f"{system_instruction}\n\n{prompt}"
                        }
                    ]
                }
            ],

            "generationConfig": {

                "temperature": 0.4,

                "maxOutputTokens": 4096
            }
        }

        response = await self.client.post(
            url,
            json=payload
        )

        response.raise_for_status()

        data = response.json()

        return (
            data["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

    # =========================================================
    # GROQ
    # =========================================================

    async def call_groq(
        self,
        prompt: str,
        system_instruction: str
    ) -> str:

        if not self.groq_key:

            raise Exception(
                "Groq API key missing."
            )

        url = (
            "https://api.groq.com/openai/v1/chat/completions"
        )

        headers = {

            "Authorization":
                f"Bearer {self.groq_key}",

            "Content-Type":
                "application/json"
        }

        payload = {

            "model":
                "llama3-70b-8192",

            "messages": [

                {
                    "role": "system",

                    "content":
                        system_instruction
                },

                {
                    "role": "user",

                    "content":
                        prompt
                }
            ],

            "temperature": 0.4
        }

        response = await self.client.post(
            url,
            json=payload,
            headers=headers
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    # =========================================================
    # OPENROUTER
    # =========================================================

    async def call_openrouter(
        self,
        prompt: str,
        system_instruction: str
    ) -> str:

        if not self.openrouter_key:

            raise Exception(
                "OpenRouter key missing."
            )

        url = (
            "https://openrouter.ai/api/v1/chat/completions"
        )

        headers = {

            "Authorization":
                f"Bearer {self.openrouter_key}",

            "Content-Type":
                "application/json"
        }

        payload = {

            "model":
                "openchat/openchat-7b:free",

            "messages": [

                {
                    "role": "system",

                    "content":
                        system_instruction
                },

                {
                    "role": "user",

                    "content":
                        prompt
                }
            ]
        }

        response = await self.client.post(
            url,
            json=payload,
            headers=headers
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    # =========================================================
    # HUGGINGFACE
    # =========================================================

    async def call_huggingface(
        self,
        prompt: str
    ) -> str:

        if not self.hf_token:

            raise Exception(
                "HF token missing."
            )

        url = (
            "https://api-inference.huggingface.co/models/"
            "mistralai/Mistral-7B-Instruct-v0.2"
        )

        headers = {

            "Authorization":
                f"Bearer {self.hf_token}"
        }

        payload = {

            "inputs": prompt
        }

        response = await self.client.post(
            url,
            json=payload,
            headers=headers
        )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):

            return data[0].get(
                "generated_text",
                ""
            )

        return str(data)

    # =========================================================
    # FAILOVER ROUTER
    # =========================================================

    async def execute_failover_chain(
        self,
        prompt: str,
        system_instruction: str
    ) -> Dict[str, Any]:

        # Route 1
        try:

            result = await self.call_gemini(
                prompt,
                system_instruction
            )

            return {

                "success": True,

                "engine":
                    "Gemini",

                "output":
                    result
            }

        except Exception as e:

            print(
                f"[Gemini Failed] {e}"
            )

        # Route 2
        try:

            result = await self.call_groq(
                prompt,
                system_instruction
            )

            return {

                "success": True,

                "engine":
                    "Groq",

                "output":
                    result
            }

        except Exception as e:

            print(
                f"[Groq Failed] {e}"
            )

        # Route 3
        try:

            result = await self.call_openrouter(
                prompt,
                system_instruction
            )

            return {

                "success": True,

                "engine":
                    "OpenRouter",

                "output":
                    result
            }

        except Exception as e:

            print(
                f"[OpenRouter Failed] {e}"
            )

        # Route 4
        try:

            result = await self.call_huggingface(
                prompt
            )

            return {

                "success": True,

                "engine":
                    "HuggingFace",

                "output":
                    result
            }

        except Exception as e:

            print(
                f"[HF Failed] {e}"
            )

        return {

            "success": False,

            "engine":
                "Recovery Layer",

            "output":
                (
                    "Effiong AI could not "
                    "reach any model provider."
                )
        }

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    def model_availability(self):

        return {

            "gemini":
                bool(self.gemini_key),

            "groq":
                bool(self.groq_key),

            "openrouter":
                bool(self.openrouter_key),

            "huggingface":
                bool(self.hf_token)
        }

    # =========================================================
    # CLEANUP
    # =========================================================

    async def shutdown(self):

        await self.client.aclose()