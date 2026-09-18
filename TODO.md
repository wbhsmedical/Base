# Plan D — OpenWebUI + shared backend

Locked. UI is OpenWebUI (colleagues included). Everything else is Python behind an OpenAI-compatible API.

Code taste: small functions, one obvious loop. Comments may be long. Code must stay short.

---

## Split (locked)

| Piece | Owns | Does not own |
|---|---|---|
| **OpenWebUI** | login, chat, model picker, upload, sharing | jobs, plans, OpenRouter key, DSH |
| **Gateway** | `/v1/models`, `/v1/chat/completions` (stream); key in env | HTML |
| **Jobs** | `data/jobs/<id>/`, pause/resume, `ask_user`, checkbox plan | rasterize, windowing |
| **Ingest** | PDF/PPTX/… → page files | cuts, model calls |
| **Demarcation** | walk → units → windows → cuts → JSON | sending units to a model |
| **Pipeline** | supervisor → orchestrator → one-Q worker | chat UX, DSH runtime |
| **DSH** (later) | plugins wrapping the same JSON | a second algorithm |

JSON/files on disk are the contract. Do not merge the PPTX engine into this tree. Do not re-walk trees in TypeScript.

---

## Reuse (unmerged — depend on contracts, do not swallow)

From `cursor/v0-v1-todos-6a38`: OpenRouter parts, `Job` dir, `tick()`, ingest, QA gate, pause/clarify.

From `cursor/context-demarcation-todo-efe3`: `plan.json` + `windows.jsonl`; after ingest, window in `_file_parts` (focus + neighbors, never the whole corpus).

OpenRouter client today is PPTX-action JSON + three pinned models. Chat needs stream + live `/models`. Same HTTP, thinner wrapper.

---

## Modes (one gateway, two `tick()` plugins)

**Chat** — OpenWebUI → gateway → OpenRouter. Optional image/PDF parts. No tools required.

**Pipeline** — OpenWebUI talks to a pipeline “model”. Backend:

1. Ingest upload → page files.
2. Demarcation → windows.
3. Supervisor writes `implementation_plan.md` (human or auto-approve).
4. Orchestrator: each `[ ]` → fresh worker, scoped pages only → structural QA → `[x]` / `[!]`.
5. Supervisor review → error report.

Resume = reread the plan file. Crash-safe. One retry then flag.

---

## Build

- [ ] Gateway: stream chat + model list; `OPENROUTER_API_KEY` server-side; OpenWebUI as the only client
- [ ] OpenWebUI compose: our `/v1` as connection; accounts for colleagues; no custom chat SPA
- [ ] Extract (copy-then-thin, don’t wait on merge): `jobs`, `ingest`, OpenRouter complete/stream
- [ ] Attach files via existing part shapes; still no full-corpus attach
- [ ] Hook demarcation after ingest (sibling `demarcation/` under the job dir)
- [ ] Pipeline `tick()`: plan parse, spawn, validate sections, checkpoint
- [ ] DSH last: OpenRouter on `ctx.llm`; demarcation tools already designed; same files

Config (not forks): base URL, favorites, `k`, globs, pipeline vs chat.

---

## Non-goals

- A second chat UI (no SPA competing with OpenWebUI)
- Dumping 40 pages into one session
- Merging PPTX + demarcation + this into one package
- Implementing DSH before chat + pipeline work
