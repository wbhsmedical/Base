"""Pull files out of OpenAI/OpenWebUI messages. Resume marker is an HTML comment."""

from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Any

JOB_RE = re.compile(r"<!--job:([a-f0-9]{12})-->")


def text_of(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        bits = []
        for p in content:
            if isinstance(p, dict) and p.get("type") == "text":
                bits.append(p.get("text") or "")
            elif isinstance(p, str):
                bits.append(p)
        return "\n".join(bits)
    return str(content)


def job_id_from(messages: list) -> str | None:
    for m in messages:
        found = JOB_RE.search(text_of(m.get("content")))
        if found:
            return found.group(1)
    return None


def files_from(messages: list) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    n = 0
    for m in messages:
        c = m.get("content")
        if not isinstance(c, list):
            continue
        for p in c:
            if not isinstance(p, dict):
                continue
            if p.get("type") == "image_url":
                url = p.get("image_url")
                url = url.get("url") if isinstance(url, dict) else url
                n += 1
                out.append(_data_url(url, f"page-{n:02d}.png"))
            elif p.get("type") == "file":
                f = p.get("file") or {}
                data = f.get("file_data") or f.get("data") or ""
                name = f.get("filename") or f"file-{n}"
                n += 1
                out.append(_data_url(data, name))
    return [(a, b) for a, b in out if b]


def _data_url(url: str | None, fallback: str) -> tuple[str, bytes]:
    if not url:
        return fallback, b""
    if not url.startswith("data:"):
        return fallback, b""
    header, _, b64 = url.partition(",")
    ext = ".png"
    if "pdf" in header:
        ext = ".pdf"
    elif "jpeg" in header or "jpg" in header:
        ext = ".jpg"
    elif "png" in header:
        ext = ".png"
    elif "webp" in header:
        ext = ".webp"
    stem = Path(fallback).stem
    name = stem + ext
    try:
        return name, base64.b64decode(b64)
    except Exception:
        return name, b""
