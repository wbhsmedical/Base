"""Job directory on disk. Resume = reload this, then tick."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    return Path(os.environ.get("BASE_DATA", ROOT / "data" / "jobs"))


@dataclass
class Job:
    id: str
    model: str
    harness: str = "pipeline"
    stage: str = "running"  # running | paused | waiting_clarify | done | failed
    paused: bool = False
    pending_question: str | None = None
    error: str | None = None
    retries: int = 0
    max_retries: int = 3
    source_name: str = "source"
    ingest: dict[str, Any] = field(default_factory=dict)
    created: float = field(default_factory=time.time)

    @property
    def dir(self) -> Path:
        return data_dir() / self.id

    def path(self, *parts: str) -> Path:
        return self.dir.joinpath(*parts)

    def save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "job.json").write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def memory(self) -> str:
        p = self.dir / "memory.md"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def append_memory(self, text: str) -> None:
        p = self.dir / "memory.md"
        with p.open("a", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n")

    def plan_md(self) -> Path:
        return self.dir / "implementation_plan.md"

    def public(self) -> dict[str, Any]:
        d = asdict(self)
        d["memory"] = self.memory()
        return d

    @classmethod
    def load(cls, job_id: str) -> Job:
        raw = json.loads((data_dir() / job_id / "job.json").read_text(encoding="utf-8"))
        return cls(**raw)

    @classmethod
    def create(cls, **kw: Any) -> Job:
        data_dir().mkdir(parents=True, exist_ok=True)
        job = cls(id=uuid.uuid4().hex[:12], **kw)
        job.dir.mkdir(parents=True, exist_ok=True)
        for name in ("work", "out", "source", "input"):
            (job.dir / name).mkdir(exist_ok=True)
        (job.dir / "memory.md").write_text(
            "# Plan\n"
            "- [ ] Ingest source\n"
            "- [ ] Demarcate\n"
            "- [ ] Survey\n"
            "- [ ] Extract\n"
            "- [ ] Review\n\n"
            "# Log\n",
            encoding="utf-8",
        )
        job.save()
        return job


def check_plan(job: Job, item: str) -> None:
    md = job.memory()
    old = f"- [ ] {item}"
    new = f"- [x] {item}"
    if old in md:
        (job.dir / "memory.md").write_text(md.replace(old, new, 1), encoding="utf-8")
