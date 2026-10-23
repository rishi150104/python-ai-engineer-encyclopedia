"""Revision 2 of the master inventory: edits master-index.yaml in place (existing IDs never change). Archived in verification/audit-tools/."""
import json
import re
import sys
from pathlib import Path

import yaml

S = Path(__file__).parent
ROOT = Path("<REPO_ROOT>")  # redacted machine path: set to the repository root
MI = ROOT / "master-index.yaml"
km = json.loads((S / "keymap.json").read_text(encoding="utf-8"))
doc = yaml.safe_load(MI.read_text(encoding="utf-8"))
nodes = doc["nodes"]
by_id = {n["id"]: n for n in nodes}
before = {n["id"]: json.dumps(n, sort_keys=True) for n in nodes}
COMP = {"P0": "implement", "P1": "practical", "P2": "conceptual", "P3": "awareness"}
newkm = {}


def next_id(domain):
    top = max(int(n["id"].split("-")[1]) for n in nodes if n["id"].startswith(domain + "-"))
    return f"{domain}-{top + 1:04d}"


def rid(key):
    if key in newkm:
        return newkm[key]
    if key in km:
        return km[key]
    sys.exit(f"unknown key {key}")


def position_after(anchor_id):
    return next(i for i, n in enumerate(nodes) if n["id"] == anchor_id) + 1


def add(key, domain, level, title, parent, priority, scope, src, prereqs=(), related=(), after=None, review=None, tags=None, comp=None):
    nid = next_id(domain)
    newkm[key] = nid
    node = dict(id=nid, level=level, title=title, parent=rid(parent) if parent in newkm or parent in km else parent, priority=priority, scope=scope,
                competency=comp or ("conceptual" if level != "concept" else COMP[priority]), prereqs=[rid(k) for k in prereqs], related=[rid(k) for k in related],
                source_category=src)
    if review:
        node["review_cycle"] = review
    idx = position_after(rid(after)) if after else len(nodes)
    nodes.insert(idx, node)
    by_id[nid] = node
    return node


def last_descendant(anchor):
    """Id of the last node (file order) that belongs to the subtree of `anchor`."""
    ids = {anchor}
    last = anchor
    for n in nodes:
        if n["parent"] in ids:
            ids.add(n["id"])
            last = n["id"]
    return last


def N(key):
    return by_id[rid(key)]


# ---------------------------------------------------------------- 1. other languages (CS)
t = add("cs.langs", "CS", "topic", "Other languages for Python engineers (awareness)", "CS", "P2",
        "Awareness of the languages Python backend and AI engineers most often meet beside Python: why they are chosen, how they differ, and how to integrate with them. Not language-learning tracks.",
        "engineering-practice", after=last_descendant(km["cs.fp"].rsplit("-", 1)[0] if False else "CS-0006") if False else None)
# place the new topic at the end of the CS block
nodes.remove(t)
nodes.insert(position_after(max((n["id"] for n in nodes if n["id"].startswith("CS-") and n["id"] != t["id"]), key=lambda i: nodes.index(by_id[i]))), t)
cs_last = t["id"]
for spec in [
    ("cs.lang.choose", "Choosing a language: Python versus compiled and JVM languages", "P2", ["py.concmodels", "py.gil", "cs.bigo"], ["cs.tradeoff"],
     "Criteria (performance profile, concurrency model, typing, ecosystem, team and hiring, deployment) and when backend or AI work moves hot paths or whole services out of Python."),
    ("cs.lang.memory", "Memory management models: garbage collection, reference counting and ownership", "P3", ["cs.memorymodel", "py.gc"], [],
     "How tracing GC, reference counting and ownership/borrowing differ and what each means for latency, memory safety and interop."),
    ("cs.lang.go", "Go for Python engineers (awareness)", "P3", ["cs.lang.choose", "cs.concfund"], ["py.async"],
     "Goroutines and channels, static typing and single-binary deployment; why infrastructure and high-concurrency services are often written in Go and how that differs from asyncio."),
    ("cs.lang.rust", "Rust for Python engineers (awareness)", "P3", ["cs.lang.choose", "cs.lang.memory"], ["py.cext"],
     "Ownership and borrowing at a conceptual level, performance and safety trade-offs, and Rust-backed Python libraries and extensions."),
    ("cs.lang.java", "Java and the JVM for Python engineers (awareness)", "P3", ["cs.lang.choose", "py.inherit"], ["ml.bigdata"],
     "JVM runtime and ecosystem, static typing and build tooling at reading level, and integrating with Java services and data-platform clients."),
    ("cs.lang.cpp", "C and C++ for Python engineers (awareness)", "P3", ["cs.lang.memory", "cs.cpu"], ["py.cext", "ml.hardware"],
     "Where native code shows up (extensions, inference runtimes, performance libraries), manual memory-management risks and reading native build errors."),
    ("cs.lang.interop", "Interoperating with other languages: FFI, bindings and service boundaries", "P3", ["py.cext", "cs.lang.choose"], ["web.grpc", "py.subprocess"],
     "ctypes/cffi, PyO3 and pybind11-style bindings, subprocess integration and gRPC/HTTP service boundaries, with the trade-offs of each."),
]:
    key, title, pr, pre, rel, scope = spec
    node = add(key, "CS", "concept", title, "cs.langs", pr, scope, "engineering-practice", pre, rel)
    nodes.remove(node)
    nodes.insert(position_after(cs_last), node)
    cs_last = node["id"]
