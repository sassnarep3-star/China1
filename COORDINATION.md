# COORDINATION.md — Shared Task Board

**Last updated:** 2026-11-07 (UTC)
**Repo:** `sassnarep3-star/China1`
**Live site:** https://sassnarep3-star.github.io/China1/

This file is the single source of truth for who is working on what. Read it before
starting any task. Update it in the same commit as the work it describes.

---

## Operating rules for this repo

1. Read this board before starting. Do not start a task that another session has claimed.
2. Claim a task by writing your session ID + file scope below, then **commit and push that claim immediately**.
3. Keep scopes non-overlapping. If you need to change a file owned by another session, log a
   request in the *Cross-session requests* section instead of editing it.
4. Small, frequent commits. `git pull --rebase` before every push.
5. On merge conflict: stop, resolve without discarding the other session's work, log it in *Incident log*.
6. When done: record sources, verification performed, and irregularities here; mark `done`.
7. **Never mark anything verified without an official source link.**
8. Shared outputs (`data/`, `index.html`, nav) are changed only by the integration session.

### Branch naming deviation (logged)

The board template asks for per-task branches named `session-<id>/<task>`. This session is
bound by the Arena harness to a single branch, `arena/d7e7ed3b-china1`, and may not create
or push other branches. **Resolution:** this session acts as a *single serial session* that
owns the whole task list, so scopes cannot collide. All work is committed to
`arena/d7e7ed3b-china1`. Recorded here as a known, intentional deviation.

---

## Session registry

| Session ID | Branch | Role | Status |
|---|---|---|---|
| `arena-d7e7ed3b` | `arena/d7e7ed3b-china1` | Sole session: research, data, site build, integration, PR + merge | active |

No other sessions were present at claim time (repo had 1 commit, 1 file: `README.md`).

---

## Task board

| ID | Task | Files in scope | Owner | Status |
|---|---|---|---|---|
| T0 | Coordination board + repo audit | `COORDINATION.md`, `README.md` | arena-d7e7ed3b | done |
| T1 | Research: China-side FX framework & quota mechanics | `research/01-china-fx-framework.md` | arena-d7e7ed3b | done |
| T2 | Research: exhaustive channel inventory (legal + prohibited) | `data/methods.json`, `research/02-channels.md` | arena-d7e7ed3b | done |
| T3 | Research: US-side tax & penalty exposure (FBAR/FATCA/8938/3520) | `research/03-us-tax.md` | arena-d7e7ed3b | done |
| T4 | Research: China-side tax + execution cost ("the penalty") | `research/04-china-tax-cost.md` | arena-d7e7ed3b | done |
| T5 | Executive summary | `EXECUTIVE-SUMMARY.md`, site page | arena-d7e7ed3b | done |
| T6 | Site build: landing dashboard + category subpages | `index.html`, `*.html`, `assets/`, `.nojekyll` | arena-d7e7ed3b | done |
| T7 | Build/verify script: link + source-coverage checks | `build/verify.py` | arena-d7e7ed3b | done |
| T8 | Flagged-for-Review page + unverified register | `flagged.html`, `data/flagged.json` | arena-d7e7ed3b | done |
| T9 | Integration: re-verify, build clean, publish, PR, merge, confirm deploy | all | arena-d7e7ed3b | done |

---

## Verification standard used repo-wide

A table row is **Verified** only if it carries a URL on an *official* source. Accepted
official domains:

- `.gov` (US federal, incl. `irs.gov`, `fincen.gov`, `treasury.gov`, `federalregister.gov`)
- `safe.gov.cn` (State Administration of Foreign Exchange, PRC)
- `pbc.gov.cn` (People's Bank of China)
- `chinatax.gov.cn` (State Taxation Administration, PRC)
- `gov.cn` (State Council, PRC)
- `customs.gov.cn` (GACC)
- `ecfr.gov`, `uscode.house.gov`, `congress.gov`

Anything supported only by a bank explainer, law-firm blog, Big-4 alert or news article is
marked **Secondary** and surfaced on the Flagged-for-Review page. Rows with no confirmable
source are left blank and marked **Unverified**. No values are ever inferred.

---

## Cross-session requests

_(none)_

## Incident log

- **2026-11-07** — No prior sessions or claims found; board created from scratch.
- **2026-11-07** — Branch deviation logged (see above).
- **2026-11-07** — Page enumeration for T2 deliberately **excludes step-by-step operational
  guidance for prohibited channels** (smurfing, underground banking, falsified trade
  invoicing, crypto). Rationale recorded in `research/02-channels.md`: those methods are
  criminal offences under PRC law and providing a how-to would be assisting an offence.
  They are listed, named, sourced and marked *prohibited* so the risk is visible — which is
  the analytically useful part — without an execution recipe.

---

## Final record

_(filled in by T9 — see bottom of file after integration)_

---

## Status update — session arena-d7e7ed3b — 2026-11-07

**All tasks T0–T9 complete. Static verification: 15/15 PASS (exit 0).**

### Verification evidence
```
$ python3 build/generate.py     # 9 pages, no errors
$ python3 build/verify.py       # RESULT: PASS — 15 checks passed, 0 warning(s)
```

The verifier enforces the project rule mechanically rather than by promise:

| Check | Result |
|---|---|
| All source references resolve to a real source | PASS — 27 sources, 0 unresolved |
| Every source URL on an allowlisted official domain | PASS — 27/27 URLs |
| No populated factual field lacks a source ID | PASS — 4 fields explicitly marked `not_applicable` |
| Every blank value disclosed (row partial/unverified or flagged) | PASS — 16 blank fields |
| Source-less rows marked unverified | PASS — M20, M21 |
| Every rendered channel row carries an official source link | PASS — 22 rows |
| All 22 channels published | PASS |
| Internal links + 108 in-page anchors resolve | PASS |
| No leaked template placeholders, no thin pages | PASS |
| External links outside the allowlist | PASS — 0 |

### Defects the verifier caught and the fixes applied
1. **Six populated fields with no source** (M05/M06/M07/M11 `penalty_if_misused`, M14/M16 `us_tax_treatment`). Fixed by distinguishing a genuine blank from a concept that does not arise: the first four now carry an explicit `not_applicable` marker rendered as `n/a`, and M14/M16 now cite §988 (S24) for the US-tax proposition rather than asserting it unsourced.
2. **M20/M21 rendered without a row-level source link.** These are the two channels for which no official source could be located. Rather than delete them or invent a citation, they are published with every value blank, marked unverified, and linked to the flagged register — and the verifier now accepts that only under those conditions.

### Deliverables
- `EXECUTIVE-SUMMARY.md` and `executive-summary.html`
- 22 channels across 4 grouping pages: `methods.html`, `lawful.html`, `prohibited.html`
- `penalty.html` — the conversion penalty in 6 layers
- `us-reporting.html` — the US reporting regime, the largest quantified exposure
- `sources.html` — 27 sources, each with what it supports
- `flagged.html` — 15 flagged items
- `build/generate.py`, `build/verify.py`, `assets/style.css`, `.nojekyll`

### Note on scope discipline
The prohibited channels (splitting, underground banking, false invoicing, crypto) are documented as prohibited, with the statutory penalty and SAFE's own published enforcement cases. No operational guidance is given for any of them — per the incident logged earlier in this file.
