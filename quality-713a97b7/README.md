# Independent quality review

A targeted review of the canonical China Money guide, not another set of transfer
recommendations. The published report is [`index.html`](index.html). The dated
baseline, source excerpts and twelve review findings are in `findings.json`.
Current site content may have changed since that baseline; do not treat a past
observation as proof that a later version still has the same wording.

## Reproduce

Node 20+ and Python 3 are required. Dependencies are locked; the browser binary
is downloaded from the npm registry as part of the pinned Chromium package.
Dependencies and optional screenshots are excluded from Git.

```sh
npm ci --prefix quality-713a97b7 --ignore-scripts
python3 quality-713a97b7/build.py
npm test --prefix quality-713a97b7
```

Set `QA_SCREENSHOTS=1` on the browser command to create ignored screenshots in
`artifacts/`. The renderer starts a temporary local HTTP server under the
`/China1/` project-site base path and closes it on completion. The browser does
not visit external source URLs or submit personal data.

## What is checked

- `audit.py` requires each data-table row on the guide and report to link to a
  registered source, checks local targets and fragments (including anchors in
  archived HTML), tests all forty amounts for every method, checks that
  incomplete costs remain blank and flagged, and
  independently compares the BOC illustration with its recorded inputs.
- `selftest.py` uses isolated malformed fixtures to check that missing sources,
  broken fragments, duplicate amounts and unflagged or filled unknown costs are
  rejected by the checker.
- `browser-check.cjs` renders each canonical page at 320, 360, 390, 768 and
  1280 pixels, exercises expandable tables, and checks HTTP status, page-level
  overflow, table containment, basic landmarks, link names and missing image
  alternatives.
- `.github/workflows/quality-713a97b7.yml` rebuilds the report, checks the
  committed output is deterministic and runs both checks on pull requests.

These checks establish structural consistency and reproduce a mathematical
scenario; **they do not verify an external page's availability, the legal meaning
of a citation, an individual's eligibility, a live FX quote, or an all-in cost.**
Those require source re-reading, the individual's facts and professional review.
The report records the official pages opened during the targeted manual review.
The site's historical pattern scan is not a substitute for a manual
line-by-line verification of every archived statement.
