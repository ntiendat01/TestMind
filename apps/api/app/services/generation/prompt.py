"""Load the versioned answer prompt and render sources."""

from __future__ import annotations

from pathlib import Path

from app.schemas.records import SearchHit

_DELIMITER = "</source>"


def load_prompt(path: Path) -> tuple[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    version = "answer.vi.1"
    body = lines
    if lines and lines[0].startswith("prompt_version:"):
        version = lines[0].split(":", 1)[1].strip()
        body = lines[1:]
    return version, "\n".join(body).strip()


def render_user_prompt(question: str, hits: list[SearchHit]) -> str:
    sources = "\n".join(_source_block(hit) for hit in hits)
    return f"Câu hỏi:\n{question}\n\nNguồn:\n{sources}"


def _source_block(hit: SearchHit) -> str:
    path = " > ".join(hit.chunk.section_path)
    body = hit.chunk.text.replace(_DELIMITER, "< /source>")
    return f'<source id="{hit.chunk.id}">\n{path}\n{body}\n</source>'
