"""One-off generator: DSL (scratchpad/inv/*.txt) -> master-index.yaml. master-index.yaml is the source of truth afterwards."""
import json
import sys
from pathlib import Path

ROOT = Path("<REPO_ROOT>")  # redacted machine path: set to the repository root
INV = Path(__file__).parent / "inv"
ORDER = [("py", "PY"), ("cs", "CS"), ("web", "WEB"), ("be", "BE"), ("db", "DB"), ("swe", "SWE"), ("sec", "SEC"),
         ("ops", "OPS"), ("sys", "SYS"), ("ai", "AI"), ("ml", "ML")]
DOMAINS = {
    "PY": ("Python", "The Python language, standard library, tooling and concurrency used in backend and AI application work."),
    "CS": ("Programming and Computer Science Fundamentals", "Complexity, data structures, algorithms, problem solving, OS and concurrency fundamentals."),
    "WEB": ("Web and Networking Fundamentals", "HTTP, networking, API design principles and HTTP clients."),
    "BE": ("Backend Engineering and FastAPI", "Application architecture, FastAPI, Pydantic, API patterns, data access, background jobs, integrations and observability."),
    "DB": ("Databases", "Relational modeling, SQL, PostgreSQL, indexes, transactions, ORMs, caching and other stores."),
    "SWE": ("Software Engineering Practices", "Git, design, configuration, testing, debugging, code quality and professional practice."),
    "SEC": ("Security", "Web/API vulnerabilities, authentication and authorization, cryptography essentials and secure operations."),
    "OPS": ("Deployment and Production Engineering", "Linux, containers, CI/CD, cloud, runtime operation, monitoring, incidents and reliability."),
    "SYS": ("System Design", "Requirements, scalability, architectural components, distributed-systems basics and design practice."),
    "AI": ("AI Engineering", "Building applications on LLMs: APIs, prompting, structured output, tools, RAG, agents, evaluation, security and production operation."),
    "ML": ("AI and Machine Learning Foundations", "Minimum math, data handling, ML and deep-learning concepts needed to build, evaluate and troubleshoot AI applications."),
}
SRC = {"od": "official-docs", "std": "standard", "rfc": "rfc", "vd": "vendor-docs", "ep": "engineering-practice", "ref": "reference"}
COMP = {"P0": "implement", "P1": "practical", "P2": "conceptual", "P3": "awareness"}
DROP = {"sec.ai", "sys.cdnarch", "sys.search", "sys.idemretry", "be.dbpool", "ai.arch.rag", "ops.health", "db.injection"}
SUBST = {"db.injection": "sec.injection", "sys.idemretry": "be.idempotency", "sys.cdnarch": "web.cdn", "sys.search": "db.search",
         "py.oop-ref": "py.inherit", "be.dbpool": "db.pooling", "ai.arch.rag": "ai.rag.arch", "ops.health": "be.health"}
EXTRA_PREREQ = {"sec.injection": ["db.sqlbasics"]}
KEEP = {"scope": "Mutable vs immutable objects, id()/is vs ==, aliasing, and shallow vs deep copy.", "competency": "production"}
TOPIC_KEEP = {"scope": "How Python objects, names and references behave."}

nodes, keymap, counters = [], {}, {}
cur_t = cur_s = None
for prefix, code in ORDER:
    default_src = "od"
    for raw in (INV / f"{prefix}.txt").read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        kind, rest = raw[0], raw[2:]
        if kind == "D":
            default_src = rest.strip()
            continue
        f = rest.split("|")
        key = f[0].strip()
        if key in DROP:
            continue
        counters[code] = counters.get(code, 0) + 1
        nid = f"{code}-{counters[code]:04d}"
        if key in keymap:
            sys.exit(f"duplicate key {key}")
        keymap[key] = nid
        if kind == "T":
            node = dict(id=nid, level="topic", title=f[1].strip(), parent=code, priority=None, scope=f[2].strip(),
                        competency="conceptual", prereqs=[], related=[], source_category=SRC[default_src], _key=key)
            cur_t, cur_s = nid, None
        elif kind == "S":
            node = dict(id=nid, level="subtopic", title=f[1].strip(), parent=cur_t, priority=None, scope=f[2].strip(),
                        competency="conceptual", prereqs=[], related=[], source_category=SRC[default_src], _key=key)
            cur_s = nid
        else:
            pr = f[2].strip()
            scope = f[5].strip()
            comp = (f[6].strip() if len(f) > 6 and f[6].strip() else COMP[pr])
            src = (f[7].strip() if len(f) > 7 and f[7].strip() else default_src)
            if scope == "KEEP":
                scope, comp = KEEP["scope"], KEEP["competency"]
            node = dict(id=nid, level="concept", title=f[1].strip(), parent=cur_s or cur_t, priority=pr, scope=scope,
                        competency=comp, prereqs=[x.strip() for x in f[3].split(",") if x.strip()],
                        related=[x.strip() for x in f[4].split(",") if x.strip()], source_category=SRC[src], _key=key)
        nodes.append(node)

