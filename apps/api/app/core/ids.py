"""Deterministic ids and content hashes."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping


def new_id() -> str:
    return str(uuid.uuid4())


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_loc(loc: Mapping[str, int | str]) -> str:
    return json.dumps(dict(loc), sort_keys=True, separators=(",", ":"))


def make_chunk_id(version_id: str, loc: Mapping[str, int | str], ordinal: int) -> str:
    raw = f"{version_id}|{canonical_loc(loc)}|{ordinal}"
    return hashlib.sha1(raw.encode()).hexdigest()
