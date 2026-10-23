"""Deterministic checks for the encyclopedia. Run from anywhere: python scripts/validate.py [--write-index]

Exit code 0 = no errors. Warnings never fail the run. This script is the authority on the schemas
described in SCHEMA.md and on the status transition rules written in progress.yaml.
"""
import gzip
import hashlib
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

LEVELS = ["domain", "topic", "subtopic", "concept"]
PRIORITIES = {"P0", "P1", "P2", "P3"}
COMPETENCIES = {"awareness", "conceptual", "practical", "implement", "production"}
CONTENT = ["NOT_STARTED", "RESEARCHED", "DRAFTED", "COMPLETE"]
VERIF = {"NOT_CHECKED", "IN_PROGRESS", "VERIFIED", "NEEDS_REVISION", "CONFLICTING_EVIDENCE"}
VERIF_NEXT = {
    "NOT_CHECKED": {"IN_PROGRESS"},
    "IN_PROGRESS": {"VERIFIED", "NEEDS_REVISION", "CONFLICTING_EVIDENCE"},
    "VERIFIED": {"IN_PROGRESS"},
    "NEEDS_REVISION": {"IN_PROGRESS"},
    "CONFLICTING_EVIDENCE": {"IN_PROGRESS"},
}
CONTENT_BACK = {("DRAFTED", "RESEARCHED"), ("COMPLETE", "DRAFTED")}
NODE_FIELDS = {"id", "level", "title", "parent", "priority", "scope", "competency",
               "prereqs", "related", "source_category"}
SOURCE_CATEGORIES = {"official-docs", "standard", "rfc", "vendor-docs", "engineering-practice", "reference"}
BROAD_SCOPE_CHARS = 320
MIN_TOPIC_CONCEPTS = 3
OPTIONAL_FIELDS = {"review_cycle", "tags"}
REVIEW_CYCLES = {"quarterly", "semiannual"}
TAGS = {"interview"}
ID_RE = re.compile(r"^[A-Z]{2,3}(-\d{4})?$")
REQUIRED_SECTIONS = ["Expected competency", "Definition", "Competency checklist",
                     "Prerequisites and related", "Sources and verification"]
MD_LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")
AUDIT_LENSES = ["official_docs", "role_competencies", "production_responsibilities",
                "interview_expectations"]
