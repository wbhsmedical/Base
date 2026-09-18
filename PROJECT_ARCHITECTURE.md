# Project Architecture

Locked from the original conversations (PPTX V0/V1, Context Demarcation, Plan D / OpenWebUI). Status is **now** vs **later**. Do not invent a fourth copy of an owned seam.

Code taste (every conversation): small functions, one obvious loop. Comments may be long. Code must stay short — handwritten gold, not verbose slop.

---

## Apps & their software stacking

### General-purpose chat

Browser → **OpenWebUI** (`:8080`, compose image `ghcr.io/open-webui/open-webui`) → **Python gateway** `server.py` (`:8000`, `/v1`) → **OpenRouter**.

| Layer | Owns | Does not own |
|---|---|---|
| **OpenWebUI** | login, chat, model picker, upload, sharing, colleague accounts | jobs, plans, `OPENROUTER_API_KEY`, DSH runtime |
| **Gateway** | `/v1/models`, `/v1/chat/completions` (SSE), job pause/answer/download | HTML / a second SPA |
| **OpenRouter** | any natively multimodal MLLM (Image + PDF, context > 100K) | UI |

Ollama is off. The API key never leaves the gateway process. Chat mode: stream through; optional image/PDF parts; **no tools required today**.

This is the only UI. The old PPTX one-page SPA is gone on purpose (colleagues + OpenWebUI features).

### PPTX generation

Same OpenWebUI + same gateway. Pick model **`pipeline/pptx`**. Backend is the Python **loop harness**, not a second app.

Upload in chat → ingest → (optional) demarcation windows → LLM JSON actions (`ask_user` / `switch_backend` / `write_script`) → **python-pptx** or **pptxgenjs** → QA → `out/deck.pptx` at `/v1/jobs/<id>/download`.

V0 target from the original spec: one small PDF, native LLM ingest, no extra input management, presentable deck after basic QA, pause/resume from disk, clarify instead of inventing facts.

V1 target: any input format; non-native files become scanned page images; markdown planner + memory.

Favorites the user personally checked for multimodality and PPT: **Claude Opus 5**, **GLM 5.3**, **Kimi K3** (`anthropic/claude-opus-5`, `z-ai/glm-5.3`, `moonshotai/kimi-k3`). Chat can still list live OpenRouter ids.

---

## Explicit pipelines / core engines

One gateway, several `tick()` plugins. Disk jobs: `data/jobs/<id>/`. Resume = reread that directory. Crash-safe. Harness is a plugin (`engine/registry.py`) so DeepSeek Harness / Claude Skills / AutoClaw can replace the loop later — **same `tick()` contract**.

### 1. Python PPTX (`pipeline/pptx`) — the only generation engine for now

`engine/harness.py` `LoopHarness`. Stage loop (not a page-analysis loop): persist → LLM → tool script → QA.

- Dual backends: **python-pptx** (prefer) and **pptxgenjs** (models differ). `job.backend = python | js`. Model may `switch_backend`.
- Actions are one JSON object only (see Contracts).
- `memory.md` checkboxes: Ingest → Draft slides → Build pptx → QA.
- Clarify: `ask_user` → `waiting_clarify` → user answer in chat or `POST /v1/jobs/<id>/answer`.
- Windowed attach when `demarcation/plan.json` exists; never dump the whole corpus as a habit.

### 2. OpenWebUI chat + basic tools (`/` live models)

Pass-through chat. OpenWebUI talks to our `/v1` like OpenAI. **Basic tools later** (OpenWebUI tool calling / a thin gateway tool set). Not a second agent runtime. Not DSH.

### 3. Extract / one-Q pipeline (`pipeline/extract`)

Ceiling from the attached MMLM proposal (38 Q&As × 40 pages): context exhaustion, error snowball, state drift. Automate the mechanical loop.

1. Ingest upload → page files.
2. Demarcation → windows (`k=1` default; neighbors are cut-off context only).
3. Supervisor writes `implementation_plan.md` (human or auto-approve).
4. Orchestrator: each `[ ]` → **fresh** worker, scoped pages only → structural QA → `[x]` / `[!]`.
5. Supervisor review → `Chapter_Error_Report.md`.

Worker sees 2–3 pages, never 40. One question per `complete()`. One retry then flag.

### 4. DeepSeek Harness (later)

Modular host for **multiple projects**. Not the UI. Same JSON on disk. Thin TypeScript/Cordis skin around the Python core. Point DSH’s OpenAI base at this gateway `/v1`. No second algorithm.

---

## Modules

Three plugins, not one. Indexing ≠ conversion ≠ analysis. Do not bury Demarcation inside LCM. Do not re-walk the tree in TypeScript.

Python owns the algorithm (PPTX engine is Python; **one implementation**). TypeScript is the Harness **skin** only.

### 1. Input format conversion (later plugin)

