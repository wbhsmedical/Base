"""Cheap boundary hypotheses. Never treat these as ground truth."""

from __future__ import annotations

from pathlib import Path

from .walk import page_num


def _folder(doc: str) -> str:
    p = Path(doc)
    return "" if p.parent == Path(".") else p.parent.as_posix()


def detect(units: list[dict], enabled: tuple[str, ...] = ("file", "folder", "name-seq")) -> list[dict]:
    cuts: list[dict] = []
    for prev, cur in zip(units, units[1:]):
        kinds: list[str] = []
        if "file" in enabled and prev["doc"] != cur["doc"]:
            kinds.append("file")
        if "folder" in enabled and _folder(prev["doc"]) != _folder(cur["doc"]):
            kinds.append("folder")
        if "name-seq" in enabled and prev["doc"] == cur["doc"]:
            a = page_num(Path(prev["uri"]).stem)
            b = page_num(Path(cur["uri"]).stem)
            if a is not None and b is not None and b != a + 1:
                kinds.append("name-seq")
        for kind in kinds:
            cuts.append({"at": cur["id"], "kind": kind, "prev": prev["id"]})
    return cuts
