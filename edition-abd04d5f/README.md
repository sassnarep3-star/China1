# China Money (CNY → USD) — edition of session arena-abd04d5f

Live: https://sassnarep3-star.github.io/China1/edition-abd04d5f/

Self-contained edition. First claimed as `edition-m/`; moved to `edition-abd04d5f/` on 2026-11-10 because session arena-1ee3ca2b claimed the same path 84 seconds later and was already writing there. Nothing outside `edition-abd04d5f/` is read at page-render time and nothing outside it is written.

| Path | What it is |
|---|---|
| `index.html` | Landing page: short answer, key figures, which route applies |
| `methods.html` | 23 methods with status, cost, limits, pros and cons |
| `costs.html` | Every method priced at each USD 10,000 step up to USD 400,000 |
| `steps.html` | Step-by-step for each lawful route |
| `taxes.html` | China and US tax, reporting and penalties, with amounts |
| `flagged.html` | Flagged for Review — everything not confirmed |
| `sources.html` | 31 official documents, what was confirmed in each, and how it was read |
| `review.html` | Findings on the earlier editions |
| `build/content.py` | All facts, each tied to a source ID |
| `build/build.py` | Deterministic generator (no clock, no network) |
| `build/verify.py` | Independent verifier: recomputes every figure with exact fractions, checks every table row has an official link, blanks are flagged, links resolve |
| `data/` | `costs.csv`, `costs.json`, `sources.json`, `methods.json`, `flags.json`, `repo_inventory.json` |

Rebuild and check:

```
python3 edition-abd04d5f/build/build.py
python3 edition-abd04d5f/build/verify.py
```

Rules followed: a value appears only if it was read on an official page on 2026-11-10; otherwise the cell says
"unverified" and links to a flag. `sources.html` states for each document whether the page itself was opened or
its text was read through a search-index excerpt of the same official URL.
