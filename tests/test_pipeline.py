from __future__ import annotations

from pathlib import Path

from PIL import Image

from engine.job import Job
from engine.parts import index_job, window_paths
from engine.pipeline import PipelineHarness
from engine.llm import FakeLLM


def png(path: Path) -> None:
    Image.new("RGB", (16, 16), "white").save(path)


def test_window_not_whole_corpus(tmp_path, monkeypatch):
    monkeypatch.setenv("BASE_DATA", str(tmp_path / "jobs"))
    job = Job.create(model="local/fake")
    for i in range(1, 7):
        png(job.dir / "source" / f"page-{i:02d}.png")
    plan = index_job(job)
    assert len(plan["units"]) == 6
    paths = window_paths(job, "u2")
    assert len(paths) == 3  # k=1 → before, focus, after
    assert len(paths) < 6


def test_pipeline_fake(tmp_path, monkeypatch):
    monkeypatch.setenv("BASE_DATA", str(tmp_path / "jobs"))
    job = Job.create(model="local/fake")
    png(job.dir / "source" / "page-01.png")
    h = PipelineHarness(FakeLLM())
    st = "continue"
    for _ in range(20):
        st = h.tick(job)
        job = Job.load(job.id)
        if st != "continue":
            break
    assert st == "done"
    assert job.stage == "done"
    assert (job.dir / "out" / "Q1_Sample.md").is_file()
    assert (job.dir / "out" / "Chapter_Error_Report.md").is_file()
    assert "- [x] Extract" in job.memory()
