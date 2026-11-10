# Repository audit — session arena-fface148 (2026-11-10)

Scope: line-by-line review of repository claims against 21 official sources fetched and read 2026-11-10 (register: `edition-j/site/sources.html`, 21 entries). Prior editions' outputs were preserved; this audit covers new Edition J plus spot checks of prior portal claims.

## What was checked

1. `README.md` / `EXECUTIVE_SUMMARY.md` — headline numbers traced to BOC tariff + board snapshot.
2. `edition-j/data/model.json` — cost model inputs vs S06/S07; tariff 0.1% min ¥50 max ¥260 + ¥150 cable verified against BOC page; board snapshot 666.22/669.03 per ¥100 at 2026-11-10 07:32:39 verified against BOC whpj.
3. `edition-j/data/methods.json` — 21 methods (15 lawful/conditional + 6 prohibited) each with ≥2 sources, pros/cons, steps, category, docs. Prohibited methods have no steps/cost ladder.
4. `edition-j/data/taxes.json` — 14 tax findings mapped to IRS/China tax law, each with source.
5. `edition-j/data/flags.json` — 18 flags covering unknown personal facts, board snapshot caveat, receiving/intermediary/tax blanks, stale-edition conflicts, Wise quote-time, tariff variation, institutional pricing, doc costs, conversion column, 3520, all-in blank.
6. `integration/` portal — 7 pages, 142 sourced rows, 43 method links verified via `python3 integration/verify.py PASS`.
7. Open PRs — PR #29 is open (stale draft from 2026-11-10 01:16, edition-i proposal); its content already merged via PR #33, so it is superseded. No other open PR blocks this edition.

## Findings

| # | Finding | Status | Evidence |
|---|---|---|---|
| A01 | README "four numbers" ($932/$83) from Edition D embed assumed $15 Chase fee + 2026-11-09 board. Scenario arithmetic, not a quote. This edition leaves receiving fees blank (F03). | needs review | README.md; edition-d/data/parameters.json |
| A02 | One-way margin 0.2104% (2026-11-10 board) vs 0.2103% (2026-11-09) — same formula, boards differ by 0.0001pp. No conflict. | verified-consistent | S07 both snapshots |
| A03 | Implementing Rules Art.39 fines repealed by Huifa[2023]No.8 — correctly noted in edition-c/s02 endnote. Flag F10 preserves. | verified | S02 endnote |
| A04 | 2004 staged remittance (S04 Art.6) vs 2014 S03 §VI(2) removal — conflict re-confirmed, published as F09. | needs review | S03, S04 |
| A05 | Root portal previously omitted edition-h; now resolved via integration/build.py consolidation (PR#30). Edition J adds additive link without altering history. | resolved | integration/build.py |
| A06 | Open PR #29 stale (>60min) — subject superseded by main. Will be closed with note at integration. | handoff noted | gh pr list |
| A07 | Edition D tax brackets 2026 $16,100 deduction — not refetched in this pass; figures not re-certified. | unverified (not reused) | edition-d/data/parameters.json |
| A08 | Edition C enforcement cases not re-fetched; directionally consistent but not re-certified. | unverified (not reused) | edition-c/data/penalties.json |
| A09 | Wise limits ¥300k/¥50k match provider help page 2026-11-10 (S17) — verified, timestamped. | verified | S17 |
| A10 | PBOC 2021 crypto notice (S18) repealed by S21 Yin Fa[2026]No.42 — correctly flagged F18. | verified | S18 vs S21 |
| A11 | uscode.house.gov outage — §988 verified from GPO 2024 edition (S14), amendment notes 1997 unchanged. | caveat F11 | S14 |
| A12 | No wholesale re-certification of editions B–H rows beyond spot checks; retained via preserved verifiers. | scope limit | COORDINATION.md |

## Verification performed

- 21 sources fetched/read 2026-11-10: SAFE ×5, PBOC ×2, Shanghai gov ×1, China tax ×1, BOC ×2, SAFE Shanghai ×1, IRS ×6, GPO ×1, Wise ×1, PBOC 2026 ×1, Customs ×1.
- `python3 edition-j/build/build.py` → 8 pages; `python3 edition-j/build/verify.py` → 1,936 checks, 0 errors (byte-identical rebuild, independent recomputation of all priced cells, 40-target grid, blank semantics, prohibited disposition, link/anchor resolution, external URL allowlist).
- Cross-checks: `python3 integration/verify.py` PASS, `python3 edition-i/build/verify.py` PASS, `python3 edition-d/build/verify.py` PASS.

## Not claimed

- No personal eligibility/tax determination (F01).
- No executable FX quote (F02).
- No guarantee external URLs remain reachable after publication.
- No re-certification of editions B–H beyond their own verifiers (A12).
