# Edition 12670774 — getting RMB out of China as a US citizen

Session `arena-12670774`, 2026-11-10. Self-contained: its own data, cost engine, verifier and static site.
Published at `/China1/edition-12670774/`.

## What it adds

- **Who may use which route**, read passage by passage on the official pages (25 sources: 21 opened, 4 at excerpt level).
- **Cost of every method at every USD 10,000 step to USD 400,000**, as arithmetic on published inputs. A part with no official input is blank and flagged.
- **Steps** for every lawful method. Prohibited channels list the penalty only.
- **A line scan of every tracked file** outside this edition, with the figures re-read today marked confirmed, out of date or not re-opened.
- **Irregularities in the official texts themselves**, listed on the Flagged for Review page.

## Pages

`index.html` overview and route finder · `summary.html` · `methods.html` · `steps.html` · `costs.html` · `tax.html` · `flagged.html` · `audit.html` · `sources.html` · `evidence.html`

## Rebuild and verify

```
python3 edition-12670774/build/audit_repo.py   # optional: rescan the repository (writes data/audit_scan.json)
python3 edition-12670774/build/build.py        # writes data/*.json, data/costs.csv and the pages
python3 edition-12670774/build/verify.py       # exit 0 only if every check passes
```

`verify.py` does not import the build. It recomputes all 760 cost rows with exact fractions, requires a link to an
official site on every table row, requires a flag on every blank, forbids steps on prohibited methods and crawls every local link.

## Files

- `build/content.py` — sources, numeric inputs and flags, hand-entered from the pages read.
- `build/methods.py` — methods, tax tables, penalties, route finder, summary.
- `research/source-notes.md` — the passages relied on, quoted as published.
- `data/` — generated JSON and CSV.

Not legal or tax advice. The bank's actual rate and fees govern.
