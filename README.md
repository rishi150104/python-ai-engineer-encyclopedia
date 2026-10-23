# Python Backend to AI Engineer Encyclopedia

Source-backed reference for a Python backend developer (~1.5 years) moving into AI engineering. Project rules: [CLAUDE.md](CLAUDE.md). Scope: [SCOPE.md](SCOPE.md). Browse everything: [MASTER_INDEX.md](MASTER_INDEX.md). Cross-domain interview index: [INTERVIEW_INDEX.md](INTERVIEW_INDEX.md). Metadata formats: [SCHEMA.md](SCHEMA.md).

Status: inventory revision 2 (787 concepts, 11 domains; IDs not yet frozen). One pilot entry exists (PY-0002, content COMPLETE / verification IN_PROGRESS pending independent review). Coverage claim is PARTIAL: see the [audit record](verification/inventory-audit.yaml) and [structure report](verification/coverage-report.md).

## Commands (from repo root)
```
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows; use .venv/bin on Linux/macOS
python scripts/validate.py                  # all checks
python scripts/validate.py --write-index    # regenerate MASTER_INDEX.md
python scripts/validate.py --init-progress  # add progress records for new concepts
python scripts/audit_inventory.py           # structure report: verification/coverage-report.md
python scripts/check_claims.py PY-0002      # quote-check claims against snapshots (--refresh re-fetches)
python scripts/run_examples.py PY-0002      # run an entry's examples; add --python PATH for another interpreter
python scripts/make_review_checklist.py PY-0002   # regenerate the independent-review checklist (reviewer file is never overwritten)
python -m pytest tests                      # tests for the scripts
mkdocs serve -f site-config/mkdocs.yml      # site_dir defaults outside the repo; override with env ENCYCLOPEDIA_SITE_DIR
```
The same Markdown files are read on GitHub and by MkDocs Material (`docs_dir` is the repo root). Nothing is copied.
