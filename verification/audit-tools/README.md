# Audit tools (archived as run)

These scripts produced `verification/inventory-audit.yaml` and `verification/audit-sources/` on 2026-10-23. They are kept so the method can be inspected, not as maintained tooling:
paths point at a scratch directory and a placeholder repository root (`<REPO_ROOT>`, redacted), and the compact concept lists that `gen_inventory.py` read are not retained
(`master-index.yaml` is the source of truth now).

- `gen_inventory.py`: one-off generator that turned a compact concept list into `master-index.yaml` (IDs assigned in order; PY-0001/PY-0002 preserved).
- `harvest.py`, `harvest2.py`: fetch source indexes, roadmap definitions and public job postings and extract item lists.
- `match.py`: token-weighted candidate matching of source items to concepts (measured precision about 52%; candidates only).
- `build_audit.py`: assembles the audit record from the reviewer's findings.

Re-running against live sites will produce different counts; the hashes and access dates in the audit identify the pages that were audited.

Revision 2 (after the project owner's decisions on 2026-10-23):
- `revise_inventory.py`: edited `master-index.yaml` in place (existing IDs untouched; new concepts take the next free number) and wrote the optional `review_cycle`/`tags` fields.
- `update_audit_rev2.py`: appended the `revision_2` section, the OWASP LLM Top 10 source and the narrowed exclusions to `verification/inventory-audit.yaml`.
`build_audit.py` and `gen_inventory.py` must not be re-run: they would overwrite the revised inventory and audit.