t["priority"] = "P2"

# ---------------------------------------------------------------- 2. providers (AI) and clouds (OPS)
prov = add("ai.providers", "AI", "topic", "Provider-specific platform knowledge (periodically reviewed)", "AI", "P2",
           "Selected provider platforms kept apart from the vendor-neutral AI concepts. Every entry here is flagged for periodic review because APIs, models and limits change quickly.", "vendor-docs")
nodes.remove(prov)
ai_last_all = max((n["id"] for n in nodes if n["id"].startswith("AI-")), key=lambda i: nodes.index(by_id[i]))
nodes.insert(position_after(ai_last_all), prov)
last = prov["id"]
for key, title, pr, scope, rv in [
    ("ai.prov.anthropic", "Anthropic Claude platform specifics", "P2", "Model family and naming conventions, Messages API features, client and server tools, prompt caching, batch processing, rate-limit tiers and key management, each mapped to the vendor-neutral concept it implements.", "quarterly"),
    ("ai.prov.openai", "OpenAI platform specifics", "P2", "Responses and chat APIs, function calling and structured outputs, embeddings, realtime and voice, batch, evals and agent SDK features, each mapped to the vendor-neutral concept it implements.", "quarterly"),
    ("ai.prov.google", "Google Gemini and Vertex AI specifics", "P2", "Gemini API versus Vertex AI, multimodal and long-context features, grounding and search tools, quotas and enterprise controls, each mapped to the vendor-neutral concept it implements.", "quarterly"),
    ("ai.prov.others", "Other providers and gateways: Mistral, Cohere, DeepSeek, open-weight hosts, OpenRouter", "P3", "What distinguishes other model providers and gateways, OpenAI-compatible endpoints and open-weight hosting options, and how to evaluate a new provider quickly.", "quarterly"),
]:
    node = add(key, "AI", "concept", title, "ai.providers", pr, scope, "vendor-docs", ["ai.api.sdk", "ai.models", "ai.api.messages"], ["ai.api.portability", "ai.api.cloud"], review=rv)
    nodes.remove(node)
    nodes.insert(position_after(last), node)
    last = node["id"]

cloud_topic = km["ops.cloudbasics"]
cloud_parent = by_id[cloud_topic]["parent"]
anchor = last_descendant(cloud_parent)
for key, title, scope in [
    ("ops.aws", "AWS essentials for backend and AI workloads", "Core AWS building blocks backend and AI workloads use: compute choices (EC2, ECS/Fargate, Lambda), S3, VPC and IAM basics, managed databases and queues, and managed model access, mapped to the vendor-neutral cloud concepts."),
    ("ops.azure", "Azure essentials for backend and AI workloads", "Core Azure building blocks: virtual machines, container and function hosting, Blob storage, networking, Entra ID and role-based access, managed databases and managed model access, mapped to the vendor-neutral cloud concepts."),
    ("ops.gcp", "Google Cloud essentials for backend and AI workloads", "Core Google Cloud building blocks: Compute Engine, Cloud Run and GKE, Cloud Functions, Cloud Storage, VPC and IAM, managed databases and Vertex AI model access, mapped to the vendor-neutral cloud concepts."),
]:
    node = add(key, "OPS", "concept", title, cloud_parent, "P2", scope + " Flagged for periodic review.", "vendor-docs",
               ["ops.cloudbasics", "ops.compute", "ops.iam", "ops.managed"], ["ops.cost", "ai.api.cloud"], review="semiannual")
    nodes.remove(node)
    nodes.insert(position_after(anchor), node)
    anchor = node["id"]

