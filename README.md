# China Money

**Live site:** https://sassnarep3-star.github.io/China1/ — the landing page is now a portal; the dashboard is Edition D.

---

## Edition D — the costed dashboard (current)

**Open it:** https://sassnarep3-star.github.io/China1/edition-d/

The first four editions in this repository established the legal taxonomy and, correctly, refused to invent
bank fees. That left the practical question unanswered: how much does each route cost, at each size, and in
what order do the steps happen? Edition D answers it with published tariffs instead of estimates.

### The four numbers

| Question | Answer | Basis |
|---|---|---|
| Is converting CNY to USD taxed? | No, in either jurisdiction | CN-05 Art. 2 (nine income categories, exchange is not one); US-01 §988(e)(2) |
| What does one lawful conversion cost? | **0.2104%** FX margin, plus fees | Derived from BOC's USD board: sell 669.29, buy 666.48, midpoint 667.885 |
| What does it cost all-in at USD 400,000? | **$932.72 (0.233%)** | BOC tariff + full-amount surcharge + named US receiving fee |
| What does it cost all-in at USD 10,000? | **$83.45 (0.834%)** | Same machinery; the capped commission and cable fee dominate |

The frequently quoted **0.42%** is the round-trip spread — the cost of converting twice. Edition D uses the
one-way margin for a single conversion and says so. See finding **R01** on the Edition D repo-review page.

### What is on the site

| Page | Contents |
|---|---|
| `/edition-d/` | Dashboard: six findings, headline numbers, cost matrix |
| `pages/summary.html` | Executive summary, ten findings, the recommendation |
| `pages/methods.html` | 16 routes: rule, cap, documents, pros and cons, lawfulness |
| `pages/costs.html` | Every costed route side by side, plus the formula and its inputs |
| `pages/costs-*.html` | Eight tables, each with 40 rows, USD 10,000 to USD 400,000 in 10,000 steps |
| `pages/steps.html` | Step-by-step procedure per route, with the provision to cite |
| `pages/tax.html` | China IIT, §988, the FBAR ladder, the penalty ranges |
| `pages/reporting.html` | FBAR, 8938, 3520 and the currency report |
| `pages/sources.html` | 17 sources, graded A/B, with what each supports and what was retrieved |
| `pages/flagged.html` | 25 items left blank on purpose |
| `pages/repo-review.html` | Line-by-line audit of the four earlier editions (15 findings) |
| `pages/methodology.html` | Rules enforced in code, the arithmetic, and the limits |

### Build and verify

```sh
python3 edition-d/build/build.py    # writes edition-d/docs/ and the root index.html
python3 edition-d/build/verify.py   # 19 checks; recomputes every cell from the parameters
```

`verify.py` does not trust the HTML. It recomputes all 320 cost cells from `edition-d/data/parameters.json`,
checks that every table row carries a source, that every blank is disclosed, that every internal link and
anchor resolves, that every external host is on the official allowlist, that no page is orphaned, and that a
rebuild is byte-identical.

### What Edition D does not do

It does not tell you which route applies to your balance, because the source of the funds is unknown (F03).
It does not price notarisation, travel or card conversion fees, because no official price exists (F14, F18,
F20). It does not model a §988 gain, because the basis is unknown (F11). And it does not touch the earlier
editions: they are preserved unchanged and linked from the portal.

---

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

## Edition E — independent blank-discipline verification layer

Added by session `arena-0614c102` after a concurrent session published Edition D. Edition E does **not** overwrite Edition D. It preserves the earlier outputs and adjudicates selected load-bearing claims against a new claim-level source register.

| Path | Contents |
|---|---|
| `edition-e/site/` | 15 generated pages: dashboard, summary, costs, tax, penalties, sources, flagged, audit, method, requirements and five category pages |
| `edition-e/data/` | 40 sources, 32 methods, 14 tax rows, 4 penalty rows, 18 flags, 10 audit findings, parameters and summary |
| `edition-e/site/data/grids.csv` | 1,280 rows: every method × USD 10,000–400,000 in USD 10,000 steps |
| `edition-e/research/` | retrieval log, source notes and arithmetic worked checks |
| `edition-e/EXECUTIVE_SUMMARY.md` | Markdown executive summary |
| `edition-e/audit.md` | inherited-edition audit, including the concurrently published Edition D |

### Build and verify

```bash
python3 edition-e/build/build.py
python3 edition-e/build/verify.py
```

The verifier recomputes all 1,280 grid rows, checks citations/hosts/kinds, blank discipline, internal links/fragments, CSV row count, accessibility basics and byte-identical rebuilds. A separate workflow is `.github/workflows/edition-e.yml`.

### Editorial rule

Personal tax, executable FX quotes, receiving-bank charges and unavailable provider prices are **blank**. Provider tariffs are labelled `provider_primary`, not government law. Computed cells are conditional arithmetic, not all-in quotes. The root portal remains generated by Edition D to preserve that edition’s reproducibility; Edition E is reachable directly at `edition-e/site/index.html` and links back to the portal.

### Live Edition E

