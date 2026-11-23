"""Take the highest-scoring hits that fit the token budget."""

from __future__ import annotations

from app.core.interfaces import TokenCounter
from app.schemas.records import SearchHit


def build_context(hits: list[SearchHit], budget: int, counter: TokenCounter) -> list[SearchHit]:
    chosen: list[SearchHit] = []
    used = 0
    for hit in hits:
        cost = max(1, counter.count(hit.chunk.text))
        if chosen and used + cost > budget:
            break
        chosen.append(hit)
        used += cost
    return chosen
