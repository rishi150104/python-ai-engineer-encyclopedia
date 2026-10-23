"""Build verification/inventory-audit.yaml and verification/audit-sources/*.json from harvested data."""
import json
import re
from pathlib import Path

import yaml

S = Path(__file__).parent
ROOT = Path("<REPO_ROOT>")  # redacted machine path: set to the repository root
km = json.loads((S / "keymap.json").read_text(encoding="utf-8"))
inv = {n["id"]: n for n in yaml.safe_load((ROOT / "master-index.yaml").read_text(encoding="utf-8"))["nodes"]}


def I(*keys):
    return [km[k] for k in keys]


# Sources whose item lists (titles only) are kept in the repo. Not kept: roadmap.sh (content license), vendor docs with no
# open license (Anthropic), and job postings (only counts, posting ids and URLs are kept).
STORE = {"A-PY-CONTENTS", "A-FASTAPI", "A-PYDANTIC", "A-PG", "A-SQLA", "A-ALEMBIC", "A-PYTEST", "A-NUMPY", "A-DOCKER", "A-K8S", "A-LANGCHAIN",
         "A-LANGGRAPH", "A-REDIS", "P-12FACTOR", "P-OWASP-API", "P-OWASP-TOP10", "P-AWS-WAF", "P-SRE", "I-SDPRIMER", "I-BACKEND-QA", "I-TIH-ALGO"}
LICENSE = {"A-PY-CONTENTS": "PSF License Agreement", "A-FASTAPI": "MIT", "A-PYDANTIC": "MIT", "A-SQLA": "MIT", "A-ALEMBIC": "MIT", "A-PYTEST": "MIT",
           "A-NUMPY": "BSD-3-Clause", "A-DOCKER": "Apache-2.0", "A-K8S": "CC BY 4.0", "A-LANGCHAIN": "MIT", "A-LANGGRAPH": "MIT",
           "P-OWASP-API": "CC BY-SA 4.0", "P-OWASP-TOP10": "CC BY-SA 4.0", "P-12FACTOR": "MIT", "P-SRE": "CC BY-NC-ND 4.0 (titles only)",
           "I-SDPRIMER": "CC BY 4.0", "I-BACKEND-QA": "see repository", "I-TIH-ALGO": "MIT", "A-PG": "PostgreSQL License", "A-REDIS": "see site terms",
           "P-AWS-WAF": "AWS site terms (6 pillar names only)"}

