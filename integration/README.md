# Consolidated dashboard

This is the maintained integration layer, not a new independent research edition. It combines the prior editions with directly retrieved government, court and first-party provider sources dated 2026-11-10.

## Build and verify

```bash
python3 integration/build.py
python3 integration/verify.py
```

`build.py` is the source of truth for the registry, findings, refreshed partial-cost formulas and consolidated templates. It generates:

- `../index.html` — executive portal and historical-edition access;
- `costs.html`, `costs.json`, `costs.csv` — 40 scenarios, $10,000–$400,000;
- `methods.html` — 43 candidates linked to Edition H’s procedures and grids;
- `tax.html` — tax/reporting distinctions and primary law;
- `review.html` — visible unresolved items and irregularities;
- `evidence.html` / `evidence.json` — direct source registry;
- `methodology.html` — formulas, source hierarchy and limitations.

Generated outputs are committed because Pages uses the legacy `main` / root source. No runtime dependencies, scripts, web fonts or credentials are used.

## Evidence and blanks

The 40 refreshed scenarios use BOC’s observed USD100 cash ask of CNY669.03 on 2026-11-10 (CNY6.6903/USD). BOC and HSBC values are published sending commissions plus cable charges only. Unknown FX execution, downstream, document, tax and all-in amounts remain JSON `null` and display as blank + UNVERIFIED. Blank never means zero.

The separate Edition H grid uses its own dated CNY6.6919 observation and remains historical. Provider pages support only that provider’s terms; government/regulator/court pages support law and tax. Source presence does not certify an individual’s eligibility or guarantee external uptime.

## Maintenance contract

1. Update source records and findings in `build.py`; do not hand-edit generated HTML/JSON/CSV.
2. Do not replace an unknown with zero or a plausible estimate.
3. Keep prohibited candidates free of execution instructions.
4. Preserve narrow-screen table labels and every historical-edition link.
5. Run the integration verifier, Edition D root preservation check and all prior-edition checks before release.
6. Record material decisions and deployment results in `../COORDINATION.md`.

`verify.py` independently recomputes 160 fee/conversion values, checks all 40 targets and 43 method links, enforces per-row source hosts, compares deterministic output hashes, and crawls local references across every repository HTML file. It is a structural/arithmetic check, not legal advice or a live transaction test.
