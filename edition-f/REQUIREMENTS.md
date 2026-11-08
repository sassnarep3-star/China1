# Edition F requirements traceability

Legend: **M** = met by an artifact/check; **M\*** = met with a documented limitation; **P** = pending publication action at the time this file is written.

| # | Requirement | Status | Evidence | Limitation / note |
|---|---|---|---|---|
| R1 | Research ways to convert CNY→USD for a US citizen | M | `data/methods.json`, `site/methods.html` | 31 methods across current-account, capital/property/corporate, cash/cards/closed-loop, prohibited/unverified. |
| R2 | List as many methods as possible with pros/cons | M | `site/methods.html` | Every method row has pros and cons; “exhaustive” is treated as a broad inventory, not a guarantee every private product exists. |
| R3 | Deep breakdown of the conversion penalty | M | `data/penalty_layers.json`, `site/penalty.html` | 12 layers separated: FX margin, issuer fees, corridor unknowns, access costs, PRC tax, US FX gain, reporting penalties, unlawful fines, cash/card costs. |
| R4 | Cost estimates in $10,000 increments from $10,000 to $400,000 | M | `site/costs.html`, `site/cost-ladder.csv`, `site/cost-ladder.json` | Exactly 40 targets; verifier recomputes from inputs. |
| R5 | Mobile-friendly tables, most important info first | M | `site/assets/style.css`, `site/index.html`, `site/costs.html` | Viewport meta, horizontal table scroll, sticky header, primary ladder columns ordered by importance; optional JS only for menu toggle. |
| R6 | Exact step-by-step mechanics per method | M* | `site/mechanics.html` | Lawful/conditional routes have published documentary steps. Prohibited/unverified wrappers receive no operational steps, with reason and source. |
| R7 | Least tax penalty analysis for a US citizen | M* | `site/tax.html`, `site/reporting.html`, `EXECUTIVE_SUMMARY.md` | No personal tax amount is computed because facts are absent; statutory rules, §988 threshold/character conflict, FEIE/FTC and reporting are separated. |
| R8 | Every table row links an official/source-verified source | M | `build/verify.py` check “every HTML table row has an external source/artifact link” | Legal/tax rows use official sources; provider prices use issuer tariffs labelled provider-primary; audit rows add repo-primary artifacts. |
| R9 | Unverifiable values stay blank and are flagged | M | `site/flagged.html`, `data/flags.json`, `data/cost_inputs.json` | Blank cells render an unverified badge; model blank fields are covered by flags; no zero/typical/midpoint substitution. |
| R10 | Official verified trusted sources | M* | `data/sources.json`, `site/sources.html` | 35 official + 12 provider-primary sources; evidence read and limitations recorded. Provider sources support only provider prices/terms. |
| R11 | Repo review flagging irregularities | M | `data/repo_audit.json`, `site/audit.html`, `audit/REVIEW_NOTES.md` | 15 findings, including root overclaims, Edition C adjusted FBAR dollars, merged Edition D assumptions, open PR #12 conflict. Earlier editions not edited. |
| R12 | Executive summary outlining important details | M | `EXECUTIVE_SUMMARY.md`, `site/index.html` | Most important actions, cost snapshot, decision fork, penalty layers, audit highlights, limits. |
| R13 | Clean landing page + category subpages | M | `site/index.html` + 10 subpages | Overview, costs, methods, mechanics, penalty, tax, reporting, audit, flagged, sources, methodology. |
| R14 | Findings in simple tables | M | All site pages | Key findings, methods, steps, costs, tax, flags, audit and sources are table rows. |
| R15 | No broken internal links | M | `build/verify.py` internal link/anchor check | External HTTP liveness is not continuously checked; flagged F21. |
| R16 | Live GitHub Pages dashboard | M | Target `https://sassnarep3-star.github.io/China1/edition-f/site/index.html`; publication record in root `COORDINATION.md` | Confirmed after PR #17 merge at e414add; Pages run 42536528502 succeeded and live pages were fetched. |
| R17 | Fully autonomous PR to main, merge, confirm deploy, log | M | Root `COORDINATION.md` session board | PR #17 merged without approval; Pages deploy confirmed; publication record appended to COORDINATION.md. |
| R18 | Read/create COORDINATION.md and claim scope | M | Root `COORDINATION.md` appended session board | Original edition-d claim superseded by edition-f scope after concurrent PR #13 merge; earlier boards preserved. |
| R19 | Non-overlapping scopes / preserve prior work | M | `audit/REVIEW_NOTES.md`, git diff | Only `edition-f/**`, `.github/workflows/edition-f.yml`, and appended COORDINATION section changed. |
| R20 | Reproducible build, no dependency risk | M | `build/build.py`, `build/verify.py`, `.github/workflows/edition-f.yml` | Pure Python 3 stdlib; byte-identical rebuild check; separate workflow, shared verify.yml untouched. |
| R21 | Machine-readable data alongside prose | M | `data/*.json`, `site/cost-ladder.csv`, `site/cost-ladder.json` | Sources, methods, inputs, penalty, tax, flags, audit and ladder exports. |
| R22 | Honest about scope limits / not advice | M | `site/methodology.html`, `site/flagged.html`, README | Dynamic quotes, date mismatch, personal facts, external liveness and prohibited-route limits are explicit. |

## Verification commands

```bash
python3 edition-f/build/build.py
python3 edition-f/build/verify.py
```

Latest local and CI result: **PASS — 27 checks, 0 failures**; PR #17 merged and Pages deployed.
