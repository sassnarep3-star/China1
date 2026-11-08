# Edition D — The CNY→USD cost ladder (`/edition-d/`)

**Live:** https://sassnarep3-star.github.io/China1/edition-d/docs/

Fifth edition, independently built and self-contained. While the sister editions quantify and
survey the *landscape* of routes, this edition answers the operational question the brief actually
asks: **what does each lawful way of moving CNY→USD cost, at every USD 10,000 from $10,000 to
$400,000 — and exactly how is each executed step by step.**

## What is inside

| Page | Contents |
|---|---|
| `docs/index.html` | Executive dashboard — the answer in one table, findings most-important-first |
| `docs/ladder.html` | **The deliverable.** Table 0 headline amounts for 5 lawful routes; Tables A–E full 40-increment ladders; Table F US FBAR exposure per balance; Table G prohibited-route statutory penalty bands; Table H the cash permit ladder |
| `docs/methods.html` | All 20 entries (5 ladder-enabled lawful, 9 non-ladder, 6 prohibited — the latter named, sourced, **no operational guidance**), each with eligibility, documents, step-by-step, pros & cons |
| `docs/penalties.html` | China regime (Art. 39/45 bands, Art. 62 关注名单） + US regime (FBAR $16,536/$165,353-or-50%; Form 8938 $10k+$10k/30d cap $50k+) |
| `docs/repo-review.html` | REPO WORK: every edition rebuilt & verified; live probes; 2 repo-wide defects found (dead OLRC links; superseded crypto notice) |
| `docs/flagged.html` | 20 flagged items — every blank and irregularity, with the exact missing authority |
| `docs/sources.html` | 28 sources, tiers A (government/regulator) and C (bank-published) |
| `docs/methodology.html` | Measured BoC board arithmetic, formulas, limits |

Plus `EXECUTIVE_SUMMARY.md` (the markdown deliverable) and `data/*.json` (machine-readable exports
incl. the 200-row ladder).

## The one-paragraph answer

CNY→USD is not taxed away in either country; the lawful cost at $400k is **≈$0.9–1.0k**
(measured 0.2104% one-way spread + ≤¥410/remittance wire fee). The binding constraint is
**capital-account control**, the largest real exposure is **US reporting** (FBAR/8938 — up to 50%
of the balance per year willfully), and the commission-eligible "penalty" story people are sold is
the **30%–100% fine band** for the unlawful shortcuts — none of which this edition enables.
Whether you are 境内个人 (USD 50,000/yr facilitation meter) or 境外个人 (foreign passport — no cap
in the rule text against documented China-source income) decides which table in
`docs/ladder.html` you use.

## Build and verify

```bash
python3 edition-d/build/generate.py   # regenerates docs/ + data/ and self-checks
python3 edition-d/build/verify.py     # 20 independent checks; exit 0 = pass
```

Pure Python 3 stdlib. The generator refuses to emit a page if any internal link breaks; the
verifier recomputes the spread, wire fees and headline totals from the captured board rather
than trusting the generator. No JavaScript required; tables are wrapped in horizontal-scroll
containers for mobile.

## Method in one line

Board spot-sell 669.29 vs mid 667.885 ⇒ 0.2104% one-way spread (bid–ask 0.4206%), captured from
Bank of China's published board 2026-11-09 05:30 Beijing time; wire = 1‰ capped ¥260 + ¥150 per
remittance (BoC 2014 counter table, bank-published tier C — 2026 online discount unconfirmed,
flag F-D02); everything else blank-and-flagged per repo rules — **no value is estimated**.
