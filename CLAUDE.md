# CLAUDE.md — Python Backend to AI Engineer Knowledge Encyclopedia

## 1. Project Mission

Build a comprehensive, source-backed, independently browsable technical knowledge encyclopedia for a Python Backend Developer with approximately 1.5 years of professional experience who wants to transition into AI Engineering.

This is a long-term technical reference project, not a conversational course, a collection of superficial notes, or a one-shot content-generation exercise.

The finished encyclopedia must allow a reader to open any individual topic and understand exactly what they are expected to know, why it matters, how it works, how to use it, how to debug it, and how to verify their understanding.

Store all primary content as Markdown files in this repository. Use structured metadata files where useful. The repository must remain understandable, maintainable, navigable, and publishable on GitHub.

## 2. Target Knowledge Level

Define the target as a developer who can independently handle ordinary Python backend tasks, maintain and debug an existing codebase, write tests, work with databases and APIs, understand production failures, and build toward AI-powered applications.

Cover the relevant progression from fundamentals to job-ready engineering and the additional competencies needed for AI engineering.

Do not assume that 1.5 years of experience means every developer has identical knowledge. Define expectations by competency and practical responsibility rather than years alone.

Use these priority labels:

- **P0 — Core:** Essential fundamentals and concepts.
- **P1 — Job-ready:** Knowledge required to perform common professional responsibilities independently.
- **P2 — Advanced:** Useful for complex systems, deeper debugging, optimization, and greater ownership.
- **P3 — Specialized:** Relevant to particular roles or systems, but not a universal requirement.

For each entry, distinguish between awareness, conceptual understanding, practical usage, independent implementation, and production-level reasoning.

## 3. Master Inventory Is the Source of Truth

Before writing detailed reference pages, create a complete hierarchical knowledge inventory.

Use the hierarchy:

Domain → Topic → Subtopic → Individual concept.

Every meaningful concept must have:
- A stable, unique ID.
- A canonical title.
- A defined parent.
- A priority.
- A concise scope description.
- An expected competency.
- Prerequisites and related concept IDs.
- A planned source or source category.
- A content and verification status.

The inventory must be detailed enough to identify missing topics and prevent important concepts from disappearing during content generation.

Maintain one canonical entry per concept. Use links rather than duplicate explanations.

Audit the inventory for missing branches, inconsistent granularity, duplicated concepts, circular prerequisites, outdated terminology, and unjustified specialist topics.

Do not declare the inventory complete merely because it is large. Document the scope, assumptions, exclusions, and results of the coverage audit.

## 4. Required Knowledge Domains

Build and validate the full domain list. At minimum, investigate these areas:

### A. Python
- Syntax, variables, names, objects, and types.
- Numeric, string, sequence, mapping, and set types.
- Mutability, identity, equality, references, and copying.
- Control flow, comprehensions, functions, arguments, scope, and closures.
- Modules, packages, imports, and project organization.
- Object-oriented programming and data model methods.
- Exceptions and error handling.
- Iterables, iterators, generators, and lazy evaluation.
- Decorators and context managers.
- Type hints, generics, protocols, and static analysis.
- Standard library capabilities relevant to application development.
- File handling, serialization, dates, regular expressions, and logging.
- Concurrency, threading, multiprocessing, and asynchronous programming.
- Memory behavior, performance, profiling, and relevant interpreter internals.
- Packaging, dependencies, virtual environments, and environment management.

### B. Programming and Computer Science Fundamentals
- Data structures and algorithms.
- Time and space complexity.
- Searching, sorting, hashing, recursion, trees, graphs, and common algorithmic patterns.
- Problem decomposition and debugging.
- Operating system and process fundamentals relevant to backend development.

### C. Web and Networking Fundamentals
- HTTP and HTTPS.
- Requests, responses, headers, status codes, cookies, and sessions.
- DNS, TCP/IP, TLS, ports, sockets, and connection lifecycles.
- REST principles and API design.
- JSON, serialization, validation, and content negotiation.
- Authentication, authorization, CORS, caching, rate limiting, and timeouts.
- Reverse proxies, load balancing, and basic networking diagnostics.

### D. Backend Engineering and FastAPI
- Application structure and architectural boundaries.
- Routing, request parsing, validation, and response serialization.
- Pydantic models and validation behavior.
- Dependency injection.
- Middleware, exception handlers, and lifecycle management.
- Synchronous and asynchronous endpoints.
- Database integration and transaction boundaries.
- Authentication, authorization, and API security.
- Pagination, filtering, sorting, idempotency, and error contracts.
- Background tasks and durable job processing.
- External service integration, retries, timeouts, and failure handling.
- API documentation and versioning.
- Performance, concurrency, observability, and production operation.

### E. Databases
- Relational modeling and normalization.
- SQL syntax and query semantics.
- PostgreSQL types, constraints, joins, aggregations, and subqueries.
- Primary keys, foreign keys, indexes, and query planning.
- Transactions, isolation levels, locking, and concurrency.
- Migrations, connection pooling, and database access patterns.
- ORM fundamentals and SQLAlchemy where relevant.
- N+1 queries, slow queries, and performance diagnosis.
- Caching and appropriate use of non-relational data stores.

