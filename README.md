# Base

OpenWebUI in front. Python gateway + jobs behind. OpenRouter is the only model API.

Still unmerged (do not duplicate): **[UNMERGED.md](UNMERGED.md)**.

| Branch | One line |
|---|---|
| [`cursor/v0-v1-todos-6a38`](https://github.com/wbhsmedical/Base/tree/cursor/v0-v1-todos-6a38) | PPTX pipeline |
| [`cursor/context-demarcation-todo-efe3`](https://github.com/wbhsmedical/Base/tree/cursor/context-demarcation-todo-efe3) | Context demarcation |

## AI agents

1. **Code.** Small functions, one obvious loop. Comments may be long. Code must stay short — handwritten gold, not verbose slop.
2. **Branches.** Read [UNMERGED.md](UNMERGED.md) before you add a package, engine, or UI. New long-lived work gets a row there in the same change. Do not reimplement an owned seam off a silent copy of `main`.
3. **Modular.** Plugins, tools, and disk contracts already exist (`tick()`, ingest, demarcation windows, gateway `/v1`, DSH wrappers). Future projects compose those. Lean: do not clone a second engine.

```bash
pip install -r requirements.txt
cp .env.example .env   # set OPENROUTER_API_KEY
python3 -m pytest -q
python3 server.py      # :8000
docker compose up      # OpenWebUI :8080 → gateway /v1
```

In OpenWebUI: connection is already `http://gateway:8000/v1`. Pick any listed model to chat. Pick `pipeline/extract` and attach page images for the scoped worker loop.

Plan: [TODO.md](TODO.md).
