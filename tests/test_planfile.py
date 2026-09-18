from __future__ import annotations

from engine.planfile import dump, parse, units_for
from engine.qa import check_output


SAMPLE = """
# implementation_plan

- [ ] **Q18** — Collodion baby
  - pages: [175, 176]
  - output: Q18_Collodion_Baby.md
  - known_issues: TGMI → TGM1
  - status: pending

- [x] **Q1** — Done one
  - units: [u0]
  - output: Q1.md
  - status: done
"""


def test_parse_roundtrip():
    tasks = parse(SAMPLE)
    assert tasks[0]["id"] == "Q18"
    assert tasks[0]["pages"] == [175, 176]
    assert tasks[0]["status"] == "pending"
    assert tasks[1]["status"] == "done"
    again = parse(dump(tasks))
    assert again[0]["pages"] == [175, 176]
    assert again[1]["units"] == ["u0"]


def test_units_for_pages():
    plan = [{"id": "u0", "uri": "page-175.png"}, {"id": "u1", "uri": "page-176.png"}]
    ids = units_for(plan, {"pages": [176], "units": []})
    assert ids == ["u1"]


def test_qa_ok(tmp_path):
    p = tmp_path / "Q1.md"
    p.write_text("# Q1. T\n\n## Answer\nA\n\n## Corrections\nC\n\n## Integrated Margin\nM\n" * 2)
    assert check_output(p) is None


def test_qa_todo(tmp_path):
    p = tmp_path / "Q1.md"
    p.write_text("# Q1. T\n\n## Answer\nTODO\n\n## Corrections\nC\n\n## Integrated Margin\nM\n")
    assert check_output(p) == "placeholder text"
