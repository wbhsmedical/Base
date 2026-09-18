# Unmerged work

`main` has the OpenWebUI gateway (Plan D). These branches are still out. **Read this file before adding a package, engine, or UI** — they already own the seams. Duplicating them will conflict on merge.

**Agents:** if you create a long-lived branch, add a row here in the same change. Ownership first — do not duplicate a seam.

| Branch | Owns | Does not own | Tree |
|---|---|---|---|
| `cursor/v0-v1-todos-6a38` | PPTX pipeline: `engine/` (`tick()`, ingest, OpenRouter PDF/image parts, QA, job dir), `server.py`, PPTX UI | Demarcation algorithm, OpenWebUI, extract orchestrator | [tree](https://github.com/wbhsmedical/Base/tree/cursor/v0-v1-todos-6a38) |
| `cursor/context-demarcation-todo-efe3` | Page index: `plan.json` + `windows.jsonl`, Python `core/`, thin DSH tools | Conversion, model loop, attaching the whole corpus | [tree](https://github.com/wbhsmedical/Base/tree/cursor/context-demarcation-todo-efe3) |

## Contracts (do not fork)

- **Disk JSON/files** are the compatibility layer. Hosts do not share a runtime.
- **Ingest** (PPTX / Plan D) writes page files. **Demarcation** indexes them after ingest. **Windows** (focus + neighbors) go to the model — never the full corpus in one turn.
- **Harness** = `tick()` on a job directory. PPTX loop, extract pipeline, and later DSH are plugins, not copies of each other.
- Plan D already **copy-then-thinned** ingest + demarcation core. Prefer merging/rebasing those originals over writing a third `engine/`.

## How to work

1. Pick the row that owns the seam you need. Branch from **that** branch, or rebase onto it — not from a silent copy of `main`.
2. If two rows must change, do one side first and leave a hook note (demarcation already notes the PPTX `_file_parts` hook).
3. After merge to `main`, delete the row here.
