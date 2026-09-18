"""Two PPTX backends. LLM writes a script; we exec it. Same return: out path."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from engine.job import ROOT, Job

NODE_MODULES = ROOT / "node_modules"


def build(job: Job, script: str) -> tuple[Path, str]:
    """Write script for job.backend, run it, return (pptx_path, combined_output)."""
    work = job.path("work")
    work.mkdir(parents=True, exist_ok=True)
    out = job.path("out", "deck.pptx")
    if out.exists():
        out.unlink()
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "PPTX_OUT": str(out),
        "NODE_PATH": str(NODE_MODULES),
    }
    if job.backend == "js":
        path = work / "build.js"
        path.write_text(script, encoding="utf-8")
        cmd = ["node", str(path)]
    else:
        path = work / "build.py"
        path.write_text(script, encoding="utf-8")
        cmd = [sys.executable, str(path)]
    r = subprocess.run(cmd, cwd=str(work), env=env, capture_output=True, text=True, timeout=90)
    log = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise RuntimeError(f"script exit {r.returncode}\n{log}")
    if not out.is_file():
        found = list(work.glob("*.pptx")) + list(job.path("out").glob("*.pptx"))
        if not found:
            raise RuntimeError("script produced no pptx\n" + log)
        shutil.copy(found[0], out)
    return out, log
