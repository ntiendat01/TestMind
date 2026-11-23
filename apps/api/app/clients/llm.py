"""DeepSeek through the W&B Inference OpenAI-compatible API."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from app.core.errors import APIError


@dataclass
class LLMCompletion:
    content: str
    tokens_in: int
    tokens_out: int


class InferenceLLMClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        max_tokens: int,
        timeout: float,
        http: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._http = http or httpx.Client(timeout=timeout)

    def complete(self, *, system: str, user: str) -> LLMCompletion:
        if not self._api_key:
            raise APIError(503, "llm_not_configured", "Set LLM_API_KEY.")
        response = self._http.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "temperature": 0,
                "max_tokens": self._max_tokens,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        if response.status_code >= 400:
            raise APIError(
                502,
                "llm_unavailable",
                f"Inference API returned HTTP {response.status_code}.",
            )
        payload = response.json()
        usage = payload.get("usage") or {}
        content = str(payload["choices"][0]["message"]["content"])
        return LLMCompletion(
            content=content,
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
        )
