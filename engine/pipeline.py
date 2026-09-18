"""Supervisor → orchestrator → one-Q worker. Fresh complete() per tick."""

from __future__ import annotations

import json
from pathlib import Path

from engine import planfile
from engine.job import Job, check_plan
from engine.llm import LLM
from engine.parts import file_part, index_job, load as load_plan, window_parts, window_paths
from engine.qa import check_output

SURVEY = """You survey ONE focus page (neighbors are cut-off context only).
Reply with markdown task blocks only, matching:
- [ ] **Q18** — Title
  - units: [u0]
  - output: Q18_Title.md
  - known_issues: ...
  - status: pending
Use the given focus unit id. If no question on the focus page, reply NONE.
"""

EXTRACT = """You extract exactly ONE question from the attached pages.
Write markdown with:
# Qn. Title
## Answer
## Corrections
## Integrated Margin
No TODO/TBD. Facts from the pages only.
"""

REVIEW = """Spot-check the extracted files against the plan. Write Chapter_Error_Report.md style markdown.
"""


class PipelineHarness:
    def __init__(self, llm: LLM):
        self.llm = llm

    def tick(self, job: Job) -> str:
        job = Job.load(job.id)
        if job.paused:
            job.stage = "paused"
            job.save()
            return "paused"
        if job.pending_question:
            job.stage = "waiting_clarify"
            job.save()
            return "waiting"

        try:
            if not (job.dir / "demarcation" / "plan.json").is_file():
                return self._demarcate(job)
            surveyed = _surveyed(job)
            plan = load_plan(job.dir / "demarcation")
            if len(surveyed) < len(plan["units"]):
                return self._survey_one(job, plan, surveyed)
            tasks = planfile.load(job.plan_md())
            pending = [t for t in tasks if t["status"] == "pending"]
            if pending:
                return self._extract_one(job, plan, tasks, pending[0])
            if not (job.dir / "out" / "Chapter_Error_Report.md").is_file():
                return self._review(job, tasks)
            check_plan(job, "Review")
            job.stage = "done"
            job.error = None
            job.save()
            return "done"
        except Exception as e:
            return self._fail_or_retry(job, str(e))

    def _demarcate(self, job: Job) -> str:
        pl = index_job(job)
        if not pl["units"]:
            raise ValueError("no pages to index — attach images or a PDF in OpenWebUI")
        check_plan(job, "Ingest source")
        check_plan(job, "Demarcate")
        job.append_memory(f"\n- demarcation units={len(pl['units'])} cuts={len(pl['cuts'])}")
        job.save()
        return "continue"

    def _survey_one(self, job: Job, plan: dict, surveyed: list[str]) -> str:
        uid = next(u["id"] for u in plan["units"] if u["id"] not in surveyed)
        parts = window_parts(job, uid)
        user = f"PHASE=survey\nfocus={uid}\nneighbors are context only.\n"
        text = self.llm.complete(model=job.model, system=SURVEY, user=user, parts=parts)
        if text.strip() and text.strip() != "NONE":
            old = planfile.load(job.plan_md())
            new = planfile.parse(text)
            # Default unit to focus if the model omitted it.
            for t in new:
                if not t["units"] and not t["pages"]:
                    t["units"] = [uid]
            planfile.save(job.plan_md(), old + new)
            job.append_memory(f"\n- survey {uid}: +{len(new)} task(s)")
        else:
            job.append_memory(f"\n- survey {uid}: none")
        surveyed.append(uid)
        _save_surveyed(job, surveyed)
        if len(surveyed) >= len(plan["units"]):
            check_plan(job, "Survey")
        job.save()
        return "continue"

    def _extract_one(self, job: Job, plan: dict, tasks: list[dict], task: dict) -> str:
        task["status"] = "in_progress"
        planfile.save(job.plan_md(), tasks)
        uids = planfile.units_for(plan["units"], task) or [plan["units"][0]["id"]]
        # One window per unit, but never more than the union of those windows' files.
        seen: set[Path] = set()
        parts = []
        for uid in uids:
            for p in window_paths(job, uid):
                if p not in seen:
                    seen.add(p)
                    parts.append(file_part(p))
        user = (
            f"PHASE=extract\n{task['id']} {task['title']}\n"
            f"known_issues: {task.get('known_issues')}\n"
            f"output: {task.get('output')}\n"
        )
        text = self.llm.complete(model=job.model, system=EXTRACT, user=user, parts=parts)
        name = task.get("output") or f"{task['id'].replace(' ', '_')}.md"
        dest = job.path("out", name)
        dest.write_text(text, encoding="utf-8")
        err = check_output(dest)
        if err and job.retries < job.max_retries:
            job.retries += 1
            job.append_memory(f"\n- extract {task['id']} retry: {err}")
            dest.unlink(missing_ok=True)
            task["status"] = "pending"
            planfile.save(job.plan_md(), tasks)
            job.save()
            return "continue"
        if err:
            task["status"] = "failed"
            job.append_memory(f"\n- extract {task['id']} failed: {err}")
        else:
            task["status"] = "done"
            job.retries = 0
            job.append_memory(f"\n- extract {task['id']} → {name}")
        planfile.save(job.plan_md(), tasks)
        if all(t["status"] in ("done", "failed") for t in tasks):
            check_plan(job, "Extract")
        job.save()
        return "continue"

    def _review(self, job: Job, tasks: list[dict]) -> str:
        listing = []
        for t in tasks:
            p = job.path("out", t.get("output") or "")
            listing.append(f"{t['id']} status={t['status']} file={p.name if p.is_file() else 'missing'}")
        user = "PHASE=review\n" + "\n".join(listing)
        text = self.llm.complete(model=job.model, system=REVIEW, user=user, parts=None)
        job.path("out", "Chapter_Error_Report.md").write_text(text, encoding="utf-8")
        job.append_memory("\n- review written")
        job.save()
        return "continue"

    def _fail_or_retry(self, job: Job, err: str) -> str:
        job.retries += 1
        job.append_memory(f"\n- error: {err}")
        if job.retries >= job.max_retries:
            job.stage = "failed"
            job.error = err
            job.save()
            return "failed"
        job.stage = "running"
        job.error = err
        job.save()
        return "continue"


def _surveyed(job: Job) -> list[str]:
    p = job.dir / "demarcation" / "surveyed.json"
    if not p.is_file():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def _save_surveyed(job: Job, ids: list[str]) -> None:
    p = job.dir / "demarcation" / "surveyed.json"
    p.write_text(json.dumps(ids), encoding="utf-8")
