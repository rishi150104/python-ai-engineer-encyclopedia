"""Revision 2 of the audit record: edits verification/inventory-audit.yaml (human-authored) after the inventory revision. Archived in verification/audit-tools/."""
import hashlib
import json
import re
from pathlib import Path

import yaml

S = Path(__file__).parent
ROOT = Path("<REPO_ROOT>")  # redacted machine path: set to the repository root
km = json.loads((S / "keymap2.json").read_text(encoding="utf-8"))
inv = {n["id"]: n for n in yaml.safe_load((ROOT / "master-index.yaml").read_text(encoding="utf-8"))["nodes"]}
before = {n["id"]: n for n in yaml.safe_load((S / "master-index.rev1.yaml").read_text(encoding="utf-8"))["nodes"]}
a = yaml.safe_load((ROOT / "verification" / "inventory-audit.yaml").read_text(encoding="utf-8"))


def I(*keys):
    return [km[k] for k in keys]


def title(i):
    return inv[i]["title"]


new_ids = [i for i in inv if i not in before]
new_concepts = [i for i in new_ids if inv[i]["level"] == "concept"]
new_topics = [i for i in new_ids if inv[i]["level"] != "concept"]

# ---- new source: OWASP LLM Top 10 (2025) for the AI security facet
raw = (S / "llm10.html").read_bytes()
items = ["LLM01:2025 Prompt Injection", "LLM02:2025 Sensitive Information Disclosure", "LLM03:2025 Supply Chain", "LLM04:2025 Data and Model Poisoning",
         "LLM05:2025 Improper Output Handling", "LLM06:2025 Excessive Agency", "LLM07:2025 System Prompt Leakage", "LLM08:2025 Vector and Embedding Weaknesses",
         "LLM09:2025 Misinformation", "LLM10:2025 Unbounded Consumption"]
sha = hashlib.sha256(raw).hexdigest()
(ROOT / "verification" / "audit-sources" / "P-OWASP-LLM.json").write_text(json.dumps({"id": "P-OWASP-LLM", "url": "https://genai.owasp.org/llm-top-10/", "accessed_on": "2026-10-23",
    "sha256": sha, "license": "CC BY-SA 4.0", "items": items}, ensure_ascii=False, indent=0), encoding="utf-8")
a["lenses"]["production_responsibilities"]["sources"].append({
    "id": "P-OWASP-LLM", "title": "OWASP Top 10 for LLM Applications 2025", "url": "https://genai.owasp.org/llm-top-10/", "kind": "standard", "accessed_on": "2026-10-23",
    "sha256": sha, "bytes": len(raw), "items": 10, "noise_items": 0, "auto_candidates": 0,
    "manual_review": "all 10 items mapped by the reviewer (see revision_2.ai_domain_review.owasp_llm_mapping)",
    "items_file": "verification/audit-sources/P-OWASP-LLM.json", "items_license": "CC BY-SA 4.0"})
a["lenses"]["production_responsibilities"]["findings"].append({"action": "ADDED_CONCEPT", "concept": km["ai.sec.output"], "title": title(km["ai.sec.output"]),
    "sources": ["P-OWASP-LLM"], "triggering_items": "LLM05:2025 Improper Output Handling"})
a["lenses"]["production_responsibilities"]["status_note"] += "; revision 2 added the OWASP LLM Top 10 (2025)"
a["inventory_size"] = {"concepts": sum(1 for n in inv.values() if n["level"] == "concept"),
                       "topics_and_subtopics": sum(1 for n in inv.values() if n["level"] in {"topic", "subtopic"}), "domains": 11}
a["date"] = "2026-10-23 (revision 2)"

# ---- priority change recorded so the validator keeps it consistent
a["priority_changes"].append({"concept": km["ai.durable"], "title": title(km["ai.durable"]), "from": "P3", "to": "P2",
    "reason": "CLAUDE.md section 4J requires framework-neutral coverage of workflow state, persistence, checkpointing and human approval; the concept was P3 because it depended on a P3 prerequisite, now rewired to the P1 job-design concept"})

