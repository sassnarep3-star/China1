# Final integration — requirements and traceability

Session `arena-f766722d`, 2026-11-11 (additive on arena-eb9f0490, 2026-11-10). Each line of the request, where it is met, and how it is checked. Re-verified live via web_search on 2026-11-11; sources still publish same rules. "Checked" means `guide/build/verify.py` fails if the statement stops being true.

## Research

| Requirement | Where it is met | Checked by |
|---|---|---|
| Best way to get the money out and convert to USD with the least tax penalty | `index.html` short answer; `guide/summary.html` | Text generated from the ladder data |
| As many CNY→USD methods as possible, with pros and cons | `guide/methods.html`: 19 methods (15 lawful, 4 prohibited) | Every method has a source; prohibited ones have no steps |
| Break down the "conversion penalty" | `guide/taxes.html`; summary table "What the conversion penalty is made of" | Every row sourced |
| Cost of every method at each $10,000 step to $400,000 | `guide/costs.html`; `guide/data/cost-ladder.csv` | 40 exact steps per method; totals recomputed independently |
| Exactly how each method works, step by step | `guide/steps.html` | Every step has a source |
| Executive summary | `guide/summary.html`; `EXECUTIVE_SUMMARY.md` | Generated from the same data |
| Clear list of questions, have/not-have, answers and suggestions to discover missing info | `guide/questions.html`: 16 blocking questions (Q01–Q16) with have/missing/answer/how-to-find, 10 known facts, best-way hierarchy (4 ranks), 8-step discovery plan | Every row carries an official source; personal-data blanks stay blank & flagged |

## Verification

| Requirement | Where it is met | Checked by |
|---|---|---|
| Every table row has an official source link | All tables | HTML parser: each row must link a host listed in `guide/data/sources.json` |
| Unconfirmed values left blank and flagged, never inferred | Blank cells link to `guide/flagged.html` | Each blank cell must carry a Flagged link; each blank ladder row must carry a flag |
| Official, trusted sources only | `guide/sources.html`: 33 sources with quoted text; 2 seen only as excerpts are flagged | Figures in `prices.json` must appear in the quoted source text |
| Review the repository line by line; flag irregularities; links for manual review | `guide/repo-review.html`; `guide/data/scan-hits.csv` | Scan snapshot present for every rule |

## Site

| Requirement | Where it is met | Checked by |
|---|---|---|
| Clean landing page plus subpages by category | `index.html` and ten pages under `guide/` (new Decide page) | Landing page must link every subpage |
| Simple dashboard, mobile-friendly tables, most important first | Stacked tables under 720 px; answer card first on every page | Viewport tag and `data-label` on every cell; no scripts or external assets |
| Flagged for Review page with source links | `guide/flagged.html` | Every flagged item has an anchor and a source |
| No broken links | Whole repository, including archived editions | Crawl of every HTML file |

## Process

| Requirement | Where it is met |
|---|---|
| Coordination protocol: claim, small commits, rebase before push, handoff notes | `COORDINATION.md`, block `arena-f766722d` (additive atop arena-eb9f0490) |
| Pull request to `main` with summary, sources and flagged items; merge; confirm deployment | Release record in `COORDINATION.md` (arena-f766722d) |
| Earlier sessions' work not discarded | All earlier editions kept in place; reachable from `guide/archive.html` |

## Limits

- The guide does not know your immigration history, where the money came from, what tax was withheld, or what you filed. Those decide which route applies.
- Prices are published tariffs and one dated rate reading, not a quote.
- Archived editions are not re-verified beyond the rule scan and their own build scripts.

## Refresh of the priced inputs, 2026-11-11 (session `arena-db079cfc`)

| Item | Change | Checked by |
|---|---|---|
| Bank of China board | re-read at 2026-11-11 10:25:02 Beijing time: buy 666.30, sell 669.11 per USD 100 (was 665.71 / 668.51 on 2026-11-10) | `verify.py` recomputes all 370 totals from `prices.json` and fails if a board figure is missing from the quoted source text |
| Wise | five fresh quotes at the amounts implied by the new midpoint (2026-11-11T02:35Z); the old five no longer matched and would have blanked the column | every figure in `prices.json` must appear in the `PR-WISEFEE` quote |
| Sources | 16 of 33 re-opened and re-read today; the sources page now prints the read date for every entry, and an entry without one fails the build | new `checked` gate in `verify.py` |
| ATM fee check | previously compared against a string hard-coded from the old exchange rate; now recomputed with exact fractions | mutation-resistant: changing `prices.json` re-derives the expectation |
| Working record | `edition-db079cfc/verification/` — per-source re-check, findings P-01…P-11, raw checker output | linked from the repository-review page |

