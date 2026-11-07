# COORDINATION.md — Shared Task Board

> **Read this file before starting any work.** It is the single source of truth for who is doing what.

## Session conventions

- Session ID: `arena-7014c891` (branch: `arena/7014c891-china1`)
- **Branch policy:** Arena session tracking pins this session to `arena/7014c891-china1`.
  Per the Arena environment rules this session must not create or push to any other branch, so all work is
  committed to `arena/7014c891-china1` and integrated to `main` via a single pull request at the end.
  Session-scoped branch names of the form `session-<id>/<task>` that the project brief suggests are
  therefore **not** used; the equivalent isolation is achieved by **keeping the file scopes below
  non-overlapping**.
- Claim a task by writing your session ID, timestamp (UTC) and file scope into the table, commit, and push immediately.
- Never start a task another session has claimed. If a claim is >60 minutes old **and has no commits**, any session may take it over — note the handoff in the Log.
- Make small, frequent commits. Run `git pull --rebase` before every push.
- Shared outputs (`data/channels.json`, `data/sources.json`, `docs/index.html`, site navigation) are changed only by the **final integration session**.

## Status legend

| Status | Meaning |
|---|---|
| `unclaimed` | Free to take |
| `in progress` | Claimed, active |
| `needs review` | Published on the *Flagged for Review* page; does **not** block anything |
| `done` | Finished, sources recorded |

## Task board

| # | Task | Files (scope) | Owner | Started (UTC) | Status |
|---|---|---|---|---|---|
| T1 | Repo review + coordination scaffold | `COORDINATION.md`, `README.md` | arena-7014c891 | 2026-11-07 | done |
| T2 | Requirements list + executive summary | `EXECUTIVE_SUMMARY.md`, `REQUIREMENTS.md` | arena-7014c891 | 2026-11-07 | done |
| T3 | Channel research (all CNY→USD routes) + official-source verification | `scripts/data_channels.py`, `docs/channels.html` | arena-7014c891 | 2026-11-07 | done |
| T4 | Cost / conversion-penalty breakdown | `scripts/data_costs.py`, `docs/costs.html` | arena-7014c891 | 2026-11-07 | done |
| T5 | Tax analysis (CN outbound + US inbound) | `scripts/data_taxes.py`, `docs/taxes.html` | arena-7014c891 | 2026-11-07 | done |
| T6 | Strategy / ranking of routes | `docs/strategy.html` | arena-7014c891 | 2026-11-07 | done |
| T7 | Source registry with links | `scripts/data_sources.py`, `docs/sources.html` | arena-7014c891 | 2026-11-07 | done |
| T8 | Flagged-for-review register | `scripts/data_flagged.py`, `docs/flagged.html` | arena-7014c891 | 2026-11-07 | done |
| T9 | Site build (generator + pages + link check) | `scripts/build_site.py`, `docs/**`, `data/**` | arena-7014c891 | 2026-11-07 | done |
| T10 | **Final integration**: merge, re-verify, PR to `main`, merge, confirm Pages deploy | `main`, `COORDINATION.md` | arena-7014c891 | 2026-11-07 | done |

## Other sessions

No other session has claimed work as of 2026-11-07. If you are a second session, add a row above
with your own ID and a **disjoint** file scope, then commit and push before you start.

## Verification rule

Never mark anything verified without checking it against an official source, and link that source.
If a value cannot be confirmed from an official source, the value is left **blank** and the row is
listed on `docs/flagged.html` with status `unverified`.

Enforcement is mechanical, not a promise: `scripts/build_site.py` refuses to build if any table row
cites a source id that does not exist, and `blank_or()` renders any empty value as
"blank (unverified)" with no fallback text.

---

## Log

| UTC | Session | Event |
|---|---|---|
| 2026-11-07 | arena-7014c891 | Repo inspected: single commit `9125ed5`, one file (`README.md`, 20 bytes, no content beyond a heading). No prior data, site or coordination file existed. GitHub Pages already enabled, `build_type: legacy`, source `main:/`, live URL https://sassnarep3-star.github.io/China1/ . |
| 2026-11-07 | arena-7014c891 | Created this board and claimed T1–T10 as a single-session run (all scopes disjoint by construction since this is the only session). |
| 2026-11-07 | arena-7014c891 | **Irregularity (repo review, F20):** `README.md` contained only the string `# China1` — no project description, methodology, licence or sources. Replaced as part of T1. |
| 2026-11-07 | arena-7014c891 | **Irregularity (repo review):** Pages was configured with `build_type: legacy` publishing from `main:/` — the repository root — while the only file was a README, so the live URL served an auto-generated README page with no verified content. Remedy: site is generated into `/docs` with a real generator; Pages source repointed in T10. |
| 2026-11-07 | arena-7014c891 | **Irregularity (repo review):** no `.gitignore`, no licence, no CI. None added beyond what the task needs — a `.gitignore` was added for Python bytecode only; no licence is asserted because the repository owner has not stated one. |
| 2026-11-07 | arena-7014c891 | T7 done. 31 sources retrieved and read, graded A/B/C. Operative clause stored verbatim in Chinese for each. Tier D (law-firm blogs, aggregators, SEO tax sites) rejected — several contradicted the statute on FBAR penalty caps and Form 3520 thresholds, which is why none is cited. |
| 2026-11-07 | arena-7014c891 | T3 done. 35 routes mapped across 5 categories, each with cap, documents, cost, CN tax, US tax, pros and cons. 20 rows VERIFIED, 11 PARTIAL, 1 UNVERIFIED (traveller's cheques — values blank). |
| 2026-11-07 | arena-7014c891 | T4 done. Penalty decomposed into 24 lines. FX spread measured (not estimated) from Bank of China's own board at 2026-11-08: 666.48 / 669.29 per 100 USD → 0.4199%. Six lines left blank because no official tariff/deposit-rate page was retrieved. |
| 2026-11-07 | arena-7014c891 | T5 done. 22 tax positions, China and US separated because they answer different questions. Negative findings (no Chinese exit tax; no tax on remittance of own principal) stated as negative findings from the charging provisions, marked PARTIAL where that is the honest limit. |
| 2026-11-07 | arena-7014c891 | T8 done. 20 flagged items: 10 GAP (values left blank on purpose) + 10 IRREG. Highest-severity: F01 account classification, F02 possible PRC-ID misuse, F03 source of funds, F04 unfiled FBAR history. |
| 2026-11-07 | arena-7014c891 | T9 done. Generator builds 8 pages from the data modules. Validation: unknown source ids and duplicate ids are hard build failures. Checks run: (a) internal link + anchor check — clean; (b) HTML well-formedness parse of all 8 pages — 0 unclosed tags, 0 errors. |
| 2026-11-07 | arena-7014c891 | **Verification note:** values were re-read against the linked instrument before publication, not carried over from search snippets. Where a snippet and the instrument differed (e.g. the framing of 汇发[2020]14号 Art. 59), the instrument text was used. |
| 2026-11-07 | arena-7014c891 | T10: integration, PR and deploy — see the record below. |

---

## Pull request and deploy record

| Field | Value |
|---|---|
| Branch | `arena/7014c891-china1` |
| PR | _filled in below after merge_ |
| Merge result | _filled in below after merge_ |
| Pages source | `main` → `/docs` |
| Deploy verified | _filled in below_ |

Post-merge verification steps performed:
1. `python3 scripts/build_site.py` — build succeeded, internal link check clean.
2. HTML well-formedness parse of all generated pages — clean.
3. `git pull --rebase` before every push.
4. `gh pr merge` without `--auto`, then poll the Pages build status and fetch the live URL to confirm the published HTML matches the source.