# ---- post-parse corrections found by the inventory checks (cycles, priority inversions, topic references)
PRIO = {"py.hash": "P0", "py.pickle": "P1", "web.jsonschema": "P1", "ops.cd": "P1", "ai.api.portability": "P1", "ml.nn": "P1",
        "be.fa.app": "P1", "be.fa.params": "P1", "be.fa.body": "P1", "be.fa.response": "P1", "be.fa.deps": "P1",
        "be.fa.asyncsync": "P1", "be.dbsession": "P1"}
DEMOTE = {  # prerequisite -> related (loose dependency, or the prerequisite is lower priority)
    "py.fileio": ["py.ctxmgr", "py.bytes"], "ai.tokens": ["py.bytes"], "cs.numrep": ["cs.bits"], "ai.schema": ["web.jsonschema"],
    "be.settings": ["py.config"], "be.pydantic": ["py.dataclass"], "be.fa.middleware": ["be.starlette"],
    "be.optlock": ["web.conditional"], "db.btree": ["cs.balanced"], "swe.interfaces": ["py.protocol"], "swe.mock": ["py.callable"],
    "sec.injection": ["py.subprocess"], "sec.hashing": ["py.hashlib"], "ops.vpc": ["web.nat"], "sys.storage": ["db.choose"],
    "sys.dbchoice": ["db.partition"], "ai.api.errors": ["be.retries"], "ai.arch.sync": ["ai.api.batch"],
    "ai.obs.trace": ["be.tracing"], "ai.prod.reliability": ["ops.backpressure"],
    "ml.nn": ["ml.loss"], "be.metrics": ["ops.metrics"], "be.tracing": ["ops.tracing"], "be.health": ["ops.health"],
}
REPLACE = {("py.urllib", "web.client"): "web.requests", ("be.settings", "swe.config"): "swe.configmgmt",
           ("be.fa.deps", "py.func"): "py.def", ("sec.jwt", "sec.crypto"): "sec.symasym"}
SCOPE_FIX = {
    "db.pooling": "Why pools exist, PgBouncer modes, connection limits, and application-side pool sizing, exhaustion and per-worker budgets.",
    "ai.rag.arch": "End-to-end RAG design: ingest-index-retrieve-generate, separating the ingestion path from the query path, and when RAG beats long context or fine-tuning.",
    "be.health": "Health, readiness and liveness endpoints and probe semantics: what to check, dependencies in readiness, startup probes, and avoiding expensive probes and restart loops.",
    "sec.apikeys": "Issuing and validating API keys for your own API's clients: generation, hashing at rest, scoping and rotation; service-to-service and mTLS awareness.",
    "ai.api.auth": "Holding and using model-provider API keys safely: per-environment keys, scoping, server-side-only use and never shipping keys to clients.",
    "py.hintsadv": "X-or-None unions, Union, Literal, Annotated metadata, TypeAlias, and type narrowing."}
PREREQ_ADD = {"cs.numrep": ["py.int"], "sys.storage": ["db.relmodel"], "ml.nn": ["ml.linalg"], "web.requests": ["web.url"],
              "py.assign": ["py.syntax"], "ai.eval.rag": ["ml.rankmetrics"], "web.methods": ["web.url"], "ai.arch.chat": ["ai.usecases"]}
