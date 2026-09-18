"""Structural gates. Extract markdown vs PPTX package — pick the one that matches the harness."""

from __future__ import annotations

import re
import zipfile
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


def check_pptx(path: Path) -> str | None:
    """Return None if ok, else a short error."""
    if not path.is_file() or path.stat().st_size < 64:
        return "missing or tiny pptx"
    try:
        z = zipfile.ZipFile(path)
        z.testzip()
    except zipfile.BadZipFile:
        return "not a zip/pptx"
    names = z.namelist()
    if "[Content_Types].xml" not in names:
        return "not a pptx package"
    slides = sorted(n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    if not slides:
        return "no slides"
    for name in slides:
        xml = z.read(name).decode("utf-8", "replace")
        texts = re.findall(r"<a:t[^>]*>([^<]*)</a:t>", xml)
        joined = " ".join(t.strip() for t in texts if t.strip())
        low = joined.lower()
        if "lorem" in low or "todo" in low:
            return f"placeholder text on {name}"
        has_pic = "<p:pic" in xml or "<a:blip" in xml
        if not joined and not has_pic:
            return f"empty slide {name}"
    return None