# ---------------------------------------------------------------- 3. frontend / demo UI (BE)
ui = add("be.ui", "BE", "topic", "Demo and internal-tool UIs (scoped)", "BE", "P2",
         "Scoped to the skills needed to ship AI demos and internal tools. Excludes single-page-app frameworks, design systems, state management, bundlers, accessibility depth and mobile.", "engineering-practice")
nodes.remove(ui)
be_last = max((n["id"] for n in nodes if n["id"].startswith("BE-") and n["id"] != ui["id"]), key=lambda i: nodes.index(by_id[i]))
nodes.insert(position_after(be_last), ui)
last = ui["id"]
for key, title, pr, pre, rel, scope, src, rv in [
    ("be.ui.browser", "Browser essentials for demos: HTML, CSS, JavaScript and fetch", "P2", ["web.reqres", "web.cors", "web.jsonapi"], [],
     "The minimum HTML, CSS and JavaScript to build a page that calls an API: forms, fetch, JSON handling, the DOM at demo depth and development-time CORS.", "official-docs", None),
    ("be.ui.python", "Python-native UI frameworks for demos and internal tools", "P2", ["py.pip", "ai.api.sdk"], ["be.ui.browser"],
     "Streamlit, Gradio and NiceGUI-style frameworks: app and rerun model, state, calling backends, file upload and chat components, and the authentication and security limits of internal tools.", "official-docs", "semiannual"),
    ("be.ui.stream", "Consuming streaming APIs in the browser: SSE, fetch streams and WebSockets", "P2", ["web.streaming", "be.ui.browser", "ai.api.streaming"], ["be.fa.streaming"],
     "EventSource and fetch-stream parsing, rendering partial tokens, cancellation and reconnection, and proxy-buffering and CORS pitfalls for chat UIs.", "official-docs", None),
    ("be.ui.htmx", "Server-rendered interactivity with Jinja templates and HTMX", "P3", ["be.fa.static", "web.reqres"], [],
     "Server-rendered fragments and HTMX-style partial updates as a lightweight alternative to JavaScript frameworks for internal tools.", "official-docs", None),
]:
    node = add(key, "BE", "concept", title, "be.ui", pr, scope, src, pre, rel, review=rv)
    nodes.remove(node)
    nodes.insert(position_after(last), node)
    last = node["id"]

# ---------------------------------------------------------------- 4. splits of genuinely independent objectives (existing IDs keep the main concept)
node = add("py.binary", "PY", "concept", "Binary data: struct, base64 and bit-level formats", km["py.text"], "P2",
           "Parsing and building fixed binary layouts with struct (endianness, alignment), base64/binascii encodings and bit masks.", "official-docs", ["py.bytes", "cs.bits"], [])
nodes.remove(node)
nodes.insert(position_after(km["py.bytes"]), node)
N("py.bytes")["scope"] = N("py.bytes")["scope"].replace("struct for binary layouts, base64/binascii and codecs", "codecs")

node = add("py.importsys", "PY", "concept", "Import system internals: finders, loaders, import hooks and module specs", N("py.importlib")["parent"], "P3",
           "How the import machinery works: sys.meta_path, finders and loaders, module specs, import hooks and replacing or instrumenting imports.", "official-docs", ["py.importlib", "py.syspath"], [])
nodes.remove(node)
nodes.insert(position_after(km["py.importlib"]), node)
N("py.importlib")["scope"] = N("py.importlib")["scope"].replace("finders, loaders, import hooks, module specs, pkgutil and runpy", "pkgutil and runpy")

node = add("db.roles", "DB", "concept", "Database roles, privileges and least-privilege access", N("db.admin")["parent"], "P1",
           "CREATE ROLE, GRANT/REVOKE and default privileges, per-service database users, pg_hba.conf and TLS settings, and row-level security awareness.", "official-docs",
           ["db.admin", "db.relmodel"], ["sec.leastpriv"])
