#!/usr/bin/env python3
"""OpenAI-compatible gateway. OpenWebUI is the client. Key stays here."""

from __future__ import annotations

import json
import os
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from engine.ingest import prepare_many
from engine.job import Job, check_plan
from engine.llm import PIPELINE_ID, PPTX_ID, openai_models, stream_chat
from engine.messages import JOB_RE, files_from, job_id_from, text_of
from engine.registry import make_harness, make_llm

MAX_TICKS = 200


def sse_chunk(cid: str, piece: str, done: bool = False) -> bytes:
    delta = {} if done else {"content": piece}
    obj = {
        "id": cid,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": PIPELINE_ID,
        "choices": [{"index": 0, "delta": delta, "finish_reason": "stop" if done else None}],
    }
    return f"data: {json.dumps(obj)}\n\n".encode()


def complete_obj(cid: str, model: str, text: str) -> dict:
    return {
        "id": cid,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print("[http]", fmt % args)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/health", "/"):
            return self._json(200, {"ok": True, "ui": "openwebui"})
        if u.path in ("/v1/models", "/models"):
            return self._json(200, openai_models())
        parts = u.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] in ("v1", "api") and parts[1] == "jobs":
            return self._jobs_get(parts[2:])
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        parts = u.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] in ("v1", "api") and parts[1] == "jobs":
            return self._jobs_post(parts[2:])
        if u.path not in ("/v1/chat/completions", "/chat/completions"):
            return self._json(404, {"error": "not found"})
        body = self._read_json()
        model = body.get("model") or ""
        stream = bool(body.get("stream"))
        messages = body.get("messages") or []
        cid = "chatcmpl-" + uuid.uuid4().hex[:12]
        if model == PIPELINE_ID or model == PPTX_ID or model.startswith("pipeline/"):
            return self._pipeline(cid, body, messages, stream, model)
        return self._chat(cid, body, model, messages, stream)

    def _chat(self, cid: str, body: dict, model: str, messages: list, stream: bool):
        if os.environ.get("GATEWAY_FAKE") or model == "local/fake":
            text = make_llm(model=model).complete(
                model=model,
                system="",
                user=text_of(messages[-1].get("content") if messages else ""),
                parts=None,
            )
            if stream:
                return self._sse([sse_chunk(cid, text), sse_chunk(cid, "", done=True), b"data: [DONE]\n\n"])
            return self._json(200, complete_obj(cid, model, text))
        extra = {k: body[k] for k in ("temperature", "max_tokens", "top_p") if k in body}
        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                for line in stream_chat(model, messages, extra):
                    self.wfile.write(line)
                    self.wfile.flush()
            except Exception as e:
                self.wfile.write(sse_chunk(cid, f"\n[gateway error] {e}"))
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            return
        from engine.llm import one_shot

        text = one_shot(model, messages, extra)
        return self._json(200, complete_obj(cid, model, text))

    def _pipeline(self, cid: str, body: dict, messages: list, stream: bool, model: str):
        pptx = model == PPTX_ID or model.endswith("/pptx")
        harness = "loop" if pptx else "pipeline"
        job_id = job_id_from(messages)
        files = files_from(messages)
        if job_id:
            try:
                job = Job.load(job_id)
            except FileNotFoundError:
                job = Job.create(
                    model=body.get("worker_model") or os.environ.get("PIPELINE_MODEL", "local/fake"),
                    harness=harness,
                )
        else:
            worker = body.get("worker_model") or os.environ.get("PIPELINE_MODEL") or (
                "local/fake"
                if os.environ.get("GATEWAY_FAKE")
                else os.environ.get("OPENROUTER_FAVORITES", "deepseek/deepseek-chat").split(",")[0]
            )
            job = Job.create(model=worker.strip(), source_name="upload", harness=harness)
        if files:
            job.ingest = prepare_many(job.dir, files)
            check_plan(job, "Ingest source")
            job.save()
        if job.pending_question:
            ans = JOB_RE.sub("", text_of(messages[-1].get("content") if messages else "")).strip()
            if ans:
                job.append_memory(f"\nUser answer: {ans}")
                job.pending_question = None
                job.paused = False
                job.stage = "running"
                job.save()
        chunks: list[str] = []

        def emit(s: str):
            chunks.append(s)
            if stream:
                self.wfile.write(sse_chunk(cid, s))
                self.wfile.flush()

        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

        h = make_harness(job)
        st = "continue"
        for _ in range(MAX_TICKS):
            before = job.memory()
            st = h.tick(job)
            job = Job.load(job.id)
            after = job.memory()
            if after != before:
                emit(after[len(before) :])
            if st != "continue":
                break
        emit(f"\n<!--job:{job.id}-->\nstatus: {st}\n")
        if job.pending_question:
            emit(f"question: {job.pending_question}\n")
        if job.plan_md().is_file():
            emit("\n" + job.plan_md().read_text(encoding="utf-8")[:4000])
        deck = job.path("out", "deck.pptx")
        if deck.is_file():
            emit(f"\ndeck: /v1/jobs/{job.id}/download\n")
        if stream:
            self.wfile.write(sse_chunk(cid, "", done=True))
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            return
        return self._json(200, complete_obj(cid, model or PIPELINE_ID, "".join(chunks)))

    def _jobs_get(self, rest: list[str]):
        if not rest:
            return self._json(404, {"error": "not found"})
        job = self._job(rest[0])
        if not job:
            return
        if len(rest) == 1:
            return self._json(200, job.public())
        if rest[1] == "download":
            path = job.path("out", "deck.pptx")
            if not path.is_file() or job.stage != "done":
                return self._json(404, {"error": "deck not ready"})
            data = path.read_bytes()
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
            self.send_header("Content-Disposition", f'attachment; filename="{job.id}.pptx"')
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return
        return self._json(404, {"error": "not found"})

    def _jobs_post(self, rest: list[str]):
        if len(rest) != 2:
            return self._json(404, {"error": "not found"})
        job = self._job(rest[0])
        if not job:
            return
        op = rest[1]
        if op == "pause":
            job.paused = True
            job.stage = "paused"
            job.save()
            return self._json(200, job.public())
        if op == "resume":
            if job.stage == "done":
                return self._json(400, {"error": "already done"})
            job.paused = False
            if job.pending_question:
                job.stage = "waiting_clarify"
            else:
                job.stage = "running"
            job.save()
            return self._json(200, Job.load(job.id).public())
        if op == "answer":
            body = self._read_json()
            text = (body.get("text") or "").strip()
            if not text:
                return self._json(400, {"error": "empty answer"})
            if not job.pending_question:
                return self._json(400, {"error": "no pending question"})
            job.append_memory(f"\nUser answer: {text}")
            job.pending_question = None
            job.paused = False
            job.stage = "running"
            job.save()
            return self._json(200, Job.load(job.id).public())
        return self._json(404, {"error": "not found"})

    def _job(self, job_id: str):
        try:
            return Job.load(job_id)
        except FileNotFoundError:
            self._json(404, {"error": "unknown job"})
            return None

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        return json.loads(self.rfile.read(n).decode())

    def _json(self, code: int, obj: dict) -> None:
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b)

    def _sse(self, parts: list[bytes]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        for p in parts:
            self.wfile.write(p)
        self.wfile.flush()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"gateway on http://{host}:{port}  (OpenWebUI → /v1)", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