ADDED = [  # (concept key, [trigger sources], trigger items)
    ("ai.api.stopreasons", ["A-ANTHROPIC"], "Refusals and fallback; Streaming refusals; Stop reasons"),
    ("ai.api.cloud", ["A-ANTHROPIC"], "Amazon Bedrock; Google Cloud; Microsoft Foundry"),
    ("db.wal", ["A-PG", "R-RM-postgresql-dba"], "28. Reliability and the Write-Ahead Log; Write-ahead Log"),
    ("db.collation", ["A-PG"], "23. Localization"),
    ("db.extensions", ["A-PG", "R-RM-postgresql-dba"], "F. Additional Supplied Modules and Extensions; Adding Extra Extensions"),
    ("db.catalog", ["A-PG"], "35. The Information Schema; 52. System Catalogs"),
    ("db.config", ["A-PG", "R-RM-postgresql-dba"], "19. Server Configuration; Using pg_upgrade"),
    ("db.errors", ["A-PG"], "A. PostgreSQL Error Codes"),
    ("db.internals", ["R-RM-postgresql-dba"], "Buffer Management; Lock Management; Physical Storage and File Layout"),
    ("db.redis.adv", ["R-RM-redis", "A-REDIS"], "Bitmaps; HyperLogLog; Streams; Geospatial Indexes; Pub/Sub; Lua Scripting; Probabilistic types"),
    ("db.redis.persist", ["R-RM-redis"], "Persistence Options; How RDB Works?; How AOF Works?; Redis Sentinel"),
    ("be.patch", ["A-FASTAPI"], "Body - Updates"),
    ("be.fa.advanced", ["A-FASTAPI"], "Custom Request and APIRoute class; Extending OpenAPI"),
    ("be.pyd.typeadapter", ["A-PYDANTIC"], "Type Adapter; Validation Decorator"),
    ("be.pyd.v1v2", ["A-FASTAPI", "A-PYDANTIC"], "Migrate from Pydantic v1 to Pydantic v2; Migration Guide"),
    ("swe.unittest", ["R-RM-python", "A-PY-CONTENTS", "A-PYTEST"], "unittest / pyUnit; unittest module; How to use unittest-based tests with pytest"),
    ("swe.pytestplugins", ["A-PYTEST"], "Writing plugins; Writing hook functions"),
    ("swe.testtypes", ["R-RM-qa"], "Smoke Testing; Sanity Testing; Exploratory Testing; UAT; Performance Testing; Test Planning"),
    ("swe.bdd", ["R-RM-qa"], "BDD; ATDD"),
    ("swe.gitadv", ["R-RM-git-github"], "Git Stash Basics; Cherry Picking Commits; Git hooks; Git Worktree; Managing Tags; Git LFS; Submodules"),
    ("swe.lld", ["I-SDPRIMER"], "Object-oriented design interview questions with solutions"),
    ("cs.intervals", ["I-TIH-ALGO"], "Interval; Matrix (study-guide topics)"),
    ("ai.own.hf", ["R-RM-ai-engineer"], "Hugging Face Hub; Hugging Face Inference SDK; Sentence Transformers"),
    ("ai.imagegen", ["R-RM-ai-engineer"], "Image Generation; DALL-E API"),
    ("ai.mcp.build", ["R-RM-ai-engineer", "R-RM-ai-agents"], "Building an MCP Server; Building an MCP Client; Connect to Local/Remote Server; Creating MCP Servers"),
    ("ai.role", ["R-RM-ai-engineer", "R-AIE-BOOK"], "What is an AI Engineer?; AI Engineering Versus ML Engineering"),
    ("ai.planning", ["R-AIE-BOOK"], "Planning AI Applications; Use Case Evaluation; Setting Expectations; Maintenance"),
    ("ai.inferperf", ["R-AIE-BOOK"], "Inference Performance Metrics; Inference Service Optimization"),
    ("sys.patterns", ["R-RM-software-design-architecture"], "Architectural Patterns; Publish-Subscribe; Microkernel; Pipes and Filters"),
    ("sys.cloudpatterns", ["R-RM-system-design"], "Cloud Design Patterns: Queue-Based Load Leveling; Competing Consumers; Claim Check; Strangler Fig; Sidecar"),
    ("ops.servicemesh", ["R-RM-devops", "R-RM-backend"], "Service Mesh; Istio; Linkerd"),
    ("ops.gitops", ["R-RM-devops"], "GitOps; ArgoCD; FluxCD"),
    ("ops.email", ["R-RM-devops"], "SMTP; SPF; DMARC; Domain Keys"),
    ("ops.k8s.workloads", ["A-K8S"], "Workload Management; ReplicaSet; StatefulSets; DaemonSet; Jobs"),
    ("ops.k8s.network", ["A-K8S"], "Services, Load Balancing, and Networking; Ingress Controllers; Network Policies"),
    ("ops.k8s.config", ["A-K8S"], "ConfigMaps; Persistent Volumes; Good practices for Kubernetes Secrets"),
    ("ops.k8s.resources", ["A-K8S"], "Resource Management for Pods and Containers; Autoscaling Workloads"),
    ("ops.k8s.kubectl", ["A-K8S"], "Organizing Cluster Access Using kubeconfig Files (kubectl workflow)"),
    ("py.introspect", ["A-PY-CONTENTS"], "6.3. The dir() Function; inspect; types"),
    ("py.compress", ["A-PY-CONTENTS", "R-RM-linux"], "10.9. Data Compression; zlib; gzip; zipfile; tarfile; Archiving and Compressing"),
    ("py.markup", ["A-PY-CONTENTS"], "xml.etree.ElementTree; html.parser"),
    ("py.i18n", ["A-PY-CONTENTS"], "gettext; locale"),
    ("py.ast", ["A-PY-CONTENTS"], "ast; tokenize; symtable"),
    ("py.notebooks", ["A-PY-CONTENTS"], "14.2. Alternatives to the Interactive Interpreter"),
    ("ml.bigdata", ["R-JOBS"], "Apache Spark (18 requirement bullets)"),
]
INTERNAL = I("py.run", "py.syntax", "py.io", "py.idioms", "py.logconfig", "cs.cpu", "web.cidr", "db.keys", "swe.aiassist", "ops.domains",
             "sys.eventsourcing", "ai.fw.agentsdk", "ai.tools.server", "ai.usecases", "ai.synthetic", "ai.realtime", "ml.rankmetrics")
