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

---

# Edition B — converter & penalty analysis (`/edition-b/`)

A **second, independently sourced research edition**, retained alongside the two above rather than replacing them. It reaches the same core conclusion by a different research path and adds a machine-enforced verification harness.

**Read it:** https://sassnarep3-star.github.io/China1/edition-b/

### What is different about this edition

| | `dossier/` | `edition-b/` |
|---|---|---|
| Route count | 35 | **22**, grouped into lawful / conditional / **non-transfer** / prohibited |
| Sources | 31 | **27**, each with the propositions it actually supports recorded |
| Verification | build-time id validation | **`verify.py`, 15 hard checks, exit 0** |
| Distinctive content | 0.42% measured spread; capital-account taxonomy | Penalty decomposed into **6 layers**; US reporting quantified as the dominant exposure |

### The finding

**No PRC tax arises on the conversion — 0%.** Savings interest has been exempt since 2008-10-09 for both RMB and FX deposits. The cost is a **quota wall** of USD 50,000/person/year, a retail spread, and — for a US citizen — **US information-reporting exposure**: USD 16,536 per report non-willfully, USD 165,353 or 50% of the balance willfully. The only fast unlawful route costs 30%–100% of the amount plus up to three years on a watch list.

Only two lawful routes move a whole balance: **emigrant transfer** (needs cancelled PRC household registration + certified foreign residence + PRC tax clearance, staged over ~2 years) and **inheritance transfer** (needs foreign citizenship or HK/Macau residence).

### Contents

| Page | Contents |
|---|---|
| `edition-b/index.html` | Landing dashboard |
| `edition-b/executive-summary.html` | Findings, four cost layers, sequencing |
| `edition-b/methods.html` | **22 channels**, every row sourced |
| `edition-b/lawful.html` | The 12 unrestricted and conditional channels |
| `edition-b/prohibited.html` | The 6 prohibited channels |
| `edition-b/penalty.html` | The penalty in **6 layers** |
| `edition-b/us-reporting.html` | FBAR, 8938, 3520 — the largest quantified exposure |
| `edition-b/sources.html` | **27 sources** with what each supports |
| `edition-b/flagged.html` | **15 flagged items** |

### Build and verify

```bash
python3 edition-b/build/generate.py   # regenerates the 9 pages from edition-b/data/*.json
python3 edition-b/build/verify.py     # 15 static checks; exit 0 = pass
```

`verify.py` is the enforcement mechanism. It hard-fails if any populated factual field lacks a source ID, if any external link leaves the allowlisted official domains, if any internal link or anchor is broken, or if any blank value is undisclosed. It caught three real defects during authoring, which were fixed rather than suppressed.

### The verification rule

Where no official source confirmed a value, the cell is **left blank and marked `unverified`** — never inferred. Two channels (QDLP, private-bank "structured repatriation") are published with every value blank because no official description could be located. Four fields carry `n/a` where the concept genuinely does not arise.

Accepted sources: PRC government and regulator publications (gov.cn, safe.gov.cn, pbc.gov.cn, chinatax.gov.cn, mof.gov.cn, customs.gov.cn, samr.gov.cn) and US government publications (irs.gov, ecfr.gov, govinfo.gov, fincen.gov, treasury.gov). Anything else is labelled secondary.

### Not advice

The decisive facts — PRC residency under Art. 52(2) of the FX Regulations, US residency per covered year, availability of a capital-account route — are not in this dataset. Prohibited channels are documented **as prohibited**, with the statutory penalty and SAFE's published enforcement cases; **no operational guidance is given** for any of them.

---

# Edition C — every channel, its cost and its penalty exposure (`/edition-c/`)

A **third, independently sourced research edition**, retained alongside the three above rather than
replacing any of them. Self-contained: it shares no file with the root edition, `dossier/` or
`edition-b/`, and can be built, verified and read on its own.

**Read it:** https://sassnarep3-star.github.io/China1/edition-c/docs/

### What is different about this edition

| | `dossier/` | `edition-b/` | `edition-c/` |
|---|---|---|---|
| Channels | 35 | 22 | **33**, in 6 categories including 5 documented as prohibited |
| Sources | 31 | 27 | **39**, each listing the specific provisions relied on |
| Enforcement cases quantified | — | referenced | **23**, all from SAFE's own case circulars |
| Flagged items | 20 | 15 | **19**, each with a stated route to resolution |
| Verification | build-time id validation | `verify.py`, 15 checks | **`linkcheck.py`, 13 checks, 0 failures 0 warnings** |
| Distinctive content | 0.42% measured spread; capital-account taxonomy | 6-layer penalty; US reporting as dominant exposure | **Live Treasury FATCA register finding**; independently recomputed fine percentages; the 2025 SAFE reform |

### The finding

**China levies no tax on the act of converting CNY into USD.** No instrument reviewed imposes a tax,
levy or conversion charge on the exchange itself. Chinese tax attaches to the event that created the
money and is owed whether or not the funds ever leave China. What conversion attracts instead is
foreign exchange control — documentary, not fiscal — plus a commercial spread, plus penalty exposure
only if the route chosen is unlawful.

Art.9 of the Measures applies the USD 50,000 annual total-amount limit to only two things: individual
FX settlement, and FX purchase by a **domestic individual**. Art.37(2) makes a foreign citizen
presenting a passport an **overseas individual**, and Art.13 lets one convert legitimate
current-account RMB income earned in China **with no stated annual ceiling**, against identity
documents and evidence including tax vouchers.

### Unique to this edition

1. **The live US Treasury FATCA register.** China is recorded as `Agreement in Substance`, Model 1,
   treated as in effect from 30 June 2014, **with no signed agreement**. There is therefore no executed
   government-to-government pipeline under which Chinese banks report US account holders automatically
   to the IRS, and the compliance burden sits entirely on the taxpayer's own filings.
