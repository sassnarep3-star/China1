# Repository audit — session arena-e90d36c3 (2026-11-10)

Scope: line-by-line review of the repository's research claims against the 20 official
sources this session fetched and read (register: `../site/sources.html`). Prior editions'
internal build systems were reviewed at data/claim level, not re-executed except where
noted. Every irregularity below is published on the site's Flagged for Review page or
cross-referenced there. Nothing here blocks the merge.

## What was checked

1. `README.md` (414 lines) — every headline numeric claim traced to its edition of origin.
2. `integration/build.py` + generated root `index.html` — portal claims against sources.
3. `edition-c/data/penalties.json`, `edition-c/data/flags.json` — penalty citations vs S02/S08.
4. `edition-d/data/parameters.json` — cost model inputs vs S06/S07; assumption labeling.
5. `COORDINATION.md` (894 lines) — publication history consistency (PRs #1–#27).
6. Open pull requests #12, #14, #25 — staleness and overlap with merged work.
7. Editions B, E, F, G, H data files — spot-checked headline claims only (see limits).

## Findings

| # | Finding | Status | Evidence |
|---|---|---|---|
| A01 | README.md "four numbers" (Edition D) presents exact all-in totals ($932.72 at $400K, $83.45 at $10K) built from a 2026-11-09 board stamp **plus an assumed $15 Chase receiving fee** ("named example only" in `edition-d/data/parameters.json`). The README headline carries no caveat. This edition leaves receiving fees blank (F03). | needs review | README.md; edition-d/data/parameters.json `receiving_bank` |
| A02 | Edition D's one-way margin 0.2103% (2026-11-09 board) is methodologically identical to this edition's 0.2104% (2026-11-10 board, S07). No conflict — the formula (sell−mid)/mid is confirmed from the same BOC board type. | verified-consistent | edition-d/data/parameters.json `fx.derivation`; S07 |
| A03 | Implementing-Rules Art. 39 fines (¥30,000/¥1,000): **repealed** by Huifa [2023] No. 8 (S02 endnote). Edition C correctly states the repeal ("that article was abolished by Huifa [2023] No.8 Annex 3"). Any residual citation of Art. 39 as current elsewhere would be wrong; none found beyond edition-c's correct treatment. | verified-consistent | edition-c/data/penalties.json; S02 |
| A04 | 2004 vs 2014 property-transfer conflict: S04 Art. 6 staged remittance (50%/1yr/2yr) vs S03 §VI(2) removal of forced staging. Prior boards already flagged this; this edition re-confirms the conflict from both texts and publishes F09. | needs review | S03, S04 |
| A05 | Root portal (`integration/build.py` archive list) omits `edition-h/site/` although Edition H is merged and live. This is the logged cross-session request from arena-c2310264. Resolved in this session's integration commit (link added together with Edition I). | resolved by this session | integration/build.py; COORDINATION.md log |
| A06 | Open PRs #12, #14 (Edition D records, 2026-11-08) and #25 (competing Edition H draft `edition-h/docs/`, 2026-11-09) belong to sessions with no commits for >60 minutes. Their subject matter is represented in `main` (Edition D in-tree; Edition H merged via PR #26 as `edition-h/site/`). PR #25 also edits `edition-d/build/build.py`, outside its own scope. | needs review (handoff noted; closed as superseded at integration) | gh pr list; COORDINATION.md |
| A07 | Edition D models 2026 U.S. tax brackets ($16,100 standard deduction etc., source "US-04"). Not re-fetched in this session's verification pass; figures not re-certified. | unverified (not reused) | edition-d/data/parameters.json `us_income_tax_2026_single` |
| A08 | Edition C's published enforcement cases (e.g. RMB 1,000,000 confiscation for 303-quota structuring) were not re-fetched from SAFE/press originals in this pass. Credible and directionally consistent with S08's warnings, but not re-certified here. | unverified (not reused) | edition-c/data/penalties.json `published_cases` |
| A09 | Wise limits cited in this edition (¥300,000/¥50,000 per transfer, tax-record eligibility) match the provider help page fetched 2026-11-10 (S17). Provider terms change; timestamped. | verified 2026-11-10 | S17 |
| A10 | PBOC 2021 crypto notice URL in this edition verified live (S18). Editions that describe crypto as "risky" rather than "illegal financial activity" understate the official wording ("一律严格禁止…非法金融活动"). | verified; wording strengthened in edition-i | S18 |
| A11 | uscode.house.gov displayed a temporary-format outage on 2026-11-10; §988 text verified from GPO govinfo.gov 2003 edition instead (S14), whose amendment notes show subsection (e) unchanged since 1997. | caveat published (F11) | S14 |
| A12 | `docs/`, `dossier/`, `edition-b`, `edition-e`, `edition-f`, `edition-g`, `edition-h` contain large claim sets (e.g. edition-g: 43 candidates × 40 targets = 1,720 rows). A full row-level re-certification of all inherited claims is beyond this session's pass; those editions retain their own verification logs. This audit confirms only the claims listed above. | scope limit, disclosed | COORDINATION.md histories |

## Verification performed by this session

- 20 sources fetched and read 2026-11-10 (SAFE ×5, PBOC ×2, China STA ×1, China Customs ×1,
  IRS ×6, GPO ×1, Shanghai gov ×1, BOC ×2, Wise ×1).
- `python3 edition-i/build/build.py` → 8 pages; `python3 edition-i/build/verify.py` →
  1,858 checks, 0 errors (independent arithmetic recomputation of all 240 priced cells,
  40 targets × 10 ladders, link/anchor resolution, external-URL allowlist, blank-cell
  semantics, prohibited-route step prohibition, byte-identical rebuild).
- Cross-checks against prior editions as listed above.

## Not claimed

- No personal eligibility determination (F01).
- No executable FX quote (F02).
- No claim that external URLs remain permanently reachable.
- No wholesale re-certification of editions B–H (A12).
