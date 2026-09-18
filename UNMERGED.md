# Unmerged work

`main` has Plan D: OpenWebUI, OpenAI-compatible gateway, `pipeline/extract`, and a copy of demarcation core.

Two product branches are still out. **Read this before adding a package, engine, or UI.** They overlap `main` on purpose — rebase; do not clone a third `engine/`.

**Agents:** new long-lived work gets a row here in the same change. After merge to `main`, delete the row.

| Branch | Owns | Overlaps `main` | Tree |
|---|---|---|---|
| `cursor/v0-v1-todos-6a38` | PPTX: `LoopHarness`, `pptx_tools`, python-pptx / pptxgenjs, PPTX UI, deck QA | `engine/ingest.py`, `job.py`, `llm.py`, `qa.py`, `registry.py`, `server.py`, `public/` — keep the gateway; add PPTX as a `tick()` plugin | [tree](https://github.com/wbhsmedical/Base/tree/cursor/v0-v1-todos-6a38) |
| `cursor/context-demarcation-todo-efe3` | Walk / windows / cuts (source of the JSON contract) | `context-demarcation/` already vendored on `main` — merge is align/rebase, not a second copy | [tree](https://github.com/wbhsmedical/Base/tree/cursor/context-demarcation-todo-efe3) |

## Contracts (do not fork)

- **Disk JSON/files** are the compatibility layer. Hosts do not share a runtime.
- **Ingest** writes page files. **Demarcation** indexes them. **Windows** (focus + neighbors) go to the model — never the full corpus in one turn.
- **Harness** = `tick()` on a job directory. Gateway chat, extract pipeline, PPTX loop, and DSH are plugins, not copies of each other.
- `main` already **copy-then-thinned** ingest + demarcation. Prefer rebasing the two branches below onto `main` over writing another engine.

## How to work

1. PPTX or demarcation: start from **that** branch, then rebase onto `main`. Not from a silent copy of old `main`.
2. If two rows must change, do one side first and leave a hook note (demarcation already notes the PPTX `_file_parts` hook).
3. After merge to `main`, delete the row here.
