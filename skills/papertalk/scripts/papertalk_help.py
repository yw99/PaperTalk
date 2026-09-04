#!/usr/bin/env python3
"""Print PaperTalk's fixed public help output."""

from __future__ import annotations

import sys
from pathlib import Path


HELP_OUTPUT = Path(__file__).resolve().parents[1] / "references" / "help-output.md"


def main() -> int:
    sys.stdout.write(HELP_OUTPUT.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