nodes.remove(node)
nodes.insert(position_after(km["db.admin"]), node)
a = N("db.admin")
a["title"] = "PostgreSQL tooling: psql and everyday administration"
a["scope"] = "psql basics and meta-commands, inspecting databases and roles, running scripts and the common administrative tasks an application developer performs."

node = add("swe.githooks", "SWE", "concept", "Git hooks, worktrees, submodules and LFS", N("swe.gitadv")["parent"], "P2",
           "Client-side hooks and the tools that run them, worktrees for parallel branches, submodules and large-file storage with their trade-offs.", "engineering-practice",
           ["swe.gitadv"], ["swe.precommit"])
nodes.remove(node)
nodes.insert(position_after(km["swe.gitadv"]), node)
g = N("swe.gitadv")
g["title"] = "Everyday Git tools: stash, cherry-pick, squash, tags and .gitignore"
g["scope"] = "stash, cherry-pick, squash, tags, .gitignore and git config at practical depth."

node = add("ai.models.select", "AI", "concept", "Selecting and evaluating models for a use case", N("ai.models")["parent"], "P1",
           "A model-selection workflow, reading public benchmarks critically, build versus buy (hosted API versus self-hosted), and validating a choice on your own evaluation set.",
           "vendor-docs", ["ai.models", "ai.eval.fund"], ["ai.own.decision"], review="quarterly")
nodes.remove(node)
nodes.insert(position_after(km["ai.models"]), node)
m = N("ai.models")
m["scope"] = m["scope"].replace("multilingual and domain-specific models, build vs buy, reading public benchmarks and a model-selection workflow", "multilingual and domain-specific models")

# narrow without splitting (single objective, wrong breadth)
f = N("py.functools")
f["title"] = "functools caching: cache, lru_cache and cached_property"
f["scope"] = "Memoization with cache, lru_cache and cached_property, cache-key and unhashable-argument pitfalls, memory growth and invalidation limits including on methods."
N("py.hof")["scope"] = N("py.hof")["scope"].rstrip(".") + ". Also covers functools.singledispatch and wraps."
# pytest scope rebalanced between existing concepts (no new ID)
N("swe.pytest")["scope"] = "Test discovery, assertions, marks, parametrize, conftest, skip/xfail, output capture, configuration files and exit codes."
N("swe.mock")["scope"] = N("swe.mock")["scope"].rstrip(".") + ". Also covers pytest monkeypatch and tmp_path."
N("swe.testdata")["scope"] = N("swe.testdata")["scope"].rstrip(".") + ". Also covers fixture scope, autouse and teardown, and parametrized fixtures."

# ---------------------------------------------------------------- 6. AI domain audit: gaps with distinct objectives
for key, title, pr, parent, pre, rel, scope, src, after in [
    ("ai.agents.hitl", "Human-in-the-loop design for agents and workflows", "P1", "ai.agents.loop", ["ai.agents.loop", "ai.tools.safety"], ["ai.lg.hitl"],
     "Approval gates, escalation and review queues, confirmation of side-effecting actions, interrupt and resume state, and measuring reviewer load; framework-neutral.", "vendor-docs", "ai.agents.reliability"),
    ("ai.rag.structured", "Retrieval over structured data: text-to-SQL and tabular question answering", "P2", "ai.rag.arch", ["ai.rag.arch", "db.sqlbasics", "ai.integrate"], ["sec.injection"],
     "Schema-aware prompting, query validation and read-only execution, result summarization and when to prefer retrieval over generated queries.", "vendor-docs", "ai.rag.retrieve"),
    ("ai.sec.output", "Handling model output as untrusted input", "P1", "ai.sec.inject", ["ai.sec.inject", "sec.injection", "sec.xss"], ["ai.pyval"],
     "Improper output handling: model text flowing into SQL, shell, HTML, templates or tool arguments; validation, encoding and sandboxing before use.", "standard", "ai.sec.inject"),
]:
    parent_id = by_id[km[parent]]["parent"]
    node = add(key, "AI", "concept", title, parent_id, pr, scope, src, pre, rel)
    nodes.remove(node)
    nodes.insert(position_after(km[after]), node)

d = N("ai.durable")
d["priority"], d["competency"] = "P2", "conceptual"
d["prereqs"] = [rid("ai.agents.loop"), rid("be.jobdesign")]
if rid("be.longworkflows") not in d["related"]:
    d["related"].append(rid("be.longworkflows"))
