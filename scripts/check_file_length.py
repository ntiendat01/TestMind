"""Fail when a source file exceeds the repository line limit."""

from __future__ import annotations

import sys
from pathlib import Path

LIMIT = 500
HEADER_LINES = 20
SKIP_DIRS = {
    ".git",
    ".next",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "venv",
}
LOCKFILES = {
    "Cargo.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "uv.lock",
    "yarn.lock",
}
TEXT_SUFFIXES = {
    ".css",
    ".ini",
    ".js",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".rs",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
BARE_NAMES = {"Dockerfile", "Makefile"}


def is_generated(path: Path) -> bool:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return False
    head = "\n".join(lines[:HEADER_LINES])
    return "AUTO-GENERATED" in head


def should_count(path: Path) -> bool:
    if path.name in LOCKFILES:
        return False
    if path.name in BARE_NAMES or path.suffix in TEXT_SUFFIXES:
        return not is_generated(path)
    return False


def line_count(path: Path) -> int | None:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except (OSError, UnicodeError):
        return None


def scan(root: Path) -> list[tuple[Path, int]]:
    offenders: list[tuple[Path, int]] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or not should_count(path):
            continue
        count = line_count(path)
        if count is not None and count > LIMIT:
            offenders.append((path, count))
    return offenders


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    offenders = scan(root)
    if not offenders:
        print(f"file length ok (<= {LIMIT} lines)")
        return 0
    for path, count in offenders:
        print(f"{path.relative_to(root)}: {count} lines")
    return 1


if __name__ == "__main__":
    sys.exit(main())