2. **Fine percentages recomputed independently.** Where both official figures share a currency, SAFE's
   published fines for underground-bank dealings compute to **7.00%, 8.00%, 8.00%, 12.01%, 12.02% and
   12.03%** of the amount moved. Where they do not, the cell is left blank rather than converted at an
   assumed rate. `linkcheck.py` recomputes every stated percentage and fails on a mismatch.
3. **The 2025 SAFE reform.** The operational guidelines annexed to Huifa [2025] No.43, retrieved from
   `safe.gov.cn`, give the current bank-side checklist for an overseas individual converting and
   remitting proceeds from selling domestic commercial property — and cap the remittance at the
   transfer price less the taxes and fees of that transfer.
4. **Three live conflicts between official sources** (F02, F09, F17), each of which means the same
   transaction can be processed differently at different bank counters.

### Contents

| Path | Contents |
|---|---|
| `edition-c/docs/` | 17 generated pages: overview, executive summary, all 33 routes, 6 category pages, China tax, US tax, treaty, penalty breakdown, flagged, sources, repo review, methodology |
| `edition-c/data/sources.json` | 39 entries with issuer, document number, date, URL on the issuing body's own domain, and the provisions relied on |
| `edition-c/data/routes.json` | 33 channels with legal basis, limit, tax cost, documentation, pros, cons, feasibility, risk |
| `edition-c/data/tax.json` | China rates, US rates, and the 1984 treaty article by article |
| `edition-c/data/penalties.json` | 6 cost layers, statutory penalty scales, 23 published cases |
| `edition-c/data/flags.json` | 19 unresolved items with a route to resolution for each |
| `edition-c/data/repo-review.json` | Repository audit, 6 irregularities, the verification standard |
| `edition-c/COORDINATION.md` | This edition's task board, source record and handoff notes |
| `edition-c/README.md` | Full description of this edition |

### Build and verify

```bash
python3 edition-c/build/build.py       # regenerates the 17 pages from edition-c/data/*.json
python3 edition-c/build/linkcheck.py   # 13 checks; exit 0 = pass
```

Both derive their root from `__file__`, so they work from any working directory. Standard library only.
Output is deterministic: rebuilding from unchanged data produces byte-identical files, and
`linkcheck.py --rewrite-check` records digests so the next run can prove it.

`linkcheck.py` caught two real defects during development — a route marked unverified while stating a
sourced limit, and a dashboard figure disagreeing with the source register. Both were fixed rather than
suppressed. It also refuses to render a blank value without an `unverified` badge beside it, so a gap
cannot be silently hidden.

### Cross-check against the other editions

No claim made by another edition was overwritten or deleted. Two points of comparison are worth
recording:

- **The conversion spread.** `dossier/` measures 0.42% from Bank of China's published board with a
  capture timestamp. This edition leaves the spread **blank** as flag **F01**, because no *regulatory*
  instrument fixes a retail spread and this session did not capture a bank board itself. The two are not
  in conflict: one is a measurement, the other is a refusal to state a regulatory value that does not
  exist. Readers wanting a number should take `dossier/`'s measurement and re-capture it on the
  transaction date.
- **Which routes move a whole balance.** `edition-b/` concludes that only emigrant transfer and
  inheritance transfer do. This edition reaches the same conclusion for *individual* channels (flag
  **F10** records the gap) and adds a third: **Art.22 paragraph 3 of the Regulation on Foreign Exchange
  Administration**, under which a lawfully terminated foreign-invested enterprise may, after liquidation
  and tax payment, have the RMB belonging to its foreign investors converted and remitted. That is an
  express statutory entitlement in a State Council regulation and is route **R18** here.

### Not advice

Research published with its sources. Not legal, tax or investment advice. Chinese FX practice varies by
branch and by officer, three official instruments conflict with each other as recorded above, and both
the Chinese and the US positions depend on facts about the origin of the funds that are not known here.
Prohibited channels are documented **as prohibited**, with the statutory penalty scale and SAFE's
published enforcement cases; no operational guidance is given for any of them.

---

# Edition D — costed at every $10,000 step

**Live:** https://sassnarep3-star.github.io/China1/edition-d/docs/ · **Summary:** [`edition-d/README.md`](edition-d/README.md)

A fifth, self-contained edition under `edition-d/` that answers the brief where the earlier editions
stopped short: a **dollar cost at every $10,000 step from $10,000 to $400,000** for every route that has
a price, a **step-by-step sequence** for each route, and a **verifier that re-derives every published
number** from the model before the site can be committed.

| Headline | Value | Basis |
|---|---|---|
| Cost of the best lawful route on $400,000 | **$940.95 (0.235%)** | Bank spread derived from the Bank of China board plus disclosed fee assumptions, stress-tested |
| Cost of the same money moved as 8 quota tranches | $1,398.60 over 8 years | USD 50,000 per person per year |
| Chinese tax on the conversion itself | **None found** | IIT Law enumerates nine income categories; conversion is not one |
| US tax on repatriating your own principal | **None** | §988(e)(2) personal transaction, unless the FX gain exceeds $200 |
| The exposure that actually bites | Willful FBAR: greater of $100,000 or 50% of the balance | IRS |
| Statutory fine band for an unlawful route | 0–30% of the amount; 30%–100% if serious | Foreign Exchange Regulation Arts. 39–45 |

Nineteen registered sources, each with the scope of what was inspected; twelve published flags,
including a genuine definitional conflict over who counts as a "domestic individual" (U09). The build
and the 36-check verifier run in CI on every pull request.
