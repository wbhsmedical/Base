"""Harness plugins. Same tick() contract; swap later for DSH."""

from __future__ import annotations

import os

from engine.job import Job
from engine.llm import FakeLLM, LLM, OpenRouterLLM
from engine.pipeline import PipelineHarness


def make_llm(job: Job | None = None, model: str | None = None) -> LLM:
    mid = model or (job.model if job else "")
    if os.environ.get("GATEWAY_FAKE") or mid == "local/fake":
        return FakeLLM()
    return OpenRouterLLM()


def make_harness(job: Job) -> PipelineHarness:
    return PipelineHarness(make_llm(job))