### F. Software Engineering Practices
- Git, branches, commits, merges, rebasing, and conflict resolution.
- Code organization, modularity, cohesion, and coupling.
- Clean interfaces and practical design patterns.
- Configuration and secrets management.
- Unit, integration, end-to-end, and contract testing.
- Mocking, fixtures, test data, and test isolation.
- Debugging, logging, tracing, and metrics.
- Code review, linting, formatting, and static analysis.
- Documentation and maintainability.

### G. Security
- Common web and API vulnerabilities.
- Input validation and output handling.
- Authentication and authorization.
- Password handling and session security.
- SQL injection, SSRF, insecure deserialization, and injection risks.
- Secrets, dependency vulnerabilities, and least privilege.
- Secure configuration and error reporting.
- Relevant OWASP guidance and framework-specific security practices.

### H. Deployment and Production Engineering
- Linux and command-line fundamentals.
- Processes, environment variables, permissions, and signals.
- Docker images, containers, networking, and volumes.
- CI/CD and automated quality checks.
- Cloud fundamentals and deployment architectures.
- Application startup, shutdown, health checks, and readiness.
- Workers, queues, background jobs, and scheduled tasks.
- Database migrations and rollback strategies.
- Monitoring, logging, tracing, alerting, and incident diagnosis.
- Reliability, scalability, availability, resource limits, and cost awareness.

### I. System Design
- Requirements and trade-offs.
- Monoliths and service boundaries.
- API gateways, queues, caches, and asynchronous workflows.
- Stateless services and state management.
- Scalability, bottlenecks, consistency, and failure modes.
- Basic distributed systems concepts.
- Architecture decisions appropriate to the target experience level.

### J. AI Engineering
- Model APIs, authentication, request handling, and usage limits.
- Prompt design and instruction management.
- Structured outputs and schema validation.
- Tool calling and external system integration.
- Streaming, asynchronous model calls, timeouts, retries, and error handling.
- Conversation state and memory design.
- Embeddings, vector similarity, and vector database fundamentals.
- Document ingestion, chunking, retrieval, reranking, and RAG.
- LangChain and LangGraph concepts and APIs.
- Workflow orchestration, state, persistence, checkpointing, and human approval.
- Evaluation datasets, quality metrics, regression tests, and tracing.
- Hallucination mitigation, prompt injection, access control, and AI-specific security.
- Cost, latency, caching, observability, and production reliability.
- Testing and deployment of AI-powered applications.

### K. Relevant AI and Machine Learning Foundations
Cover the minimum ML, statistics, data handling, and model-evaluation knowledge needed to build, integrate, and troubleshoot AI applications.

Clearly distinguish AI application engineering from model training, research-level ML, deep learning specialization, and advanced mathematics. Include those additional areas only where justified by the target role or label them P2/P3.

This domain list is a starting constraint, not proof of completeness. Identify additional necessary domains and justify exclusions.

## 5. Individual Reference Page Standard

Every individual reference page must be independently understandable.

Use an appropriate subset of this structure:

1. Title, stable ID, priority, and domain.
2. Expected competency and scope boundaries.
3. Definition and purpose.
4. Mental model and underlying behavior.
5. Rules, syntax, APIs, variants, parameters, and defaults.
6. Practical examples with explanations.
7. Edge cases and failure modes.
8. Common mistakes and debugging.
9. Testing methods and expected results.
10. Production applications and trade-offs.
11. Security and performance implications where relevant.
12. Interview expectations where relevant.
13. Competency checklist.
14. Prerequisites and related entries.
15. Sources, applicable versions, verification status, and review date.

Do not force irrelevant sections into a topic. Do not substitute a list of concept names for explanations. Avoid both shallow coverage and unnecessary verbosity.

When an API or syntax variant is within scope, explain the differences that matter. Include edge cases based on realistic usage, not arbitrary trivia.

Code examples must be correct, minimal enough to understand, and accompanied by expected behavior or output where useful.

## 6. Research and Source Requirements

Use primary sources whenever possible.

Preferred sources include:
- Official language and library documentation.
- Official framework and database documentation.
- Official API documentation and release notes.
- Maintained security standards and authoritative security guidance.
- Reputable technical references for practical trade-offs not adequately explained by primary sources.

For each entry:
- Record the source title and URL.
- Identify the relevant section and the claims it supports.
- Record the applicable language, framework, library, or API version when material.
- Prefer version-specific documentation for version-sensitive behavior.
- Identify deprecated or removed functionality.
- Distinguish official behavior from common practice and engineering judgment.

Never fabricate a source, URL, citation, API, benchmark, default, test result, or claim of verification.

Do not claim to have browsed a source unless it was actually accessed. If network access is unavailable, create an explicit research limitation and do not pretend the content has been externally verified.

When sources conflict, record the conflict and investigate version differences or contextual explanations. Leave unresolved conflicts visible.

## 7. Anti-Hallucination and Verification Rules

Content generation and verification must be separate stages.

