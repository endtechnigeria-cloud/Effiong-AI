from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import base64
import httpx
import os  # ← Fixed: Missing import added
from datetime import datetime
import logging

from ..core.orchestrator import AIModelOrchestrator
from ..core.memory import VectorMemory

router = APIRouter()

orchestrator = AIModelOrchestrator(
    gemini_key=os.getenv("GEMINI_API_KEY"),
    tavily_key=os.getenv("TAVILY_API_KEY"),
    groq_key=os.getenv("GROQ_API_KEY")
)

logger = logging.getLogger(__name__)

# Pydantic Models
class ChatRequest(BaseModel):
    prompt: str
    history: List[Dict] = []

class HeritageRequest(BaseModel):
    contributor: str = ""
    type: str
    record: str
    consent: bool = False

class ChatResponse(BaseModel):
    response: str
    core: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None

# Background GitHub Archive
async def archive_to_github(content: str):
    try:
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPO")
        if not token or not repo or not content:
            return

        file_path = "effiong_brain_ledger.txt"
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            sha = ""
            current_text = ""
            if res.status_code == 200:
                file_data = res.json()
                sha = file_data.get("sha", "")
                current_text = base64.b64decode(file_data["content"]).decode("utf-8")

            timestamp = datetime.now().isoformat()
            updated_text = current_text + f"\n\n[Event {timestamp}]\n{content[:800]}"

            encoded = base64.b64encode(updated_text.encode("utf-8")).decode("utf-8")
            payload = {
                "message": "⚡ Effiong AI Sovereign Update",
                "content": encoded,
                "branch": "main"
            }
            if sha:
                payload["sha"] = sha

            await client.put(url, headers=headers, json=payload)
    except Exception as e:
        logger.error(f"GitHub archive failed: {e}")


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    try:
        result = await orchestrator.process(
            prompt=request.prompt,
            history=request.history
        )

        # Generate voice synthesis
        audio_url = None
        if os.getenv("GEMINI_API_KEY"):
            try:
                audio_url = await orchestrator.generate_speech(result["response"])
            except Exception as e:
                logger.warning(f"TTS failed: {e}")

        # Archive conversation
        background_tasks.add_task(
            archive_to_github,
            f"User: {request.prompt}\nEffiong: {result['response'][:500]}"
        )

        return ChatResponse(
            response=result["response"],
            core=result["core"],
            image_url=result.get("image_url"),
            video_url=result.get("video_url"),
            audio_url=audio_url
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Sovereign neural core temporarily unavailable")


@router.post("/api/heritage")
async def submit_heritage(request: HeritageRequest, background_tasks: BackgroundTasks):
    if not request.record:
        raise HTTPException(status_code=400, detail="Record data is required")

    try:
        commit_payload = f"""
Contributor: {request.contributor or 'Anonymous'}
Type: {request.type}
Record: {request.record}
Consent: {request.consent}
        """

        VectorMemory().add(commit_payload, {
            "type": "heritage",
            "contributor": request.contributor,
            "timestamp": datetime.now().isoformat()
        })

        if request.consent:
            background_tasks.add_task(archive_to_github, commit_payload)

        return {"status": "success", "message": "Heritage record archived in sovereign memory"}

    except Exception as e:
        logger.error(f"Heritage submission failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive heritage record")


@router.get("/api/health")
async def health():
    return {"status": "healthy", "version": "5.1.1", "core": "EFFIONG Sovereign Intelligence"}
