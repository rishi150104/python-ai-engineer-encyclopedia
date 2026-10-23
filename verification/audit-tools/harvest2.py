"""Second harvest: roadmap.sh role definitions and public job postings (Greenhouse boards). Output audit/<id>.json"""
import hashlib
import html
import json
import re
from pathlib import Path

S = Path(__file__).parent
OUT = S / "audit"
TODAY = "2026-10-23"
NOISE = re.compile(r"^(horizontal node|vertical node|Scrimba|Pre-requisites|Roadmap|Join|Click|Check|Visit|Learn more|Free|Newsletter)", re.I)

ROADMAPS = ["ai-engineer", "prompt-engineering", "ai-agents", "backend", "python", "system-design", "api-design", "docker",
            "git-github", "postgresql-dba", "redis", "software-design-architecture", "code-review", "qa", "devops", "linux"]


def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


for r in ROADMAPS:
    raw = (S / "rm" / f"{r}.json").read_bytes()
    d = json.loads(raw)
    labels = []
    for n in walk(d.get("nodes")):
        data = n.get("data") if isinstance(n.get("data"), dict) else None
        if data and data.get("label") and n.get("type") in {"topic", "subtopic"}:
            labels.append(re.sub(r"\s+", " ", data["label"]).strip())
    labels = [l for l in dict.fromkeys(labels) if not NOISE.match(l) and 2 < len(l) < 120]
    (OUT / f"R-RM-{r}.json").write_text(json.dumps({
        "id": f"R-RM-{r}", "lens": "role_competencies", "title": f"roadmap.sh {d.get('title', r)} roadmap (topic and subtopic nodes)",
        "url": f"https://roadmap.sh/{r}", "kind": "reference", "accessed_on": TODAY, "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw), "items": labels}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(r, len(labels))

ROLE = re.compile(r"(AI|A\.I\.|LLM|Applied|Machine Learning|\bML\b|Backend|Back-End|Back End|Software Engineer|Forward Deployed|Solutions Engineer|Platform|Infrastructure|Python)", re.I)
BAD = re.compile(r"(Manager|Director|Recruit|Sales|Account|Marketing|Legal|Counsel|Finance|Designer|Researcher|Scientist|Security Engineer|Hardware|Mechanical|Data Center|GTM|Partner|Support)", re.I)
BULLET = re.compile(r"(experience|proficien|knowledge|familiar|understanding|ability|strong|skilled|background|expertise|comfortable|fluen|\b\d\+? years)", re.I)
total = 0
for b in ["anthropic", "databricks", "scaleai", "assemblyai", "vercel", "cloudflare", "mongodb", "datadog"]:
    raw = (S / "jobs" / f"{b}.json").read_bytes()
    jobs = json.loads(raw)["jobs"]
    sel = [j for j in jobs if re.search(r"Engineer", j["title"], re.I) and ROLE.search(j["title"]) and not BAD.search(j["title"])]
    items, ids = [], []
    for j in sel:
        content = html.unescape(j.get("content") or "")
        for li in re.findall(r"<li[^>]*>(.*?)</li>", content, re.S | re.I):
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", li)).strip()
            if 15 < len(t) < 260 and BULLET.search(t):
                items.append(t)
        ids.append({"id": j["id"], "title": j["title"], "url": j.get("absolute_url")})
    total += len(sel)
    (OUT / f"R-JOBS-{b}.json").write_text(json.dumps({
        "id": f"R-JOBS-{b}", "lens": "role_competencies", "title": f"{b} public job postings (Greenhouse board), engineering roles matching AI/backend/platform titles",
        "url": f"https://boards-api.greenhouse.io/v1/boards/{b}/jobs?content=true", "kind": "reference", "accessed_on": TODAY,
        "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "postings": ids, "items": items}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(b, len(jobs), "jobs;", len(sel), "selected;", len(items), "requirement bullets")
print("selected postings:", total)