# ---- exclusions narrowed by the decisions
for e in a["exclusions"]:
    if e["category"].startswith("non-Python language stacks"):
        e["rationale"] += ". Revision 2: awareness-level concepts for Go, Rust, Java and C++ were added (topic cs.langs); full language tracks, PHP, Ruby and Node.js remain excluded"
    elif e["category"].startswith("frontend and web UI"):
        e["rationale"] += ". Revision 2: a scoped demo/internal-tool UI topic was added (be.ui); SPA frameworks, design systems, state management, bundlers, accessibility depth and mobile remain excluded"
    elif e["category"].startswith("individual products and vendors"):
        e["rationale"] += ". Revision 2: one concept each for Anthropic, OpenAI, Google (plus one for other providers) and for AWS, Azure and GCP were added with periodic-review flags; service-by-service entries remain excluded"

# ---- broad-scope review
flagged_before = ["PY-0009", "PY-0010", "PY-0016", "PY-0022", "PY-0024", "PY-0030", "PY-0032", "PY-0034", "PY-0035", "PY-0040", "PY-0055", "PY-0058", "PY-0060", "PY-0061", "PY-0064", "PY-0082",
                  "PY-0083", "PY-0087", "PY-0090", "PY-0103", "PY-0121", "PY-0133", "PY-0147", "WEB-0002", "WEB-0027", "BE-0016", "DB-0007", "DB-0014", "DB-0023", "DB-0056", "DB-0073", "DB-0075",
                  "SWE-0007", "SWE-0008", "SWE-0016", "SWE-0029", "SWE-0036", "OPS-0002", "OPS-0044", "OPS-0052", "SYS-0016", "AI-0007", "AI-0010", "AI-0061", "ML-0009", "ML-0025"]
