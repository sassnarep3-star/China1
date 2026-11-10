# Edition M

A self-contained edition of the China money project, built by session arena-1ee3ca2b on 2026-11-10.

It closes the gap left by the earlier editions: an actual cost for every method at every USD 10,000 step
to USD 400,000, built only from figures read on official pages that day.

| Page | What it holds |
|---|---|
| `index.html` | Overview dashboard: short answer, which route fits, cost by method and amount |
| `costs.html` | Nine 40-row cost tables covering all 13 methods |
| `methods.html` | Methods with limits, pros and cons; prohibited channels and their penalties |
| `steps.html` | Numbered steps for each method |
| `tax.html` | Every layer of cost and tax, the US currency-gain table, penalties, relief |
| `flagged.html` | Flagged for Review: 34 items |
| `audit.html` | Line-by-line repository audit: 389 files, 172,119 lines |
| `sources.html` | 57 official pages with the sentence relied on |
| `summary.html` | Executive summary and requirement checklist |

## Rebuild and verify

```
python3 edition-m/build/build.py
python3 edition-m/build/verify.py
```

`build.py` is deterministic (no network, no clock). `verify.py` recomputes every cost row with its own
arithmetic, checks that every table row carries a link to an official host, that every blank links to a flag,
that all internal links resolve, and that every source cited exists.

`build/audit.py` rescans the rest of the repository and rewrites `data/audit_scan.json`. It is not part of
CI because its result changes when other editions change.

## Data

- `data/sources.json` — pages read, with quotes and how each was read
- `data/inputs.json` — every number used, with its source id
- `data/methods.json`, `data/tax.json`, `data/flags.json`, `data/audit.json` — page content
- `data/ladders.json`, `data/ladders.csv` — generated cost tables
- `data/_research_log.md` — raw notes taken while reading the official pages
