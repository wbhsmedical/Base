# Base

Cloud Agent stub. **Unmerged product work is not on `main`.**

Start here: **[UNMERGED.md](UNMERGED.md)** — branches, ownership, what not to duplicate.

| Branch | One line |
|---|---|
| [`cursor/v0-v1-todos-6a38`](https://github.com/wbhsmedical/Base/tree/cursor/v0-v1-todos-6a38) | PPTX pipeline |
| [`cursor/context-demarcation-todo-efe3`](https://github.com/wbhsmedical/Base/tree/cursor/context-demarcation-todo-efe3) | Context demarcation |
| [`cursor/plan-d-openwebui-todo-9f4c`](https://github.com/wbhsmedical/Base/tree/cursor/plan-d-openwebui-todo-9f4c) | OpenWebUI + OpenRouter gateway |

## AI agents

1. **Code.** Small functions, one obvious loop. Comments may be long. Code must stay short — handwritten gold, not verbose slop.
2. **Branches.** Read [UNMERGED.md](UNMERGED.md) before you add a package, engine, or UI. New long-lived work gets a row there in the same change. Do not reimplement an owned seam off a silent copy of `main`.
3. **Modular.** Plugins, tools, and disk contracts already exist (`tick()`, ingest, demarcation windows, gateway `/v1`, DSH wrappers). Future projects compose those. Lean: do not clone a second engine.
