# Edition I — verified CNY→USD research dashboard

**Live:** https://sassnarep3-star.github.io/China1/edition-i/site/

Session `arena-e90d36c3`, built 2026-11-10. Independent research pass: 21 official sources
fetched and read during this session (government: SAFE, PBOC, China STA, China Customs,
IRS, GPO govinfo; provider: Bank of China, Wise). Every displayed row links the official
page it was checked against. Values that cannot be confirmed are **blank + flagged**, never
inferred.

## What is here

| Page | Contents |
|---|---|
| `site/index.html` | Dashboard: bottom line, KPIs, decision table, headline costs |
| `site/executive-summary.html` | The direct answer to the brief, with cost preview |
| `site/methods.html` | 21 methods (15 lawful/conditional + 6 prohibited) with pros/cons |
| `site/steps.html` | Step-by-step procedures per lawful route |
| `site/costs.html` | 10 cost ladders × 40 targets ($10,000–$400,000 in $10,000 steps) |
| `site/taxes.html` | 14 tax/penalty findings: CN IIT, §988, FBAR, 8938, FTC |
| `site/sources.html` | 21-source register with retrieval notes |
| `site/flagged.html` | 18 published flags (F01–F18), non-blocking |

## Model (all inputs sourced)

- BOC board snapshot 2026-11-10 07:32:39 (S07): buy 666.22 / sell 669.03 CNY per 100 USD
  → one-way FX margin 0.2104% vs midpoint; sell 6.6903 CNY/USD.
- BOC e-banking cross-border TT tariff (S06): 0.1% handling, min ¥50, max ¥260, + ¥150 cable.
- Known subtotal = FX margin + handling + cable. Receiving bank, intermediary and tax
  components are blank + UNVERIFIED (F03–F05). Blank ≠ zero (F17).
- Headline outputs (recomputed by the verifier): $10,000 single wire = **$53.47**;
  $400,000 single wire = **$903.07 (0.2258%)**; $400,000 in 8 × $50,000 quota wires =
  **$1,332.05 (0.3330%)**.

## Build and verify

```sh
python3 edition-i/build/build.py    # deterministic; writes edition-i/site/
python3 edition-i/build/verify.py   # 1,858 checks, 0 errors
```

The verifier rebuilds and requires byte-identical output, independently recomputes every
priced cell from `data/model.json`, checks 40 targets × 10 ladders, requires UNVERIFIED
markers on every unconfirmed cell, resolves every internal link/anchor, restricts external
links to the 20 registered sources, and confirms prohibited methods carry no steps.

## Verification record

- All 21 sources fetched 2026-11-10 via direct page retrieval; quoted figures read from the
  fetched text (quota USD 50,000 = S02 Art. 2; tariff = S06; board = S07; §988(e)(2) $200
  exclusion = S14 statutory text; FBAR/8938 thresholds and penalties = S10–S12; property
  steps = S05; property-transfer reforms = S03 §VI; 2004 transfer framework = S04;
  cash limits = S19/S20; crypto prohibition = S18; IIT categories/rates = S09).
- Irregularities found and published on `site/flagged.html`: 2004 vs 2014 staged-remittance
  conflict (F09), repealed Implementing-Rules Art. 39 fines (F10), uscode.house.gov outage
  requiring GPO 2003-edition text (F11), BOC tariff local-variation caveat (F12), Wise
  quote-time-only fees (F07), and others.
- Nothing is marked verified without a checked official source behind it.

## Scope limits

Source of funds, ID classification (境内/境外), tax history and destination bank are unknown
(F01) — no personalized determination is possible. This edition does not re-certify every
inherited row of editions B–H; disagreements found against this edition's verified sources
are listed in `audit/REPO_AUDIT.md`.
