# Session `arena-db079cfc` — verification record (2026-11-11)

This directory is the working record for the session that refreshed and re-verified the
live guide at the repository root (`index.html` + `guide/`). It is deliberately small: it
holds the evidence, not a second copy of the research.

| File | What it is |
|---|---|
| `verification/source-recheck.md` | Every entry of `guide/data/sources.json`, whether it was re-opened on 2026-11-11, and what the re-read found |
| `verification/findings.md` | The irregularities found while doing that, what was fixed, and what is still open |
| `verification/checks.txt` | Raw output of every checker in the repository, run at the commit that was merged |

The guide itself is generated from `guide/data/*.json` by `guide/build/build.py` and gated
by `guide/build/verify.py`. Nothing in this directory is generated; it is a record.

Rules applied: no figure was carried over without being present in the text of an
official page; a figure that could not be confirmed was left blank and published on
`guide/flagged.html`; no personal facts were inferred — they became questions on
`guide/questions.html` with a stated way to find the answer.
