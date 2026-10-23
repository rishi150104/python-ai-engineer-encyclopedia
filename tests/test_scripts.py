"""Tests for check_claims.py / run_examples.py and the generated-vs-human file split."""
import gzip
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


cc, rx, v = load("check_claims"), load("run_examples"), load("validate")

HTML311 = b"<html><body><p>Objects are never <code>explicitly</code> destroyed.</p> 3.11.17 Documentation</body></html>"
HTML313 = b"<html><body><p>Objects are never explicitly destroyed.</p> 3.13.17 Documentation</body></html>"
RECORD = """# human comment that must survive
id: T-1
claims:
- {id: C1, text: t, importance: critical, support: direct, source: SRC-X-3.11, section: s, quotes: [Objects are never explicitly destroyed]}
examples:
- {id: E1, file: ex.py, requires: [], expected_output: hi}
"""
REGISTRY = """# human comment in registry
sources:
- {id: SRC-X-3.11, title: t, url: http://x/3.11, kind: official, version: v, license: l}
- {id: SRC-X-3.13, title: t, url: http://x/3.13, kind: official, version: v, license: l}
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "verification" / "snapshots").mkdir(parents=True)
    (tmp_path / "verification" / "generated").mkdir()
    (tmp_path / "verification" / "T-1.yaml").write_text(RECORD)
    (tmp_path / "source-registry.yaml").write_text(REGISTRY)
    (tmp_path / "ex.py").write_text("print('hi')")
    gen = {"sources": {}}
    for sid, raw in (("SRC-X-3.11", HTML311), ("SRC-X-3.13", HTML313)):
        (tmp_path / "verification" / "snapshots" / f"{sid}.html.gz").write_bytes(gzip.compress(raw, mtime=0))
        gen["sources"][sid] = {"sha256": hashlib.sha256(raw).hexdigest(), "snapshot": f"verification/snapshots/{sid}.html.gz",
                               "doc_version": "3.11.17", "accessed_on": "d"}
    (tmp_path / "verification" / "generated" / "sources.yaml").write_text(yaml.safe_dump(gen))
    for m in (cc, rx):
        monkeypatch.setattr(m, "ROOT", tmp_path)
    return tmp_path


def test_scripts_never_modify_human_files(repo):
    before = {p: (repo / p).read_bytes() for p in ("verification/T-1.yaml", "source-registry.yaml")}
    with pytest.raises(SystemExit) as e:
        cc.main("T-1")
    assert e.value.code == 0
    with pytest.raises(SystemExit):
        rx.main("T-1")
    assert {p: (repo / p).read_bytes() for p in before} == before        # comments and layout intact
    assert b"human comment that must survive" in (repo / "verification/T-1.yaml").read_bytes()
    res = yaml.safe_load((repo / "verification/generated/T-1.results.yaml").read_text())
    assert res["claims"]["C1"]["versions"] == {"3.11": "PASS", "3.13": "PASS"}
    assert res["examples"]["E1"]["execution"] == "PASSED"
    assert "explicitly destroyed" in (repo / "verification/generated/T-1.excerpts.md").read_text()


def test_inline_markup_does_not_break_quotes():
    # <code> inside the phrase must not insert whitespace (bug found in the pilot)
    assert "never explicitly destroyed" in cc.to_text(HTML311)


def test_version_specific_quotes_and_failure():
    claims = [{"id": "C1", "source": "SRC-X-3.11", "quotes": ["only in 3.11"], "quotes_by_version": {"3.13": ["destroyed"]}}]
    texts = {"SRC-X-3.11": "only in 3.11", "SRC-X-3.13": "never destroyed"}
    r = cc.evaluate(claims, texts, {"SRC-X-3.11", "SRC-X-3.13"})
    assert r["C1"]["versions"] == {"3.11": "PASS", "3.13": "PASS"}
    texts["SRC-X-3.13"] = "reworded"
    assert cc.evaluate(claims, texts, {"SRC-X-3.11", "SRC-X-3.13"})["C1"]["versions"]["3.13"] == "FAIL"


def test_extra_python_run_is_recorded_without_changing_primary(repo):
    with pytest.raises(SystemExit):
        rx.main("T-1")
    with pytest.raises(SystemExit):
        rx.main("T-1", sys.executable)
    ex = yaml.safe_load((repo / "verification/generated/T-1.results.yaml").read_text())["examples"]["E1"]
    assert ex["execution"] == "PASSED" and ex["extra_runs"][0]["execution"] == "PASSED"


def test_snapshot_hash_is_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "ROOT", tmp_path)
    snap = tmp_path / "verification" / "snapshots" / "S.html.gz"
    snap.parent.mkdir(parents=True)
    snap.write_bytes(gzip.compress(b"page", mtime=0))
    reg = {"sources": [{"id": "S", "title": "t", "url": "u", "kind": "official", "version": "v", "license": "l"}]}
    good = {"sources": {"S": {"access_status": "FETCHED", "accessed_on": "d", "doc_version": "3", "snapshot": "verification/snapshots/S.html.gz",
                              "sha256": hashlib.sha256(b"page").hexdigest()}}}
    v.errors.clear()
    v.check_sources(reg, good)
    assert v.errors == []
    good["sources"]["S"]["sha256"] = "0" * 64
    v.check_sources(reg, good)
    assert any("does not match" in e for e in v.errors)
    v.errors.clear()
    del good["sources"]["S"]["snapshot"]
    v.check_sources(reg, good)
    assert any("a hash alone is not an accessible source" in e for e in v.errors)


def test_verified_needs_full_entailment_and_flags_missing_independent_review():
    c = dict(id="C1", text="t", importance="critical", support="direct", source="S", section="x", check="PASS",
             checked_on="d", quotes=["q"], review={"entailment": "PARTIAL", "reviewer": "r", "independent": False})
    rec = {"id": "X", "claims": [c], "examples": [], "independent_review": {"status": "NOT_DONE"}}
    v.errors.clear()
    v.warnings.clear()
    v.check_record("X", rec, {"S": {"access_status": "FETCHED"}}, "VERIFIED", "[C1]")
    assert any("review.entailment is PARTIAL" in e for e in v.errors)
    assert any("requires independent_review" in e for e in v.errors)


def test_merge_record_keeps_human_fields_and_defaults_unchecked():
    rec = {"id": "X", "claims": [{"id": "C1", "text": "t"}], "examples": [{"id": "E1", "file": "f"}]}
    out = v.merge_record(rec, {"claims": {"C1": {"check": "PASS"}}})
    assert out["claims"][0] == {"id": "C1", "text": "t", "check": "PASS"}
    assert out["examples"][0]["execution"] == "NOT_RUN"
    assert "check" not in rec["claims"][0]                          # input not mutated


REV_REC = {"id": "T-1", "independent_review": {"status": "DONE"},
           "claims": [{"id": "C1", "source": "S", "support": "direct"}, {"id": "C2", "support": "judgment"}]}


def _reviewer(tmp_path, monkeypatch, data):
    monkeypatch.setattr(v, "ROOT", tmp_path)
    d = tmp_path / "verification" / "review"
    d.mkdir(parents=True)
    (d / "T-1.reviewer.yaml").write_text(yaml.safe_dump(data))
    v.errors.clear()
    v.warnings.clear()
    v.check_reviewer("T-1", REV_REC)
    return list(v.errors)


GOOD_REVIEWER = {"name": "R", "kind": "human", "date": "2026-10-24", "independent_of_author": True}


def test_done_needs_every_sourced_claim_settled(tmp_path, monkeypatch):
    errs = _reviewer(tmp_path, monkeypatch, {"reviewer": GOOD_REVIEWER, "claims": {"C1": {"verdict": "PENDING"}}})
    assert any("C1 is not settled" in e for e in errs)


def test_done_accepts_agree_and_accepted_resolution(tmp_path, monkeypatch):
    assert _reviewer(tmp_path, monkeypatch, {"reviewer": GOOD_REVIEWER, "claims": {"C1": {"verdict": "AGREE"}}}) == []


def test_resolved_disagreement_needs_acceptance(tmp_path, monkeypatch):
    c = {"verdict": "DISAGREE", "comment": "overclaims", "resolution": "RESOLVED_CORRECTED", "resolution_note": "narrowed",
         "reviewer_accepts_resolution": None}
    assert any("not settled" in e for e in _reviewer(tmp_path, monkeypatch, {"reviewer": GOOD_REVIEWER, "claims": {"C1": c}}))


def test_done_rejects_non_independent_reviewer(tmp_path, monkeypatch):
    rv = {**GOOD_REVIEWER, "independent_of_author": False}
    assert any("independent_of_author" in e for e in _reviewer(tmp_path, monkeypatch, {"reviewer": rv, "claims": {"C1": {"verdict": "AGREE"}}}))


def test_disagree_needs_comment(tmp_path, monkeypatch):
    errs = _reviewer(tmp_path, monkeypatch, {"reviewer": GOOD_REVIEWER, "claims": {"C1": {"verdict": "DISAGREE"}}})
    assert any("needs a comment" in e for e in errs)


def test_reviewer_file_is_never_rewritten(repo, monkeypatch):
    mk = load("make_review_checklist")
    monkeypatch.setattr(mk, "ROOT", repo)
    with pytest.raises(SystemExit):
        cc.main("T-1")                       # fills generated sources/results the checklist reads
    mk.main("T-1")
    rpath = repo / "verification" / "review" / "T-1.reviewer.yaml"
    assert "verdict: PENDING" in rpath.read_text()
    rpath.write_text(rpath.read_text().replace("verdict: PENDING", "verdict: AGREE") + "# reviewer note kept" + chr(10))
    before = rpath.read_bytes()
    mk.main("T-1")                           # regenerate: checklist rewritten, reviewer file untouched
    assert rpath.read_bytes() == before
    text = (repo / "verification" / "review" / "T-1.checklist.md").read_text(encoding="utf-8")
    assert "Objects are never" in text and "⟦" in text