MERGED = [  # (kind, removed concept title, change description, surviving concept key)
    ("duplicate", "Parameterized queries and SQL injection prevention", "db.injection merged into", "sec.injection"),
    ("duplicate", "Connection pooling in applications", "be.dbpool merged into", "db.pooling"),
    ("duplicate", "Architecture of a RAG service", "ai.arch.rag merged into", "ai.rag.arch"),
    ("duplicate", "Health checks, readiness and liveness", "ops.health merged into", "be.health"),
    ("duplicate", "CDN and edge architecture", "sys.cdnarch merged into", "web.cdn"),
    ("duplicate", "Search and indexing subsystems", "sys.search merged into", "db.search"),
    ("duplicate", "Idempotency, retries and exactly-once myths", "sys.idemretry merged into", "be.idempotency"),
    ("fragmentation", "Security for AI features: pointer to the AI security topics", "sec.ai removed (pointer-only); AI security lives in the ai.sec topic", None),
    ("too broad", "Evaluation metrics: precision, recall, F1 and ranking metrics", "ml.metrics split into classification/regression metrics and ranking/retrieval metrics", "ml.rankmetrics"),
]
REPRIO = [("ops.k8s", "P2", "P1", "Kubernetes appears in 85 of 3096 sampled job-requirement bullets (2.7%), more than docker alone (67 bullets incl. containers)"),
          ("swe.tech-comm", "P2", "P1", "communication/stakeholders appear in 119 bullets (3.8%)"),
          ("web.jsonschema", "P2", "P1", "needed as a prerequisite of OpenAPI, Pydantic schema export and LLM tool schemas"),
          ("py.hash", "P1", "P0", "dict and set depend on hashability"), ("py.pickle", "P2", "P1", "prerequisite of insecure-deserialization (P1)"),
          ("ops.cd", "P2", "P1", "prerequisite of environments and migrations-in-deploy (P1)"),
          ("ai.api.portability", "P2", "P1", "prerequisite of framework-vs-SDK choice (P1)"), ("ml.nn", "P2", "P1", "prerequisite of transformer concepts (P1)")]
