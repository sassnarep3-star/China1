# Requirements — line-by-line coverage (Edition I)

Status: `met` = delivered and verified · `met-conditional` = delivered as a conditional
method because the personal facts needed for a single answer do not exist ·
`not-met` = deliberately not claimed, with the reason.

| # | Requirement (from the brief) | Status | Where |
|---|---|---|---|
| R1 | Collect, organize and analyze a full list of requirements | met | This file; `site/requirements.html` |
| R2 | Create an executive summary of important details | met | `site/index.html` (bottom line + six findings) |
| R3 | As a US citizen, find the best way to get money out of China with least tax penalty | met-conditional | `site/index.html` decision tree; routes P01/C01/C02/C03/C05 |
| R4 | Research CNY→USD conversion methods | met | `site/routes.html` — 32 routes |
| R5 | List as many ways as possible | met | 32 routes across 6 categories |
| R6 | List pros and cons of every way | met | Every `method-*.html` page has separate pros/cons |
| R7 | Break down the conversion penalty | met | `site/penalty.html` — 26 components, 7 scenarios |
| R8 | Estimate costs in $10,000 increments to $400,000 | met | 40 rows × 32 routes = 1,280 generated rows; `cost-ladder.csv` |
| R9 | Mobile-friendly table, most important info first | met | Mobile-first CSS: stacked cards < 640px, sticky nav, KPI block first |
| R10 | Actually estimate costs for every method | met-conditional | Published components computed; unpublished components blank (F07) |
| R11 | Step-by-step explanation of each method | met | Numbered steps on every lawful route page |
| R12 | No manual input on my part | met | No form, login, upload or account data anywhere |
| R13 | Verify line by line against official sources | met | Every route and row carries source links; 7,556 verifier checks |
| R14 | Blank + flagged when a value cannot be confirmed | met | Blank/UNVERIFIED cells; 18 flags in `site/review.html` |
| R15 | Review the repo, flag irregularities, link sources | met | `site/repo-review.html` + flags F01–F18 |
| R16 | Clean landing page and category subpages | met | 9 sections, 42 pages |
| R17 | GitHub Pages live site | met | Published from `main` at the repository root |
| R18 | Coordinate with other sessions, avoid conflicts | met | `COORDINATION.md` claim, isolated `edition-i/` scope |
| R19 | Open a PR, merge without waiting, confirm Pages | met | See publication record below |
| R20 | Publish flagged items so they can be reviewed later | met | `site/review.html`, clearly labelled, non-blocking |

## Deliberately not claimed

| Item | Why |
|---|---|
| An exact personal all-in quote | Requires your bank, execution rate, receiving bank and fee tier |
| An exact personal tax figure | Requires residency, basis, acquisition dates, source and compliance history |
| Certification that a bank will process a specific amount | No public source can provide this |
| Certification that no China inheritance tax applies | No statute was located, but absence of a located statute is not proof |
| A treaty-reduced 10% dividend rate for your facts | Relief depends on shareholder eligibility and claim procedure |
| Gold or offshore-RMB routes | No official rule or price was verified; published as unverified, not recommended |

## Publication record

Filled in after merge and deployment; see `COORDINATION.md` for the authoritative log.