AUDIT_STATUS = {"NOT_STARTED", "IN_PROGRESS", "DONE"}

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load(rel):
    p = ROOT / rel
    if not p.exists():
        err(f"{rel}: missing")
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- inventory
def check_inventory(inv):
    nodes = {}
    retired = {}
    for r in inv.get("retired_ids") or []:
        if not isinstance(r, dict) or not ID_RE.match(str(r.get("id", ""))) or not r.get("reason"):
            err(f"master-index: retired_ids entries need an id and a reason: {r!r}")
            continue
        if r["id"] in retired:
            err(f"master-index: retired id {r['id']} listed twice")
        retired[r["id"]] = r
    for n in inv.get("nodes") or []:
        nid = n.get("id", "<no id>")
        missing = NODE_FIELDS - n.keys()
        if missing:
            err(f"master-index: {nid} missing fields {sorted(missing)}")
            continue
        extra = n.keys() - NODE_FIELDS - OPTIONAL_FIELDS
        if extra:
            err(f"master-index: {nid} unknown fields {sorted(extra)} (statuses live in progress.yaml)")
        if not ID_RE.match(str(nid)):
            err(f"master-index: bad id format {nid}")
        if nid in nodes:
            err(f"master-index: duplicate id {nid}")
        nodes[nid] = n
        if n["level"] not in LEVELS:
            err(f"master-index: {nid} bad level {n['level']}")
        if n["priority"] not in PRIORITIES:
            err(f"master-index: {nid} bad priority {n['priority']}")
        if n["competency"] not in COMPETENCIES:
            err(f"master-index: {nid} bad competency {n['competency']}")
        if not str(n["scope"]).strip() or not str(n["title"]).strip():
            err(f"master-index: {nid} empty title/scope")
        for f in ("prereqs", "related"):
            if not isinstance(n[f], list):
                err(f"master-index: {nid}.{f} must be a list")
        if "review_cycle" in n and n["review_cycle"] not in REVIEW_CYCLES:
            err(f"master-index: {nid} bad review_cycle {n['review_cycle']}")
        if "tags" in n:
            if not isinstance(n["tags"], list) or not set(n["tags"]) <= TAGS:
                err(f"master-index: {nid} tags must be a list drawn from {sorted(TAGS)}")
            elif n["level"] != "concept":
                err(f"master-index: {nid} only concepts can be tagged")
    for rid_ in retired:
        if rid_ in nodes:
            err(f"master-index: retired id {rid_} is in use; retired ids are never reused")
    for nid, n in nodes.items():
        lvl = n["level"]
        if lvl == "domain":
            if n["parent"] is not None:
                err(f"master-index: domain {nid} must have parent null")
            if "-" in nid:
                err(f"master-index: domain id {nid} must be a bare code")
            continue
        p = nodes.get(n["parent"])
        if p is None:
            err(f"master-index: {nid} parent {n['parent']} not found")
            continue
        if lvl in LEVELS and p["level"] in LEVELS and LEVELS.index(p["level"]) >= LEVELS.index(lvl):
            err(f"master-index: {nid} ({lvl}) has parent {p['id']} of level {p['level']}")
        if lvl == "concept" and p["level"] == "domain":
            err(f"master-index: concept {nid} must sit under a topic or subtopic")
        if nid.split("-")[0] != top_domain(nodes, nid):
            err(f"master-index: {nid} id prefix does not match its domain {top_domain(nodes, nid)}")
        for f in ("prereqs", "related"):
            for ref in n[f] if isinstance(n[f], list) else []:
                if ref not in nodes:
                    err(f"master-index: {nid}.{f} references unknown id {ref}")
    # prerequisite cycles (DFS)
    state = {}

    def dfs(a, stack):
        state[a] = 1
        for b in nodes[a]["prereqs"] if isinstance(nodes[a]["prereqs"], list) else []:
            if b not in nodes:
                continue
            if state.get(b) == 1:
                err(f"master-index: prerequisite cycle {' -> '.join(stack + [a, b])}")
            elif b not in state:
                dfs(b, stack + [a])
        state[a] = 2

    for a in nodes:
        if a not in state:
            dfs(a, [])
    check_inventory_semantics(nodes)
    return nodes


def check_inventory_semantics(nodes):
    """Consistency checks beyond field shape: hierarchy, priorities, duplicates, granularity."""
    kids = {}
    for n in nodes.values():
        kids.setdefault(n["parent"], []).append(n)
    seen = {}
    for nid, n in nodes.items():
        if n["source_category"] not in SOURCE_CATEGORIES:
            err(f"master-index: {nid} bad source_category {n['source_category']}")
        if n["level"] in {"topic", "subtopic"}:
            ch = kids.get(nid) or []
            if not ch:
                err(f"master-index: {n['level']} {nid} has no children")
                continue
            best = min(c["priority"] for c in ch)
            if n["priority"] != best:
                err(f"master-index: {nid} priority {n['priority']} but its most important child is {best}")
            if n["level"] == "topic":
                count = sum(1 for c in ch if c["level"] == "concept") + sum(
                    1 for c in ch if c["level"] == "subtopic" for g in kids.get(c["id"], []))
                if count < MIN_TOPIC_CONCEPTS:
                    warn(f"master-index: topic {nid} has only {count} concepts (possible fragmentation)")
        if n["level"] != "concept":
            continue
        key = re.sub(r"[^a-z0-9]+", " ", n["title"].lower()).strip()
        if key in seen:
            err(f"master-index: {nid} and {seen[key]} have the same title {n['title']!r}")
        seen[key] = nid
        if len(n["scope"]) > BROAD_SCOPE_CHARS:
            warn(f"master-index: {nid} scope is {len(n['scope'])} chars (possibly too broad for one entry)")
        for f in ("prereqs", "related"):
            for ref in n[f]:
                if ref in nodes and nodes[ref]["level"] != "concept":
                    err(f"master-index: {nid}.{f} references {ref}, which is a {nodes[ref]['level']}, not a concept")
        for ref in n["prereqs"]:
            if ref in nodes and nodes[ref]["level"] == "concept" and int(nodes[ref]["priority"][1]) > int(n["priority"][1]):
                err(f"master-index: priority inversion: {nid} ({n['priority']}) requires {ref} ({nodes[ref]['priority']})")
        if set(n["prereqs"]) & set(n["related"]):
            err(f"master-index: {nid} lists the same id as prerequisite and related")


