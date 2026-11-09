# China Money — Edition H

Independent, additive CNY→USD research edition. Earlier editions and the shared portal are intentionally unchanged.

- Published dashboard (after merge/deploy): <https://sassnarep3-star.github.io/China1/edition-h/site/>
- Research date: **2026-11-09 UTC**.
- 43 candidates in five categories; 40 requested amount points per candidate; 1,720 cost rows.
- 53 registered sources; S52 is an excluded secondary cross-check and is never cited by a method or cost row.
- Unknown JSON values are `null` and render as a visibly blank cell plus **UNVERIFIED**. **N/A** is reserved for non-executable/non-applicable candidates.
- Known/partial sender charges are not all-in totals. Live FX, correspondent/receiver fees, document costs and personal tax remain separately identified.

## Rebuild and verify

```bash
python3 edition-h/build/audit.py
python3 edition-h/build/build.py
python3 edition-h/build/verify.py
```

The standard-library generator writes 58 static HTML pages, `site/assets/style.css`, `.nojekyll`, and the full `site/cost-ladder.csv`. The verifier checks row counts, the exact amount grid, source coverage, arithmetic, blank semantics, prohibited-method dispositions, local links/anchors and mobile markup. Results are written to `audit/verification.json`.

## Important interpretation

A legal entitlement (for example, documented current income or an emigrant-property approval) and an execution rail (for example, a BOC telegraphic transfer) are alternatives at different layers, not cumulative charges. Personal-entitlement grids use an explicitly labeled conditional BOC TT scenario. Business/entity routes do not assume a personal-bank tariff. Prohibited candidates are identified for risk awareness but receive no operational instructions or legitimising prices.
