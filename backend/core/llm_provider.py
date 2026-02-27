"""
LLM Provider Abstraction Layer
Supports: OpenAI (default), Gemini (future), Claude (future)
Switch via LLM_PROVIDER env var.
"""
from __future__ import annotations

import os
import json
from abc import ABC, abstractmethod
from typing import Any
import structlog
from dotenv import load_dotenv

# Load .env file explicitly — must happen before any os.getenv() calls
load_dotenv(override=True)

log = structlog.get_logger()


class LLMResponse:
    def __init__(self, content: str, model: str, usage: dict | None = None):
        self.content = content
        self.model = model
        self.usage = usage or {}

    def parse_json(self) -> Any:
        """Parse response as JSON, stripping markdown fences if needed."""
        text = self.content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        return json.loads(text)


class BaseLLMProvider(ABC):
    """Abstract base — implement this to add a new LLM provider."""

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


# ─────────────────────────────────────────────
# OpenAI Provider (Active)
# ─────────────────────────────────────────────
class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", "gpt-4o")

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        msg = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        }
        return LLMResponse(content=msg, model=self.model, usage=usage)


# ─────────────────────────────────────────────
# Google Gemini Provider (Stub — ready to enable)
# ─────────────────────────────────────────────
class GeminiProvider(BaseLLMProvider):
    """
    Enable: pip install google-generativeai
    Set:    LLM_PROVIDER=gemini  GEMINI_API_KEY=...
    """
    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.model = genai.GenerativeModel(
                os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
            )
            self._model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        except ImportError:
            raise RuntimeError(
                "google-generativeai not installed. Run: pip install google-generativeai"
            )

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        import asyncio
        prompt = f"{system_prompt}\n\n{user_message}\n\nRespond ONLY with valid JSON."
        generation_config = {"temperature": temperature, "max_output_tokens": max_tokens}
        response = await asyncio.to_thread(
            self.model.generate_content, prompt, generation_config=generation_config
        )
        return LLMResponse(content=response.text, model=self._model_name)


# ─────────────────────────────────────────────
# Anthropic Claude Provider (Stub — ready to enable)
# ─────────────────────────────────────────────
class ClaudeProvider(BaseLLMProvider):
    """
    Enable: pip install anthropic
    Set:    LLM_PROVIDER=claude  ANTHROPIC_API_KEY=...
    """
    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            self._model_name = os.getenv("CLAUDE_MODEL", "claude-opus-4-6")
        except ImportError:
            raise RuntimeError(
                "anthropic not installed. Run: pip install anthropic"
            )

    @property
    def provider_name(self) -> str:
        return "claude"

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        response = await self.client.messages.create(
            model=self._model_name,
            max_tokens=max_tokens,
            system=system_prompt + "\n\nAlways respond with valid JSON only.",
            messages=[{"role": "user", "content": user_message}],
            temperature=temperature,
        )
        return LLMResponse(
            content=response.content[0].text,
            model=self._model_name,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
        )


# ─────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────
_provider_instance: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    """Return singleton LLM provider based on LLM_PROVIDER env var."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    log.info("llm_provider_init", provider=provider)

    if provider == "openai":
        _provider_instance = OpenAIProvider()
    elif provider == "gemini":
        _provider_instance = GeminiProvider()
    elif provider == "claude":
        _provider_instance = ClaudeProvider()
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. Use: openai | gemini | claude"
        )

    return _provider_instance
