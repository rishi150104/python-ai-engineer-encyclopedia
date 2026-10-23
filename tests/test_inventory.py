"""Tests for inventory-level checks: hierarchy, priority inversion, duplicates, source categories, progress coverage and the audit record."""
import copy
import importlib.util
from pathlib import Path

import yaml

spec = importlib.util.spec_from_file_location("validate", Path(__file__).resolve().parent.parent / "scripts" / "validate.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def node(id, level, parent, priority="P0", title=None, **kw):
    base = dict(id=id, level=level, title=title or f"T {id}", parent=parent, priority=priority, scope="s", competency="practical",
                prereqs=[], related=[], source_category="official-docs")
    base.update(kw)
    return base


def inv():
    return [node("PY", "domain", None, title="Python"), node("PY-0001", "topic", "PY"),
            node("PY-0002", "concept", "PY-0001", title="A"), node("PY-0003", "concept", "PY-0001", title="B"),
            node("PY-0004", "concept", "PY-0001", title="C")]


def errs(nodes):
    v.errors.clear()
    v.warnings.clear()
    v.check_inventory({"nodes": nodes})
    return list(v.errors)


def test_valid_inventory_has_no_errors():
    assert errs(inv()) == []


def test_priority_inversion_is_an_error():
    n = inv()
    n[2]["priority"] = "P0"
    n[3]["priority"] = "P1"
    n[2]["prereqs"] = ["PY-0003"]                      # P0 depends on a P1
    assert any("priority inversion" in e for e in errs(n))


def test_duplicate_titles_and_bad_source_category_and_empty_topic():
    n = inv()
    n[3]["title"] = "a"
    n[4]["source_category"] = "blog"
    n.append(node("PY-0005", "topic", "PY"))
    e = " ".join(errs(n))
    assert "same title" in e and "bad source_category" in e and "has no children" in e


def test_topic_priority_must_match_best_child_and_prereq_must_be_concept():
    n = inv()
    n[1]["priority"] = "P2"
    n[2]["prereqs"] = ["PY-0001"]
    e = " ".join(errs(n))
    assert "most important child" in e and "not a concept" in e


def test_same_id_as_prereq_and_related_rejected():
    n = inv()
    n[2]["prereqs"] = ["PY-0003"]
    n[2]["related"] = ["PY-0003"]
    assert any("prerequisite and related" in e for e in errs(n))


def test_every_concept_needs_a_progress_record(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "ROOT", tmp_path)
    (tmp_path / "entries").mkdir()
    nodes = {n["id"]: n for n in inv()}
    v.errors.clear()
    v.check_progress({"entries": {"PY-0002": {"content_status": "NOT_STARTED", "verification_status": "NOT_CHECKED",
                                              "history": [{"content": "NOT_STARTED", "verification": "NOT_CHECKED"}]}}}, nodes, {})
    assert any("PY-0003 has no record" in e for e in v.errors)
    assert not any("PY-0002 has no record" in e for e in v.errors)


def audit(**over):
    a = {"coverage_claim": "PARTIAL", "limitations": ["x"], "inventory_size": {"concepts": 3},
         "lenses": {k: {"status": "DONE", "sources": [{"id": "S", "url": "u", "accessed_on": "d", "sha256": "h"}], "findings": []} for k in v.AUDIT_LENSES}}
    a.update(over)
    return a


def run_audit(tmp_path, monkeypatch, a):
    monkeypatch.setattr(v, "ROOT", tmp_path)
    (tmp_path / "verification").mkdir(exist_ok=True)
    (tmp_path / "verification" / "inventory-audit.yaml").write_text(yaml.safe_dump(a))
    nodes = {n["id"]: n for n in inv()}
    v.errors.clear()
    v.warnings.clear()
    v.check_audit(nodes)
    return list(v.errors), list(v.warnings)


def test_audit_clean_and_stale_size_warns(tmp_path, monkeypatch):
    e, w = run_audit(tmp_path, monkeypatch, audit())
    assert e == [] and w == []
    e, w = run_audit(tmp_path, monkeypatch, audit(inventory_size={"concepts": 99}))
    assert e == [] and any("stale" in x for x in w)


def test_audit_references_must_exist_and_priority_must_match(tmp_path, monkeypatch):
    a = audit(priority_changes=[{"concept": "PY-0002", "to": "P3"}, {"concept": "PY-9999", "to": "P0"}],
              job_signal={"themes": [{"theme": "t", "covered_by": ["PY-8888"]}]}, merges_and_removals=[{"target": "PY-0001"}])
    a["lenses"]["official_docs"]["findings"] = [{"concept": "PY-7777"}]
    e = " ".join(run_audit(tmp_path, monkeypatch, a)[0])
    assert "priority is P0 but the audit recorded P3" in e and "unknown concept PY-9999" in e and "PY-8888" in e and "PY-7777" in e
    assert "merge target PY-0001 is not a concept" in e


def test_done_lens_source_needs_hash_and_limitations_required(tmp_path, monkeypatch):
    a = audit(limitations=[])
    del a["lenses"]["official_docs"]["sources"][0]["sha256"]
    e = " ".join(run_audit(tmp_path, monkeypatch, a)[0])
    assert "missing sha256" in e and "limitations must be recorded" in e


def test_items_file_hash_must_match(tmp_path, monkeypatch):
    (tmp_path / "verification" / "audit-sources").mkdir(parents=True)
    (tmp_path / "verification" / "audit-sources" / "S.json").write_text('{"sha256": "other"}')
    a = audit()
    a["lenses"]["official_docs"]["sources"][0]["items_file"] = "verification/audit-sources/S.json"
    assert any("different page version" in x for x in run_audit(tmp_path, monkeypatch, a)[0])


def test_removed_title_must_really_be_gone(tmp_path, monkeypatch):
    a = audit(merges_and_removals=[{"removed_title": "C", "target": "PY-0002"}])      # inv() still has a concept titled C
    assert any("still exists" in e for e in run_audit(tmp_path, monkeypatch, a)[0])
    a = audit(merges_and_removals=[{"removed_title": "Gone", "target": "PY-0002"}])
    assert run_audit(tmp_path, monkeypatch, a)[0] == []


# ---- revision 2: optional fields, retired ids, interview index
def test_review_cycle_and_tags_are_validated():
    n = inv()
    n[2]["review_cycle"] = "weekly"
    n[3]["tags"] = ["interview", "mystery"]
    n[1]["tags"] = ["interview"]
    e = " ".join(errs(n))
    assert "bad review_cycle" in e and "tags must be a list drawn from" in e and "only concepts can be tagged" in e
    n = inv()
    n[2]["review_cycle"] = "quarterly"
    n[3]["tags"] = ["interview"]
    assert errs(n) == []


def test_retired_ids_are_never_reused():
    def run(retired):
        v.errors.clear()
        v.check_inventory({"nodes": inv(), "retired_ids": retired})
        return list(v.errors)
    assert run([{"id": "PY-0009", "reason": "merged into PY-0002"}]) == []
    assert any("never reused" in e for e in run([{"id": "PY-0003", "reason": "merged"}]))     # PY-0003 exists in inv()
    assert any("need an id and a reason" in e for e in run([{"id": "PY-0010"}]))
    assert any("listed twice" in e for e in run([{"id": "PY-0010", "reason": "x"}, {"id": "PY-0010", "reason": "y"}]))


def test_interview_index_lists_only_tagged_concepts(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "ROOT", tmp_path)
    n = inv()
    n[3]["tags"] = ["interview"]
    nodes = {x["id"]: x for x in n}
    text = v.render_interview_index(nodes, {})
    assert "**PY-0003**" in text and "**PY-0002**" not in text and "1 tagged concepts" in text


def test_master_index_marks_periodic_review(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "ROOT", tmp_path)
    n = inv()
    n[2]["review_cycle"] = "quarterly"
    assert "review quarterly" in v.render_index({x["id"]: x for x in n}, {})