def top_domain(nodes, nid):
    seen = set()
    while nodes[nid]["parent"] is not None and nid not in seen:
        seen.add(nid)
        if nodes[nid]["parent"] not in nodes:
            break
        nid = nodes[nid]["parent"]
    return nid


# ---------------------------------------------------------------- sources
def check_sources(reg, gen):
    """Merge the human registry with generated fetch data (verification/generated/sources.yaml)."""
    out = {}
    for s in reg.get("sources") or []:
        sid = s.get("id", "<no id>")
        for f in ("id", "title", "url", "kind", "version", "license"):
            if not s.get(f):
                err(f"source-registry: {sid} missing {f}")
        if sid in out:
            err(f"source-registry: duplicate {sid}")
        if s.get("kind") not in {"official", "standard", "reference"}:
            err(f"source-registry: {sid} bad kind")
        g = (gen.get("sources") or {}).get(sid, {})
        out[sid] = {**s, "access_status": "NOT_ACCESSED", **g}
    for sid in (gen.get("sources") or {}).keys() - out.keys():
        err(f"generated/sources.yaml: {sid} is not in source-registry.yaml")
    for sid, s in out.items():
        if s["access_status"] not in {"NOT_ACCESSED", "FETCHED"}:
            err(f"generated/sources.yaml: {sid} bad access_status")
        if s["access_status"] == "FETCHED":
            for f in ("accessed_on", "sha256", "doc_version", "snapshot"):
                if not s.get(f):
                    err(f"generated/sources.yaml: {sid} FETCHED needs {f} (a hash alone is not an accessible source)")
            snap = ROOT / str(s.get("snapshot", ""))
            if not snap.is_file():
                err(f"generated/sources.yaml: {sid} snapshot {s.get('snapshot')} missing")
            elif hashlib.sha256(gzip.decompress(snap.read_bytes())).hexdigest() != s.get("sha256"):
                err(f"generated/sources.yaml: {sid} snapshot does not match recorded sha256")
    return out


# ---------------------------------------------------------------- verification records
def load_yaml(path):
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.exists() else {}


def merge_record(rec, res):
    """Human-authored record + machine-written results (verification/generated/<ID>.results.yaml)."""
    rec = {**rec, "claims": [dict(c) for c in rec.get("claims") or []], "examples": [dict(e) for e in rec.get("examples") or []]}
    for c in rec["claims"]:
        c.update({"check": "UNCHECKED", **((res.get("claims") or {}).get(c.get("id"), {}))})
    for e in rec["examples"]:
        e.update({"execution": "NOT_RUN", **((res.get("examples") or {}).get(e.get("id"), {}))})
    return rec


