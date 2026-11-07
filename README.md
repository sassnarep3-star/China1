# China1 — getting CNY out of China into USD, with the smallest lawful penalty

A verified research dossier answering one question: **a US citizen has CNY sitting in a mainland Chinese bank account and wants USD in the US with the least tax penalty possible. What are the options, what do they really cost, and what does the law actually say?**

Live site: **<https://sassnarep3-star.github.io/China1/>**

> Research dossier, not legal, tax or investment advice. Every legal proposition is traced to a published instrument with a link. Every number is either quoted from an official source or plainly labelled as derived from one. Anything that could not be confirmed is left **blank** and listed on the *Flagged for review* page.

## The finding, in short

| Belief | Reality | Source |
|---|---|---|
| Converting CNY→USD is taxed | No such tax exists in either jurisdiction | [CN-14](https://tianjin.chinatax.gov.cn/11200000000/0300/030004/03000418/20260727143202317.shtml), [US-04](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section988&num=0&edition=prelim) |
| The conversion penalty is large | It is a bank spread of **0.42%** | [CN-11](https://www.boc.cn/sourcedb/whpj/) |
| The blocker is tax | It is *capital-account* inconvertibility | [CN-01](http://m.safe.gov.cn/safe/2006/1225/5319.html) |
| The risk is a 20% bill | The risk is a **50%-of-balance** FBAR penalty | [US-03](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title31-section5321&num=0&edition=prelim) |

Read the full argument in [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md).

## Repository map

```
EXECUTIVE_SUMMARY.md      the deliverable: findings, numbers, routes, sequence, gaps
REQUIREMENTS.md           the brief restated as 42 testable requirements + traceability
COORDINATION.md           shared task board, verification log, PR/merge record

scripts/
  data_sources.py         31 sources, graded A/B/C, with the operative clause verbatim
  data_channels.py        35 routes: cap, documents, cost, CN tax, US tax, pros, cons
  data_costs.py           24-line decomposition of the "conversion penalty"
  data_taxes.py           22 tax positions, China and US separated
  data_flagged.py         20 flagged items: 10 gaps (blank on purpose) + 10 irregularities
  build_site.py           generator + validator + internal link and anchor checker

docs/                     the published site (GitHub Pages source)
  index.html              overview: five findings, the decision fork, headline numbers
  channels.html           every route, grouped by the category that governs it
  costs.html              the penalty breakdown, line by line
  taxes.html              the tax matrix + the full US reporting stack
  strategy.html           the sequenced plan and the ranked outcomes
  flagged.html            unverified values and irregularities — review this
  sources.html            source registry with links
  methodology.html        how verification was done, and its limits

data/                     JSON exports of every table, for re-use
```

## Rebuilding the site

```bash
python3 scripts/build_site.py
```

Pure Python 3 standard library — no dependencies, no build toolchain, no CDN. The generator:

1. refuses to build if any table row cites a source id that does not exist, or if two rows share an id;
2. renders all eight pages from the same data modules the markdown deliverables describe, so the site and the documents cannot drift;
3. writes `data/*.json`;
4. runs an internal link **and anchor** check across every generated page and exits non-zero on any failure.

## Source grading

| Tier | What it is | Count |
|---|---|---|
| **A** | The instrument itself, or the issuing authority's own page — SAFE, PBOC, State Council / gov.cn, State Taxation Administration, GACC customs, CSRC, IRS, FinCEN, CBP, U.S. Code | 27 |
| **B** | An official republication of the instrument on another official domain (state gazette, state news agency) — used only where the primary page was not retrievable | 1 |
| **C** | A regulated institution publishing its own data (Bank of China rate board, CFETS benchmark) | 3 |

Nothing below tier C is used for a factual claim. Where a fact appeared only on a law-firm blog, an accountancy article or a news aggregator, it went to the *Flagged* page instead of onto a table — and several of those sources contradicted the statute, which is why none are cited.

## What is not verified

Twenty items are published rather than filled in. The five that change the answer:

- **F01** how the bank classifies the account holder (境内个人 vs 境外个人) — this single fact decides whether the USD 50,000 quota applies at all
- **F02** whether a PRC resident identity is still in use by a US citizen
- **F03** the source of the funds (salary / property / inheritance / inward remittance)
- **F04** whether prior FBAR and Form 8938 filings were made
- **F05** whether the balance is a bank deposit or a fund / investment-linked insurance product (PFIC)

See [`docs/flagged.html`](docs/flagged.html) for all twenty, with sources and the action to take.

## Scope limits

- Application to a specific person requires a **PRC-qualified lawyer** for the China side and a **US CPA or tax attorney** for the US side. Cross-border work of this kind is routinely done by a pair.
- Criminal exposure for individuals is **outside scope**. The administrative fine bands quoted are statutory ceilings, not predictions.
- 8 unlawful routes are documented with their statutory penalties. Documenting a prohibited route is not an endorsement of it; omitting them would leave the reader unable to recognise the option they are about to be offered.
- The FX spread is a **snapshot dated 2026-11-08**. The structure of the cost is stable; the number is not.
