"""Discover page files. A document is a folder, or a filename prefix at root."""

from __future__ import annotations

import re
from pathlib import Path

# Trailing page index: "slide-12", "p001". Used for doc id and name-seq cuts.
_NUM = re.compile(r"^(.*?)(\d+)$")
_DIGITS = re.compile(r"(\d+)")

DEFAULT_INCLUDE = ("**/*.png", "**/*.jpg", "**/*.jpeg", "**/*.webp", "**/*.gif", "**/*.tif", "**/*.tiff", "**/*.bmp")


def nkey(s: str) -> tuple:
    """Numeric path sort: page-2 before page-10."""
    parts = _DIGITS.split(s)
    return tuple(int(p) if p.isdigit() else p.lower() for p in parts)


def stem_doc(stem: str) -> str:
    m = _NUM.match(stem)
    if not m or not m.group(1):
        return stem
    return m.group(1).rstrip("-_. ") or stem


def page_num(stem: str) -> int | None:
    m = _NUM.match(stem)
    return int(m.group(2)) if m else None


def doc_of(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    if rel.parent.parts:
        return rel.parent.as_posix()
    return stem_doc(rel.stem)


def list_files(root: Path, include: tuple[str, ...] = DEFAULT_INCLUDE, exclude: tuple[str, ...] = ()) -> list[Path]:
    root = root.resolve()
    found: set[Path] = set()
    for pat in include:
        found.update(p for p in root.glob(pat) if p.is_file())
    for pat in exclude:
        found.difference_update(root.glob(pat))
    return sorted(found, key=lambda p: nkey(p.relative_to(root).as_posix()))


def units_from(root: Path, files: list[Path], kind: str = "page-image") -> list[dict]:
    """Assign id/doc/i/n in walk order. i resets when doc changes."""
    root = root.resolve()
    units: list[dict] = []
    last_doc: str | None = None
    i = 0
    for n, path in enumerate(files):
        doc = doc_of(root, path)
        i = 0 if doc != last_doc else i + 1
        last_doc = doc
        units.append(
            {
                "id": f"u{n}",
                "kind": kind,
                "uri": path.relative_to(root).as_posix(),
                "doc": doc,
                "i": i,
                "n": n,
            }
        )
    return units
