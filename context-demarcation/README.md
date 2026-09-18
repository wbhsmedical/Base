# Context Demarcation

Walk page images → `plan.json` + `windows.jsonl`. No conversion. No model loop.

```bash
cd context-demarcation
python3 -m unittest tests.test_core -q
python3 -m core index /path/to/pages -o /tmp/plan
python3 -m core window /tmp/plan --id u0
```

Python hosts: `from core import index, load, window_for`.

DeepSeek Harness: add this directory (`dsh plugin add …`); tools shell into `python3 -m core`.

PPTX pipeline: after `ingest.prepare`, `index(job.dir, job.dir / "demarcation")`. Window in `_file_parts`. Do not import Cordis.
