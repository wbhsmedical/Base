"""implementation_plan.md — human-readable, regex-extractable. This is the DB."""

from __future__ import annotations

import re
from pathlib import Path

HEAD = re.compile(r"^- \[([ xX!])\] \*\*(.+?)\*\*(?: — | - |: )?(.*)$")


def parse(md: str) -> list[dict]:
    tasks: list[dict] = []
    cur = None
    for line in md.splitlines():
        m = HEAD.match(line)
        if m:
            if cur:
                tasks.append(cur)
            mark = m.group(1)
            status = {" ": "pending", "x": "done", "X": "done", "!": "failed"}[mark]
            cur = {
                "id": m.group(2).strip(),
                "title": m.group(3).strip(),
                "pages": [],
                "units": [],
                "output": "",
                "known_issues": "",
                "status": status,
            }
            continue
        if not cur:
            continue
        if "pages:" in line:
            cur["pages"] = [int(x) for x in re.findall(r"\d+", line.split("pages", 1)[1])]
        elif "units:" in line:
            cur["units"] = re.findall(r"u\d+", line)
        elif "output:" in line:
            cur["output"] = line.split(":", 1)[1].strip().strip("`'\"")
        elif "known_issues:" in line:
            cur["known_issues"] = line.split(":", 1)[1].strip()
        elif "status:" in line:
            v = line.split(":", 1)[1].strip()
            if v:
                cur["status"] = v
    if cur:
        tasks.append(cur)
    return tasks


def dump(tasks: list[dict]) -> str:
    lines = ["# implementation_plan\n"]
    for t in tasks:
        mark = {"pending": " ", "in_progress": " ", "done": "x", "failed": "!"}.get(t["status"], " ")
        title = t.get("title") or ""
        lines.append(f"- [{mark}] **{t['id']}** — {title}")
        if t.get("units"):
            lines.append(f"  - units: [{', '.join(t['units'])}]")
        if t.get("pages"):
            lines.append(f"  - pages: {t['pages']}")
        if t.get("output"):
            lines.append(f"  - output: {t['output']}")
        if t.get("known_issues"):
            lines.append(f"  - known_issues: {t['known_issues']}")
        lines.append(f"  - status: {t['status']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return parse(path.read_text(encoding="utf-8"))


def save(path: Path, tasks: list[dict]) -> None:
    path.write_text(dump(tasks), encoding="utf-8")


def units_for(plan_units: list[dict], task: dict) -> list[str]:
    if task.get("units"):
        return list(task["units"])
    want = set(task.get("pages") or [])
    ids = []
    for u in plan_units:
        nums = re.findall(r"\d+", Path(u["uri"]).stem)
        if nums and int(nums[-1]) in want:
            ids.append(u["id"])
    return ids
