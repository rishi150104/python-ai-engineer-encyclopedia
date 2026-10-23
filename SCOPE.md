# Scope

**Target reader:** a Python backend developer, ~1.5 years of experience, moving to AI engineering. Expectations are defined by competency (awareness, conceptual, practical, implement, production), not years.

**Priorities:** P0 core, P1 job-ready, P2 advanced, P3 specialized. A prerequisite is never lower priority than the concept that needs it (enforced by `scripts/validate.py`).

## Taxonomy

Domain -> topic -> (optional subtopic) -> concept. Only concepts get entry pages. The inventory is [master-index.yaml](master-index.yaml); the browsable map is [MASTER_INDEX.md](MASTER_INDEX.md).

| Domain | Scope | Concepts (P0/P1/P2/P3) |
|---|---|---|
| PY Python | language, stdlib, typing, concurrency, performance, packaging | 153 (47/60/32/14) |
| CS Computer science fundamentals | complexity, data structures, algorithms, OS, concurrency, awareness of other languages | 50 (8/16/18/8) |
| WEB Web and networking | HTTP, networking, API design, HTTP clients | 44 (13/18/9/4) |
| BE Backend and FastAPI | architecture, FastAPI, Pydantic, API patterns, data access, jobs, integrations, observability, demo/internal-tool UIs (scoped) | 82 (4/52/21/5) |
| DB Databases | relational modeling, SQL, PostgreSQL, indexes, transactions, roles, ORMs, Redis and other stores | 75 (12/33/24/6) |
| SWE Software engineering | Git, design, configuration, testing, debugging, quality, professional practice | 58 (14/25/15/4) |
| SEC Security | web/API vulnerabilities, auth, crypto essentials, secure operations | 40 (10/20/9/1) |
| OPS Deployment and production | Linux, containers, CI/CD, cloud (neutral and AWS/Azure/GCP), Kubernetes, runtime, monitoring, reliability | 66 (8/29/26/3) |
| SYS System design | requirements, architecture, distributed-systems basics, worked designs | 32 (0/11/18/3) |
| AI AI engineering | LLM APIs, prompting, structured output, tools, state, embeddings, RAG, frameworks, agents, evaluation, AI security, production, open-weight models, provider-specific platforms | 151 (17/70/52/12) |
| ML ML foundations | math, data handling, ML and deep-learning concepts, MLOps awareness | 36 (1/15/13/7) |
| **Total** | | **787 (134/349/237/67)** |

## Scoped inclusions (revision 2)

- **Other languages** (topic `cs.langs`): awareness of Go, Rust, Java and C++ and interop with them, not language-learning tracks.
- **Provider-specific platforms** (topic `ai.providers`, plus AWS/Azure/GCP concepts under cloud): selected providers only, one concept each, foundations stay vendor-neutral. These and other fast-changing concepts carry a `review_cycle` flag (quarterly or semiannual) and are marked in the index.
- **Demo and internal-tool UIs** (topic `be.ui`): only what is needed to ship AI demos and internal tools; no SPA frameworks, design systems, state management, bundlers, accessibility depth or mobile.
- **Interview expectations** stay inside entries. There is no interview domain; [INTERVIEW_INDEX.md](INTERVIEW_INDEX.md) is a generated cross-domain index of concepts tagged `interview`.

## Exclusions

Recorded with rationale in [verification/inventory-audit.yaml](verification/inventory-audit.yaml). Main ones: full language tracks and other non-Python backend stacks, frontend engineering beyond demos and internal tools, CPython build/platform setup and C-API internals, deprecated or GUI/multimedia stdlib modules, PostgreSQL and Kubernetes cluster administration, service-by-service product and vendor knowledge, career/process content, QA-role specialization, Linux sysadmin depth, AI research and training infrastructure. Model training and advanced mathematics appear only as P2/P3 awareness where the target role justifies them.

## Open items

See `unresolved_questions` in the audit record: ownership of periodic review, tagging PY-0002 for the interview index, seven broad-scope flags kept for drafting, thin production and interview lenses, and archived audit tooling.

## Coverage statement

`coverage_claim` is **PARTIAL**. Four lenses (official documentation, role competencies, production responsibilities, interview expectations) were examined against 48 sources; two lenses are IN_PROGRESS; the reviewer is the model that built the inventory; automatic matching was measured at ~52% precision. No claim of completeness is made. See the audit record for the limitations.

**Assumptions:** source versions are pinned per claim (e.g. Python 3.11). Sources that were not fetched are never cited as verification. Concept IDs are stable from the acceptance of this inventory: never renumber or reuse an ID; add new concepts with the next free number in their domain.
