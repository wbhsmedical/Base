"""2 docs × 3 pages, plus a name-seq hole and numeric sort."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import around, index, load, window_for  # noqa: E402
from core.cuts import detect  # noqa: E402
from core.walk import list_files, nkey, units_from  # noqa: E402


def touch_tree(base: Path, spec: list[str]) -> None:
    for rel in spec:
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"")


class Walk(unittest.TestCase):
    def test_numeric_sort(self):
        self.assertLess(nkey("page-2.png"), nkey("page-10.png"))

    def test_two_docs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            touch_tree(
                root,
                [
                    "a/page-01.png",
                    "a/page-02.png",
                    "a/page-03.png",
                    "b/page-01.png",
                    "b/page-02.png",
                    "b/page-03.png",
                ],
            )
            files = list_files(root)
            units = units_from(root, files)
            self.assertEqual([u["id"] for u in units], ["u0", "u1", "u2", "u3", "u4", "u5"])
            self.assertEqual([u["doc"] for u in units], ["a", "a", "a", "b", "b", "b"])
            self.assertEqual([u["i"] for u in units], [0, 1, 2, 0, 1, 2])
            self.assertEqual(around(units, 0, 1), {"focus": "u0", "before": [], "after": ["u1"]})
            self.assertEqual(around(units, 2, 1), {"focus": "u2", "before": ["u1"], "after": ["u3"]})
            self.assertEqual(around(units, 5, 1), {"focus": "u5", "before": ["u4"], "after": []})
            kinds = {(c["at"], c["kind"]) for c in detect(units)}
            self.assertIn(("u3", "file"), kinds)
            self.assertFalse(any(c["kind"] == "name-seq" for c in detect(units)))
            self.assertFalse(any(c["kind"] == "folder" for c in detect(units)))


class Cuts(unittest.TestCase):
    def test_name_seq_hole(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            touch_tree(root, ["a/page-01.png", "a/page-03.png"])
            units = units_from(root, list_files(root))
            self.assertEqual(detect(units), [{"at": "u1", "kind": "name-seq", "prev": "u0"}])

    def test_folder_cut(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            touch_tree(root, ["x/a/page-01.png", "y/b/page-01.png"])
            units = units_from(root, list_files(root))
            kinds = {c["kind"] for c in detect(units)}
            self.assertEqual(kinds, {"file", "folder"})


class PlanCli(unittest.TestCase):
    def test_index_and_window(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "in"
            out = Path(d) / "out"
            touch_tree(
                root,
                [
                    "a/page-01.png",
                    "a/page-02.png",
                    "a/page-03.png",
                    "b/page-01.png",
                    "b/page-02.png",
                    "b/page-03.png",
                ],
            )
            plan = index(root, out, k=1)
            self.assertEqual(plan["v"], 1)
            self.assertEqual(len(plan["units"]), 6)
            self.assertEqual(len([c for c in plan["cuts"] if c["kind"] == "file"]), 1)
            self.assertEqual(window_for(out, "u2")["after"], ["u3"])
            lines = (out / "windows.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 6)
            self.assertEqual(json.loads(lines[0])["focus"], "u0")
            self.assertEqual(load(out)["units"][3]["doc"], "b")

            r = subprocess.run(
                [sys.executable, "-m", "core", "window", str(out), "--id", "u0"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(r.stdout)["after"], ["u1"])


if __name__ == "__main__":
    unittest.main()
