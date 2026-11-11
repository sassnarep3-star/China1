# Session `arena-db079cfc` — verification record (2026-11-11)

This directory is the working record of the session that re-read the priced inputs of the
live guide (`index.html` + `guide/`) and re-checked its sources on 2026-11-11. It holds
evidence, not a second copy of the research: the guide stays the single published site.

| File | What it is |
|---|---|
| `verification/source-recheck.md` | Every entry of `guide/data/sources.json`, whether it was re-opened on 2026-11-11, and what the re-read found |
| `verification/findings.md` | The irregularities found, what was fixed, what is still open, and how the collision with a concurrent session was resolved |
| `verification/checks.txt` | Raw output of every checker in the repository at the merged commit |

The guide is generated from `guide/data/*.json` by `guide/build/build.py` and gated by
`guide/build/verify.py`. Nothing here is generated.

Rules applied: no figure was carried over without being present in the text of an
official page; anything that could not be confirmed stayed blank and is on
`guide/flagged.html`; no personal facts were inferred.
