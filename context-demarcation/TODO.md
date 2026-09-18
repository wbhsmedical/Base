# Context Demarcation

Index a folder of pages (images now; text/code later). Emit a **plan**: ordered units, neighbor windows, candidate cuts.

Not a converter. Not the analysis loop. Not MapReduce/REPL.

Code taste: small functions, one obvious loop, no helper soup. Comments may be long. Code must stay short.

---

## Split (locked)

| Piece | Owns | Does not own |
|---|---|---|
| **Input conversion** (future plugin) | PDF/PPTX/… → ordered page files | cuts, windows, model calls |
| **Demarcation** (this) | walk → units → windows → cuts → JSON | sending units to a model |
| **Long context / LCM** (future) | consume a plan: 1-focus-per-turn, MapReduce, REPL | discovering units |

Indexing loop: here. Analysis loop: LCM (or a host like the PPTX `tick()`).

Three plugins, not one. Do not bury this inside LCM. Do not import Cordis in the core.

---

## Contract

JSON on disk is the compatibility layer. Any host (DeepSeek Harness, PPTX pipeline, a script) reads files. No shared runtime.

```
plan.schema.json     # versioned; bump when fields change
plan.json            # { v, root, units[], cuts[] }
windows.jsonl        # one Window per line (do not load 10k windows as one array)
```

**Unit** — opaque. `id`, `kind` (`page-image` | later `text` | `code`), `uri` (path or `file:`), `doc`, `i` (in doc), `n` (global). Optional cheap flags later (`blank`, `phash`).

**Window** — `focus`, `before[]`, `after[]`. Default `k=1`. Windows **may cross documents** (spillover is the point). Host scores the **focus**; neighbors are cut-off context only.

**Cut** — hypothesis: `file` | `folder` | `name-seq` | later `blank` | `phash`. Never a hard fact.

**Plan** — `v`, `root`, `units`, `cuts`. Resume = rewrite from last `n`.

v1 detectors: file / folder / filename-sequence only. No MMLM pass to label cuts.

---

## Layout

```
context-demarcation/
  schema/plan.schema.json
  core/                 # pure Python — the algorithm. Zero web, zero Cordis, zero OpenRouter.
    walk.py             # recurse, stable numeric sort, glob include/exclude
    window.py           # k-neighborhood; may cross docs
    cuts.py             # cheap boundary list
    plan.py             # write/read plan.json + windows.jsonl; resume
    cli.py              # stdin/argv → files. This is what other repos call.
  dsh/                  # thin Harness wrapper: tools that shell/read the JSON. No second algorithm.
```

Python core on purpose: the in-progress PPTX engine is Python. One implementation. DSH talks to the CLI / JSON, it does not re-walk the tree in TypeScript.

---

## Host: PPTX / extract on `main`

`ingest.prepare` still writes `job.ingest`. `LoopHarness.tick` is a job-stage loop, not a page-analysis loop. Conversion lives in `engine/ingest.py` until the Conversion plugin exists. Do not duplicate it here.

Plug in **without** Cordis or a second walker:

1. After ingest, before first useful `tick`: `index` on `job.dir` → `data/jobs/<id>/demarcation/plan.json`.
2. Keep `job.ingest` as the file manifest. Demarcation is a sibling, not a replacement.
3. Windowing belongs in `engine/parts.py`: attach focus + neighbors, not the whole corpus.
4. Page-analysis looping belongs in extract `tick` (or future LCM), not in this package. `memory.md` logs observations.
5. Generation can emit units too (`kind=slide`). Same windower for “don’t split a thought.”

Do not import this package from `engine/harness.py` beyond the existing `engine.parts` / CLI / files.

---

## Host: DeepSeek Harness

Class service `ctx.contextDemarcation` wrapping the same JSON.

Tools: `demarcation_index`, `demarcation_get_window`, `demarcation_get_plan`.

No custom `agent-loop`. Conversion plugin optional (`ctx.get`). LCM `inject`s this service later.

---

## Build

- [x] `plan.schema.json` (`v: 1`)
- [x] `walk` — subfolders, numeric sort, checkpoint every N units
- [x] `window(k)` — cross-doc
- [x] `cuts` — file / folder / name-seq
- [x] `cli` — `index <root> -o <dir>` and `window <plan> --id …`
- [x] tests: tiny fixture tree (2 docs × 3 pages); assert ids, k=1 windows, 1 file-cut
- [x] DSH thin tools (after CLI is stable)
- [x] Host hook on `main`: extract + PPTX harnesses write sibling `demarcation/` under the job dir and window via `engine/parts.py`.

Config (not forks): `root`, globs, `kind`, `k`, `cuts[]`, `checkpoint`.

---

## Non-goals

- PDF/PPTX rasterization (conversion plugin / existing `engine/ingest.py`)
- MapReduce, REPL, page-per-turn **model** loop (LCM / host `tick`)
- Text/code unit factories (same types later; don’t design them now)
- Loading the corpus into a chat session