RELATED_ADD = {"py.float": ["cs.numrep"], "ops.dhealth": ["be.health"], "sys.ex.rag": ["ai.rag.arch"]}
TITLE_FIX = {"ai.rag.arch": "RAG architecture and service design", "be.health": "Health, readiness and liveness endpoints"}
APPEND = {'py.syntax': 'line continuation, identifiers and keywords, literals, pass and __future__ imports', 'py.sort': 'ordering comparisons of sequences', 'py.import': 'compiled .pyc files and __pycache__', 'py.trace': 'SyntaxError vs runtime errors, the traceback module and faulthandler', 'py.raise': 'add_note exception notes', 'py.attr': 'bound methods, name mangling for private names and namespaces', 'py.bytes': 'struct for binary layouts, base64/binascii and codecs', 'py.str': 'Unicode normalization (unicodedata)', 'py.pathlib': 'glob and fnmatch patterns', 'py.osenv': 'getpass, platform information and exit codes', 'py.subprocess': 'shlex quoting', 'py.pickle': 'shelve and dbm persistence', 'py.urllib': 'http.client/http.server and urllib.parse', 'py.importlib': 'finders, loaders, import hooks, module specs, pkgutil and runpy', 'py.meta': 'customizing instance/subclass checks and emulating generic types (__class_getitem__)', 'py.main': 'atexit handlers', 'py.textutil': 'difflib', 'py.depmgr': 'conda environments', 'py.pip': 'ensurepip', 'be.otherfw': 'Django/Flask and async frameworks (aiohttp, Tornado, Sanic)', 'swe.docs': 'documentation generators (Sphinx) and doctest examples', 'web.rest': 'URI design, HATEOAS and REST vs SOAP/RPC styles', 'web.tcpip': 'the OSI model vs the TCP/IP model', 'web.nat': 'firewalls, netfilter/iptables and routing awareness', 'sec.authz': 'ReBAC, policy-based and discretionary/mandatory models', 'sec.oauth': 'SAML/SSO awareness', 'sec.hashing': 'the status of MD5 and SHA-family functions', 'sec.bac': 'property-level authorization, mass assignment and excessive data exposure', 'sec.misconfig': 'API inventory management: unretired and undocumented endpoints', 'sec.validation': 'treating third-party API responses as untrusted input', 'sec.privacy': 'PCI DSS, HIPAA and CCPA awareness', 'sec.ratelimit': 'DDoS and resource-consumption limits', 'sec.tls': 'man-in-the-middle attacks', 'sec.keymgmt': 'secret stores such as Vault and sealed secrets', 'swe.principles': "separation of concerns, Law of Demeter, tell-don't-ask, command-query separation and the robustness principle", 'swe.patterns': 'MVC/MVVM, anti-corruption layer and dependency injection', 'swe.solid': 'dependency inversion and inversion of control', 'be.boundaries': 'anemic vs rich domain models', 'be.layers': 'transaction script vs domain model', 'sys.partial': 'the fallacies of distributed computing', 'sys.cache': 'write-behind and refresh-ahead and sizing a cache', 'sys.scale': 'throughput vs latency and performance vs scalability', 'sys.gateway': 'the backend-for-frontend (BFF) pattern', 'sys.bottleneck': 'performance antipatterns such as busy database, extraneous fetching and noisy neighbor', 'db.rediscache': 'eviction policies and memory management', 'db.kv': 'DynamoDB/Cassandra/Memcached-style stores', 'db.admin': 'privileges (GRANT/REVOKE, default privileges), pg_hba.conf and TLS settings', 'db.backup': 'pg_dump/pg_restore, base backups and tools such as pgBackRest and WAL-G', 'db.replication': 'streaming vs logical replication and automated-failover awareness', 'db.slowq': 'pg_stat_activity, log-analysis tools and plan visualizers', 'db.joins': 'LATERAL joins', 'ops.iac': 'configuration management (Ansible) and Pulumi/CloudFormation/CDK', 'ops.ssh': 'SFTP and rsync file transfer', 'ops.artifacts': 'artifact repositories (Artifactory/Nexus)', 'ops.k8s': 'managed container services (EKS/GKE/AKS, ECS/Fargate)', 'ops.ciconcept': 'other CI systems (Jenkins, CircleCI, GitLab CI)', 'ops.cli': 'terminal editors (vim/nano), archives (tar/gzip) and links', 'ops.images': 'OCI images and union filesystems', 'ops.compose': 'hot-reload development workflows', 'ops.resources': 'ulimits', 'ops.revproxy': 'running FastAPI behind a proxy: root_path and forwarded headers', 'ops.backpressure': 'cascading failures, retry storms and noisy neighbors', 'ops.metrics': 'Prometheus/Grafana-style stacks', 'ops.alerting': 'error budgets and risk', 'cs.sorting': 'external sorting of huge files', 'cs.race': 'starvation and livelock', 'cs.fd': 'the C10K problem', 'ai.reasoning': 'effort and thinking-budget controls', 'ai.sampling': 'frequency/presence/repetition penalties, stopping criteria and maximum length', 'ai.prod.ratelimit': 'end-user identifiers for abuse tracking', 'ai.api.portability': 'OpenAI-compatible endpoints and gateways such as OpenRouter', 'ai.embed.concept': 'applications such as semantic search, recommendation, anomaly detection and classification', 'ai.multimodal': 'image and video understanding and audio (speech-to-text) inputs', 'ai.mcp': 'hosts, clients, transports and local vs remote servers', 'ai.prompt.reasoning': 'ReAct, chain-of-thought, tree-of-thought, self-consistency and zero-shot prompting', 'ai.state.engineering': 'context isolation, sharing context between agents and context security', 'ai.state.memory': 'episodic vs semantic memory, user profiles and forgetting strategies', 'ai.agents.planning': 'ReAct, planner-executor, DAG agents and self-critique', 'ai.fw.others': 'LlamaIndex, Haystack, AutoGen, CrewAI, Pydantic AI and Google ADK', 'ai.lc.tools': 'agent middleware', 'ml.responsible': 'AI safety, misuse and user disclosure for application builders', 'swe.contract': 'API mocking and collection-based API tests', 'swe.e2e': 'browser automation (Playwright/Selenium) and headless runs', 'swe.remote': 'protected branches, templates and issue linking', 'swe.tech-comm': 'stakeholder communication, written and verbal', 'be.fa.openapi': 'callbacks, webhooks and SDK generation', 'be.fa.response': 'headers and cookies, direct Response returns and jsonable_encoder', 'be.fa.testing': 'async tests and WebSocket tests', 'be.pyd.config': 'forward references, recursive models and dynamic models'}
APPEND.update({'swe.pytest': 'fixture scope, autouse and teardown, parametrized fixtures, tmp_path, monkeypatch, skip/xfail, capsys/caplog, warnings and pytest.approx', 'db.migrations': 'the Alembic environment (env.py), revision identifiers, downgrades and migration history', 'ai.lg.concepts': 'the Graph API vs the Functional API and recursion limits', 'ai.lg.persist': 'fault tolerance, retries and common error conditions', 'ml.numpy': 'array creation, indexing, ufuncs, structured arrays and performance', 'ai.vec.db': 'Redis vector search and other engines', 'py.layout': 'pytest import mechanisms: rootdir and sys.path interactions'})
PRIO.update({'ops.k8s': 'P1', 'swe.tech-comm': 'P1'})
bykey = {n["_key"]: n for n in nodes}
for k, t in TITLE_FIX.items():
    bykey[k]["title"] = t
