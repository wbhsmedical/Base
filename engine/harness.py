"""PPTX loop harness. Same tick() contract as PipelineHarness."""

from __future__ import annotations

import json
from dataclasses import dataclass

from engine.job import Job, check_plan
from engine.llm import LLM
from engine.parts import file_part, index_job, window_parts
from engine.pptx_tools import build
from engine.qa import check_pptx

SYSTEM = """You convert the given source into a short presentable PowerPoint.
Reply with ONE JSON object only, no other keys:
  {"action":"write_script","backend":"python"|"js","script":"..."}
  {"action":"switch_backend","backend":"python"|"js"}
  {"action":"ask_user","question":"..."}
Rules:
- If audience, length, branding, or missing content is unclear: ask_user. Do not invent facts not in the source.
- python script: use python-pptx. Save with prs.save(os.environ["PPTX_OUT"]).
- js script: use pptxgenjs (require("pptxgenjs")). Write with pptx.writeFile({fileName: process.env.PPTX_OUT}).
- No lorem, no TODO, no empty slides. 16:9. Real titles and bullets from the source.
- Prefer python unless you need js.
"""


@dataclass
class Action:
    kind: str  # write_script | switch_backend | ask_user
    backend: str | None = None
    script: str | None = None
    question: str | None = None
    raw: str = ""


def parse_action(text: str) -> Action:
    blob = _json_blob(text)
    if not blob:
        raise ValueError("no JSON object in model output")
    data = json.loads(blob)
    kind = data.get("action")
    if kind == "ask_user":
        q = (data.get("question") or "").strip()
        if not q:
            raise ValueError("ask_user missing question")
        return Action("ask_user", question=q, raw=text)
    if kind == "switch_backend":
        b = data.get("backend")
        if b not in ("python", "js"):
            raise ValueError("switch_backend needs backend python|js")
        return Action("switch_backend", backend=b, raw=text)
    if kind == "write_script":
        b = data.get("backend") or "python"
        if b not in ("python", "js"):
            raise ValueError("write_script backend python|js")
        script = data.get("script")
        if not script or not str(script).strip():
            raise ValueError("write_script missing script")
        return Action("write_script", backend=b, script=str(script), raw=text)
    raise ValueError(f"unknown action {kind!r}")


def _json_blob(text: str) -> str | None:
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                t = p
                break
    i = t.find("{")
    if i < 0:
        return None
    depth = 0
    for j, ch in enumerate(t[i:], i):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return t[i : j + 1]
    return None


class LoopHarness:
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
        if job.stage in ("done", "failed"):
            return job.stage
        if not (job.dir / "demarcation" / "plan.json").is_file() and job.ingest:
            try:
                index_job(job)
                check_plan(job, "Ingest source")
            except Exception:
                pass

        user = (
            f"backend={job.backend}\nretries={job.retries}/{job.max_retries}\n"
            f"source={job.source_name}\ningest={job.ingest}\n\n"
            f"memory.md:\n{job.memory()}\n\n"
            "Produce the next action JSON."
        )
        try:
            act = parse_action(
                self.llm.complete(model=job.model, system=SYSTEM, user=user, parts=_parts(job))
            )
        except Exception as e:
            return self._fail_or_retry(job, f"llm error: {e}")

        if act.kind == "ask_user":
            job.pending_question = act.question
            job.stage = "waiting_clarify"
            job.append_memory(f"\n- asked: {act.question}")
            job.save()
            return "waiting"

        if act.kind == "switch_backend":
            job.backend = act.backend or job.backend
            job.append_memory(f"\n- backend → {job.backend}")
            job.save()
            return "continue"

        return self._write(job, act)

    def _write(self, job: Job, act: Action) -> str:
        if act.backend:
            job.backend = act.backend
        check_plan(job, "Draft slides")
        try:
            path, log = build(job, act.script or "")
        except Exception as e:
            return self._fail_or_retry(job, f"build error: {e}")
        job.append_memory(f"\n- build ok ({path.name})\n```\n{log[-1500:]}\n```")
        check_plan(job, "Build pptx")
        err = check_pptx(path)
        if err:
            return self._fail_or_retry(job, f"qa: {err}")
        check_plan(job, "QA")
        job.stage = "done"
        job.error = None
        job.save()
        return "done"

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


def _parts(job: Job):
    demarc = job.dir / "demarcation" / "plan.json"
    if demarc.is_file():
        plan = json.loads(demarc.read_text(encoding="utf-8"))
        units = plan.get("units") or []
        if units:
            return window_parts(job, units[0]["id"])
    files = (job.ingest or {}).get("files") or []
    out = []
    for rel in files:
        p = job.path(rel)
        if p.is_file():
            out.append(file_part(p))
    return out
