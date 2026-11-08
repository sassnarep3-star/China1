# Requirements — full list, with traceability

Every requirement from the brief, restated as a testable item, with where it is satisfied and how compliance was checked. Nothing is marked met unless there is an artifact to point at.

Legend: **M** = met · **M\*** = met with a documented limitation (see the Flagged page).

## A. Research requirements

| # | Requirement | Status | Where satisfied | Evidence / how checked |
|---|---|---|---|---|
| R1 | Research ways to convert CNY into USD | M | `dossier/channels.html`, `data/channels.json` | 35 routes across 5 categories (current account, capital account, cash & cards, keep-in-place, unlawful). |
| R2 | "List as many as possible" | M | same | Includes the closed-loop investment schemes, the three cash tiers, card spending vs card withdrawal, the capital-account transfers, and the 8 unlawful routes people are actually offered. |
| R3 | List pros and cons of **all** the ways | M | `dossier/channels.html` (expandable detail per route) | Every one of the 35 routes has a pros list and a cons list. |
| R4 | Keep researching / break down the conversion penalty | M | `dossier/costs.html`, `data/costs.json` (`HEADLINE` + 24 line items) | Split into (a) unavoidable cost, (b) real Chinese tax unrelated to converting, (c) penalty exposure for skipping a lawful route, (d) comparison baselines. |
| R5 | "Think about this problem deeply" | M | `dossier/index.html` findings 1–5, `dossier/strategy.html`, `EXECUTIVE_SUMMARY.md` | The reframing — the premise itself is the most expensive part — plus the 境内/境外 fork, the current/capital-account split, and the identification of 50% FBAR exposure as the only genuinely large number. |
| R6 | As a US citizen, what is the best route with least tax penalty | M | `dossier/strategy.html` | Sequenced plan + ranked outcomes for the stated fact pattern, with the caveat that the ranking forks on facts flagged F01–F05. |

## B. Verification requirements

| # | Requirement | Status | Where satisfied | Evidence / how checked |
|---|---|---|---|---|
| R7 | No hallucinations | M | `scripts/build_site.py` validation + `scripts/data_*.py` | Every numeric cell is either quoted from a linked official source or derived by stated arithmetic from a quoted value. Nothing is estimated. The generator hard-fails on an unknown source id. |
| R8 | Verify from official verified trusted sources | M | `dossier/sources.html`, `data/sources.json` | 31 sources, graded into tiers A/B/C. Tier A = the instrument or the issuing authority's own page (SAFE, PBOC, State Council/gov.cn, STA, GACC, CSRC, IRS, FinCEN, CBP, USC). No tier-D (law-firm blog, aggregator, SEO tax site) supports any claim. |
| R9 | Provide links for manual review | M | Every table row on `channels`, `costs`, `taxes`, `flagged`; full registry on `sources` | Clickable source tags on every row. |
| R10 | Every table row must have a source link to an official site | M | same | Enforced by construction: each row carries a `basis`/`sources` array of source ids, and the build fails if any id is unknown. Rows with no available source are published as UNVERIFIED with all values blank. |
| R11 | If a value can't be confirmed, leave it blank and flag it unverified | M | `dossier/flagged.html` (10 GAP items), blank cells rendered as "blank (unverified)" | Cell values literally absent from the data files for F06–F12 items. Never substituted with a range, midpoint or "typical". |
| R12 | Never infer or fill in values | M | `blank_or()` in `scripts/build_site.py` | Any empty value renders as "blank (unverified)" regardless of the row's status — there is no fallback text. |
| R13 | Work line by line | M | `COORDINATION.md` log, per-source `key_text` fields | The operative clause of each instrument is stored verbatim in Chinese alongside the link, so each sentence can be re-checked against the source page. |

## C. Deliverable requirements

| # | Requirement | Status | Where satisfied |
|---|---|---|---|
| R14 | Collect, organize, and analyze against a full requirements list | M | this file |
| R15 | Executive summary outlining important details | M | `EXECUTIVE_SUMMARY.md`; also rendered as the site's Overview page |
| R16 | No manual input required from the user | M | All tasks executed end-to-end in this session: research, data, site, verification, PR, merge, deploy. |
| R17 | Review the repo / flag irregularities | M | `COORDINATION.md` log (2 repo irregularities recorded); `dossier/flagged.html` (10 IRREG items) |
| R18 | Flag anything irregular for review | M | `dossier/flagged.html` — 20 items, 10 gaps + 10 irregularities, each with severity, what is missing, and the action the reader should take |

