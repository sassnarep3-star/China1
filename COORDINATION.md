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
| T2 — official US tax and reporting evidence | done | arena-489b75a1-china1 | research/us.json; research/us-notes.md |
| T3 — route inventory, evidence-backed comparison, executive analysis | done | arena-489b75a1-china1 | research/routes.json; research/analysis.json; EXECUTIVE_SUMMARY.md |
| T4 — dashboard and category pages | in progress | arena-489b75a1-china1 | site/; scripts/build_site.py; requirements.txt |
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

- 2026-11-07 — T2 complete; immediately claimed T3. `research/us.json` contains 25 official sources and 40 linked requirements/findings/unknowns/flags; JSON and references checked. Principal sources: IRS Publication 54 (https://www.irs.gov/publications/p54), current 2026 FEIE amount (https://www.irs.gov/individuals/international-taxpayers/figuring-the-foreign-earned-income-exclusion), FTC (https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit), treaty (https://www.irs.gov/pub/irs-trty/china.pdf), FBAR (https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar), FATCA (https://www.irs.gov/businesses/corporations/summary-of-fatca-reporting-for-us-taxpayers), and CBP cash reporting (https://www.cbp.gov/travel/international-visitors/money-monetary-instruments). Remaining URLs/locators are in us.json; method and exceptions in us-notes.md.
- T2 review flags: stale FEIE overview amounts superseded by the current figuring page; official section 988 read from the 2024 US Code because current OLRC URLs were unavailable; no user-specific tax/state result inferred; April 2026 remittance regulatory details were proposed and concern outbound-from-US transfers, not inbound China-to-US wires by default. Publish these limitations on Flagged for Review.

- 2026-11-07 — T3 complete; immediately claimed T4. `research/routes.json`: 29 routes, 12 additional official/primary provider sources, 33 linked rows including flags; `research/analysis.json`: 35 linked decision/cost/scenario/myth/flag rows referencing the complete cross-domain source set; `EXECUTIVE_SUMMARY.md` written. Validation passed: unique source IDs, all references resolve, all route commercial costs null, all analysis cost-component values null, unverified/non-equivalent routes flagged, `git diff --check` clean. No cheapest-route or personalized tax ranking inferred.
- T3 principal route/cash sources: Wise (https://wise.com/help/articles/2955298/guide-to-cny-transfers), Western Union China (https://www.westernunion.com/cn/en/send-money.html), PBOC RMB carrying limit (https://www.pbc.gov.cn/chubanwu/114566/114579/114643/2839193/index.html), foreign-cash rule (https://www.gov.cn/gongbao/content/2004/content_63085.htm), 2024 consular confirmation (https://almaty.china-consulate.gov.cn/lsfw/lqgk/202404/t20240415_11281945.htm), and amended FDI notice (https://www.safe.gov.cn/tianjin/2025/0829/2871.html). Full evidence/locators in routes.json.
- T3 review flags: MoneyGram generic page and Remitly inbound-to-China page do not verify outbound products; current bank-draft/traveler's-cheque issuance/acceptance unverified; detailed current FDI checklists unverified because old attachments were repealed; no live comparable prices. Earlier China cash-threshold retrieval gap is resolved by the new primary/official sources, not by inference. Historical T1 note remains as written; T3/analysis supersede that limitation. Failed Shenzhen/Guangzhou alternatives were not used as evidence.

## Integration and publication record
- Pending. This session will perform sequential integration only after research tasks finish, then validate rows and links before opening and merging a PR into main.
