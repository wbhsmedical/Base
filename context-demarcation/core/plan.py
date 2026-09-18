"""plan.json + windows.jsonl.

Indexing is a glob + one pass — cheap next to any model call.
Checkpoint writes a prefix plan so a kill leaves a readable artifact.
Resume: if uris already match the tree, keep the plan and refresh windows.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import cuts as cuts_mod
from . import walk, window as win

V = 1
PLAN_NAME = "plan.json"
WINDOWS_NAME = "windows.jsonl"


def dump(out: Path, plan: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / PLAN_NAME).write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")


def write_windows(out: Path, units: list[dict], k: int) -> None:
    lines = [json.dumps(win.around(units, u["n"], k), separators=(",", ":")) for u in units]
    (out / WINDOWS_NAME).write_text("\n".join(lines) + ("\n" if units else ""), encoding="utf-8")


def load(out: Path) -> dict:
    return json.loads((out / PLAN_NAME).read_text(encoding="utf-8"))


def index(
    root: Path,
    out: Path,
    *,
    k: int = 1,
    kind: str = "page-image",
    include: tuple[str, ...] | None = None,
    exclude: tuple[str, ...] = (),
    cut_kinds: tuple[str, ...] = ("file", "folder", "name-seq"),
    checkpoint: int = 200,
    resume: bool = True,
) -> dict:
    root = root.resolve()
    files = walk.list_files(root, include or walk.DEFAULT_INCLUDE, exclude)
    uris = [f.relative_to(root).as_posix() for f in files]
    if resume and (out / PLAN_NAME).is_file():
        old = load(out)
        if old.get("v") == V and old.get("k") == k and old.get("kind") == kind:
            if [u["uri"] for u in old.get("units", [])] == uris:
                write_windows(out, old["units"], k)
                return old

    units = walk.units_from(root, files, kind)
    if checkpoint:
        for n in range(checkpoint, len(units), checkpoint):
            dump(out, _plan(root, units[:n], k, kind, cut_kinds))
    plan = _plan(root, units, k, kind, cut_kinds)
    dump(out, plan)
    write_windows(out, units, k)
    return plan


def _plan(root: Path, units: list[dict], k: int, kind: str, cut_kinds: tuple[str, ...]) -> dict:
    return {
        "v": V,
        "root": str(root),
        "k": k,
        "kind": kind,
        "units": units,
        "cuts": cuts_mod.detect(units, cut_kinds),
    }


def window_for(out: Path, uid: str) -> dict:
    plan = load(out)
    return win.by_id(plan["units"], uid, plan.get("k", 1))
