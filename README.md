# China money — CNY → USD evidence guide

Source-linked research and a static dashboard for a **US citizen with CNY in a mainland-China bank account** who wants to convert to USD and move funds out with the least avoidable tax/cost friction.

**Live site:** https://sassnarep3-star.github.io/China1/

**Evidence date:** 2026-11-07 UTC

**Status:** research complete; flagged/unverified items are published, not guessed.

## Bottom line

There is no verified universal “conversion tax” on the whole balance. Start by proving the lawful source of the CNY and use the matching documented bank/approval route. China FX controls, China income tax, US federal tax, currency gain/loss, reporting penalties and commercial FX/transfer fees are separate buckets. No cheapest provider or personalized tax total is ranked without the missing user facts and comparable live quotes.

## Site pages

- `index.html` — clean dashboard and coverage stats
- `executive-summary.html` — decision-ready summary
- `china.html` — China exchange-control and tax requirements/findings
- `us.html` — US federal tax and reporting requirements/findings
- `routes.html` — 29 routes with conditions, limits, pros/cons and sources
- `requirements.html` — combined checklist and unknown inputs
- `costs.html` — delivered-USD formula and blank/unverified cost matrix
- `analysis.html` — decision steps, conditional recommendations, scenarios, myths
- `flagged.html` — Flagged for Review register
- `sources.html` — 58 official/primary sources with locators and verification dates

## Repository layout

```text
research/           JSON evidence + notes (china, us, routes, analysis)
EXECUTIVE_SUMMARY.md
scripts/            deterministic site builder and CSV exporter
site/               CSS/JS source and generated public/ artifact
data/               flat evidence.csv and sources.csv exports
tests/              offline acceptance checks
docs/verification.md
.github/workflows/pages.yml
COORDINATION.md     task claims, verification log, PR/merge/deployment record
```

## Build and verify locally

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/export_data.py
.venv/bin/python -m unittest discover -s tests -v
node --check site/app.js
python -m http.server 8000 --bind 0.0.0.0 --directory site/public
```

The build is deterministic and self-contained: no CDN, analytics or browser-side backend calls. Every rendered data row links to at least one official/primary source. Unverified numeric cells are intentionally blank, not zero.

## Verification and flags

See [`docs/verification.md`](docs/verification.md) for the repository audit, source policy, irregularities, failed retrievals and reproduction steps. Flagged items appear on the live **Flagged for Review** page and do not block publication; the site must still pass build/structural checks before merge and deploy.

## Coordination

Work is tracked in [`COORDINATION.md`](COORDINATION.md). The execution environment fixes the working branch to `arena/489b75a1-china1`; sequential non-overlapping scopes replace per-task branches. The integration PR is opened from that fixed branch into `main`, merged autonomously after checks pass, and the Pages deployment result is recorded there.

## Disclaimer

This is source-backed research, not personalized tax, legal or investment advice. User-specific balance, income source, residence/status, asset history, filings, bank, destination and live quotes were not supplied and remain unverified.
