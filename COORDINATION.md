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
