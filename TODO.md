# TODO

Source of truth for **what to build next**. Locked splits and stacking live in [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md). This file keeps the original conversation details so they are not lost after branches were deleted.

Code taste: small functions, one obvious loop. Comments may be long. Code must stay short — handwritten gold, not verbose slop.

---

## Locked (do not reopen)

- **UI is OpenWebUI only.** Colleagues included. Everything else is Python behind an OpenAI-compatible gateway. No second SPA.
- **OpenRouter** for any MLLM (native Image + PDF, context > 100K). Key stays on the server. Claude-only client is out.
- **JSON/files on disk** are the compatibility layer. Cordis only at the DeepSeek Harness edge. PPTX does not import Cordis.
- **Three modules, not one:** Conversion | Demarcation | LCM. Indexing loop in Demarcation; analysis loop in LCM (or today’s `tick()`); Conversion strictly upstream.
- **Python = algorithm** (ingest, demarcation core, PPTX loop). **TypeScript = DSH skin.** Do not migrate the PPTX harness to TypeScript.
- Harness is a **plugin**. Future DeepSeek Harness / Claude Skills / AutoClaw: same `tick()` — do not clone `engine/`.

---

## Apps

### OpenWebUI + gateway

- [x] Gateway: stream chat + model list; `OPENROUTER_API_KEY` server-side
- [x] OpenWebUI compose: our `/v1` as connection; accounts for colleagues; Ollama off
- [ ] **Basic tools on the chat path** (OpenWebUI tools or a thin gateway tool set). Pass-through only today. Keep it basic — not a second agent runtime.

### PPTX generation (original V0 / V1)

Pipeline the user wrote: *Input (source) → Modular Engine (DeepSeek Harness + Claude Skills or AutoClaw, replaceable) → PPTX.*

**V0 — PPTX from one small PDF** (shipped as `pipeline/pptx`; UI is OpenWebUI not the old HTML):

- [x] Multiple tools: **python-pptx** and **pptxgenjs** (different models prefer different tools)
- [x] Native LLM ingest for one small PDF (no extra input management in V0)
- [x] Presentable deck after basic quality / error checking
- [x] Upload + download
- [x] Model dropdown — **three options for now** (user checked multimodality & PPT): Claude Opus 5, GLM 5.3, Kimi K3
- [x] Pause pipeline and resume later from disk
- [x] Clarify dialogue instead of confidently inventing missing facts (`ask_user`)
- [x] Swappable harness slot (`registry.py`)

**V1 — any input format** (ingest helpers exist; server no longer rejects non-PDF):

- [x] Non-native (DOCX, PPTX, etc.) → scanned page images via simple Python (zip XML + rasterize). Text / image / PDF stay native.
- [x] Central planner + memory: markdown checkboxes + error / observation log (`memory.md`)
- [ ] Named conversion plugin (**pptxtoimages** and friends) — still the future Conversion module, not more code stuffed into Demarcation
- [ ] Expand the model list past the three V0 favorites when needed (“for now”)

---

## Pipelines / engines

- [x] **Python PPTX** `pipeline/pptx` — only generation engine for now
- [x] **Extract / one-Q** `pipeline/extract` — ingest → windows → survey → fresh worker per `[ ]` → structural QA → review. Worker sees 2–3 pages, never the whole corpus. Resume = plan file. One retry then `[!]`.
- [ ] **OpenWebUI basic tools** on general chat (see Apps)
- [ ] **DeepSeek Harness as multi-project host** (later). Thin adapter; JSON unchanged; DSH OpenAI base = this gateway `/v1`. No custom `agent-loop` inside Demarcation. Optional later: run a PPTX job *inside* Harness via adapter, not a rewrite.

Extract ceiling (original proposal; not extra product): supervisor `implementation_plan.md` + `Chapter_Error_Report.md`; worker `Q##_Title.md` with Answer / Corrections / Integrated Margin. Later extras named only in that proposal — do not build unless asked: parallel workers, multi-chapter, cost tracking, diff-based review, self-healing survey.

---

## Modules

### 1. Input format conversion — later plugin

- [ ] Own PDF/PPTX/… → ordered page files. **pptxtoimages**-class tools live here.
- [ ] Demarcation v1 should **fail closed** on a raw PDF/PPTX tree and point here (already-rendered pages only unless Conversion ran).
- Does not own cuts, windows, or model calls.

### 2. Context Demarcation — core shipped

- [x] `plan.schema.json` (`v: 1`)
- [x] Walk: subfolders, numeric sort, checkpoint
- [x] `window(k)` — default `k=1`, **may cross documents**
- [x] Cheap cuts: file / folder / name-seq
- [x] CLI + Python `index` / `load` / `window_for`
- [x] Thin DSH tools that shell/read JSON (no second TypeScript walker)
- [x] Host hook: extract + PPTX write `data/jobs/<id>/demarcation/` and window in `engine/parts.py` (focus + neighbors)
- [ ] Text / code unit factories — “think about design later”; freeze schema so LCM does not care if a unit is a PNG or a function
- [ ] Later cut enrichers: blank-page, phash-jump, optional MMLM topic break (not v1)
- [ ] SQLite if the index hits tens of thousands (JSON first)

Config, not forks: `root`, globs, `kind`, `k`, `cuts[]`, checkpoint.

### 3. Long context management — later plugin

- [ ] Consume a plan: 1-focus-per-turn, improvised **LLMxMapReduce / REPL**, resume, retries
- [ ] Replace extract/`tick` **analysis** looping without changing `plan.json`
- Does not discover units. Do not fold Demarcation under LCM.

---

## Extra tools (keep adding)

- [x] OpenRouter gateway
- [x] python-pptx
- [x] pptxgenjs
- [x] Pillow rasterize
- [ ] pptxtoimages (Conversion)
- [ ] OpenWebUI / gateway basic tools
- [ ] pdftoppm as a first-class documented Conversion path (optional today)

---

## Non-goals

- A second chat UI
- Dumping 40 pages into one session
- Merging PPTX + demarcation + extract into one package
- Migrating PPTX `tick()` to TypeScript
- Implementing DSH or LCM before chat + current `tick()` hosts are enough
- Loading the corpus into a chat session as the index
- Importing Cordis in Python core or the PPTX engine
