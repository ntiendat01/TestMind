"""Forge client request shape."""

import json

import httpx
from app.clients.llm import InferenceLLMClient


def test_posts_chat_completion_to_wandb_inference() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 3},
            },
        )

    client = InferenceLLMClient(
        base_url="https://api.inference.wandb.ai/v1",
        api_key="test-key",
        model="deepseek-ai/DeepSeek-V4.1-Flash-1017",
        max_tokens=80,
        timeout=5,
        http=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.complete(system="sys", user="user")
    body = seen["body"]
    assert isinstance(body, dict)
    assert seen["url"] == "https://api.inference.wandb.ai/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    assert body["model"] == "deepseek-ai/DeepSeek-V4.1-Flash-1017"
    assert body["temperature"] == 0
    assert "tools" not in body
    assert result.tokens_in == 2