for k, add in PREREQ_ADD.items():
    for a in add:
        if a not in bykey[k]["prereqs"]:
            bykey[k]["prereqs"].append(a)
for k, add in RELATED_ADD.items():
    for a in add:
        if a not in bykey[k]["related"]:
            bykey[k]["related"].append(a)
for k, p in PRIO.items():
    bykey[k]["priority"] = p
for k, dem in DEMOTE.items():
    n = bykey[k]
    for d in dem:
        if d in n["prereqs"]:
            n["prereqs"].remove(d)
        if d not in n["related"]:
            n["related"].append(d)
for (k, old), new in REPLACE.items():
    n = bykey[k]
    for f in ("prereqs", "related"):
        n[f] = [new if x == old else x for x in n[f]]
for k, sc in SCOPE_FIX.items():
    bykey[k]["scope"] = sc
APPEND2 = {'py.hof': 'the operator module (itemgetter, attrgetter, methodcaller)', 'ai.prompt.structure': 'role prompting', 'ai.prompt.reasoning': 'step-back prompting', 'ai.state.engineering': 'context failure modes (poisoning, distraction, confusion), compaction and long-context processing', 'sys.cloudpatterns': 'materialized view, leader election, gateway routing/offloading/aggregation, bulkhead, compensating transaction, priority queue and scheduler-agent-supervisor', 'be.versioning': 'API lifecycle management', 'be.fa.static': 'mounting sub-applications and WSGI apps', 'ai.state.window': 'compaction and context editing', 'ai.tools.design': 'tool search for large tool sets', 'ai.state.memory': 'client-side memory tools and stores', 'ai.lg.persist': 'stores for long-term memory', 'swe.pytest': 'configuration files and exit codes', 'ops.metrics': 'the four golden signals', 'sys.gateway': 'service discovery', 'ops.availability': 'active-active and active-passive failover patterns', 'py.hints': 'static vs dynamic typing', 'ai.models': 'multilingual and domain-specific models, build vs buy, reading public benchmarks and a model-selection workflow', 'ai.eval.metrics': 'functional correctness for code and similarity against references', 'ai.eval.judge': 'comparative (pairwise) evaluation and ranking', 'ai.rag.ingest': 'RAG beyond text: tables, images and code', 'ai.own.peft': 'model merging and multi-task fine-tuning', 'ai.own.finetune': 'dataset curation, deduplication, formatting and distillation'}
merged = {}
for d in (APPEND, APPEND2):
    for k, v in d.items():
        merged.setdefault(k, []).append(v)
