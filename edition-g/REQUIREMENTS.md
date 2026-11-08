# Edition G — Requirements coverage

Research date: 2026-11-08 UTC. This edition is additive; earlier editions are preserved.

| # | Requirement | Where satisfied | Verification |
|---|---|---|---|
| R1 | Enumerate as many CNY→USD routes as possible with pros/cons | `data/methods.json`: 43 distinct candidates in 5 categories; `docs/category-*.html`, `docs/method-*.html` | `build/verify.py` checks categories, sources, steps, pros/cons presence |
| R2 | Least-tax-penalty lawful path | `docs/executive-summary.html`, `data/summary.json` decision order | Source-linked; no universal percentage claimed |
| R3 | Decompose the "conversion penalty" | `docs/penalty.html`, `data/penalty.json`: 7 distinct layers | Unknown amounts blank; penalty ceilings not added to transfer costs |
| R4 | Cost estimates at every $10k increment $10k–$400k for every method | `data/costs.json`: 1,720 rows (43×40); rendered on every method page | `verify.py` enforces exact 40-point grid per candidate |
| R5 | Mobile-friendly tables, most important information first | Responsive sticky-first-column tables; cost grid placed before eligibility/steps on method pages | CSS media queries; cost grid is first content section |
| R6 | Exact step-by-step execution instructions | `steps` on every lawful/conditional method; verification-only steps for unverified candidates; none for prohibited | `verify.py` forbids steps on prohibited candidates |
| R7 | Executive summary | `docs/executive-summary.html` | Source-linked findings |
| R8 | Full requirements list | `docs/requirements.html` + this file | Per-method requirements aggregated |
| R9 | Every table row carries an official-source link | Cost rows link registry sources; registry distinguishes government vs provider-origin | `verify.py` checks every rendered cost row has source links + UNVERIFIED badge |
| R10 | Unverifiable values blank and flagged, never inferred | `cny_principal`, FX, downstream, documentation, tax, all-in all null; sender fees only published bounds/zeros/observed quotes | `verify.py` enforces null discipline |
| R11 | Repo reviewed line by line; irregularities flagged | `build/audit.py` scans every tracked text line; `data/repo-review.json`; `docs/repo-review.html` | 92 files / 18,148 lines scanned; 20 findings published, prior editions untouched |
| R12 | Clean dashboard GitHub Pages site with landing + category subpages | `docs/index.html` + 5 category pages + 58 total pages | Internal link/fragment checks |
| R13 | Coordinate via COORDINATION.md; non-overlapping scope; small commits | Root `COORDINATION.md` session board; exclusive `edition-g/**` scope | Claim committed/pushed before build |
| R14 | Final integration re-verifies combined data and links | All five editions' generators/checks re-run together | All pass with clean diffs |
| R15 | PR to main merged without waiting; Pages confirmed; recorded | See root `COORDINATION.md` integration log | Recorded after merge/deploy |
| R16 | Flagged items published without blocking | `docs/flagged.html`: 47 flags | Open flags do not block; unsafe claims blank/rejected |
| R17 | Retry failed builds/checks/deploys until live | CI workflow `edition-g-verify.yml`; integration log | Recorded after deploy |

## Known limits (published, not hidden)

- No executable CNY→USD quote exists for the user's unknown amount/date; all-in totals are blank.
- Wise current full fee schedule unverified; only four public source-CNY quotes observed.
- MoneyGram/PayPal/Revolut/Remitly/Xoom outbound CNY corridors unverified.
- National 2024 capital-account PDF extraction stopped before §6.4; official local service guides citing §6.4 are used instead.
- Personal tax facts unknown; tax amounts blank.
