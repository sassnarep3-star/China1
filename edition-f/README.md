# Edition F — independent CNY→USD verification dashboard

**Live:** https://sassnarep3-star.github.io/China1/edition-f/site/index.html  
**Report date:** 2026-11-08 UTC  
**Branch:** `arena/5b35ee3f-china1`

Edition F is an additive, independently sourced verification edition. It was originally claimed as `edition-d/`, but another session merged a different Edition D in PR #13 while this research was underway. To avoid overwriting that work — and a later concurrent Edition E merged in PRs #15/#16 — this deliverable lives in `edition-f/` and does not edit the root portal, earlier editions, or the shared `verify.yml`.

## What is different

- **Issuer-tariff arithmetic:** BOC personal tariff effective 2025-11-11; HSBC China tariff effective 2026-10-31; SkyRemit single-capture rate pair; Wise single live quote. No 40-point Wise curve is inferred.
- **40-row ladder:** $10,000 → $400,000 by $10,000, with BOC known cost, SkyRemit scenario, HSBC local fee, and blank personal tax/unknown fees. CSV/JSON exports.
- **31 methods:** pros/cons, limits, cost status, and step-by-step mechanics where lawful. Prohibited routes are named and penalised, not instructed.
- **Tax/reporting separation:** PRC IIT, treaty saving clause, US worldwide income/FEIE/FTC/§988, FBAR/8938/3520/FinCEN 105. Current adjusted FBAR dollars and personal tax remain blank.
- **Repository audit:** 15 findings against earlier editions and concurrent Edition D work, with official comparators and non-destructive actions.

## Contents

| Path | Contents |
|---|---|
| `site/index.html` | Landing dashboard, most important actions, cost snapshot, decision fork |
| `site/costs.html` | 40-row primary ladder, detailed inputs, provider one-point quotes, method cost coverage |
| `site/methods.html` | 31 methods grouped by category with pros/cons |
| `site/mechanics.html` | Step-by-step documentary sequences; no steps for prohibited/unverified wrappers |
| `site/penalty.html` | 12-layer conversion-penalty breakdown |
| `site/tax.html` | China, treaty, US tax rows |
| `site/reporting.html` | FBAR, 8938, 3520, cash declarations |
| `site/audit.html` | Repository irregularities and overclaims |
| `site/flagged.html` | 22 review flags and blank-field registry |
| `site/sources.html` | 47 sources (35 official, 12 provider-primary) with evidence read and limits |
| `site/methodology.html` | Build/verify standard and known limitations |
| `data/*.json` | Source register, methods, cost inputs, penalty layers, tax/reporting, flags, repo audit |
| `build/build.py` | Pure-stdlib static generator |
| `build/verify.py` | 27-check verification gate |
| `EXECUTIVE_SUMMARY.md` | Most important findings first |
| `REQUIREMENTS.md` | Requirement traceability |

## Build and verify

```bash
python3 edition-f/build/build.py
python3 edition-f/build/verify.py
```

The verifier checks source-id resolution, issuer-domain allowlists, internal links/anchors, an external source/artifact link on every HTML table row, 40-row ladder recomputation, blank discipline, prohibited-step absence, key table counts, mobile overflow, and byte-identical rebuild. It does **not** prove external HTTP liveness or factual correctness of a source; load-bearing sources were opened manually during research and are flagged for re-opening before execution.

## Verification standard

- Legal/tax propositions cite government/regulator/statute sources.
- Provider prices cite the issuer’s own tariff/product page and are labelled `provider-primary`; they never establish a legal entitlement.
- Unknown values are blank and appear on `flagged.html`; they are not zero, typical, midpoint or inferred.
- Repository audit rows link primary GitHub artifacts plus official comparators where a factual correction is made.
- Prohibited channels receive no operational guidance.

## Not advice

Research with linked sources and shown arithmetic. Not legal, tax or investment advice, and not a bank quote. Rates, tariffs, branch practice and personal facts change the result. Re-quote and obtain fact-specific professional review before executing.
