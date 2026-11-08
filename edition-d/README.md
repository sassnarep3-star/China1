# Edition D — verified CNY→USD cost dashboard

Additive edition. Earlier editions remain intact; irregularities found in them are
flagged on `docs/repo-review.html` and `docs/flagged.html`, not silently edited.

## What is here

- `data/sources.json` — 52 registered sources (government/regulator/court + provider-origin; one secondary cross-check excluded from row citations).
- `data/methods.json` — 43 distinct candidates: legal entitlements, execution rails, business routes, adjacent alternatives, rejected/unavailable candidates. They are not double-counted as independent ways to move the same money.
- `data/costs.json` — 1,720 cost rows: every candidate × every $10,000 increment from $10,000 to $400,000. Unknown values are `null` and rendered blank + UNVERIFIED, never zero.
- `data/taxes.json`, `data/penalty.json`, `data/flags.json`, `data/summary.json`, `data/repo-review.json`.
- `docs/` — 58 static pages: landing dashboard, executive summary, cost explorer, 5 category pages, 43 method pages with cost grids and step-by-step instructions, tax, penalty breakdown, requirements, sources, Flagged for Review, repo audit, methodology.

## Build and verify

```bash
python3 edition-d/build/audit.py     # line-by-line repo scan -> data/repo-review.json
python3 edition-d/build/build.py     # data -> costs.json + docs/
python3 edition-d/build/verify.py    # citations, grids, blanks, links, reproducibility
```

CI: `.github/workflows/edition-d-verify.yml` runs the same commands plus all
earlier editions' checks and requires clean diffs.

## Cost-model rules

1. Target USD is the desired receipt amount; CNY principal is unknown without a live quote.
2. Sender-fee cells show only published tariff bounds/zeros (BOC, HSBC) or explicitly observed Wise public quotes (listed separately, not extrapolated).
3. FX cost, correspondent/receiver charges, documentation, tax and all-in totals are blank + UNVERIFIED.
4. A legal entitlement is priced by choosing an execution rail; rail fees are not added twice.
5. Prohibited schemes receive no execution instructions and no legitimising price.