For every entry, check:
- Factual claims against the recorded evidence.
- API names, signatures, defaults, and version behavior.
- Example correctness and expected behavior.
- Relevant edge cases and failure handling.
- Source relevance and link validity.
- Completeness against the entry's defined scope.
- Consistency with related encyclopedia entries.

Execute code examples whenever feasible. Use isolated test files or directories, pinned dependencies, and documented environments when appropriate.

Do not run destructive commands or untrusted code without reviewing their effects.

Use explicit statuses:
- NOT_STARTED
- RESEARCHED
- DRAFTED
- VERIFIED
- NEEDS_REVISION
- CONFLICTING_EVIDENCE

Mark an entry VERIFIED only when its required verification checks have passed. A second AI review alone is insufficient.

Record what was checked, what passed, what failed, and what remains unresolved.

## 8. Repository and File Organization

Use a clear Markdown-first structure, adapting it as needed:

- README.md — project overview and navigation.
- CLAUDE.md — permanent project instructions.
- SCOPE.md — target profile, priorities, inclusions, and exclusions.
- MASTER_INDEX.md — human-readable master knowledge map.
- master-index.yaml — structured inventory and stable IDs.
- source-registry.yaml — source metadata.
- progress.yaml — work and verification statuses.
- entries/ — canonical reference pages grouped by domain.
- verification/ — audit records, coverage reports, and test artifacts.
- scripts/ — deterministic validation and maintenance utilities.
- tests/ — tests for scripts, links, metadata, and executable examples.

Keep content in Markdown and structured metadata in YAML where appropriate. Avoid duplicate sources of truth.

Each reference page should use stable IDs in its metadata or heading. Relative links must remain valid when the repository is published on GitHub or rendered through a documentation site.

Do not create thousands of empty placeholder files. Generate entries in manageable batches.

## 9. Master Index and Navigation

The reader must be able to:
- Browse the complete hierarchy.
- Find an entry by ID or title.
- Understand the scope of each entry without opening it.
- Navigate to prerequisites and related topics.
- Identify priorities and verification status.
- See which concepts remain incomplete.

Maintain a predictable naming convention and avoid filenames that change whenever wording is improved.

The master index must link to actual files, and automated checks should detect broken internal links and missing inventory entries.

## 10. Completeness Audits

Perform audits at both inventory and content levels.

Inventory audits should identify:
- Missing required concepts.
- Missing prerequisite relationships.
- Duplicates and overlapping scope.
- Inconsistent granularity.
- Unjustified exclusions.
- Missing AI engineering competencies.
- Topics that exceed the target level without justification.

Content audits should identify:
- Inventory entries without reference pages.
- Pages absent from the inventory.
- Required sections missing from an entry.
- Unsupported claims and missing sources.
- Untested code examples.
- Broken links and outdated references.
- Incomplete or contradictory explanations.

Maintain a coverage report. Report exactly what has been audited and what has not. Never use an unsupported claim of 100% completeness.

## 11. Progress and Session Continuity

Update progress metadata after meaningful work.

Track status by entry ID, not only by broad domain. Maintain the current batch, next entry to process, unresolved questions, failed checks, and required follow-up actions.

At the end of a work session, update the project files so another session can resume without relying on previous conversation history.

Do not mark a concept complete simply because a draft file exists.

## 12. GitHub Publishing Rules

GitHub is the version-controlled publishing destination. The local repository is the working source.

- Inspect the existing Git state before modifying or committing anything.
- Never overwrite unrelated user work.
- Keep secrets, credentials, personal information, temporary files, and environment files out of Git.
- Maintain an appropriate .gitignore.
- Use clear, focused commits.
- Run relevant validation before proposing publication.
- Do not automatically publish unverified content.
- Do not force-push or rewrite shared history without explicit approval.
- Do not create or publish a public repository without my authorization.
- Preserve the local Markdown files as the source of truth.
- Keep the content compatible with GitHub Markdown and, if configured, a documentation-site generator such as MkDocs.

## 13. Operating Procedure

For each batch:

1. Select the next inventory entries by dependency and priority.
2. Research them and collect evidence.
3. Draft the reference pages.
4. Verify claims and examples.
5. Run applicable automated checks.
6. Update statuses and audit results.
7. Review links and cross-references.
8. Summarize completed work and unresolved issues.

Do not silently skip an entry. If an entry cannot be completed, record the blocker and move on only when appropriate.

Do not repeatedly regenerate already verified pages without a reason. Preserve stable IDs and established conventions.

## 14. Mandatory First Actions

When beginning work in this repository:

1. Inspect the directory, files, Git status, and available tooling.
2. Read this instruction file.
3. Determine whether the repository is new or contains existing work.
4. Propose the repository structure, metadata schema, source policy, verification workflow, and Git publishing approach.
5. Identify practical limitations, especially network access, documentation retrieval, code execution, and version validation.
6. Define acceptance criteria for the master inventory and for an individual verified entry.
7. Wait for approval before major structural changes or large-scale content generation.

Once approved, build the infrastructure, then the master inventory, then test the process on a pilot entry. Expand the encyclopedia in batches only after the pilot demonstrates that the workflow is reliable.

**Final principle:** Optimize for accurate, traceable, comprehensive knowledge—not for the number of files or the speed at which content is generated.