# Base

OpenWebUI in front. Python gateway behind it (`/v1`). Jobs on disk.

```bash
docker compose up --build
# OpenWebUI :8080  gateway :8000/health
```

| Piece | What it is |
|---|---|
| **OpenWebUI** | The only UI. Pick chat, `pipeline/extract`, or `pipeline/pptx`. |
| **Gateway** | `server.py` — `/v1/models`, `/v1/chat/completions`, job pause/answer/download. |
| **Extract** | `engine/pipeline.py` — ingest → demarcation windows → survey → one-Q workers → review. |
| **PPTX** | `engine/harness.py` — ingest → windowed source → `ask_user` / python-pptx or pptxgenjs → QA. |
| **Demarcation** | `context-demarcation/` — `plan.json` + `windows.jsonl`. Never attach the whole corpus. |

Set `OPENROUTER_API_KEY`. Favorites default to Opus 5, GLM 5.3, Kimi K3, plus DeepSeek/Gemini.

## AI agents

1. **Code.** Small functions, one obvious loop. Comments may be long. Code must stay short.
2. **One tree.** Work on `main` (or a short-lived PR branch). Do not resurrect `engine/` on a sidecar branch.
3. **Plugins.** `tick()` harnesses, ingest, windows, gateway `/v1`, DSH wrappers. Compose those. Do not clone a second engine or a second chat SPA.
