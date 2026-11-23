"""Embedders and LLM clients that do not touch the network."""

from __future__ import annotations

import json
import re

from app.clients.llm import LLMCompletion


class TaggedEmbedder:
    model_name = "tagged"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            if "3.2" in text or "điều kiện" in lowered:
                vectors.append([1.0, 0.0, *([0.0] * 1022)])
            else:
                vectors.append([0.0, 1.0, *([0.0] * 1022)])
        return vectors


class ScriptedLLM:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, *, system: str, user: str) -> LLMCompletion:
        del system
        self.calls += 1
        chunk_id = _refund_source(user)
        payload = {
            "insufficient_evidence": False,
            "answer": "Khách được hoàn tiền trong 7 ngày.",
            "claims": [{"text": "Khách được hoàn tiền trong 7 ngày.", "chunk_ids": [chunk_id]}],
            "notes": "",
        }
        return LLMCompletion(content=json.dumps(payload), tokens_in=3, tokens_out=4)


class BrokenLLM:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, *, system: str, user: str) -> LLMCompletion:
        del system, user
        self.calls += 1
        if self.calls == 1:
            return LLMCompletion(content="not-json", tokens_in=1, tokens_out=1)
        payload = {
            "insufficient_evidence": False,
            "answer": "ok",
            "claims": [{"text": "ok", "chunk_ids": ["missing"]}],
            "notes": "",
        }
        return LLMCompletion(content=json.dumps(payload), tokens_in=1, tokens_out=1)


def _refund_source(user: str) -> str:
    for match in re.finditer(r'<source id="([^"]+)">([\s\S]*?)</source>', user):
        if "hoàn" in match.group(2).lower():
            return match.group(1)
    return "missing"