def check_record(eid, rec, sources, status, page_text):
    """Structural checks always; evidence gate when status is VERIFIED."""
    where = f"verification/{eid}.yaml"
    gate = status == "VERIFIED"
    if rec.get("id") != eid:
        err(f"{where}: id mismatch")
    claims = rec.get("claims") or []
    if gate and not claims:
        err(f"{where}: VERIFIED needs at least one claim")
    cids = set()
    for c in claims:
        cid = c.get("id", "<no id>")
        if cid in cids:
            err(f"{where}: duplicate claim {cid}")
        cids.add(cid)
        for f in ("id", "text", "importance", "support", "check"):
            if not c.get(f):
                err(f"{where}: claim {cid} missing {f}")
        if c.get("importance") not in {"critical", "important", "minor"}:
            err(f"{where}: claim {cid} bad importance")
        if c.get("support") not in {"direct", "inferred", "judgment"}:
            err(f"{where}: claim {cid} bad support")
        if c.get("check") not in {"PASS", "FAIL", "UNCHECKED"}:
            err(f"{where}: claim {cid} bad check")
        src = c.get("source")
        if c.get("support") != "judgment":
            if src not in sources:
                err(f"{where}: claim {cid} source {src!r} not in source-registry")
            elif not c.get("section"):
                err(f"{where}: claim {cid} needs the source section")
        if c.get("check") == "PASS" and c.get("support") != "judgment" and not c.get("quotes"):
            err(f"{where}: claim {cid} PASS needs verbatim quotes")
        if c.get("support") == "inferred" and c.get("importance") in {"critical", "important"}:
            by = {e.get("id"): e for e in rec.get("examples") or []}
            if not any(by.get(x, {}).get("execution") == "PASSED" for x in c.get("verified_by") or []):
                err(f"{where}: inferred claim {cid} needs verified_by with a PASSED example")
        if c.get("check") == "PASS":
            if c.get("support") != "judgment" and sources.get(src, {}).get("access_status") != "FETCHED":
                err(f"{where}: claim {cid} PASS but source {src} was never FETCHED")
            if not c.get("checked_on"):
                err(f"{where}: claim {cid} PASS needs checked_on")
        rv = c.get("review") or {}
        if c.get("support") != "judgment" and rv.get("entailment") not in {"FULL", "PARTIAL", "NONE"} and gate:
            err(f"{where}: VERIFIED but claim {cid} has no review.entailment")
        if gate and c.get("importance") in {"critical", "important"} and c.get("support") != "judgment"                 and rv.get("entailment") != "FULL":
            err(f"{where}: VERIFIED but claim {cid} review.entailment is {rv.get('entailment')}")
        if rv and (not rv.get("reviewer") or not isinstance(rv.get("independent"), bool)):
            err(f"{where}: claim {cid} review needs reviewer and boolean independent")
        for ver, res in (c.get("versions") or {}).items():
            if res not in {"PASS", "FAIL", "NOT_CHECKED"}:
                err(f"{where}: claim {cid} versions[{ver}] bad value {res}")
        if c.get("support") == "judgment" and c.get("importance") == "critical":
            err(f"{where}: claim {cid} critical claims cannot be pure judgment")
        if gate:
            if c.get("importance") in {"critical", "important"} and c.get("check") != "PASS":
                err(f"{where}: VERIFIED but {c['importance']} claim {cid} is {c.get('check')}")
            if c.get("check") == "FAIL":
                err(f"{where}: VERIFIED but claim {cid} FAILED")
    ind = (rec.get("independent_review") or {}).get("status")
    if ind not in {"DONE", "NOT_DONE"}:
        err(f"{where}: independent_review.status must be DONE or NOT_DONE")
    elif gate and ind == "NOT_DONE":
        err(f"{where}: VERIFIED requires independent_review.status DONE (recorded reviews are same-model passes)")
    if page_text is not None:
        markers = set(re.findall(r"\[(C\d+)\]", page_text))
        for m in markers - cids:
            err(f"{where}: page marker [{m}] has no claim record")
        for c in claims:
            if c.get("importance") in {"critical", "important"} and c.get("id") not in markers:
                err(f"{where}: {c.get('importance')} claim {c.get('id')} is not marked in the page")
    for ex in rec.get("examples") or []:
        xid = ex.get("id", "<no id>")
        if not (ROOT / ex.get("file", "")).is_file():
            err(f"{where}: example {xid} file {ex.get('file')} not found")
        mode = ex.get("execution")
        if mode not in {"NOT_RUN", "PASSED", "FAILED", "NOT_EXECUTABLE"}:
            err(f"{where}: example {xid} bad execution {mode}")
        if mode == "NOT_EXECUTABLE" and not ex.get("reason"):
            err(f"{where}: example {xid} NOT_EXECUTABLE needs a reason")
        if mode in {"PASSED", "FAILED"}:
            env = ex.get("environment") or {}
            for f in ("expected_output", "actual_output", "run_on", "dependencies"):
                if ex.get(f) is None:
                    err(f"{where}: example {xid} {mode} needs {f}")
            if not env.get("python") or not env.get("os"):
                err(f"{where}: example {xid} needs environment.python and environment.os")
        for run in ex.get("extra_runs") or []:
            if not run.get("python") or run.get("execution") not in {"PASSED", "FAILED"}:
                err(f"{where}: example {xid} extra_run needs python and execution PASSED|FAILED")
        if mode == "PASSED" and str(ex.get("expected_output")).strip() != str(ex.get("actual_output")).strip():
            err(f"{where}: example {xid} PASSED but expected != actual")
        if gate and mode not in {"PASSED", "NOT_EXECUTABLE"}:
            err(f"{where}: VERIFIED but example {xid} is {mode}")


