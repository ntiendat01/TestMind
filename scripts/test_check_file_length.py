"""Tests for the file-length gate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_file_length import LIMIT, scan  # noqa: E402


def test_flags_file_past_limit(tmp_path: Path) -> None:
    target = tmp_path / "big.py"
    target.write_text("\n".join(["x"] * (LIMIT + 1)), encoding="utf-8")
    found = scan(tmp_path)
    assert [item[0].name for item in found] == ["big.py"]


def test_skips_lockfile_and_generated(tmp_path: Path) -> None:
    lock = tmp_path / "uv.lock"
    lock.write_text("\n".join(["x"] * (LIMIT + 5)), encoding="utf-8")
    generated = tmp_path / "schema.ts"
    header = "/* AUTO-GENERATED. Do not edit. */\n"
    generated.write_text(header + "\n".join(["x"] * (LIMIT + 5)), encoding="utf-8")
    assert scan(tmp_path) == []