d["scope"] = d["scope"].rstrip(".") + ". Also covers framework-neutral workflow state persistence, checkpointing and resumability."
h = N("ai.lg.hitl")
h["prereqs"] = h["prereqs"] + [rid("ai.agents.hitl")]

EXT = {
    "ai.eval.fund": "designing the evaluation pipeline: component-level versus end-to-end evaluation",
    "ai.prod.cost": "budgets, alerts and per-feature cost attribution",
    "ai.sec.inject": "system prompt leakage and poisoned retrieved content",
    "ai.sec.supply": "data and model poisoning, including poisoned RAG documents and fine-tuning data",
    "ai.rag.acl": "vector and embedding weaknesses such as cross-tenant leakage through shared indexes",
    "ai.prod.ratelimit": "unbounded consumption and denial-of-wallet protection",
    "ai.obs.trace": "OpenTelemetry GenAI conventions",
    "ai.prod.deploy": "eval gates in CI/CD and canary or shadow rollouts of prompt and model changes",
}
for k, v in EXT.items():
    N(k)["scope"] = N(k)["scope"].rstrip(".") + ". Also covers " + v + "."

# ---------------------------------------------------------------- volatile material flags and interview cross-index tags
QUARTERLY = """ai.models ai.api.limits ai.api.cost ai.api.caching ai.api.batch ai.api.cloud ai.reasoning ai.mcp ai.mcp.build ai.tools.server ai.fw.others ai.fw.agentsdk ai.fw.choice
ai.lc.core ai.lc.retrieval ai.lc.tools ai.lg.concepts ai.lg.persist ai.lg.hitl ai.lg.stream ai.lg.multi ai.lsmith ai.vec.db ai.own.hf ai.own.local ai.imagegen ai.realtime
ai.computeruse ai.versions ai.api.files ai.api.routing""".split()
SEMI = "ai.own.quant ai.own.peft ai.eval.tools ai.multimodal ai.api.portability".split()
for k in QUARTERLY:
    N(k)["review_cycle"] = "quarterly"
for k in SEMI:
    N(k)["review_cycle"] = "semiannual"
INTERVIEW = """py.hash py.dict py.set py.list py.tuple py.gen py.iterable py.decor py.closure py.ctxmgr py.dataclass py.args py.scope py.inherit py.dm py.eqorder py.gil py.thread py.async
py.asynctasks py.blocking py.concmodels py.gc py.comp py.try py.excdef py.hints py.generics py.sort py.recur py.perfpat py.functools py.meta py.slots py.descriptors py.race
cs.bigo cs.da cs.ll cs.stackq cs.hashtable cs.heap cs.tree cs.balanced cs.trie cs.graph cs.search cs.sorting cs.recursion cs.divide cs.dp cs.greedy cs.twoptr cs.bfsdfs cs.shortest cs.topo cs.intervals
cs.bits cs.strings cs.concfund cs.race cs.sync cs.process cs.fp
web.methods web.status web.headers web.cookies web.cors web.caching web.tcp web.tls web.dns web.lb web.proxy web.rest web.apidesign web.websocket web.streaming web.webhooks
web.ratelimitconcept web.versions web.graphql web.grpc
be.layers be.boundaries be.fa.deps be.fa.asyncsync be.pydantic be.pagination be.idempotency be.errcontract be.queue be.jobdesign be.retries be.timeouts be.circuit be.outbox be.n1 be.respcache
be.workers be.versioning
db.normal db.joins db.nulls db.aggregates db.window db.subqueries db.btree db.btreeidx db.explain db.acid db.isolation db.locks db.deadlock db.optpess db.migrations db.n1 db.ormconcept db.redis
db.rediscache db.replication db.partition db.choose db.pooling db.mvcc
swe.solid swe.patterns swe.testpyramid swe.mock swe.tdd swe.rebase swe.branch swe.refactor swe.smells swe.lld swe.review
sec.owasp sec.injection sec.xss sec.csrf sec.ssrf sec.bac sec.passwords sec.jwt sec.oauth sec.session sec.hashing sec.symasym sec.authz
ops.containers ops.dockerfile ops.cd ops.k8s ops.incident ops.alerting ops.availability ops.ciconcept ops.lifecycle
sys.requirements sys.estimation sys.scale sys.availcap sys.consistency sys.latency sys.monolith sys.boundaries sys.gateway sys.stateless sys.cache sys.queues sys.partial sys.sagas sys.consensus
sys.replication sys.interview sys.ex.shortener sys.ex.ratelimiter sys.ex.notify sys.ex.upload sys.ex.chat sys.ex.rag sys.patterns sys.cloudpatterns sys.failure sys.bottleneck
ai.whatllm ai.tokens ai.context ai.sampling ai.limits ai.prompt.structure ai.prompt.fewshot ai.schema ai.tools.loop ai.rag.arch ai.rag.chunk ai.rag.retrieve ai.embed.concept ai.embed.similarity
ai.vec.index ai.rerank ai.agents.loop ai.agents.vs ai.eval.fund ai.eval.judge ai.eval.rag ai.sec.inject ai.sec.halluc ai.prod.cost ai.prod.latency ai.prod.cache ai.own.decision ai.state.window
ai.api.errors ai.api.streaming ai.arch.chat ai.agents.hitl ai.sec.output ai.models.select
ml.linalg ml.metrics ml.overfit ml.transformer ml.rankmetrics ml.split ml.supervised ml.loss""".split()
for k in INTERVIEW:
    N(k)["tags"] = ["interview"]

