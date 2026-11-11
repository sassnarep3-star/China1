# China money — getting CNY out of a mainland bank account and into USD

Live site: **https://sassnarep3-star.github.io/China1/**

A research guide for a US citizen holding CNY in a mainland China bank account: which routes are lawful, what each costs at every $10,000 step up to $400,000, what tax and reporting follow, and what could not be confirmed.

Priced inputs re-read **2026-11-11**: Bank of China board at 10:25:02 Beijing time (buy 666.30, sell 669.11 per USD 100), Wise re-quoted live at 02:35Z, and 16 of the 33 sources re-opened and re-read. The sources page prints the date each source was read; the per-source record and the irregularities found are in `edition-db079cfc/verification/`.

## Where things are

| Path | What it is |
|---|---|
| `index.html` | Landing page (generated) |
| `guide/*.html` | Summary, decision readiness (16 blocking questions + 8-step plan), methods, cost ladder, steps, taxes, Flagged for Review, sources, repository review, archive (generated) |
| `guide/data/*.json` | The data behind every page: sources with quoted text, prices, methods, taxes, flagged items, review rules |
| `guide/data/cost-ladder.csv` | Every method at every amount (generated) |
| `guide/build/build.py` | Builds the site from the data. Standard library only |
| `guide/build/verify.py` | Checks the site: sources on every row, blanks flagged, arithmetic recomputed, all links crawled |
| `guide/build/scan.py` | Line-by-line rule scan of the archived editions; writes the snapshot used by the review page |
| `guide/audit/evidence-notes.md` | Working log of the text read on each official page |
| `EXECUTIVE_SUMMARY.md` | Short summary (generated) |
| `REQUIREMENTS.md` | The request, item by item, and where each is met |
| `COORDINATION.md` | Parallel-session protocol, claims and release log |
| `legacy-portal.html`, `integration/`, `edition-*/`, `docs/`, `dossier/`, `data/`, `pages/`, `scripts/`, `assets/`, `overview.html` | Earlier editions, kept unchanged as an archive. Do not take figures from them |

## Rebuild and check

```sh
python3 guide/build/build.py
python3 guide/build/verify.py
```

Both need only Python 3.9 or later. CI (`.github/workflows/guide.yml`) runs the same two commands on every pull request and fails if the committed pages differ from a fresh build.

## Rules the data follows

- Every table row links to the official page the figure was read on.
- A value that could not be confirmed on an official page is left blank and listed on the Flagged for Review page. Nothing is inferred.
- Sources are the regulator, tax authority, statute, or the bank's or provider's own price list. Third-party articles are not used.
- Figures are dated. The exchange rate is one Bank of China board reading on 2026-11-10 (re-verified live on 2026-11-11); re-check before acting.

This is research, not legal or tax advice.