EXCLUSIONS = [
    ("non-Python language stacks and frameworks (Java, Scala, Go, Rust, C++, PHP, Ruby; Node.js)", "SCOPE: Python backend. In sampled job bullets Java/Scala/Go/Rust/C++ appear in 268 of 3096 (8.7%): flagged as a decision for the user",
     "R-RM-backend; R-RM-devops; R-JOBS-*"),
    ("frontend and web UI engineering (HTML/CSS/JS, SPAs, SSR/CSR, React, browsers)", "outside backend-to-AI scope; JS/TS/React appear in 121 of 3096 job bullets (3.9%), mostly full-stack roles", "R-RM-backend; R-RM-qa; I-BACKEND-QA; R-JOBS-*"),
    ("CPython installation, building and platform-specific usage (Windows, macOS, Unix, WebAssembly), C API and extension internals", "environment setup and implementer detail, not application development", "A-PY-CONTENTS"),
    ("deprecated or removed stdlib modules; GUI, terminal-UI, multimedia and legacy internet-protocol modules (tkinter, turtle, curses, audio*, nntplib, telnetlib, imap/pop/ftp clients, xmlrpc)", "not used in modern backend/AI work", "A-PY-CONTENTS"),
    ("language-implementer detail: full grammar, lexical-analysis minutiae, frame/code-object internals", "kept at concept level only (py.bytecode, py.ast)", "A-PY-CONTENTS"),
    ("PostgreSQL installation, server programming (extending SQL, writing FDWs and index access methods), C client interfaces and source-level internals", "beyond application-developer needs; awareness via db.internals, db.config", "A-PG; R-RM-postgresql-dba"),
    ("Kubernetes cluster administration (scheduler internals, dynamic resource allocation, node management, Windows nodes, CSI/storage classes, API server internals)", "operator-level; developer-facing concepts are ops.k8s.*", "A-K8S"),
    ("individual products and vendors (specific databases, vector databases, observability vendors, CI vendors, cloud-provider services, LLM vendors and model versions)", "covered by category concepts; product specifics change faster than the encyclopedia. AWS/Azure/GCP appear in 91 job bullets (2.9%): flagged as a decision", "R-RM-*; R-JOBS-*; A-ANTHROPIC"),
    ("career and process content (resumes, behavioral interviews, negotiation, project-management methodologies, team organization, SRE organization/culture chapters)", "not technical knowledge; agile at awareness (swe.agile), communication in swe.tech-comm", "I-TIH-ALGO; I-BACKEND-QA; P-SRE; R-RM-qa"),
    ("QA-role tooling and manual-testing process (test-management tools, mobile and browser automation suites, accessibility tools)", "developer-owned testing is covered; QA specialization is not", "R-RM-qa"),
    ("Linux system administration beyond developer needs (boot process, LVM, disks, DHCP, netfilter internals)", "developer-level Linux is ops.linux", "R-RM-linux; R-RM-devops"),
    ("AI research and training infrastructure (distributed training, GPU kernels, model-architecture and alignment research)", "awareness only (ml.hardware, ai.training, ai.own.*)", "R-AIE-BOOK; R-JOBS-*"),
    ("transient provider features and marketing/navigation content (Anthropic fast mode, task budgets, customer stories, console pages)", "generalized into concepts such as ai.reasoning, ai.prod.latency", "A-ANTHROPIC"),
    ("site chrome, translations, legal, sponsorship and navigation lines", "not topics", "all"),
    ("sustainability pillar of the AWS Well-Architected Framework", "niche for this audience", "P-AWS-WAF"),
    ("worked system-design problems beyond the six included (Pastebin, Twitter timeline, web crawler, Mint, key-value store, sales ranking)", "can be added on demand as sys.ex.* concepts", "I-SDPRIMER"),
]
JOBSIGNAL = [  # term, bullets, share %, covering concept keys
    ("python", 160, 5.2, ["py.def", "py.async", "be.fa.app"]), ("LLM", 109, 3.5, ["ai.whatllm", "ai.api.messages"]), ("agents", 129, 4.2, ["ai.agents.loop", "ai.agents.vs"]),
    ("RAG / retrieval", 45, 1.5, ["ai.rag.arch", "ai.rag.retrieve"]), ("embeddings / vector search", 29, 0.9, ["ai.embed.concept", "ai.vec.db"]), ("prompting", 24, 0.8, ["ai.prompt.structure"]),
    ("evaluation / evals", 98, 3.2, ["ai.eval.fund", "ai.eval.datasets"]), ("fine-tuning", 20, 0.6, ["ai.own.finetune", "ai.own.decision"]), ("MCP / tool use", 27, 0.9, ["ai.tools.loop", "ai.mcp"]),
    ("inference", 45, 1.5, ["ai.inferperf", "ai.own.local"]), ("GPU / CUDA", 28, 0.9, ["ml.hardware"]), ("machine learning (general)", 146, 4.7, ["ml.supervised", "ml.metrics"]),
    ("PyTorch / TensorFlow", 17, 0.5, ["ml.pytorch"]), ("safety / guardrails / red teaming", 37, 1.2, ["ai.sec.inject", "ai.sec.redteam"]), ("FastAPI / Django / Flask", 3, 0.1, ["be.fa.app", "be.otherfw"]),
    ("APIs / REST", 116, 3.7, ["web.rest", "web.apidesign"]), ("gRPC / GraphQL", 7, 0.2, ["web.grpc", "web.graphql"]), ("SQL / PostgreSQL", 41, 1.3, ["db.sqlbasics", "db.joins"]),
    ("NoSQL / Redis / MongoDB", 40, 1.3, ["db.redis", "db.document"]), ("Kafka / queues / streaming", 38, 1.2, ["sys.queues", "be.broker"]), ("distributed systems", 238, 7.7, ["sys.partial", "sys.consistency"]),
    ("microservices", 3, 0.1, ["sys.monolith", "sys.boundaries"]), ("async / concurrency", 25, 0.8, ["py.async", "cs.concfund"]), ("caching", 17, 0.5, ["sys.cache", "db.rediscache"]),
    ("Docker / containers", 67, 2.2, ["ops.dockerfile", "ops.containers"]), ("Kubernetes", 85, 2.7, ["ops.k8s", "ops.k8s.workloads"]), ("Terraform / IaC", 41, 1.3, ["ops.iac"]),
    ("CI/CD", 54, 1.7, ["ops.ciconcept", "ops.ci"]), ("cloud (AWS/Azure/GCP)", 91, 2.9, ["ops.cloudbasics", "ops.compute"]), ("Linux", 27, 0.9, ["ops.cli", "ops.procs"]),
    ("observability / monitoring", 174, 5.6, ["ops.metrics", "ops.logagg", "be.tracing"]), ("on-call / incidents", 50, 1.6, ["ops.incident"]), ("testing", 64, 2.1, ["swe.testpyramid", "swe.pytest"]),
    ("security / authentication", 157, 5.1, ["sec.authn", "sec.authz", "sec.owasp"]), ("git / code review", 16, 0.5, ["swe.gitbasics", "swe.review"]), ("system design / architecture", 205, 6.6, ["sys.requirements", "sys.scale"]),
    ("performance / latency", 208, 6.7, ["be.perf", "sys.latency"] if False else ["sys.latency", "be.workers"]), ("cost", 43, 1.4, ["ops.cost", "ai.prod.cost"]), ("data pipelines / Spark", 49, 1.6, ["ml.bigdata", "ai.prod.pipelines"]),
    ("pandas / numpy", 1, 0.0, ["ml.pandas", "ml.numpy"]), ("communication / stakeholders", 119, 3.8, ["swe.tech-comm"]), ("mentoring / leadership", 130, 4.2, []),
    ("Java / Scala / Go / Rust / C++", 268, 8.7, []), ("JavaScript / TypeScript / React", 121, 3.9, []),
]


