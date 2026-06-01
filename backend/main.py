from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

from .api.routes import router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("effiong_ai")

app = FastAPI(
    title="EFFIONG AI Sovereign Backend",
    description="Multi-Neural Sovereign Intelligence Platform",
    version="5.1"
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
