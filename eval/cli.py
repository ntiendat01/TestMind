"""Eval entrypoint. The dataset runner arrives in M2."""

from __future__ import annotations

import sys


def main() -> int:
    print("eval: no dataset is wired yet (M2). Nothing to score.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