def source_record(sid):
    d = json.loads((S / "audit" / f"{sid}.json").read_text(encoding="utf-8"))
    res = S / "results" / f"{sid}.json"
    rec = {"id": sid, "title": d["title"], "url": d["url"], "kind": d["kind"], "accessed_on": d["accessed_on"], "sha256": d["sha256"], "bytes": d["bytes"]}
    if res.exists():
        r = json.loads(res.read_text(encoding="utf-8"))
        rec.update(items=len(d["items"]), noise_items=len(r["noise"]), auto_candidates=len(r["matched"]))
        rec["manual_review"] = "every item read; coverage judged by the reviewer, not by the auto-match"
    else:
        rec.update(postings_selected=len(d.get("postings", [])), requirement_bullets=len(d["items"]))
        rec["postings"] = [{"id": p["id"], "title": p["title"], "url": p["url"]} for p in d.get("postings", [])]
    if sid in STORE:
        out = ROOT / "verification" / "audit-sources"
        out.mkdir(exist_ok=True)
        (out / f"{sid}.json").write_text(json.dumps({"id": sid, "url": d["url"], "accessed_on": d["accessed_on"], "sha256": d["sha256"],
                                                      "license": LICENSE.get(sid), "items": d["items"]}, ensure_ascii=False, indent=0), encoding="utf-8")
        rec["items_file"] = f"verification/audit-sources/{sid}.json"
        rec["items_license"] = LICENSE.get(sid)
    else:
        rec["items_file"] = None
        rec["items_not_stored_reason"] = "job postings: only ids/urls/counts kept" if sid.startswith("R-JOBS") else "no redistribution licence for the item list; counts and hash only"
    return rec


ids = sorted(p.stem for p in (S / "audit").glob("*.json"))
bylens = {}
for sid in ids:
    d = json.loads((S / "audit" / f"{sid}.json").read_text(encoding="utf-8"))
    bylens.setdefault(d["lens"], []).append(sid)
lens_of = {s: l for l, v in bylens.items() for s in v}


def lens_findings(lens):
    out = []
    for key, srcs, items in ADDED:
        ls = {lens_of.get(s, "role_competencies" if s == "R-JOBS" else None) for s in srcs}
        if lens in ls:
            out.append({"action": "ADDED_CONCEPT", "concept": km[key], "title": inv[km[key]]["title"], "sources": srcs, "triggering_items": items})
    return out


