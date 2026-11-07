# Shared task board — China money

## Session and branch protocol
- Session ID: `arena-489b75a1-china1`.
- Fixed working branch: `arena/489b75a1-china1`. The execution environment requires all work and pushes on this branch and prohibits creating or switching branches. This takes precedence over the requested `session-<id>/<task>` naming convention; sequential, non-overlapping scopes are recorded below.
- Shared data, navigation, and integration outputs are opened only after the research scopes are complete. Other sessions must add claims here before touching files. No other claims existed at inspection.
- Before each push: fetch and `git pull --rebase`. Preserve other sessions' work on conflicts and record the resolution below.

## Task board
| Task | Status | Owner | Files / exclusive scope |
|---|---|---|---|
| T0 — coordination and repository audit | in progress | arena-489b75a1-china1 | COORDINATION.md; read-only repository audit |
| T1 — official China exchange-control and tax evidence | unclaimed | — | research/china.json; research/china-notes.md |
| T2 — official US tax and reporting evidence | unclaimed | — | research/us.json; research/us-notes.md |
| T3 — route inventory, evidence-backed comparison, executive analysis | unclaimed | — | research/routes.json; research/analysis.json; EXECUTIVE_SUMMARY.md |
| T4 — dashboard and category pages | unclaimed | — | site/; scripts/build_site.py; requirements.txt |
| T5 — final integration, source/row validation, build and link checks | unclaimed | — | tests/; data/; docs/; index.html; .github/workflows/; .nojekyll; README.md |
| T6 — PR, merge, GitHub Pages deployment and publication record | unclaimed | — | COORDINATION.md; deployment record |

Statuses: unclaimed / in progress / done / needs review. `needs review` items are published on Flagged for Review and do not block integration. No numerical gap will be inferred to complete a row.

## Claim and handoff log
- 2026-11-07: Session `arena-489b75a1-china1` inspected the repository: only README.md (`# China1`) and the initial commit were present; no existing substantive entries or task claims to audit. Claimed T0 and created this board before research. No user-specific balance, income source, Chinese/US tax residence, location, account holder nationality beyond US citizenship, or historical tax filings were supplied; these remain unknown, not assumed.

## Verification and irregularity log
- To be populated with source URLs, exact verification performed, missing evidence, and review flags as each task completes.

## Integration and publication record
- Pending. This session will perform sequential integration only after research tasks finish, then validate rows and links before opening and merging a PR into main.
