"""Multimodal parts. Windowed attach — never the whole corpus."""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path
from typing import Any

from engine.job import Job

_CD = Path(__file__).resolve().parent.parent / "context-demarcation"
if str(_CD) not in sys.path:
    sys.path.insert(0, str(_CD))

from core.plan import index, load, window_for  # noqa: E402

TEXT = {".txt", ".md", ".json", ".csv", ".tsv"}
MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def file_part(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    suf = path.suffix.lower()
    if suf == ".pdf":
        b64 = base64.b64encode(raw).decode("ascii")
        return {
            "type": "file",
            "file": {"filename": path.name, "file_data": f"data:application/pdf;base64,{b64}"},
        }
    if suf in TEXT:
        return {"type": "text", "text": f"SOURCE ({path.name}):\n{raw.decode('utf-8', 'replace')}"}
    b64 = base64.b64encode(raw).decode("ascii")
    mime = MIME.get(suf, "image/png")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def index_job(job: Job) -> dict:
    src = job.dir / "source"
    root = src if src.exists() and any(src.iterdir()) else job.dir
    k = int(os.environ.get("DEMARC_K", "1"))
    include = (
        "**/*.png",
        "**/*.jpg",
        "**/*.jpeg",
        "**/*.webp",
        "**/*.gif",
        "**/*.pdf",
        "**/*.txt",
        "**/*.md",
    )
    return index(root, job.dir / "demarcation", k=k, include=include, exclude=("input/**", "out/**", "demarcation/**"))


def window_paths(job: Job, uid: str) -> list[Path]:
    out = job.dir / "demarcation"
    plan = load(out)
    w = window_for(out, uid)
    ids = w["before"] + [w["focus"]] + w["after"]
    by = {u["id"]: u for u in plan["units"]}
    root = Path(plan["root"])
    paths = []
    for i in ids:
        p = root / by[i]["uri"]
        if p.is_file():
            paths.append(p)
    return paths


def window_parts(job: Job, uid: str) -> list[dict[str, Any]]:
    return [file_part(p) for p in window_paths(job, uid)]