# ---------------------------------------------------------------- progress + entries
def parse_front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (yaml.safe_load(m.group(1)) if m else None), (text[m.end():] if m else text)


def check_progress(prog, nodes, sources):
    entries = prog.get("entries") or {}
    for nid, n in nodes.items():
        if n["level"] == "concept" and nid not in entries:
            err(f"progress: concept {nid} has no record (run python scripts/validate.py --init-progress)")
    files = {p.stem: p for p in (ROOT / "entries").rglob("*.md")}
    for eid in files:
        if eid not in nodes:
            err(f"entries/{eid}.md: page not in inventory")
        elif eid not in entries:
            err(f"entries/{eid}.md: page has no progress.yaml record")
    for eid, e in entries.items():
        if eid not in nodes or nodes[eid]["level"] != "concept":
            err(f"progress: {eid} is not a concept in the inventory")
            continue
        cs, vs = e.get("content_status"), e.get("verification_status")
        if cs not in CONTENT:
            err(f"progress: {eid} bad content_status {cs}")
            continue
        if vs not in VERIF:
            err(f"progress: {eid} bad verification_status {vs}")
            continue
        hist = e.get("history") or []
        if not hist:
            err(f"progress: {eid} has no history")
        else:
            if (hist[-1].get("content"), hist[-1].get("verification")) != (cs, vs):
                err(f"progress: {eid} last history step != current status")
            if (hist[0].get("content"), hist[0].get("verification")) != ("NOT_STARTED", "NOT_CHECKED"):
                err(f"progress: {eid} history must start at NOT_STARTED/NOT_CHECKED")
            for a, b in zip(hist, hist[1:]):
                check_step(eid, a, b)
        has_file = eid in files
        if CONTENT.index(cs) >= 2 and not has_file:
            err(f"progress: {eid} is {cs} but entries/ has no page")
        if CONTENT.index(cs) < 2 and has_file:
            warn(f"progress: {eid} has a page but content_status is {cs}")
        if vs != "NOT_CHECKED" and CONTENT.index(cs) < 2:
            err(f"progress: {eid} verification {vs} requires content >= DRAFTED")
        if vs == "VERIFIED" and cs != "COMPLETE":
            err(f"progress: {eid} VERIFIED requires content COMPLETE")
        page_text = None
        if has_file:
            page_text = check_page(eid, files[eid], nodes[eid], cs)
        rec_path = ROOT / "verification" / f"{eid}.yaml"
        if rec_path.exists():
            res = load_yaml(ROOT / "verification" / "generated" / f"{eid}.results.yaml")
            check_record(eid, merge_record(load_yaml(rec_path), res), sources, vs, page_text)
            check_reviewer(eid, load_yaml(rec_path))
        elif vs in {"VERIFIED", "IN_PROGRESS"}:
            err(f"progress: {eid} {vs} but verification/{eid}.yaml is missing")


