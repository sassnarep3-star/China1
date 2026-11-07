# China Money

Official-source research dashboard on lawful mainland-China CNY → USD transfers for a US citizen.

**Live site:** https://sassnarep3-star.github.io/China1/

## Contents
- Executive summary and conditional route recommendation
- 18 routes, service variants and excluded workarounds, with pros/cons
- Cost/tax components with unknown personal values left blank
- US reporting requirements and published evidence limitations
- Official-source registry and verification method

No private financial records, credentials, live exchange-rate guesses or personal tax determinations are stored. Provider guidance is not legislation; editorial comparisons are labeled. Review `docs/review.html` before acting.

## Build and checks
```sh
python scripts/build.py
python scripts/verify.py
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```
No dependencies or external fonts/scripts. Generated HTML supports navigation without JavaScript; JavaScript only filters the transfer table. Edit research records in `scripts/build.py`, regenerate and run verification. Pages serves `main:/`; the supplemental site is under `/docs/`. See COORDINATION.md for deployment and PR records.

## Preserved earlier dashboard

The concurrent session’s original dashboard remains at the repository root, with its pages and assets preserved. The expanded research dashboard is at https://sassnarep3-star.github.io/China1/docs/.

---

# Verified dossier — `/dossier/`

**Read this one first.** A second, independent research edition that answers the same question with a
measured cost figure instead of an unknown, an explicit legal taxonomy for every route, and a hard rule
that no value is ever estimated.

**Live:** https://sassnarep3-star.github.io/China1/dossier/

> Research dossier, not legal, tax or investment advice. Every legal proposition is traced to a published
> instrument with a link. Every number is quoted from an official source or plainly labelled as derived
> from one. Anything that could not be confirmed is left **blank** and listed on the *Flagged for review*
> page — never estimated, never given a "typical" range.

## The finding, in one table

| Belief | Reality | Source |
|---|---|---|
| Converting CNY→USD is taxed | No such tax exists in either jurisdiction | [CN-14](https://tianjin.chinatax.gov.cn/11200000000/0300/030004/03000418/20260727143202317.shtml), [US-04](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section988&num=0&edition=prelim) |
| The conversion penalty is large | It is a bank spread of **0.42%**, measured from Bank of China's own board on 2026-11-08 | [CN-11](https://www.boc.cn/sourcedb/whpj/) |
| The blocker is tax | It is *capital-account* inconvertibility (`个人外汇管理办法` Art. 3) | [CN-01](http://m.safe.gov.cn/safe/2006/1225/5319.html) |
| The 20% figure is the danger | The danger is a **50%-of-balance** willful-FBAR penalty | [US-03](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title31-section5321&num=0&edition=prelim) |
| USD 50,000/yr is the wall | USD 50,000/**year** is the *purchase* quota for 境内个人; USD 50,000/**day** is the *remittance* threshold for FX already held | [CN-03](https://www.gov.cn/gongbao/content/2020/content_5560296.htm) |
| A US citizen is subject to the quota | Not if the bank holds a passport: 汇发[2020]14号 Art. 59 states no annual cap for a 境外个人 buying FX against lawful China-source income | [CN-03](https://www.gov.cn/gongbao/content/2020/content_5560296.htm) |

Full argument: [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md).

## Dossier contents

```
EXECUTIVE_SUMMARY.md       findings, numbers, the five routes that matter, the penalty ladder, the gaps
REQUIREMENTS.md            the brief restated as 42 testable requirements + traceability

dossier/                   the published dossier (8 pages, self-contained, no JS required)
  index.html               five findings, the decision fork, headline numbers
  channels.html            35 routes grouped by the category that governs them, pros & cons each
  costs.html               24-line decomposition of the "conversion penalty"
  taxes.html               22 tax positions + the full US reporting stack
  strategy.html            the sequenced plan and the ranked outcomes
  flagged.html             20 items: 10 gaps left blank on purpose + 10 irregularities
  sources.html             source registry, graded A/B/C, with the operative clause verbatim
  methodology.html         how verification was done, and its limits

scripts/data_sources.py    31 sources, graded, each with the operative Chinese clause quoted
scripts/data_channels.py   35 routes: cap, documents, cost, CN tax, US tax, pros, cons
scripts/data_costs.py      24 cost lines, split into unavoidable / real tax / penalty exposure
scripts/data_taxes.py      22 tax positions, China and US separated
scripts/data_flagged.py    20 flagged items
scripts/build_site.py      generator + validator + internal link and anchor checker

data/*.json                machine-readable export of every table
```

## Why this edition exists alongside the others

The root edition and `/docs/` were produced by concurrent sessions working from the same brief. This one
was produced independently and adds three things they record as unknown or do not raise:

1. **A measured spread** (0.42%) instead of "net proceeds unverified", derived from an official bank board
   with the capture timestamp stated.
2. **The capital-account taxonomy** — `移民转移` / `继承转移` under PBOC Announcement [2004] No. 16 is the
   only general-purpose exit for a whole balance, and it does not appear in the other two editions.
3. **The 境外个人 carve-out** in 汇发[2020]14号 Art. 59, which is the difference between a ten-year plan and
   a single approval.

No claim made by the other editions was overwritten or deleted. Where this edition reaches a sharper
conclusion it is because the instrument was read directly; each such case is logged in `COORDINATION.md`
under "Cross-check against the other editions".

## Rebuilding

```bash
python3 scripts/build_site.py     # regenerates dossier/ and data/
```

Pure Python 3 standard library. The generator refuses to build if any table row cites a source id that
does not exist or if two rows share an id, then writes `data/*.json`, then runs an internal link **and
anchor** check across every generated page and exits non-zero on any failure.
