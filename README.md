# China1 — getting RMB out of China lawfully, as a US citizen

**Live site:** https://sassnarep3-star.github.io/China1/

A source-verified research record answering one question: *a US citizen has RMB stuck in a mainland-China bank account — what are the lawful ways to turn it into USD, and what does each actually cost in tax and penalties?*

Every number in this project traces to an official instrument. Where no official source fixes a value, the value is **left blank and flagged**, never estimated.

---

## The finding

**There is no Chinese tax on converting RMB to USD.** No such provision appears in the FX Regulations, PBoC Order [2006] No.3, the 2020 Current Account Guidelines, or the Individual Income Tax Law.

What actually blocks the money is a classification fact almost every guide gets wrong:

> A US citizen is an **境外个人** (*overseas individual*) under PBoC Order [2006] No.3 Art.37 — nationality decides, not residence. Under Art.54/Art.59 of 汇发〔2020〕14号, the USD 50,000 annual quota applies to *domestic* individuals' purchases. An overseas individual gets **no purchase quota at all** unless they hold a Chinese Foreigner's Permanent Residence ID.
>
> **The quota is gone — but so is the ceiling.** Once the money is documented, the matching route has no cap.

And the largest real cost is somewhere else entirely:

| | |
|---|---|
| Chinese tax on converting | **0%** |
| Chinese IIT on a property gain | **20%** of the gain |
| US penalty for *not filing an FBAR* | **$16,536** non-willful / **$165,353** willful, per violation per year |

The FBAR penalty accrues **whether or not you ever convert a single yuan**. On a $100,000 balance, the spread costs about $1,000; three unreported years cost up to ~$49,608. **Fix reporting first.**

---

## What's here

```
index.html            Dashboard: the answer, the KPIs, the route at a glance
plan.html             The order to do things in, plus an evidence checklist
channels.html         21 channels — including the ones that don't work
costs.html            The "conversion penalty" decomposed into 18 components
china-rules.html      The Chinese framework, article by article
us-tax.html           FinCEN 114 (FBAR), Form 8938, IRC §988, the streamlined procedures
prohibited.html       Six routes that cost up to 100% of the amount
flagged.html          7 unconfirmed claims + 7 irregularities in public sources
sources.html          30 sources, each with a verification status
about.html            Method, scope limits, and the corrections made mid-research

data/                 The single source of truth — 6 JSON files, every row and citation
research/             Executive summary, repo review, line-by-line verification log
scripts/build_site.py Generates assets/data.js and validates the whole project
scripts/render_check.js  Headless render check (needs `npm i jsdom`)
COORDINATION.md       Shared task board and session log
```

The site is plain static HTML with **no runtime network dependency** — `assets/data.js` is generated from `data/*.json`, so it works from `file://` as well as GitHub Pages.

## Building

```bash
python3 scripts/build_site.py      # regenerate assets/data.js + run all checks
```

The build **fails** if any cited source ID does not resolve, if any internal link points at a missing file, if a cost row marked *verified* cites no source, or if a cost row marked *unverified* carries a value. Fabrication is a build error, not a style preference.

For the headless render check:

```bash
python3 -m http.server 8080 --bind 0.0.0.0 &
cd scripts && npm i jsdom && node render_check.js
```

## Verification states

Shown explicitly, because "I read it" and "a search result quoted it" are different claims:

- **retrieved** (11) — page fetched and the cited text read directly.
- **excerpt** (12) — official-domain page confirmed with the operative text quoted, but not fetched end-to-end.
- **unverified** (7) — no official page confirmed. Never used to fill a value; listed on the Flagged page.

**Live HTTP link checking was not possible from the build environment** — outbound access to the cited government hosts is blocked, so `curl` returns `000` for all of them. Link validity rests on the fetches performed during research, not on an automated checker. That limitation is stated rather than hidden.

## Two corrections made during research

1. **银发〔2021〕237号** — the Chinese crypto prohibition everyone cites — was **repealed on 2026-02-06** by **银发〔2026〕42号**. Most search results still present the 2021 notice as current law.
2. A widely used legal database labels **汇发〔2020〕14号** as "wholly repealed". It isn't. 汇发〔2025〕13号 repealed five unrelated documents; SAFE's own pages still apply the 2020 Guidelines.

Both are logged as R01 and R02 with sources.

## Not advice

This is a research record, not legal, tax or investment advice, and it creates no adviser relationship. Every route must be executed by a bank against documents you actually hold, and banks may refuse any transaction they cannot verify. If anything here conflicts with the instrument it cites, **the instrument prevails**.