def check_reviewer(eid, rec):
    """Structure of the reviewer's input file; when independent_review is DONE, require a complete, settled review."""
    where = f"verification/review/{eid}.reviewer.yaml"
    path = ROOT / "verification" / "review" / f"{eid}.reviewer.yaml"
    done = (rec.get("independent_review") or {}).get("status") == "DONE"
    if not path.exists():
        if done:
            err(f"{where}: independent_review is DONE but the reviewer file is missing")
        return
    data = load_yaml(path)
    ids = {c["id"] for c in rec.get("claims") or []}
    sourced = [c["id"] for c in rec.get("claims") or [] if c.get("source") and c.get("support") != "judgment"]
    entries = data.get("claims") or {}
    for cid, e in entries.items():
        if cid not in ids:
            err(f"{where}: unknown claim {cid}")
        if e.get("verdict") not in {"PENDING", "AGREE", "DISAGREE", "UNABLE_TO_JUDGE"}:
            err(f"{where}: {cid} bad verdict {e.get('verdict')}")
        elif e["verdict"] in {"DISAGREE", "UNABLE_TO_JUDGE"} and not str(e.get("comment") or "").strip():
            err(f"{where}: {cid} {e['verdict']} needs a comment")
    if not done:
        return
    r = data.get("reviewer") or {}
    if not r.get("name") or not r.get("date") or r.get("kind") not in {"human", "other_model"} or r.get("independent_of_author") is not True:
        err(f"{where}: DONE needs reviewer name, date, kind human|other_model and independent_of_author: true")
    for cid in sourced:
        e = entries.get(cid) or {}
        settled = e.get("verdict") == "AGREE" or (
            e.get("verdict") == "DISAGREE" and e.get("resolution") in {"RESOLVED_CORRECTED", "RESOLVED_REJECTED"}
            and e.get("reviewer_accepts_resolution") is True and str(e.get("resolution_note") or "").strip())
        if not settled:
            err(f"{where}: {cid} is not settled (verdict {e.get('verdict', 'missing')})")
    if data.get("page_comments"):
        warn(f"{where}: page_comments present; confirm each was addressed")


def check_step(eid, a, b):
    ca, cb = a["content"], b["content"]
    va, vb = a["verification"], b["verification"]
    if ca not in CONTENT or cb not in CONTENT or va not in VERIF or vb not in VERIF:
        err(f"progress: {eid} history has an unknown status")
        return
    ia, ib = CONTENT.index(ca), CONTENT.index(cb)
    back = (ca, cb) in CONTENT_BACK
    if ib > ia + 1 or (ib < ia and not back):
        err(f"progress: {eid} illegal content transition {ca} -> {cb}")
    if va != vb and not (vb in VERIF_NEXT[va] or (vb == "NOT_CHECKED" and back)):
        err(f"progress: {eid} illegal verification transition {va} -> {vb}")
    if back and vb != "NOT_CHECKED":
        err(f"progress: {eid} content moved back {ca} -> {cb}; verification must reset to NOT_CHECKED")


def check_page(eid, path, node, cs):
    text = path.read_text(encoding="utf-8")
    fm, body = parse_front_matter(text)
    rel = path.relative_to(ROOT).as_posix()
    if fm is None:
        err(f"{rel}: missing front matter")
        return text
    exp_dir = f"entries/{eid.split('-')[0].lower()}"
    if path.parent.relative_to(ROOT).as_posix() != exp_dir:
        err(f"{rel}: must live in {exp_dir}/")
    for f, want in (("id", eid), ("title", node["title"]), ("priority", node["priority"]),
                    ("domain", eid.split("-")[0])):
        if fm.get(f) != want:
            err(f"{rel}: front matter {f}={fm.get(f)!r}, inventory says {want!r}")
    if cs == "COMPLETE":
        heads = {h.strip().lower() for h in re.findall(r"^#{2,3}\s+(.+)$", body, re.M)}
        for sec in REQUIRED_SECTIONS:
            if not any(h.startswith(sec.lower()) for h in heads):
                err(f"{rel}: COMPLETE page lacks section '{sec}'")
    return text


