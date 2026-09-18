"""OpenRouter: live model list, one-shot complete, SSE stream. Key never leaves the process."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Iterator

OPENROUTER = "https://openrouter.ai/api/v1"
CHAT = OPENROUTER + "/chat/completions"
MODELS = OPENROUTER + "/models"
PIPELINE_ID = "pipeline/extract"


def _headers() -> dict[str, str]:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    h = {
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "http://localhost:8080"),
        "X-Title": os.environ.get("OPENROUTER_TITLE", "base-gateway"),
    }
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def _urlopen(req: urllib.request.Request, timeout: int = 180):
    return urllib.request.urlopen(req, timeout=timeout)


def favorites() -> list[str]:
    raw = os.environ.get("OPENROUTER_FAVORITES", "deepseek/deepseek-chat,google/gemini-2.0-flash-001")
    return [x.strip() for x in raw.split(",") if x.strip()]


def list_models() -> list[dict[str, str]]:
    """OpenAI-style rows. pipeline/extract is ours; the rest are OpenRouter ids."""
    rows = [{"id": PIPELINE_ID, "label": "Pipeline extract"}]
    if os.environ.get("GATEWAY_FAKE"):
        rows.append({"id": "local/fake", "label": "Fake (tests)"})
        for mid in favorites():
            rows.append({"id": mid, "label": mid})
        return rows
    try:
        req = urllib.request.Request(os.environ.get("OPENROUTER_MODELS_URL", MODELS), headers=_headers())
        with _urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
        for m in payload.get("data") or []:
            mid = m.get("id")
            if mid:
                rows.append({"id": mid, "label": m.get("name") or mid})
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        for mid in favorites():
            rows.append({"id": mid, "label": mid})
    return rows


def openai_models() -> dict:
    return {
        "object": "list",
        "data": [
            {"id": r["id"], "object": "model", "created": 0, "owned_by": "openrouter" if r["id"] != PIPELINE_ID else "base"}
            for r in list_models()
        ],
    }


def one_shot(model: str, messages: list, extra: dict | None = None) -> str:
    body = {"model": model, "messages": messages, "stream": False}
    if extra:
        body.update(extra)
    req = urllib.request.Request(
        os.environ.get("OPENROUTER_URL", CHAT),
        data=json.dumps(body).encode(),
        headers=_headers(),
        method="POST",
    )
    with _urlopen(req) as resp:
        payload = json.loads(resp.read().decode())
    text = payload["choices"][0]["message"]["content"]
    if isinstance(text, list):
        text = "".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in text)
    return text or ""


class LLM:
    def complete(self, *, model: str, system: str, user: str, parts: list[dict[str, Any]] | None = None) -> str:
        raise NotImplementedError


class OpenRouterLLM(LLM):
    def complete(self, *, model: str, system: str, user: str, parts: list[dict[str, Any]] | None = None) -> str:
        content: list[dict[str, Any]] = [{"type": "text", "text": user}]
        content.extend(parts or [])
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            "plugins": [{"id": "file-parser", "pdf": {"engine": "native"}}],
        }
        req = urllib.request.Request(
            os.environ.get("OPENROUTER_URL", CHAT),
            data=json.dumps(body).encode(),
            headers=_headers(),
            method="POST",
        )
        with _urlopen(req) as resp:
            payload = json.loads(resp.read().decode())
        text = payload["choices"][0]["message"]["content"]
        if isinstance(text, list):
            text = "".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in text)
        return text or ""


def stream_chat(model: str, messages: list, extra: dict | None = None) -> Iterator[bytes]:
    """Pipe OpenRouter SSE through. Caller writes bytes to the client."""
    body = {"model": model, "messages": messages, "stream": True}
    if extra:
        for k, v in extra.items():
            if k not in ("model", "messages", "stream") and v is not None:
                body[k] = v
    req = urllib.request.Request(
        os.environ.get("OPENROUTER_URL", CHAT),
        data=json.dumps(body).encode(),
        headers=_headers(),
        method="POST",
    )
    with _urlopen(req, timeout=300) as resp:
        while True:
            line = resp.readline()
            if not line:
                break
            yield line


class FakeLLM(LLM):
    def complete(self, *, model: str, system: str, user: str, parts: list[dict[str, Any]] | None = None) -> str:
        if "PHASE=survey" in user:
            return (
                "- [ ] **Q1** — Sample question\n"
                "  - units: [u0]\n"
                "  - output: Q1_Sample.md\n"
                "  - known_issues: none\n"
                "  - status: pending\n"
            )
        if "PHASE=extract" in user:
            return (
                "# Q1. Sample question\n\n"
                "## Answer\nFrom the page.\n\n"
                "## Corrections\nNone.\n\n"
                "## Integrated Margin\nNone.\n"
            )
        if "PHASE=review" in user:
            return "# Chapter_Error_Report\n\nNo issues in fake run.\n"
        return "ok"