remaining = [
    ("DB-0007", "PostgreSQL data types: numeric/text/time versus uuid/enum/array/range may deserve separate pages; decide when drafting."),
    ("SWE-0016", "Practical design patterns: a catalog; may be drafted as creational/structural/behavioral sections or split by pattern family."),
    ("SYS-0016", "Cloud design patterns: messaging-and-scaling patterns versus structural/migration patterns are separable; decide when drafting."),
    ("AI-0061", "Context engineering: selection/ordering versus failure modes and compaction overlap with ai.state.window; check for overlap when drafting."),
    ("PY-0016", "Integers and arithmetic operators: includes bitwise operators and bool; fine unless the page exceeds a comfortable length."),
    ("PY-0022", "String methods: a catalog of methods; organize by task, not by method, when drafting."),
    ("OPS-0002", "Shell navigation and core commands: includes editors, archives and links; may be split if it grows."),
]
a["revision_2"] = {
    "date": "2026-10-23",
    "decisions_applied": [
        {"n": 1, "decision": "awareness-level concepts for Go, Rust, Java and C++", "outcome": "topic cs.langs with a comparison concept, a memory-model concept, four language-awareness concepts and an interop concept; all P3 except the P2 comparison"},
        {"n": 2, "decision": "selected provider-specific concepts, vendor-neutral foundations kept, flag volatile material", "outcome": "topic ai.providers (3 provider concepts + others), cloud concepts for AWS/Azure/GCP; optional review_cycle field added to the schema and applied to the new concepts and to 36 existing volatile ones"},
        {"n": 3, "decision": "small explicitly scoped frontend/demo-UI topic", "outcome": "topic be.ui with 4 concepts and an exclusion statement in its scope"},
        {"n": 4, "decision": "review the 46 broad flags, split only independent objectives", "outcome": "5 splits with independent learning objectives, 2 narrowings without new concepts (functools; pytest/fixtures/mocking rebalance), 7 flags kept for drafting"},
        {"n": 5, "decision": "no interview domain; cross-domain index", "outcome": "optional tags field; INTERVIEW_INDEX.md generated from the interview tag (PY-0002 deliberately left untagged so its record is untouched)"},
        {"n": 6, "decision": "retain AI scale provisionally; audit its facets", "outcome": "facet audit below; 3 concepts added, 1 reprioritized, 8 scope extensions; no domain-size or other priority changes"},
    ],
    "id_policy": {
        "ids_changed": [],
        "ids_retired": [],
        "new_ids_assigned": {i: title(i) for i in new_ids},
        "statement": "No existing ID changed, was retired or was reused. New concepts took the next free number in their domain, so file order differs from numeric order. master-index.yaml now has a retired_ids list (empty) enforced by the validator.",
        "pre_revision_ids_changed_in_earlier_phase": "IDs were regenerated several times before this revision while the inventory was still a draft; the 761-concept inventory of the previous report is the baseline kept intact here.",
    },
    "added_topics": [{"id": i, "title": title(i), "priority": inv[i]["priority"]} for i in new_topics],
    "added_concepts": [{"id": i, "title": title(i), "priority": inv[i]["priority"], "topic": title(inv[i]["parent"]),
                        "learning_objective": inv[i]["scope"]} for i in new_concepts],
    "splits": [
        {"kept_id": km["py.bytes"], "new_id": km["py.binary"], "reason": "text encoding versus fixed binary layouts (struct, base64, bit masks) are independent objectives"},
        {"kept_id": km["py.importlib"], "new_id": km["py.importsys"], "reason": "dynamic imports/plugin loading versus import-machinery internals (finders, loaders, hooks, specs)"},
        {"kept_id": km["db.admin"], "new_id": km["db.roles"], "reason": "psql tooling versus roles, privileges and least-privilege access (a security objective)"},
        {"kept_id": km["swe.gitadv"], "new_id": km["swe.githooks"], "reason": "day-to-day history tools versus repository automation and structure (hooks, worktrees, submodules, LFS)"},
        {"kept_id": km["ai.models"], "new_id": km["ai.models.select"], "reason": "knowing model families versus the decision workflow (benchmarks, build vs buy, validating on own evals)"},
    ],
    "narrowed_without_split": [
        {"id": km["py.functools"], "old_title": "functools: cache, lru_cache, wraps, cached_property, singledispatch", "new_title": title(km["py.functools"]),
         "reason": "one objective (memoization); singledispatch moved to py.hof scope, wraps stays under py.decor"},
        {"id": km["swe.pytest"], "change": "scope rebalanced: fixture depth moved to swe.testdata, monkeypatch/tmp_path to swe.mock"},
        {"id": km["swe.testdata"], "change": "absorbs fixture scope, autouse, teardown and parametrized fixtures"},
        {"id": km["swe.mock"], "change": "absorbs pytest monkeypatch and tmp_path"},
        {"id": km["db.admin"], "change": "retitled to psql and everyday administration after the roles split"},
        {"id": km["swe.gitadv"], "change": "retitled to everyday Git tools after the hooks split"},
    ],
    "reprioritized": [{"id": km["ai.durable"], "from": "P3", "to": "P2", "reason": "see priority_changes"}],
    "scope_extensions_rev2": [{"concept": km[k], "title": title(km[k])} for k in ["ai.eval.fund", "ai.prod.cost", "ai.sec.inject", "ai.sec.supply", "ai.rag.acl", "ai.prod.ratelimit",
                                                                                  "ai.obs.trace", "ai.prod.deploy", "py.hof", "ai.durable"]],
    "review_cycle_flags": {"quarterly": sorted(i for i, n in inv.items() if n.get("review_cycle") == "quarterly"),
                           "semiannual": sorted(i for i, n in inv.items() if n.get("review_cycle") == "semiannual"),
                           "meaning": "Entries must be re-checked against current provider documentation at this cadence; their sources are vendor documentation that changes quickly.",
                           "mechanism": "the review_cycle field is shown in MASTER_INDEX.md and listed in verification/coverage-report.md; no automated reminder exists yet"},
    "interview_tagging": {"tagged": sum(1 for n in inv.values() if "interview" in (n.get("tags") or [])), "index": "INTERVIEW_INDEX.md",
                          "basis": "reviewer judgment informed by the System Design Primer, Back-End Developer Interview Questions and Tech Interview Handbook lists; not exhaustive and not independently reviewed",
                          "deliberately_untagged": ["PY-0002"], "reason": "PY-0001/PY-0002 records are frozen until the independent review of the pilot is complete"},
    "broad_scope_review": {
        "flagged_before": len(flagged_before), "heuristic": "scope lists of 6 or more comma-separated items, or titles listing 3 or more items",
        "outcome": "5 splits, 2 narrowings, remaining flags below; the rest were judged single-objective (a list of closely related members of one topic)",
        "remaining_flags_for_drafting": [{"concept": c, "note": n} for c, n in remaining],
        "heuristic_prompts_now": "the structure report lists more prompts than before mainly because new provider, cloud and language concepts enumerate examples in their scope; reviewed and judged intentional (bounded by the 'essentials' and 'awareness' framing)",
    },
    "duplicate_candidates_reviewed": [
        {"pair": I("cs.lang.go", "cs.lang.rust"), "decision": "distinct: concurrency/infrastructure services versus ownership/safety and Python extensions; shared template wording only"},
        {"pair": I("cs.lang.go", "cs.lang.cpp"), "decision": "distinct objectives; shared template wording only"},
        {"pair": I("cs.lang.rust", "cs.lang.cpp"), "decision": "distinct: ownership-based safety versus manual memory management"},
        {"pair": I("cs.lang.java", "cs.lang.cpp"), "decision": "distinct: JVM ecosystem versus native code"},
        {"pair": I("ops.aws", "ops.azure"), "decision": "intentionally parallel per-provider mappings onto the same vendor-neutral concepts; each has its own services and review flag; not service-by-service"},
    ],
    "ai_domain_review": {
        "principle": "AI stays at its current scale provisionally; sizes are not equalized and priorities changed only with evidence (one change).",
        "size": {"concepts": sum(1 for i, n in inv.items() if i.startswith("AI-") and n["level"] == "concept"), "share_of_inventory": round(sum(1 for i, n in inv.items() if i.startswith("AI-") and n["level"] == "concept") / sum(1 for n in inv.values() if n["level"] == "concept"), 3)},
        "facets": [
            {"facet": "evaluation", "concepts": I("ai.eval.fund", "ai.eval.datasets", "ai.eval.metrics", "ai.eval.judge", "ai.eval.regress", "ai.eval.rag", "ai.eval.agents", "ai.eval.human", "ai.eval.online", "ai.eval.tools", "ai.synthetic", "ai.models.select", "ml.rankmetrics", "ml.abtest"),
             "evidence": ["R-AIE-BOOK chapters 3-4", "roadmap.sh ai-engineer and ai-agents", "Anthropic docs"], "gap_action": "scope extension for evaluation-pipeline design; model-selection workflow split out (ai.models.select)"},
            {"facet": "retrieval", "concepts": I("ai.embed.concept", "ai.embed.similarity", "ai.embed.models", "ai.vec.index", "ai.vec.db", "ai.vec.filter", "ai.rerank", "ai.rag.arch", "ai.rag.ingest", "ai.rag.chunk", "ai.rag.index", "ai.rag.retrieve", "ai.rag.assemble", "ai.rag.failure", "ai.rag.fresh", "ai.rag.agentic", "ai.rag.graph", "ai.rag.acl", "ai.rag.structured"),
             "evidence": ["R-AIE-BOOK chapter 6", "roadmap.sh ai-engineer", "OWASP LLM08"], "gap_action": "added ai.rag.structured (text-to-SQL and tabular QA); extended ai.rag.acl for vector/embedding weaknesses"},
            {"facet": "tool use", "concepts": I("ai.tools.loop", "ai.tools.design", "ai.tools.safety", "ai.tools.errors", "ai.tools.parallel", "ai.tools.server", "ai.mcp", "ai.mcp.build", "ai.integrate", "ai.computeruse"),
             "evidence": ["Anthropic docs tool-use pages", "roadmap.sh ai-agents", "R-AIE-BOOK chapter 6"], "gap_action": "none found"},
            {"facet": "orchestration", "concepts": I("ai.agents.loop", "ai.agents.vs", "ai.agents.patterns", "ai.agents.eval-opt", "ai.agents.planning", "ai.agents.reliability", "ai.agents.multi", "ai.agents.hitl", "ai.durable", "ai.lc.core", "ai.lg.concepts", "ai.lg.persist", "ai.lg.hitl", "ai.fw.choice", "ai.fw.agentsdk", "ai.arch.async", "ai.arch.webhooks", "be.queue"),
             "evidence": ["CLAUDE.md section 4J (persistence, checkpointing, human approval)", "LangGraph llms.txt index", "roadmap.sh ai-agents"],
             "gap_action": "added framework-neutral human-in-the-loop (ai.agents.hitl); ai.durable P3 to P2 and its prerequisite rewired; ai.lg.hitl now depends on the neutral concept"},
            {"facet": "reliability", "concepts": I("ai.api.errors", "ai.api.stopreasons", "ai.repair", "ai.prod.reliability", "ai.agents.reliability", "ai.api.routing", "ai.tools.errors", "be.retries", "be.circuit", "ops.backpressure"),
             "evidence": ["Anthropic docs stop reasons", "R-AIE-BOOK chapter 10", "SRE book chapters 21-22"], "gap_action": "none found"},
            {"facet": "security", "concepts": I("ai.sec.halluc", "ai.sec.inject", "ai.sec.exfil", "ai.sec.tenant", "ai.sec.pii", "ai.sec.moderation", "ai.sec.jailbreak", "ai.sec.privacy", "ai.sec.redteam", "ai.sec.supply", "ai.sec.output", "sec.injection", "sec.xss"),
             "evidence": ["OWASP LLM Top 10 2025", "R-AIE-BOOK chapter 5", "roadmap.sh ai-engineer"], "gap_action": "added ai.sec.output (improper output handling); scope extensions for system prompt leakage, poisoning, embedding weaknesses and unbounded consumption"},
            {"facet": "cost", "concepts": I("ai.api.cost", "ai.prod.cost", "ai.prod.cache", "ai.api.caching", "ai.api.batch", "ai.prod.ratelimit", "ai.inferperf", "ai.tenant", "ops.cost"),
             "evidence": ["Anthropic docs (caching, batch, token counting)", "R-AIE-BOOK chapters 9-10"], "gap_action": "scope extension: budgets, alerts and per-feature attribution; denial-of-wallet"},
            {"facet": "tracing and observability", "concepts": I("ai.obs.trace", "ai.lsmith", "be.tracing", "ops.tracing", "ai.eval.online", "ai.prod.feedback", "be.logs"),
             "evidence": ["roadmap.sh ai-engineer (LLM observability)", "R-AIE-BOOK chapter 10"], "gap_action": "scope extension: OpenTelemetry GenAI conventions"},
            {"facet": "deployment", "concepts": I("ai.prod.deploy", "ai.arch.chat", "ai.arch.async", "ai.arch.sync", "ai.arch.fastapi", "ai.prod.testing", "ai.prod.versioning", "ai.prod.pipelines", "ai.own.local", "ops.pydocker"),
             "evidence": ["R-AIE-BOOK chapter 10", "roadmap.sh ai-engineer"], "gap_action": "scope extension: eval gates in CI/CD, canary and shadow rollouts"},
        ],
        "owasp_llm_mapping": [
            {"item": "LLM01 Prompt Injection", "covered_by": I("ai.sec.inject"), "action": "covered"},
            {"item": "LLM02 Sensitive Information Disclosure", "covered_by": I("ai.sec.pii", "ai.sec.exfil"), "action": "covered"},
            {"item": "LLM03 Supply Chain", "covered_by": I("ai.sec.supply", "sec.supplychain"), "action": "covered"},
            {"item": "LLM04 Data and Model Poisoning", "covered_by": I("ai.sec.supply"), "action": "scope extension (poisoned RAG documents, fine-tuning data)"},
            {"item": "LLM05 Improper Output Handling", "covered_by": I("ai.sec.output"), "action": "ADDED concept"},
            {"item": "LLM06 Excessive Agency", "covered_by": I("ai.sec.exfil", "ai.tools.safety", "ai.agents.hitl"), "action": "covered"},
            {"item": "LLM07 System Prompt Leakage", "covered_by": I("ai.sec.inject"), "action": "scope extension"},
            {"item": "LLM08 Vector and Embedding Weaknesses", "covered_by": I("ai.rag.acl"), "action": "scope extension"},
            {"item": "LLM09 Misinformation", "covered_by": I("ai.sec.halluc"), "action": "covered"},
            {"item": "LLM10 Unbounded Consumption", "covered_by": I("ai.prod.ratelimit", "ai.prod.cost"), "action": "scope extension"},
        ],
        "residual_risk": "The facet audit is the reviewer's reading against a handful of sources; it is not an independent check and does not prove the AI domain is complete or correctly sized.",
    },
}
a["limitations"] += [
    "Revision 2: provider-specific concepts describe product categories (APIs, tools, services) that change quickly; their scopes were written from the reviewer's knowledge plus the provider documentation indexes already audited, not re-fetched for this revision. They carry review_cycle flags and should be refreshed against live documentation before entries are drafted.",
    "Revision 2: interview tagging (228 concepts) is editorial judgment; the interview lens still has only three community sources and no AI-engineer interview source.",
    "Revision 2: the AI-domain facet review was done by the same model that built the domain; no independent review.",
]
a["unresolved_questions"] = [
    "Who owns periodic review of review_cycle concepts and what triggers it (calendar reminder, release feed)? No automated mechanism exists.",
    "Should PY-0002 be tagged for the interview index once the pilot's independent review is complete?",
    "Seven broad-scope flags remain for drafting (see revision_2.broad_scope_review); is it acceptable to split them reactively?",
    "Interview lens and production lens remain IN_PROGRESS; should an AI-engineer-specific interview source be located before entries are drafted?",
    "Should the audit tools be rebuilt as maintained scripts (they are archived as run and have machine-specific paths)?",
]
a["decisions_recorded_earlier"] = ["Go/Rust/Java/C++ awareness: yes (applied)", "provider-specific concepts: yes, selected (applied)", "demo/internal-tool UI topic: yes, scoped (applied)",
                                  "broad-scope concepts: split only independent objectives (applied)", "interview domain: no, cross-index instead (applied)", "AI scale: provisional (applied)"]
head = ("# Inventory audit record (human-authored; edited by scripted revisions recorded under revision_2). Four lenses; a lens is DONE only with recorded sources.\n"
        "# coverage_claim: NONE | PARTIAL | AUDITED_WITH_LIMITATIONS. 'Complete' is not allowed.\n"
        "# Structure checks (duplicates, breadth, prerequisites) are in verification/coverage-report.md (generated by scripts/audit_inventory.py).\n")
(ROOT / "verification" / "inventory-audit.yaml").write_text(head + yaml.safe_dump(a, sort_keys=False, allow_unicode=True, width=140), encoding="utf-8", newline="\n")
print("audit updated; new concepts:", len(new_concepts), "topics:", len(new_topics))
