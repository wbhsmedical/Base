# Base

OpenWebUI in front. Python gateway + jobs behind. OpenRouter is the only model API.

```bash
pip install -r requirements.txt
cp .env.example .env   # set OPENROUTER_API_KEY
python3 -m pytest -q
python3 server.py      # :8000
docker compose up      # OpenWebUI :8080 → gateway /v1
```

In OpenWebUI: connection is already `http://gateway:8000/v1`. Pick any listed model to chat. Pick `pipeline/extract` and attach page images for the scoped worker loop.

Plan: [TODO.md](TODO.md).
