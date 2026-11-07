# Moving money out of China (CNY → USD) as a US citizen

A sourced evidence pack on converting a CNY balance held in mainland China into USD with the least tax and penalty exposure. Every figure traces to an official source.

**Read the site:** https://sassnarep3-star.github.io/China1/

---

## The finding, in one paragraph

**There is no Chinese tax on converting CNY to USD — the rate is 0%**, and savings-deposit interest has been provisionally exempt from PRC individual income tax since 9 October 2008. So the cost is not a conversion tax. It is three other things: a **quota wall** of USD 50,000 per person per year; a **retail FX spread** that no official source publishes; and, for a US citizen, **US information-reporting exposure** on the account itself, which runs to USD 16,536 per report non-willfully and USD 165,353 or 50% of the balance willfully. The only route that is both fast and unlawful costs 30%–100% of the amount in fines, plus up to three years on a watch list.

Only **two** lawful routes can move an entire balance rather than a quota's worth: emigrant property transfer (requires cancelled PRC household registration, certified foreign residence and a PRC tax clearance) and inheritance transfer (requires foreign citizenship or HK/Macau residence). If neither applies to your facts, no lawful mechanism exists to move a large balance quickly — and no intermediary can lawfully change that.

---

## What is in here

| Page | Contents |
|---|---|
| [Executive summary](EXECUTIVE-SUMMARY.md) | The findings, the four cost layers, the sequencing |
| `index.html` | Landing dashboard |
| `methods.html` | **22 channels**, all columns, every row sourced |
| `lawful.html` | The 12 unrestricted and conditional channels in detail |
| `prohibited.html` | The 6 prohibited channels and why they are not cheaper |
| `penalty.html` | The "conversion penalty" decomposed into **6 layers** |
| `us-reporting.html` | FBAR, Form 8938, Form 3520 — the largest quantified exposure |
| `sources.html` | **27 sources**, each with what it supports |
| `flagged.html` | **15 flagged items** — everything not confirmable |

### Data

| File | Contents |
|---|---|
| `data/sources.json` | S01–S27: tier, URL, retrieval date, propositions supported |
| `data/methods.json` | M01–M22: limits, PRC tax, US tax, US reporting, penalty, pros, cons |
| `data/penalties.json` | 6 penalty layers, each finding with value + verbatim basis + source |
| `data/flagged.json` | F01–F15: unverified methods, open legal questions, blank-value families |

### Build

```bash
python3 build/generate.py   # regenerates the 9 pages from data/*.json
python3 build/verify.py     # 15 static checks; exit 0 = pass
```

`build/verify.py` is the enforcement mechanism, not decoration. It fails the build if any populated factual field lacks a source ID, if any external link leaves the allowlisted official domains, if any internal link or anchor is broken, or if any blank value is undisclosed. The site is generated server-side and loads no JavaScript, no fonts and no trackers, so the tables are readable and checkable as plain HTML.

---

## The verification rule

Every table row carries a link to an official source. Where no official source confirmed a value, **the cell is left blank and marked `unverified`** — it is never inferred, estimated or filled from a blog, a bank's marketing page or a law firm's summary. Two channels (QDLP, private-bank "structured repatriation programmes") are retained with every value blank because no official description could be located; four fields are marked `n/a` where the concept genuinely does not arise.

Accepted sources are PRC government and regulator publications (gov.cn, safe.gov.cn, pbc.gov.cn, chinatax.gov.cn, mof.gov.cn, customs.gov.cn, samr.gov.cn) and US government publications (irs.gov, ecfr.gov, govinfo.gov, fincen.gov, treasury.gov). Anything else is labelled secondary.

---

## Limits

This is a documented evidence pack, not tax, legal or investment advice. The decisive facts — your PRC residency status under Art. 52(2) of the FX Regulations, your US residency for each covered year, whether a capital-account route is open to you — are not in this dataset and cannot be resolved from public sources. Consult a qualified cross-border adviser before filing or transferring.

Prohibited channels are documented as prohibited, with the statutory penalty and SAFE's published enforcement cases. No operational guidance is given for any of them.
