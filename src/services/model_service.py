"""Backwards-compatible alias: the multi-tier LLM engine now lives in llm_providers.py."""
from src.services.llm_providers import BRAIN, REGISTRY, PROFILES, AllProvidersFailed, ProviderError, LLMResponse  # noqa: F401

model_service = BRAIN  # legacy name some modules imported