for k, adds in merged.items():
    n = bykey[k]
    n["scope"] = n["scope"].rstrip(".") + ". Also covers " + "; ".join(adds) + "."

errors = []
def resolve(k, owner):
    k = SUBST.get(k, k)
    if k in DROP:
        return None
    if k not in keymap:
        errors.append(f"{owner}: unknown key {k}")
        return None
    return keymap[k]

for n in nodes:
    if n["level"] != "concept":
        continue
    pre = n["prereqs"] + EXTRA_PREREQ.get(n["_key"], [])
    n["prereqs"] = list(dict.fromkeys(x for x in (resolve(k, n["_key"]) for k in pre) if x and x != n["id"]))
    n["related"] = [x for x in dict.fromkeys(resolve(k, n["_key"]) for k in n["related"]) if x and x != n["id"] and x not in n["prereqs"]]
# topic/subtopic priority = highest (numerically lowest) child priority
byid = {n["id"]: n for n in nodes}
for n in reversed(nodes):
    if n["level"] == "concept":
        continue
    kids = [c["priority"] for c in nodes if c["parent"] == n["id"] and c["priority"]]
    n["priority"] = min(kids) if kids else "P3"
    if n["level"] == "topic":
        pass
if errors:
    print("\n".join(sorted(set(errors))))
    sys.exit(1)

def q(s):
    return json.dumps(s, ensure_ascii=False)
def lst(x):
    return "[" + ", ".join(x) + "]"
out = ["# Master inventory: the single source of truth for concepts. Statuses are NOT stored here (see progress.yaml).",
       "# Hierarchy: domain -> topic -> subtopic -> concept. Concepts sit under a topic or subtopic. Only concepts get entry pages.",
       "# IDs are stable and never reused: domain = bare code (PY); others = CODE-NNNN, assigned in order of creation. Never renumber.",
       "# Priority: P0 core, P1 job-ready, P2 advanced, P3 specialized. Topic/subtopic priority is that of the most important child.",
       "# competency = expected level for the concept: awareness < conceptual < practical < implement < production.",
       "# prereqs: must be understood first (acyclic; a prerequisite is never lower priority than its dependent). related: see-also links.",
       "# source_category: official-docs | standard | rfc | vendor-docs | engineering-practice | reference (where the entry's evidence should come from).",
       "schema_version: 1", "nodes:"]
for prefix, code in ORDER:
    t, s = DOMAINS[code]
    out.append(f"  - {{id: {code}, level: domain, title: {q(t)}, parent: null, priority: P0, scope: {q(s)}, competency: conceptual, prereqs: [], related: [], source_category: official-docs}}")
for n in nodes:
    p = n["priority"]
    out.append(f"  - {{id: {n['id']}, level: {n['level']}, title: {q(n['title'])}, parent: {n['parent']}, priority: {p}, scope: {q(n['scope'])}, "
               f"competency: {n['competency']}, prereqs: {lst(n['prereqs'])}, related: {lst(n['related'])}, source_category: {n['source_category']}}}")
(ROOT / "master-index.yaml").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
# key -> id map kept in scratchpad for later editing sessions
(Path(__file__).parent / "keymap.json").write_text(json.dumps(keymap, indent=0), encoding="utf-8")
from collections import Counter
c = Counter((n["id"].split("-")[0], n["priority"]) for n in nodes if n["level"] == "concept")
print(len([n for n in nodes if n["level"] == "concept"]), "concepts;", len([n for n in nodes if n["level"] != "concept"]), "topics/subtopics")
