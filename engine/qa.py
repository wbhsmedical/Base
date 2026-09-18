"""Structural gate for one worker file. Content truth is the supervisor's job."""

from __future__ import annotations

import re
from pathlib import Path

REQUIRED = (
    (r"^# Q\d+", "heading"),
    (r"^## Answer", "Answer"),
    (r"^## Corrections", "Corrections"),
    (r"^## Integrated Margin", "Integrated Margin"),
)
BAD = re.compile(r"\b(TODO|TBD|\[insert\])\b", re.I)


def check_output(path: Path) -> str | None:
    if not path.is_file() or path.stat().st_size < 40:
        return "missing or tiny output"
    text = path.read_text(encoding="utf-8")
    if BAD.search(text):
        return "placeholder text"
    for pat, name in REQUIRED:
        if not re.search(pat, text, re.M):
            return f"missing {name}"
    return None
