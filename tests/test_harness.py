from __future__ import annotations

import pytest

from engine.harness import LoopHarness, parse_action
from engine.job import Job
from engine.llm import FakeLLM
from engine.qa import check_pptx


@pytest.fixture
def job(tmp_path, monkeypatch):
    monkeypatch.setenv("BASE_DATA", str(tmp_path / "jobs"))
    return Job.create(model="local/fake", source_name="brief.pdf", harness="loop")


def test_parse_fenced():
    a = parse_action('sure\n```json\n{"action":"ask_user","question":"How many slides?"}\n```\n')
    assert a.kind == "ask_user"
    assert "slides" in a.question


def test_clarify_then_deck(job):
    h = LoopHarness(FakeLLM())
    assert h.tick(job) == "waiting"
    job = Job.load(job.id)
    assert job.pending_question
    job.append_memory("\nUser answer: exec team")
    job.pending_question = None
    job.stage = "running"
    job.save()
    assert h.tick(job) == "done"
    job = Job.load(job.id)
    assert job.stage == "done"
    assert check_pptx(job.path("out", "deck.pptx")) is None
    assert "- [x] QA" in job.memory()


def test_pause(job):
    job.paused = True
    job.save()
    h = LoopHarness(FakeLLM())
    assert h.tick(job) == "paused"
    job = Job.load(job.id)
    assert job.stage == "paused"
