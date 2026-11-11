# Final integration — requirements and traceability

Session `arena-eb9f0490`, 2026-11-10. Each line of the request, where it is met, and how it is checked. "Checked" means `guide/build/verify.py` fails if the statement stops being true.

## Research

| Requirement | Where it is met | Checked by |
|---|---|---|
| Best way to get the money out and convert to USD with the least tax penalty | `index.html` short answer; `guide/summary.html` | Text generated from the ladder data |
| A clear list of questions, information and answers needed before any decision, with suggestions for finding what is missing | `guide/decision.html`: 24 questions, each with what the rules say, what is missing, how to find it and a status | `guide/build/verify.py`: every question must have an official source, a source for the how-to and a valid status; an open question must be flagged |
| As many CNY→USD methods as possible, with pros and cons | `guide/methods.html`: 20 methods (16 lawful, 4 prohibited) | Every method has a source; prohibited ones have no steps |
| Break down the "conversion penalty" | `guide/taxes.html`; summary table "What the conversion penalty is made of" | Every row sourced |
| Cost of every method at each $10,000 step to $400,000 | `guide/costs.html`; `guide/data/cost-ladder.csv` | 40 exact steps × 20 methods = 800 rows; 370 priced totals recomputed independently; the price table also shows the previous day's board so the effect of a rate move is visible |
| Exactly how each method works, step by step | `guide/steps.html` | Every step has a source |
| Executive summary | `guide/summary.html`; `EXECUTIVE_SUMMARY.md` | Generated from the same data |

## Verification

| Requirement | Where it is met | Checked by |
|---|---|---|
| Every table row has an official source link | All tables | HTML parser: each row must link a host listed in `guide/data/sources.json` |
| Unconfirmed values left blank and flagged, never inferred | Blank cells link to `guide/flagged.html` | Each blank cell must carry a Flagged link; each blank ladder row must carry a flag |
| Official, trusted sources only | `guide/sources.html`: 33 sources with quoted text and the date each was last read; 2 seen only as excerpts are flagged | Figures in `prices.json` must appear in the quoted source text |
| Review the repository line by line; flag irregularities; links for manual review | `guide/repo-review.html`; `guide/data/scan-hits.csv` | Scan snapshot present for every rule |

## Site

| Requirement | Where it is met | Checked by |
|---|---|---|
| Clean landing page plus subpages by category | `index.html` and ten pages under `guide/` | Landing page must link every subpage; 11 pages crawled |
| Simple dashboard, mobile-friendly tables, most important first | Stacked tables under 720 px; answer card first on every page | Viewport tag and `data-label` on every cell; no scripts or external assets |
| Flagged for Review page with source links | `guide/flagged.html` | Every flagged item has an anchor and a source |
| No broken links | Whole repository, including archived editions | Crawl of every HTML file |

## Process

| Requirement | Where it is met |
|---|---|
| Coordination protocol: claim, small commits, rebase before push, handoff notes | `COORDINATION.md`, block `arena-eb9f0490` |
| Pull request to `main` with summary, sources and flagged items; merge; confirm deployment | Release record in `COORDINATION.md` |
| Earlier sessions' work not discarded | All earlier editions kept in place; reachable from `guide/archive.html` |

## Limits

- The guide does not know your immigration history, where the money came from, what tax was withheld, or what you filed. Those decide which route applies.
- Prices are published tariffs and one dated rate reading, not a quote.
- Archived editions are not re-verified beyond the rule scan and their own build scripts.
