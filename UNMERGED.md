# Unmerged work

`main` is the empty Base stub. Product work lives on the branches below. **Read this file before adding a package, engine, or UI** — those trees already own the seams. Duplicating them on a fourth branch will conflict on merge.

Update this table in the same PR when you open a new long-lived branch.

| Branch | Owns | Does not own | Tree |
|---|---|---|---|
| `cursor/v0-v1-todos-6a38` | PPTX pipeline: `engine/` (`tick()`, ingest, OpenRouter PDF/image parts, QA, job dir), `server.py`, PPTX UI | Demarcation algorithm, OpenWebUI, extract orchestrator | [tree](https://github.com/wbhsmedical/Base/tree/cursor/v0-v1-todos-6a38) |
| `cursor/context-demarcation-todo-efe3` | Page index: `plan.json` + `windows.jsonl`, Python `core/`, thin DSH tools | Conversion, model loop, attaching the whole corpus | [tree](https://github.com/wbhsmedical/Base/tree/cursor/context-demarcation-todo-efe3) |
| `cursor/plan-d-openwebui-todo-9f4c` | OpenWebUI compose, OpenAI-compatible gateway, chat + `pipeline/extract` (windowed workers) | PPTX backends, a second chat SPA | [tree](https://github.com/wbhsmedical/Base/tree/cursor/plan-d-openwebui-todo-9f4c) |

## Contracts (do not fork)

- **Disk JSON/files** are the compatibility layer. Hosts do not share a runtime.
- **Ingest** (PPTX / Plan D) writes page files. **Demarcation** indexes them after ingest. **Windows** (focus + neighbors) go to the model — never the full corpus in one turn.
- **Harness** = `tick()` on a job directory. PPTX loop, extract pipeline, and later DSH are plugins, not copies of each other.
- Plan D already **copy-then-thinned** ingest + demarcation core. Prefer merging/rebasing those originals over writing a third `engine/`.

## How to work

1. Pick the row that owns the seam you need. Branch from **that** branch, or rebase onto it — not from a silent copy of `main`.
2. If two rows must change, do one side first and leave a hook note (demarcation already notes the PPTX `_file_parts` hook).
3. After merge to `main`, delete the row here.