- Dashboard: https://sassnarep3-star.github.io/China1/edition-e/site/index.html
- PR #15 merged into `main` at `7ce3a7f`; GitHub Pages build reported `built`.

---

## Edition G — verified cost dashboard (2026-11-08)

`edition-g/` is an additive, self-contained edition by session `arena-e58c83ae`.
It was originally built as `edition-d/` but relocated to `edition-g/` after a
concurrent session merged a different Edition D (PR #13) plus Editions E and F.
No merged edition was overwritten. 43 distinct candidates (legal entitlements,
execution rails, business routes, alternatives and rejected candidates counted
separately), 1,720 cost rows covering every $10,000 increment from $10,000 to
$400,000, 52 registered sources, 47 review flags, and a line-by-line repository
audit. Unknown values are blank and flagged, never zero.

- Site: `edition-g/docs/index.html`
- Build/verify: `python3 edition-g/build/build.py && python3 edition-g/build/verify.py`
- CI: `.github/workflows/edition-g-verify.yml`

---

## Final integration (2026-11-09, session `arena-cf89967d`)

All parallel editions are merged and live. The root portal (`index.html`) now links **every** published
dashboard — original root edition, supplemental `/docs/`, `/dossier/`, Editions B, C, D, E, F and G —
closing the open cross-session requests from the Edition F and Edition G boards. The portal is generated by
`edition-d/build/build.py` (edit the template, not the output); `edition-d/build/verify.py` passes with the
new links.

Re-verification of the combined site on 2026-11-09: every edition builder/verifier passes; an independent
whole-repository crawl of 151 HTML files found 13,043 internal references with **0 broken**; six load-bearing
official sources were re-fetched and confirmed (gov.cn 汇发〔2020〕14号 Arts. 54–65, IRS FBAR page, 26 U.S.C. §988,
31 U.S.C. §5321). External-link liveness is not guaranteed; unverified personal values remain blank and are
published on each edition's Flagged-for-Review page. Details: `COORDINATION.md`, session board `arena-cf89967d`.

**Not legal, tax or financial advice.** Consult a China-qualified FX/tax adviser and a U.S. international tax
professional before moving funds; the decisive facts (source of funds, residency, documents) are case-specific.
- PR [#21](https://github.com/sassnarep3-star/China1/pull/21) merged 2026-11-09 (`c35e131`); GitHub Pages reported `built` at that exact commit; live site verified with the new archive links.

---

## Edition H — current-source review (2026-11-09)

`edition-h/` is an additive, self-contained edition by session `arena-c2310264`; earlier editions and the shared portal are unchanged. It publishes 43 candidates, 1,720 amount-specific cost rows, 53 registered sources, 52 review flags, China/U.S. tax layers and step-by-step mechanics. Published sender charges are partial estimates only; unknown FX, downstream, document, personal-tax and all-in values remain blank and unverified.

- Live dashboard: <https://sassnarep3-star.github.io/China1/edition-h/site/>
- Rebuild/verify: `python3 edition-h/build/audit.py && python3 edition-h/build/build.py && python3 edition-h/build/verify.py`
- Publication: PR [#26](https://github.com/sassnarep3-star/China1/pull/26), merge `430b0d9`; Pages deployment succeeded and public content was retrieved.

---

# Edition I — verified refresh (2026-11-10)

**Live:** https://sassnarep3-star.github.io/China1/edition-i/site/

Session `arena-e90d36c3`. Independent research pass with 21 official sources fetched and
read the same day (SAFE, PBOC, China STA, China Customs, IRS, GPO govinfo, Shanghai
government, Bank of China, Wise). Every displayed row links the official page it was
checked against; unconfirmable values are blank + flagged, never inferred.

- Executive summary ranked by source of funds: `edition-i/site/executive-summary.html`
- 21 methods (15 lawful/conditional + 6 prohibited) with pros/cons: `edition-i/site/methods.html`
- Step-by-step procedures: `edition-i/site/steps.html`
- 10 cost ladders × 40 targets ($10,000–$400,000 step $10,000): `edition-i/site/costs.html`
- Tax and penalty breakdown (CN IIT, §988 $200 exclusion, FBAR, 8938, FTC): `edition-i/site/taxes.html`
- 21-source register with retrieval notes: `edition-i/site/sources.html`
- 18 flags incl. 2004/2014 property-transfer conflict and repealed Art. 39 fines: `edition-i/site/flagged.html`
- Repo line-by-line audit of inherited claims: `edition-i/audit/REPO_AUDIT.md`

Model (S06/S07, BOC board 2026-11-10 07:32:39): one-way FX margin 0.2104%; handling 0.1%
min ¥50 max ¥260 + ¥150 cable. Verified components only: $10,000 wire = $53.47;
$400,000 single wire = $903.07 (0.2258%); $400,000 in 8 × $50,000 quota wires = $1,332.05
(0.3330%). Receiving-bank, intermediary and tax cells stay blank + UNVERIFIED.

Build/verify: `python3 edition-i/build/build.py && python3 edition-i/build/verify.py`
(1,858 checks: independent arithmetic recomputation, source allowlist, link/anchor
resolution, blank-cell semantics, prohibited-route step prohibition, deterministic rebuild).
