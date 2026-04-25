import json
import logging
from typing import Any, Optional
from openai import AsyncOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """Wrapper around OpenAI API for all LLM calls in Vital AI."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model

    async def chat_completion(
        self,
        system_prompt: str,
        user_message: str,
        json_mode: bool = False,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Send a chat completion request and return the response text."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def chat_completion_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> dict:
        """Send a chat completion request and parse JSON response."""
        raw = await self.chat_completion(
            system_prompt=system_prompt,
            user_message=user_message,
            json_mode=True,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM JSON response: %s", raw)
            return {}

    async def chat_with_history(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        json_mode: bool = False,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Send a multi-turn chat completion with message history."""
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def chat_with_history_json(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> dict:
        """Multi-turn chat completion that returns parsed JSON."""
        raw = await self.chat_with_history(
            system_prompt=system_prompt,
            messages=messages,
            json_mode=True,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM JSON response: %s", raw)
            return {}


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
