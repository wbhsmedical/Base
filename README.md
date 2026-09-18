# Base

Personal MMLM stack: **OpenWebUI** in front, a **Python OpenRouter gateway** behind it, jobs and plans as **files on disk**.

Colleagues chat on `:8080`. Gateway (`:8000/v1`) holds the API key. Pick a live model for chat, `pipeline/pptx` for decks, or `pipeline/extract` for windowed one-question work. Never dump the whole corpus into one turn.

Map of apps, engines, modules (Conversion / Demarcation / LCM), tools, and contracts: **[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md)**. What to build next: **[TODO.md](TODO.md)**.

```bash
cp .env.example .env   # set OPENROUTER_API_KEY
docker compose up --build
# OpenWebUI :8080   gateway :8000/health
pip install -r requirements.txt && python3 -m pytest -q
```

## AI agents

1. **Code.** Small functions, one obvious loop. Comments may be long. Code must stay short — handwritten gold, not verbose slop.
2. **One tree.** Work on `main` (or a short-lived PR branch). Read [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) and [TODO.md](TODO.md) before adding a package, engine, or UI. Do not resurrect a sidecar `engine/` or a second chat SPA.
3. **Modular / lean.** Compose existing plugins and disk contracts (`tick()`, ingest, demarcation windows, gateway `/v1`, DSH wrappers). Future Conversion and LCM are separate plugins — do not bury them in Demarcation or clone a second algorithm in TypeScript.
