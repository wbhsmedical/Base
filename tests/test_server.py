from __future__ import annotations

import json
import threading
from http.client import HTTPConnection

import pytest

from server import Handler, ThreadingHTTPServer


@pytest.fixture
def httpd(monkeypatch):
    monkeypatch.setenv("GATEWAY_FAKE", "1")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.shutdown()


def _conn(httpd) -> HTTPConnection:
    c = HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=10)
    return c


def test_models(httpd):
    c = _conn(httpd)
    c.request("GET", "/v1/models")
    r = c.getresponse()
    body = json.loads(r.read())
    ids = {m["id"] for m in body["data"]}
    assert "pipeline/extract" in ids
    assert "local/fake" in ids


def test_fake_chat(httpd):
    c = _conn(httpd)
    c.request(
        "POST",
        "/v1/chat/completions",
        json.dumps({"model": "local/fake", "messages": [{"role": "user", "content": "hi"}], "stream": False}),
        {"Content-Type": "application/json"},
    )
    r = c.getresponse()
    body = json.loads(r.read())
    assert body["choices"][0]["message"]["content"] == "ok"


def test_pipeline_via_api(httpd, tmp_path, monkeypatch):
    monkeypatch.setenv("BASE_DATA", str(tmp_path / "jobs"))
    from PIL import Image
    import base64
    import io

    buf = io.BytesIO()
    Image.new("RGB", (16, 16), "white").save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    msg = {
        "role": "user",
        "content": [
            {"type": "text", "text": "extract"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ],
    }
    c = _conn(httpd)
    c.request(
        "POST",
        "/v1/chat/completions",
        json.dumps({"model": "pipeline/extract", "messages": [msg], "stream": False}),
        {"Content-Type": "application/json"},
    )
    r = c.getresponse()
    body = json.loads(r.read())
    text = body["choices"][0]["message"]["content"]
    assert "<!--job:" in text
    assert "status: done" in text
    assert "Q1" in text
