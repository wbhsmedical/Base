"""CLI for hosts that should not import Python (DeepSeek Harness, shell)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import plan as P


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="demarcation")
    sub = p.add_subparsers(dest="cmd", required=True)

    ix = sub.add_parser("index", help="walk root → plan.json + windows.jsonl")
    ix.add_argument("root")
    ix.add_argument("-o", "--out", required=True)
    ix.add_argument("-k", type=int, default=1)
    ix.add_argument("--kind", default="page-image")
    ix.add_argument("--include", action="append", default=None)
    ix.add_argument("--exclude", action="append", default=[])
    ix.add_argument("--checkpoint", type=int, default=200)
    ix.add_argument("--no-resume", action="store_true")

    w = sub.add_parser("window", help="one window from an existing plan")
    w.add_argument("out")
    w.add_argument("--id", required=True)

    g = sub.add_parser("plan", help="print plan.json")
    g.add_argument("out")

    a = p.parse_args(argv)
    if a.cmd == "index":
        pl = P.index(
            Path(a.root),
            Path(a.out),
            k=a.k,
            kind=a.kind,
            include=tuple(a.include) if a.include else None,
            exclude=tuple(a.exclude),
            checkpoint=a.checkpoint,
            resume=not a.no_resume,
        )
        print(json.dumps({"units": len(pl["units"]), "cuts": len(pl["cuts"])}))
        return 0
    if a.cmd == "window":
        print(json.dumps(P.window_for(Path(a.out), a.id)))
        return 0
    print((Path(a.out) / P.PLAN_NAME).read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
