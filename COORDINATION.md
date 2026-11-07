# Shared task board — China money

## Session and branch protocol
- Session ID: `arena-489b75a1-china1`.
- Fixed working branch: `arena/489b75a1-china1`. The execution environment requires all work and pushes on this branch and prohibits creating or switching branches. This takes precedence over the requested `session-<id>/<task>` naming convention; sequential, non-overlapping scopes are recorded below.
- Shared data, navigation, and integration outputs are opened only after the research scopes are complete. Other sessions must add claims here before touching files. No other claims existed at inspection.
- Before each push: fetch and `git pull --rebase`. Preserve other sessions' work on conflicts and record the resolution below.

## Task board
| Task | Status | Owner | Files / exclusive scope |
|---|---|---|---|
| T0 — coordination and repository audit | done | arena-489b75a1-china1 | COORDINATION.md; read-only repository audit |
| T1 — official China exchange-control and tax evidence | done | arena-489b75a1-china1 | research/china.json; research/china-notes.md |
| T2 — official US tax and reporting evidence | in progress | arena-489b75a1-china1 | research/us.json; research/us-notes.md |
| T3 — route inventory, evidence-backed comparison, executive analysis | unclaimed | — | research/routes.json; research/analysis.json; EXECUTIVE_SUMMARY.md |
| T4 — dashboard and category pages | unclaimed | — | site/; scripts/build_site.py; requirements.txt |
| T5 — final integration, source/row validation, build and link checks | unclaimed | — | tests/; data/; docs/; index.html; .github/workflows/; .nojekyll; README.md |
| T6 — PR, merge, GitHub Pages deployment and publication record | unclaimed | — | COORDINATION.md; deployment record |

Statuses: unclaimed / in progress / done / needs review. `needs review` items are published on Flagged for Review and do not block integration. No numerical gap will be inferred to complete a row.

## Claim and handoff log
- 2026-11-07: Session `arena-489b75a1-china1` inspected the repository: only README.md (`# China1`) and the initial commit were present; no existing substantive entries or task claims to audit. Claimed T0 and created this board before research. No user-specific balance, income source, Chinese/US tax residence, location, account holder nationality beyond US citizenship, or historical tax filings were supplied; these remain unknown, not assumed.

- 2026-11-07: T0 complete; initial `git pull --rebase` reported that the fixed remote branch did not yet exist. Created that same permitted branch with the initial push; no other branch was created. Claimed T1. All subsequent pushes will rebase first.

## Verification and irregularity log
- 2026-11-07 — T1 complete, immediately claimed T2 (sequential scope handoff to the same session). `research/china.json` contains 21 official sources and 41 requirements/findings/unknowns/flags, all row-linked; JSON and source-reference integrity checked. Detailed verification method and exceptions are in `research/china-notes.md`.
- T1 principal official sources: SAFE current-account guide (https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html), SAFE 2026 salary Q&A (https://www.safe.gov.cn/tianjin/2026/0713/3088.html), SAFE 2024 emigration amendments (https://www.safe.gov.cn/tianjin/2024/0903/2594.html), 2024 Anhui capital-account guidance (https://www.safe.gov.cn/anhui/file/file/20250925/43f09589bb2046c2a01a58d3a80c2b5f.pdf), and the 2026 dividend change at MOF (http://szs.mof.gov.cn/zhengcefabu/202609/t20260901_3996442.htm) and STA (https://fgk.chinatax.gov.cn/zcfgk/c102416/c5252107/content.html). Every remaining URL and locator is recorded beside its source ID in china.json.
- T1 flags: former FIE-dividend exemption repealed effective 2026-09-01; old staged property-transfer schedule superseded; user eligibility, balance, income source and prices unknown; China cash-exit thresholds not substantively exposed by the retrieved Customs page, so no number inferred. Failed/insufficient retrieval attempts are documented in china-notes.md. These review items do not block integration but must be published.

## Integration and publication record
- Pending. This session will perform sequential integration only after research tasks finish, then validate rows and links before opening and merging a PR into main.