## D. Site requirements

| # | Requirement | Status | Where satisfied |
|---|---|---|---|
| R19 | GitHub Pages live site | M | `dossier/` published from `main; deploy confirmed in `COORDINATION.md` |
| R20 | Clean landing page | M | `dossier/index.html` — hero, five findings, decision fork, headline numbers, scope stats |
| R21 | Subpages organized by category | M | 8 pages, with `channels.html` grouped into categories A–E with in-page anchors |
| R22 | Clean, user friendly, simple, dashboard-like UI | M | Single stylesheet (`dossier/assets/style.css`), sticky nav, card grid, stat tiles, colour-coded verification badges, responsive tables |
| R23 | All entries and findings in simple, easy-to-read table format | M | 15 tables across the site; every route, cost line, tax position, source and flag is a table row |
| R24 | Include all analysis and findings | M | Analysis lives in the lead paragraphs and "what this shows" card grids around each table, plus `strategy.html` and `methodology.html` |
| R25 | Site must build with no broken links | M | The generator runs an internal link and anchor check and exits non-zero on any failure; the final run reported "Internal link check: clean." |

## E. Collaboration / process requirements

| # | Requirement | Status | Where satisfied |
|---|---|---|---|
| R26 | Read/create `COORDINATION.md` before starting | M | `COORDINATION.md` created in the first commit; the repo had none |
| R27 | Task board with status, owner, file scope | M | `COORDINATION.md` task board T1–T10 |
| R28 | Claim before starting, commit and push the claim | M | Claims committed early; see the commit log |
| R29 | Non-overlapping scopes | M\* | Single session, so scopes are disjoint by construction. The brief's `session-<id>/<task>` branch convention was **not** used because the Arena environment pins this session to `arena/7014c891-china1` and forbids creating other branches; isolation is achieved through file scopes instead. Documented at the head of `COORDINATION.md`. |
| R30 | Small frequent commits; `git pull --rebase` before push | M | See commit log |
| R31 | Record sources, verification and irregularities when done | M | `COORDINATION.md` log + `dossier/flagged.html` |
| R32 | Never mark verified without an official source | M | Enforced by the `vstatus` field and the build-time source-id validation |
| R33 | Shared outputs changed only by a final integration session | M | This session performed both the component work and the integration pass; noted in `COORDINATION.md` |
| R34 | Do not stop for review; create the PR, merge it, confirm Pages deploys, record PR link and merge result | M | `COORDINATION.md` log |
| R35 | Publish flagged/unverified items on a clearly labelled page with source links | M | `dossier/flagged.html`, linked from the main navigation as "Flagged for review" |
| R36 | Do not merge a broken site | M | Build + link check + HTML well-formedness check run before merge |

## F. Non-functional

| # | Requirement | Status | Note |
|---|---|---|---|
| R37 | No build toolchain / dependency risk | M | Pure Python 3 standard library. No npm, no frameworks, no CDN calls. |
| R38 | Works without JavaScript | M | Progressive enhancement only; navigation and tables are plain HTML. |
| R39 | Accessible and mobile-readable | M | Semantic headings, responsive tables, no colour-only signalling (status is a text badge). |
| R40 | Reproducible | M | `python3 scripts/build_site.py` regenerates every page and JSON export from the data modules. |
| R41 | Machine-readable data alongside the prose | M | `data/sources.json`, `channels.json`, `costs.json`, `taxes.json`, `flagged.json` |
| R42 | Honest about scope limits | M | `dossier/methodology.html` "Known limits", `EXECUTIVE_SUMMARY.md` §11, flagged F15/F19 |


## G. Amount-scenario addition (arena-22534b4a)

| # | Requirement | Status | Where satisfied | Evidence / limitation |
|---|---|---|---|---|
| R43 | Show USD 10,000 through USD 400,000 in USD 10,000 increments | M* | `pages/estimates.html` | 40 rows; CNY equivalent and arithmetic midpoint spread proxy use the linked Bank of China posted USD rates. The quote's displayed date (2026-11-09) is later than this report date (2026-11-08 UTC), so the result is conditional and explicitly flagged, not a transaction quote. |
| R44 | Cost every route without filling unverified values | M* | `pages/estimates.html` method comparison; `pages/review.html` | Every listed route has a source link. Exact route costs, bank/wire fees, eligibility and taxes remain blank where no official transaction-specific quote was confirmed. Only the posted BOC scenario is calculated; it is not universal. |
