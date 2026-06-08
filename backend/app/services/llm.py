from __future__ import annotations

import json

import httpx

from app.core.config import settings


class LLMProviderError(RuntimeError):
    pass


def openai_enabled(provider: str) -> bool:
    return provider.lower() in {"openai", "openai-compatible"} and bool(settings.openai_api_key)


def chat_completion(system: str, user: str) -> str:
    if not settings.openai_api_key:
        raise LLMProviderError("OPENAI_API_KEY is not configured")
    payload = {
        "model": settings.openai_chat_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": settings.llm_temperature,
        "max_tokens": settings.max_output_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMProviderError("OpenAI-compatible provider request failed") from exc
    data = response.json()
    return str(data["choices"][0]["message"]["content"]).strip()


def extract_json_object(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMProviderError("Provider response did not contain a JSON object")
    return json.loads(stripped[start : end + 1])
