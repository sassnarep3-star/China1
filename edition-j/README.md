# Edition J — verified CNY→USD research dashboard

**Live:** https://sassnarep3-star.github.io/China1/edition-j/site/

Session `arena-3843fb62`, built 2026-11-10. Independent re-verification pass: 14 official
sources fetched and read live during this session (government: SAFE, PBOC, China STA,
IRS, GPO govinfo; provider: Bank of China, HSBC China, Wise). Two further sources
(S15, S16) are inherited from the integration evidence log and flagged (F12). Every
displayed row links the official page it was checked against. Values that cannot be
confirmed are **blank + flagged**, never inferred.

## What is here

| Page | Contents |
|---|---|
| `site/index.html` | Dashboard: bottom line, KPIs, decision order, headline costs |
| `site/executive-summary.html` | The direct answer to the brief, with cost preview |
| `site/methods.html` | 20 methods (14 lawful/conditional + 6 prohibited) with pros/cons |
| `site/steps.html` | Step-by-step procedures per lawful route |
| `site/costs.html` | 8 cost ladders × 40 targets ($10,000–$400,000 in $10,000 steps) |
| `site/taxes.html` | 15 tax/penalty findings: CN IIT, §988, FBAR, 8938, 3520, FTC |
| `site/sources.html` | 16-source register with retrieval notes |
| `site/flagged.html` | 15 published flags (F01–F15), non-blocking |
| `site/methodology.html` | Formula, worked example, limits |

## Model (all inputs sourced)

- BOC board snapshot 2026-11-10 13:49:58 (S07): buy 665.86 / sell 668.66 CNY per 100 USD
  → one-way FX margin 0.2098% vs midpoint; sell 6.6866 CNY/USD.
- BOC cross-border TT tariff (S06): 0.1% handling, min ¥50, max ¥260, + ¥150 cable.
- HSBC Premier/Advance TT tariff (S08): 0.1%, min ¥100, max ¥500, + ¥120 cable.
- Known subtotal = FX margin + handling + cable. Receiving bank, intermediary and tax
  components are blank + UNVERIFIED. Blank ≠ zero.
- Headline outputs (recomputed by the verifier): $10,000 single wire = **$53.41**;
  $400,000 single wire = **$900.57**; $400,000 in 8 × $50,000 wires = higher (see L3/L4).

## Build and verify

```sh
python3 edition-j/build/build.py    # deterministic; writes edition-j/site/ and edition-j/data/
python3 edition-j/build/verify.py   # 2,462 checks, 0 errors
```

The verifier rebuilds and requires byte-identical output, independently recomputes every
priced cell from `data/model.json`, checks 40 targets × 8 ladders, requires UNVERIFIED
markers on every unconfirmed cell, resolves every internal link/anchor, restricts external
links to the 16 registered sources, and confirms prohibited methods carry no steps.

## Verification record

- All 14 live sources fetched 2026-11-10 via direct page retrieval; quoted figures read
  from the fetched text (Measures Arts. 3/7/9/13/37 = S01; 2020 Arts. 54–65 = S02;
  2014 §VI = S03; card caps = S04; IIT = S05; BOC tariff = S06; board = S07;
  HSBC tariff = S08; Wise = S09; §988(e)(2) = S10; FBAR/8938 = S11; gifts = S12;
  FTC = S13; PBC 2026 No. 42 = S14).
- Irregularities found and published on `site/flagged.html` and `audit/REPO_AUDIT.md`:
  intraday BOC board move (A02), conversion-tax premise (A03), USD50,000 conflation
  (A04), §988 $200 misquote (A05), staged-emigrant conflict (A06), gift thresholds
  (A07), remittance-tax direction (A08), virtual-currency update (A09), stale PR #29
  (A10).
- Nothing is marked verified without a checked official source behind it.

## Scope limits

Source of funds, ID classification (境内/境外), tax history and destination bank are unknown
(F01) — no personalized determination is possible. This edition does not re-certify every
inherited row of editions B–I; disagreements found against this edition's verified sources
are listed in `audit/REPO_AUDIT.md`.