PDF / PPTX / DOCX / … → **ordered page files** (images now). Owns rasterize / `pptxtoimages`-class tools. Does not own cuts, windows, or model calls.

Today a thin copy lives in `engine/ingest.py` (native PDF/text/image; zip-XML + Pillow “scan” for office-ish). Do not grow a second converter inside Demarcation. Fail closed in Demarcation v1 if the tree is still a raw PDF/PPTX — point at Conversion.

### 2. Context Demarcation (now)

`context-demarcation/core/` — walk → units → windows → cuts → JSON. Indexing loop even with no LLM.

- v1 units: `page-image`. Text / code later (same schema; LCM must not care if a unit is a PNG or a function).
- Windows may **cross documents** (spillover is the point). Host scores **focus**.
- v1 cuts: cheap hypotheses only — `file` / `folder` / `name-seq`. Later: `blank`, `phash`, optional MMLM enricher. Never a hard fact.
- DSH tools (thin): `demarcation_index`, `demarcation_get_window`, `demarcation_get_plan`. No custom `agent-loop`. No Cordis import in the core.

### 3. Long context management (later)

Consumes a plan: 1-focus-per-turn, improvised LLMxMapReduce, REPL, resume, retries. Does not discover units. Can replace the extract/`tick` analysis loop without changing `plan.json`.

---

## Extra tools

Keep adding here. Do not fork a tool into a second engine.

| Tool | Role |
|---|---|
| **OpenRouter gateway** | `server.py` `/v1`; key in env; stream + `one_shot` + native file-parser PDF plugin |
| **python-pptx** | Default PPTX backend; script saves `os.environ["PPTX_OUT"]` |
| **pptxgenjs** | JS PPTX backend; `pptx.writeFile({ fileName: process.env.PPTX_OUT })` |
| **Pillow** | Page-image rasterize for non-native ingest |
| **pdftoppm** (optional) | PDF → page PNGs when present; else native PDF part |
| **pptxtoimages** (later) | Conversion plugin — not Demarcation |
| **DSH / Cordis** | Optional in-process bus when the process *is* Harness (`dsh/cordis.patch.yml`) |
| **OpenWebUI tools** (later) | Basic tools on the chat path |

---

## Contracts

**JSON / files on disk are the compatibility layer.** Hosts do not share a runtime. PPTX must not import Cordis. Chat context is not the corpus.

### Demarcation

```
plan.schema.json     # v: 1; bump when fields change
plan.json            # { v, root, k, kind, units[], cuts[] }
windows.jsonl        # one Window per line (do not load 10k as one array)
```

Job path: `data/jobs/<id>/demarcation/`.

**Unit** — `id`, `kind`, `uri`, `doc`, `i` (in doc), `n` (global).

**Window** — `focus`, `before[]`, `after[]`. Default `k=1`.

**Cut** — `{ at, kind, prev }`. Hypothesis.

**JSON vs Cordis:** not competitors. JSON = source of truth (crash/resume, other languages, thousands of pages). Cordis = `inject` / `ctx.tools` only at the DSH edge. “None at all” (stuffing every page into `_file_parts`) is the bug Demarcation exists to stop.

### Jobs

```
data/jobs/<id>/
  job.json
  memory.md                 # checkboxes + log
  implementation_plan.md    # extract pipeline SoT
  input/  source/  work/  out/
  demarcation/plan.json + windows.jsonl
  out/deck.pptx             # PPTX
  out/Q##_Title.md          # extract
```

Pause/resume = this directory.

### Extract plan / worker files

`implementation_plan.md` is the checkpoint DB. Task: `Q#`, `pages[]` / `units[]`, output filename, `known_issues`, `status ∈ {pending, in_progress, done, failed}` with `[ ]` / `[x]` / `[!]`.

Worker markdown: heading `^# Q\d+`, `## Answer`, `## Corrections`, `## Integrated Margin`. No `TODO` / `TBD` / `[insert]`.

### PPTX LLM action

```json
{"action":"write_script","backend":"python"|"js","script":"..."}
{"action":"switch_backend","backend":"python"|"js"}
{"action":"ask_user","question":"..."}
```

### Harness swap

`tick(job) → continue | paused | waiting | done | failed`. Add `"deepseek"` / `"claude_skills"` / `"autoclaw"` in `registry.py` later — do not copy `engine/`.

### HTTP (gateway)

OpenAI: `GET /v1/models`, `POST /v1/chat/completions`.

Jobs: `GET /v1/jobs/:id`, `POST .../pause|resume|answer`, `GET .../download`.

---

## What not to do

- A second chat SPA competing with OpenWebUI.
- Dumping 40 pages into one session.
- Merging PPTX + demarcation + extract into one harness (plugins + files).
- Migrating the PPTX loop to TypeScript.
- Implementing DSH or LCM before the chat + `tick()` hosts are enough.
- Duplicating Conversion inside Demarcation or Demarcation inside LCM.