ext = []
for n in inv.values():
    m = re.search(r"Also covers (.*)\.$", n["scope"])
    if m and n["level"] == "concept":
        ext.append({"concept": n["id"], "title": n["title"], "added_to_scope": m.group(1)})

audit = {
    "schema_version": 2,
    "coverage_claim": "PARTIAL",
    "coverage_claim_reason": "Four lenses were examined against 47 sources, but two lenses are thin (production, interview), the reviewer is the same model that built the inventory, "
                             "and automatic matching was measured at ~52% precision, so no claim stronger than PARTIAL is made.",
    "date": "2026-10-23",
    "inventory_size": {"concepts": sum(1 for n in inv.values() if n["level"] == "concept"), "topics_and_subtopics": sum(1 for n in inv.values() if n["level"] in {"topic", "subtopic"}), "domains": 11},
    "method": [
        "1. Build inventory from CLAUDE.md section 4 plus a first internal review pass (duplicates, fragmentation, missing foundations).",
        "2. Fetch source tables of contents / indexes / role definitions / public job postings (raw HTTP, 2026-10-23); extract titles, headings, roadmap nodes, requirement bullets.",
        "3. Token-weighted auto-matching of source items to concepts, used only to generate candidates (measured precision below).",
        "4. The reviewer read every item list (matched and unmatched) and judged coverage against the inventory by reading; dispositions are recorded at group level, with per-item records only for gaps.",
        "5. Gaps were closed by adding concepts, extending scopes, merging duplicates or re-prioritizing; validator and structure audit re-run after each change.",
        "6. Matcher quality and residual gaps were sampled with a fixed seed (7).",
    ],
    "matcher_quality": {
        "seed": 7,
        "matched_sample_n": 40, "matched_sample_right_concept": 21, "precision_estimate": 0.52,
        "interpretation": "About half of auto-matches pointed to a plausible covering concept; spurious matches came from generic single words (Databases, Policies, Python API). Auto-matches are therefore NOT counted as coverage evidence.",
        "unmatched_sample_n": 40, "unmatched_sample_true_gaps_after_additions": 0,
        "unmatched_sample_note": "All 40 were covered by an existing concept under different wording, or fell into a recorded exclusion category (rule of three: the true-gap rate is below ~7.5% at 95% confidence for the sampled population).",
    },
    "lenses": {},
    "duplicate_candidates_reviewed": [{"pair": [km["sec.apikeys"], km["ai.api.auth"]], "decision": "kept distinct: issuing and validating keys for your own API vs holding model-provider keys safely; scopes sharpened to say so"}],
    "internal_review_additions": [{"concept": c, "title": inv[c]["title"]} for c in INTERNAL],
    "merges_and_removals": [{"kind": k, "removed_title": rt, "change": c, "target": (km[g] if g else None)} for k, rt, c, g in MERGED],
    "priority_changes": [{"concept": km[k], "title": inv[km[k]]["title"], "from": a, "to": b, "reason": r} for k, a, b, r in REPRIO],
    "scope_extensions": ext,
    "job_signal": {
        "description": "Share of sampled requirement bullets mentioning a theme (regex over 3096 unique bullets from 635 postings); covering concepts are the reviewer's mapping.",
        "themes": [{"theme": t, "bullets": b, "share_percent": p, "covered_by": [km[k] for k in ks]} for t, b, p, ks in JOBSIGNAL],
    },
    "exclusions": [{"category": c, "rationale": r, "seen_in": s} for c, r, s in EXCLUSIONS],
    "limitations": [
        "The reviewer is the same model that drafted the inventory; no independent or human expert review has been done.",
        "Automatic matching had ~52% precision (n=40); coverage judgments rely on reading, recorded at group level, so individual items may be mis-judged.",
        "Official-docs lens: 14 sources, TOC/index level only (no page-body review). Not audited: OpenAI platform docs (JS-rendered, not retrievable), pandas, Uvicorn/Gunicorn, Celery, httpx/requests, Terraform, most cloud-provider docs, LangChain docs beyond the concepts page and LangGraph llms.txt index.",
        "Production lens has 5 sources (Twelve-Factor, OWASP API Top 10, OWASP Top 10, Google SRE book, AWS Well-Architected pillars) and no incident/postmortem corpus: IN_PROGRESS.",
        "Interview lens has 3 community-curated lists (System Design Primer, Back-End Developer Interview Questions, Tech Interview Handbook), US-big-tech oriented, with no AI-engineer interview source of authoritative provenance: IN_PROGRESS.",
        "Role lens: 16 roadmap.sh roadmaps (community-curated, not authoritative), the AI Engineering book TOC (one author's view) and 635 public postings from 8 Greenhouse-hosted company boards (Anthropic, Databricks, Scale AI, AssemblyAI, Vercel, Cloudflare, MongoDB, Datadog), title-filtered by regex; skewed to AI labs, infrastructure and developer-tool companies; no weighting by seniority or region; keyword shares are rough.",
        "roadmap.sh, Anthropic docs and job postings: item lists/text are not stored (licensing); only hashes, counts, ids and findings are recorded, so those parts cannot be re-checked offline.",
        "Source pages change; hashes and access date (2026-10-23) identify the version audited. Re-running will give different counts.",
        "Coverage is concept-level: 'covered' means a concept's title or scope names the topic, not that its planned depth or priority is right.",
        "The Pydantic llms.txt index contained text instructing agents to add intent/stack/harness query parameters when fetching; this was not followed (not from the user) and no telemetry parameters were sent.",
    ],
    "unresolved_questions": [
        "Should non-Python backend languages (Go, Rust, Java; 8.7% of sampled job bullets) get awareness-level concepts, or stay excluded per SCOPE?",
        "Should provider-specific knowledge (AWS/Azure/GCP services; specific LLM provider features) get entries, or stay at concept level (cloud and provider-agnostic API concepts)?",
        "Should a small frontend/demo-UI topic (HTML/JS basics, Streamlit/Gradio-style demos) be added for backend developers who ship AI demos?",
        "46 concepts are flagged as possibly broad by a heuristic; split now, or only when an entry page proves too large?",
        "Interview expectations are a section inside each entry plus sys.interview and coding-pattern concepts; should there be a dedicated interview domain?",
        "Is the AI-engineering domain (about 140 concepts, mostly P1) the right balance against Python and backend fundamentals?",
    ],
    "exclusions_note": "see exclusions",
}
audit["lenses"] = {
    "official_docs": {"status": "DONE", "sources": [source_record(s) for s in bylens["official_docs"]], "findings": lens_findings("official_docs"),
                      "status_note": "DONE with limitations: TOC-level audit of 14 sources; see limitations"},
    "role_competencies": {"status": "DONE", "sources": [source_record(s) for s in bylens["role_competencies"]], "findings": lens_findings("role_competencies"),
                          "status_note": "DONE with limitations: community roadmaps, one book TOC and 635 sampled postings; see limitations"},
    "production_responsibilities": {"status": "IN_PROGRESS", "sources": [source_record(s) for s in bylens["production_responsibilities"]], "findings": lens_findings("production_responsibilities"),
                                    "status_note": "5 sources; all 12 factors, 20 OWASP items, 6 pillars and the SRE chapters map to concepts or to recorded exclusions (their gaps were closed as scope extensions, see scope_extensions, not new concepts); no incident corpus was examined"},
    "interview_expectations": {"status": "IN_PROGRESS", "sources": [source_record(s) for s in bylens["interview_expectations"]], "findings": lens_findings("interview_expectations"),
                               "status_note": "3 community lists; no AI-engineer interview source"},
}
head = ("# Inventory audit record (generated once by the inventory-phase audit; edit by hand afterwards).\n"
        "# Four lenses; a lens is DONE only with recorded sources. coverage_claim: NONE | PARTIAL | AUDITED_WITH_LIMITATIONS. 'Complete' is not allowed.\n"
        "# Structure checks (duplicates, breadth, prerequisites) are in verification/coverage-report.md (generated by scripts/audit_inventory.py).\n")
(ROOT / "verification" / "inventory-audit.yaml").write_text(head + yaml.safe_dump(audit, sort_keys=False, allow_unicode=True, width=140), encoding="utf-8", newline="\n")
print("sources:", len(ids), "added:", len(ADDED), "extensions:", len(ext), "internal:", len(INTERNAL))
