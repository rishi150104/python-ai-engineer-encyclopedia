"""Tests for scripts/validate.py. Tests point validate.ROOT at a tmp dir where files are needed."""
import copy
import importlib.util
from pathlib import Path

import yaml

spec = importlib.util.spec_from_file_location("validate", Path(__file__).resolve().parent.parent / "scripts" / "validate.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def node(id, level, parent, **kw):
    return dict(id=id, level=level, title="T", parent=parent, priority="P0", scope="s",
                competency="practical", prereqs=[], related=[], source_category="official-docs", **kw)


NODES = [node("PY", "domain", None), node("PY-0001", "topic", "PY"), node("PY-0002", "concept", "PY-0001")]


def run(fn, *args):
    v.errors.clear()
    v.warnings.clear()
    fn(*args)
    return list(v.errors)


def test_clean_inventory():
    assert run(v.check_inventory, {"nodes": NODES}) == []


def test_inventory_catches_cycle_dup_and_status_field():
    n = copy.deepcopy(NODES)
    n[2]["prereqs"] = ["PY-0003"]
    n.append(node("PY-0003", "concept", "PY-0001", status="DRAFTED"))
    n[3]["prereqs"] = ["PY-0002"]
    n.append(copy.deepcopy(NODES[1]))
    errs = " ".join(run(v.check_inventory, {"nodes": n}))
    assert "cycle" in errs and "duplicate" in errs and "unknown fields" in errs


def test_transitions():
    def ok(a, b):
        return run(v.check_step, "X", dict(content=a[0], verification=a[1]), dict(content=b[0], verification=b[1])) == []
    assert ok(("NOT_STARTED", "NOT_CHECKED"), ("RESEARCHED", "NOT_CHECKED"))
    assert not ok(("NOT_STARTED", "NOT_CHECKED"), ("DRAFTED", "NOT_CHECKED"))   # skipped a stage
    assert not ok(("COMPLETE", "NOT_CHECKED"), ("COMPLETE", "VERIFIED"))        # skipped IN_PROGRESS
    assert not ok(("COMPLETE", "VERIFIED"), ("DRAFTED", "VERIFIED"))            # stale verification
    assert ok(("COMPLETE", "VERIFIED"), ("DRAFTED", "NOT_CHECKED"))             # reset on back-step


def rec(**claim):
    c = dict(id="C1", text="t", importance="critical", support="direct", source="S", section="3.1",
             check="PASS", checked_on="2026-10-23", quotes=["q"],
             review={"entailment": "FULL", "reviewer": "r", "independent": False})
    c.update(claim)
    return {"id": "X", "claims": [c], "examples": [], "independent_review": {"status": "DONE"}}


def test_verified_gate():
    fetched = {"S": {"access_status": "FETCHED"}}
    page = "text [C1]"
    assert run(v.check_record, "X", rec(), fetched, "VERIFIED", page) == []
    assert any("never FETCHED" in e for e in run(v.check_record, "X", rec(), {"S": {"access_status": "NOT_ACCESSED"}}, "IN_PROGRESS", page))
    assert any("claim C1 is UNCHECKED" in e for e in run(v.check_record, "X", rec(check="UNCHECKED"), fetched, "VERIFIED", page))
    assert any("not marked" in e for e in run(v.check_record, "X", rec(), fetched, "VERIFIED", "no markers"))
    assert any("pure judgment" in e for e in run(v.check_record, "X", rec(support="judgment"), fetched, "IN_PROGRESS", page))


def test_example_must_match_expected(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "ROOT", tmp_path)
    (tmp_path / "e.py").write_text("print(1)")
    ex = dict(id="E1", file="e.py", execution="PASSED", expected_output="1", actual_output="2",
              run_on="d", dependencies={}, environment={"python": "3", "os": "x"})
    r = {"id": "X", "claims": [], "examples": [ex], "independent_review": {"status": "DONE"}}
    assert any("expected != actual" in e for e in run(v.check_record, "X", r, {}, "IN_PROGRESS", None))


def test_audit_rejects_complete_claim(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "ROOT", tmp_path)
    (tmp_path / "verification").mkdir()
    a = {"coverage_claim": "COMPLETE", "lenses": {k: {"status": "NOT_STARTED"} for k in v.AUDIT_LENSES}}
    (tmp_path / "verification" / "inventory-audit.yaml").write_text(yaml.safe_dump(a))
    assert any("never 'complete'" in e for e in run(v.check_audit))


def test_pass_needs_quotes_and_inferred_needs_passed_example():
    fetched = {"S": {"access_status": "FETCHED"}}
    assert any("needs verbatim quotes" in e for e in run(v.check_record, "X", rec(quotes=[]), fetched, "IN_PROGRESS", None))
    r = rec(quotes=["q"], support="inferred", importance="important", verified_by=["E1"])
    assert any("inferred claim C1" in e for e in run(v.check_record, "X", r, fetched, "IN_PROGRESS", None))