# topic priorities follow their best child
kids = {}
for n in nodes:
    kids.setdefault(n["parent"], []).append(n)
for n in reversed(nodes):
    if n["level"] in {"topic", "subtopic"}:
        n["priority"] = min(c["priority"] for c in kids[n["id"]])


# ---------------------------------------------------------------- write (same format as the original, plus optional fields)
def q(x):
    return json.dumps(x, ensure_ascii=False)


def lst(x):
    return "[" + ", ".join(x) + "]"


head = [
    "# Master inventory: the single source of truth for concepts. Statuses are NOT stored here (see progress.yaml).",
    "# Hierarchy: domain -> topic -> subtopic -> concept. Concepts sit under a topic or subtopic. Only concepts get entry pages.",
    "# IDs are stable and never reused: domain = bare code (PY); others = CODE-NNNN, next free number in the domain. Never renumber; file order is for reading only.",
    "# A removed concept's ID is listed under retired_ids and is never assigned again.",
    "# Priority: P0 core, P1 job-ready, P2 advanced, P3 specialized. Topic/subtopic priority is that of the most important child.",
    "# competency = expected level for the concept: awareness < conceptual < practical < implement < production.",
    "# prereqs: must be understood first (acyclic; a prerequisite is never lower priority than its dependent). related: see-also links.",
    "# source_category: official-docs | standard | rfc | vendor-docs | engineering-practice | reference (where the entry's evidence should come from).",
    "# Optional fields: review_cycle (quarterly | semiannual) marks fast-changing material for periodic review; tags: [interview] marks concepts listed in INTERVIEW_INDEX.md.",
    "schema_version: 1",
    "retired_ids: []",
    "nodes:",
]
out = list(head)
for n in nodes:
    tail = ""
    if "review_cycle" in n:
        tail += f", review_cycle: {n['review_cycle']}"
    if "tags" in n:
        tail += f", tags: {lst(n['tags'])}"
    parent = "null" if n["parent"] is None else n["parent"]
    out.append(f"  - {{id: {n['id']}, level: {n['level']}, title: {q(n['title'])}, parent: {parent}, priority: {n['priority']}, scope: {q(n['scope'])}, "
               f"competency: {n['competency']}, prereqs: {lst(n['prereqs'])}, related: {lst(n['related'])}, source_category: {n['source_category']}{tail}}}")
MI.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
(S / "keymap2.json").write_text(json.dumps({**km, **newkm}, indent=0), encoding="utf-8")

# report ID facts
after = {n["id"]: json.dumps({k: v for k, v in n.items() if k not in {"review_cycle", "tags"}}, sort_keys=True) for n in nodes}
changed_ids = [i for i in before if i not in after]
modified = [i for i in before if i in after and before[i] != after[i]]
print("new nodes:", len(newkm), "| removed ids:", changed_ids, "| existing nodes whose fields changed:", len(modified))
print("PY-0001/PY-0002 unchanged:", all(before[i] == json.dumps(next(n for n in nodes if n["id"] == i), sort_keys=True) for i in ("PY-0001", "PY-0002")) or "CHANGED")
print({k: v for k, v in newkm.items()})
