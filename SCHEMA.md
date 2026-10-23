# Metadata schemas

Authoritative enforcement is `scripts/validate.py`; this page is the human summary.

| File | Owner | Purpose |
|---|---|---|
| `master-index.yaml` | human | Inventory nodes: `id, level, title, parent, priority, scope, competency, prereqs, related, source_category`. No statuses. |
| `progress.yaml` | human | Per-concept `content_status`, `verification_status`, `history[]`, plus session continuity. Transition rules are in its header comment. |
| `source-registry.yaml` | human | Source metadata only: `id, title, url, kind, version, license`. One id per documentation version (`SRC-...-3.11`, `-3.13`). |
| `verification/<ID>.yaml` | human | Claims (text, importance, support, source, section, verbatim `quotes`, optional `quotes_by_version`, `verified_by`, `version_note`, `review`), examples (`file`, `requires`, `expected_output`), `independent_review`. Scripts never write it. |
| `verification/generated/sources.yaml` | machine | Fetch results per source: `access_status, accessed_on, retrieval, sha256, bytes, doc_version, snapshot`. |
| `verification/generated/<ID>.results.yaml` | machine | Claim `check` and per-version `versions`; example `execution`, `actual_output`, environment, dependency versions, `extra_runs` on other interpreters. |
| `verification/generated/<ID>.excerpts.md` | machine | Source text around each quote. |
| `verification/snapshots/<SRC-ID>.html.gz` | machine | Raw fetched page (gzip, mtime 0). Retained under the source's license; the sha256 is of the uncompressed bytes. |
| `verification/review/<ID>.checklist.md` | machine | Independent-review package: per sourced claim the wording, source/version, exact excerpts, version notes, and the author's judgment (collapsed). Regenerate freely. |
| `verification/review/<ID>.reviewer.yaml` | reviewer | The reviewer's verdict per claim (`AGREE`/`DISAGREE`/`UNABLE_TO_JUDGE`), comments, author resolution, reviewer acceptance. Created once; scripts only append blocks for new claims. |
| `verification/inventory-audit.yaml` | human | Four-lens inventory audit: sources with hashes, findings (added concepts, scope extensions, merges, priority changes, exclusions), matcher quality, limitations, open questions. Cross-checked against the inventory by the validator. |
| `verification/audit-sources/<SRC>.json` | machine | Title lists of audited sources that may be redistributed, with the source hash. |
| `verification/audit-tools/` | archive | The scripts that produced the audit, kept for transparency. |
| `verification/coverage-report.md` | machine | Structure report from `scripts/audit_inventory.py`: counts, duplicate candidates, breadth, prerequisite gaps, cross-domain edges. |
| `verification/examples/<ID>/*.py` | human | Executable examples referenced by the record. |
| `entries/<domain>/<ID>.md` | human | Reference page. Front matter `id, title, priority, domain` must match the inventory. |

Page markers: `[Cn]` documented (claim record), `E1`.. observed (example run), `[J]` judgment. Observed behavior is never presented as documented.

## Content status
`NOT_STARTED -> RESEARCHED -> DRAFTED -> COMPLETE`. Back-steps: `DRAFTED -> RESEARCHED`, `COMPLETE -> DRAFTED`. A backward move resets verification to `NOT_CHECKED`.

## Verification status
`NOT_CHECKED -> IN_PROGRESS -> VERIFIED | NEEDS_REVISION | CONFLICTING_EVIDENCE`; each of those three returns only via `IN_PROGRESS`. `IN_PROGRESS` and later need content >= `DRAFTED`.

## `VERIFIED` gate (enforced)
- content is `COMPLETE`; `verification/<ID>.yaml` exists; every claim `PASS` is backed by verbatim quotes found in a snapshot of a FETCHED source (hash verified, snapshot present).
- every `critical` and `important` claim is `PASS`, is marked `[Cn]` in the page, and has `review.entailment: FULL` (the quoted text entails the claim as worded). `inferred` claims must name a `verified_by` example that PASSED. `judgment` claims have no source and can never be critical.
- every example is `PASSED` (expected equals actual, with python/os/dependency versions and date) or `NOT_EXECUTABLE` with a reason.
- `independent_review.status` is `DONE`, which the validator accepts only if the reviewer file names a reviewer with `independent_of_author: true` and every sourced claim is `AGREE` or a `DISAGREE` whose resolution the reviewer accepted. Reviews by the drafting model are recorded (`review.independent: false`) but do not satisfy this.
- minor claims may stay `UNCHECKED`. Citations alone do not verify a page: only claims listed in the record count.

## Claim record
Human fields: `{id, text, importance: critical|important|minor, support: direct|inferred|judgment, source, section, quotes, review: {entailment: FULL|PARTIAL|NONE, reviewer, independent, date, note}}`. Generated: `check: PASS|FAIL|UNCHECKED`, `checked_on`, `versions: {"3.11": PASS, "3.13": PASS}`.

## Example record
Human: `{id, file, requires, expected_output, [not_executable_reason]}`. Generated: `execution: NOT_RUN|PASSED|FAILED|NOT_EXECUTABLE`, `actual_output`, `environment`, `dependencies`, `run_on`, `extra_runs[]`.

## Inventory rules (enforced by `scripts/validate.py`)
- IDs: domain = bare code; others `CODE-NNNN`, never renumbered. Concepts sit under a topic or subtopic; topics/subtopics must have children and take the priority of their most important child.
- `prereqs` and `related` point to concepts only, are disjoint, and are acyclic. A prerequisite may not have lower priority than its dependent (priority inversion is an error).
- Concept titles are unique. `source_category` is one of official-docs, standard, rfc, vendor-docs, engineering-practice, reference.
- Every concept has a record in `progress.yaml` (`python scripts/validate.py --init-progress` appends NOT_STARTED/NOT_CHECKED records for new concepts).
- The audit record's references (findings, priority changes, job themes, merge targets) must exist; its priority changes must match the current inventory; a stale concept count is reported.
- Optional node fields: `review_cycle` (`quarterly` | `semiannual`) marks fast-changing material that must be re-checked at that cadence (shown in MASTER_INDEX.md and the structure report); `tags: [interview]` (concepts only) feeds the generated INTERVIEW_INDEX.md.
- `retired_ids` (top-level list of `{id, reason}`) records IDs that are no longer assigned; a retired ID may never appear as a node. New concepts take the next free number in their domain, so file order is for reading only.
- `MASTER_INDEX.md` and `INTERVIEW_INDEX.md` are generated by `python scripts/validate.py --write-index`; the validator fails if either is stale.
- The audit record's `merges_and_removals[].removed_title` must not exist in the inventory.