# ---------------------------------------------------------------- links, index, audit
def check_links():
    for md in ROOT.rglob("*.md"):
        if any(part in {".venv", "_site", ".pytest_cache"} for part in md.parts) or md.name == "CLAUDE.md":
            continue
        for target in MD_LINK_RE.findall(md.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            if not (md.parent / target.split("#")[0]).exists():
                err(f"{md.relative_to(ROOT).as_posix()}: broken link {target}")


def render_index(nodes, prog):
    ents = prog.get("entries") or {}
    kids = {}
    for n in nodes.values():
        kids.setdefault(n["parent"], []).append(n)
    out = ["# Master Index", "",
           "<!-- GENERATED by scripts/validate.py --write-index from master-index.yaml and progress.yaml. Do not edit. -->",
           "", "Status format: content / verification. Only concepts have pages.", ""]

    def walk(n, depth):
        label = f"**{n['id']}** {n['title']} ({n['priority']})"
        if n["level"] == "concept":
            e = ents.get(n["id"], {})
            path = f"entries/{n['id'].split('-')[0].lower()}/{n['id']}.md"
            if (ROOT / path).exists():
                label = f"[{label}]({path})"
            label += f" — {e.get('content_status', 'NOT_STARTED')} / {e.get('verification_status', 'NOT_CHECKED')}"
            if n.get("review_cycle"):
                label += f" — ↻ review {n['review_cycle']}"
            label += f" — {n['scope']}"
        out.append("  " * depth + "- " + label)
        for k in kids.get(n["id"], []):
            walk(k, depth + 1)

    for d in kids.get(None, []):
        walk(d, 0)
    return "\n".join(out) + "\n"


def render_interview_index(nodes, prog):
    """Cross-domain index of concepts tagged `interview`; there is no interview domain, expectations live inside entries."""
    ents = prog.get("entries") or {}
    out = ["# Interview index", "",
           "<!-- GENERATED by scripts/validate.py --write-index from the `interview` tag in master-index.yaml. Do not edit. -->", "",
           "Concepts whose entries carry an \"Interview expectations\" section of particular weight. Tagging is editorial judgment informed by the interview sources in "
           "[the audit record](verification/inventory-audit.yaml); it is not exhaustive. Status format: content / verification.", ""]
    by_dom = {}
    for n in nodes.values():
        if n["level"] == "concept" and "interview" in (n.get("tags") or []):
            by_dom.setdefault(n["id"].split("-")[0], []).append(n)
    total = sum(len(v) for v in by_dom.values())
    out += [f"{total} tagged concepts.", ""]
    for d, items in sorted(by_dom.items(), key=lambda kv: list(nodes).index(kv[0])):
        out += [f"## {d} {nodes[d]['title']} ({len(items)})", ""]
        for n in sorted(items, key=lambda n: (n["priority"], n["id"])):
            e = ents.get(n["id"], {})
            path = f"entries/{d.lower()}/{n['id']}.md"
            label = f"**{n['id']}** {n['title']} ({n['priority']})"
            if (ROOT / path).exists():
                label = f"[{label}]({path})"
            out.append(f"- {label} — {e.get('content_status', 'NOT_STARTED')} / {e.get('verification_status', 'NOT_CHECKED')}")
        out.append("")
    return "\n".join(out) + "\n"


def check_audit(nodes=None):
    a = load("verification/inventory-audit.yaml")
    if a is None:
        return
    lenses = a.get("lenses") or {}
    for l in AUDIT_LENSES:
        if lenses.get(l, {}).get("status") not in AUDIT_STATUS:
            err(f"inventory-audit: lens {l} missing or bad status")
    done = all(lenses.get(l, {}).get("status") == "DONE" for l in AUDIT_LENSES)
    claim = a.get("coverage_claim")
    if claim not in {"NONE", "PARTIAL", "AUDITED_WITH_LIMITATIONS"}:
        err("inventory-audit: coverage_claim must be NONE | PARTIAL | AUDITED_WITH_LIMITATIONS (never 'complete')")
    if claim == "AUDITED_WITH_LIMITATIONS" and not (done and a.get("limitations")):
        err("inventory-audit: AUDITED_WITH_LIMITATIONS needs all lenses DONE and documented limitations")
    for l in AUDIT_LENSES:
        if lenses.get(l, {}).get("status") == "DONE" and not lenses[l].get("sources"):
            err(f"inventory-audit: lens {l} DONE without recorded sources")
    for l in AUDIT_LENSES:
        for src in lenses.get(l, {}).get("sources") or []:
            for f in ("id", "url", "accessed_on", "sha256"):
                if not src.get(f):
                    err(f"inventory-audit: {l} source {src.get('id')} missing {f}")
            fp = src.get("items_file")
            if fp:
                if not (ROOT / fp).is_file():
                    err(f"inventory-audit: {fp} missing")
                elif load(fp).get("sha256") != src.get("sha256"):
                    err(f"inventory-audit: {fp} was captured from a different page version than the recorded hash")
    if nodes is None:
        return
    concepts = {i for i, n in nodes.items() if n["level"] == "concept"}
    size = (a.get("inventory_size") or {}).get("concepts")
    if size != len(concepts):
        warn(f"inventory-audit: audited inventory had {size} concepts, current inventory has {len(concepts)}; audit may be stale")
    for l in AUDIT_LENSES:
        for fnd in lenses.get(l, {}).get("findings") or []:
            if fnd.get("concept") not in concepts:
                err(f"inventory-audit: {l} finding references unknown concept {fnd.get('concept')}")
    for c in a.get("priority_changes") or []:
        if c.get("concept") not in concepts:
            err(f"inventory-audit: priority change references unknown concept {c.get('concept')}")
        elif nodes[c["concept"]]["priority"] != c.get("to"):
            err(f"inventory-audit: {c['concept']} priority is {nodes[c['concept']]['priority']} but the audit recorded {c.get('to')}")
    for ex in (a.get("job_signal") or {}).get("themes") or []:
        for cid in ex.get("covered_by") or []:
            if cid not in concepts:
                err(f"inventory-audit: job theme {ex.get('theme')!r} maps to unknown concept {cid}")
    for m in a.get("merges_and_removals") or []:
        if m.get("target") and m["target"] not in concepts:
            err(f"inventory-audit: merge target {m['target']} is not a concept")
        gone = re.sub(r"[^a-z0-9]+", " ", str(m.get("removed_title", "")).lower()).strip()
        if gone and any(re.sub(r"[^a-z0-9]+", " ", nodes[c]["title"].lower()).strip() == gone for c in concepts):
            err(f"inventory-audit: {m['removed_title']!r} is recorded as merged/removed but a concept with that title still exists")
    if not a.get("limitations"):
        err("inventory-audit: limitations must be recorded")


def init_progress(nodes):
    """Append NOT_STARTED/NOT_CHECKED records for concepts that have none (text append: never rewrites the file)."""
    import datetime
    path = ROOT / "progress.yaml"
    have = set((yaml.safe_load(path.read_text(encoding="utf-8")).get("entries") or {}).keys())
    today = datetime.date.today().isoformat()
    add = [f'  {nid}: {{content_status: NOT_STARTED, verification_status: NOT_CHECKED, history: '
           f'[{{content: NOT_STARTED, verification: NOT_CHECKED, on: {today}, note: "registered by inventory"}}]}}'
           for nid, n in nodes.items() if n["level"] == "concept" and nid not in have]
    if add:
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(add) + "\n")
    print(f"progress.yaml: added {len(add)} records")


def main():
    inv, reg, prog = load("master-index.yaml"), load("source-registry.yaml"), load("progress.yaml")
    if None in (inv, reg, prog):
        return finish()
    nodes = check_inventory(inv)
    if "--init-progress" in sys.argv:
        init_progress(nodes)
        prog = load("progress.yaml")
    sources = check_sources(reg, load_yaml(ROOT / "verification" / "generated" / "sources.yaml"))
    check_progress(prog, nodes, sources)
    check_audit(nodes)
    idx = ROOT / "MASTER_INDEX.md"
    want = render_index(nodes, prog)
    iidx = ROOT / "INTERVIEW_INDEX.md"
    iwant = render_interview_index(nodes, prog)
    if "--write-index" in sys.argv:
        idx.write_text(want, encoding="utf-8", newline="\n")
        iidx.write_text(iwant, encoding="utf-8", newline="\n")
    else:
        for path, text in ((idx, want), (iidx, iwant)):
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                err(f"{path.name} is stale or missing: run python scripts/validate.py --write-index")
    check_links()
    finish()


def finish():
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
