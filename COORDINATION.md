# COORDINATION.md — Shared Task Board

**Repo:** `sassnarep3-star/China1`
**Last updated:** 2026-11-07

## Session registry

| Session ID | Branch | Role | Status |
|---|---|---|---|
| `arena-fb9ad5f3` | `arena/fb9ad5f3-china1` | Research → build → final integration (single active session) | active |

> **Parallelism note.** At start, `git branch -a` showed only `main` and `arena/fb9ad5f3-china1`, and no other session had written to this file. This session therefore claimed **all** tasks in one non-overlapping scope and is acting as its own final integration session. A later session that sees a claim older than 60 minutes with no commits may take over per protocol.

## Task board

| # | Task | Status | Owner | File scope | Result |
|---|---|---|---|---|---|
| T1 | Repo review + irregularity log | **done** | `arena-fb9ad5f3` | `research/00-repo-review.md` | Repo held one 8-byte README; nothing to verify on arrival. Recorded as R07. |
| T2 | China-side legal framework | **done** | `arena-fb9ad5f3` | `research/02-verification-log.md`, `china-rules.html` | 7 instruments; 17 claims verified line by line (log §A–D) |
| T3 | Channel inventory | **done** | `arena-fb9ad5f3` | `data/channels.json`, `channels.html` | **21** channels incl. 4 that don't exist/aren't routes |
| T4 | Penalty & cost decomposition | **done** | `arena-fb9ad5f3` | `data/costs.json`, `costs.html` | **18** components; 6 deliberately blank (no official source) |
| T5 | US tax & reporting obligations | **done** | `arena-fb9ad5f3` | `data/usForms.json`, `us-tax.html` | 6 forms; 4 fully verified, 2 partial and flagged |
| T6 | Prohibited / high-risk routes | **done** | `arena-fb9ad5f3` | `data/prohibited.json`, `prohibited.html` | **6** routes, each with the citing article |
| T7 | Executive summary | **done** | `arena-fb9ad5f3` | `research/01-executive-summary.md` | 9 sections; leads with the premise correction |
| T8 | Static site build | **done** | `arena-fb9ad5f3` | `site` at repo root, `assets/` | 10 pages, dashboard + 8 category subpages + method |
| T9 | Link + data validation | **done** | `arena-fb9ad5f3` | `scripts/build_site.py`, `scripts/render_check.js` | Build gate passes; 199 internal links resolve; all 10 pages render headless |
| T10 | PR → main, merge, Pages deploy confirm | **in progress** | `arena-fb9ad5f3` | git only | see log below |

## Log

### 2026-11-07 — session `arena-fb9ad5f3`

**Start state.** Commit `9125ed5`: one file, `README.md`, contents `# China1` (8 bytes). No data, no site, no `COORDINATION.md`, no other branches. GitHub Pages already enabled on `main` (`build_type: legacy`, path `/`, public, HTTPS enforced) → `https://sassnarep3-star.github.io/China1/`.

**Scope decision.** Because the repo was empty, T1–T7 were claimed in a single non-overlapping scope. Shared outputs (table data, site index and navigation) were authored by this session after content tasks closed, per the integration rule.

**Sources used.** 30 registered in `data/sources.json`. China: State Council Gazette (gov.cn), SAFE and its Tianjin/Xiamen sub-bureaus (safe.gov.cn), PBoC (pbc.gov.cn), SAT (chinatax.gov.cn). US: U.S. Code, eCFR, irs.gov, fincen.gov. Secondary reprints were used only as pointers to official text, never as citations.

**Verification performed.** Every claim logged in `research/02-verification-log.md` with one of three states — `retrieved` (11), `excerpt` (12), `unverified` (7). Enforced mechanically: `scripts/build_site.py` fails the build if a cited source id does not resolve, if an internal link is missing, if a *verified* cost row cites nothing, or if an *unverified* cost row carries a value.

**Build/deploy evidence.**
- `python3 scripts/build_site.py` → `OK — build clean, no broken internal links, all references resolve.` (30 sources, 10 pages, 199 internal links, 21 channels, 18 cost rows, 6 forms, 6 prohibited routes, 7+7 flags)
- `node scripts/render_check.js` (jsdom) → all 10 pages render, no JS errors, no empty containers.
- **Caveat, stated rather than hidden:** live HTTP link-checking is impossible here — the sandbox has no outbound access to government hosts (`curl` → `000` for irs.gov, safe.gov.cn, ecfr.gov, gov.cn, pbc.gov.cn, fincen.gov). Link validity rests on fetches done during research, not an automated checker.

**Irregularities flagged** (published on the site's *Flagged for Review* page; none block publication):

| ID | Finding |
|---|---|
| **R01** | 银发〔2021〕237号 (the "924 notice") was **repealed 2026-02-06** by 银发〔2026〕42号 — most online advice still cites the dead instrument |
| **R02** | A third-party legal database labels 汇发〔2020〕14号 "wholly repealed". It is not: 汇发〔2025〕13号 repealed 5 unrelated documents; SAFE still applies the 2020 Guidelines |
| **R03** | The USD 50,000 figure is a *facilitation threshold*, not a ceiling — and does not apply to an overseas individual's purchases at all |
| **R04** | Many guides wrongly give foreigners the same USD 50,000 purchase allowance as citizens |
| **R05** | The user's premise (large tax on conversion) matches no rule found; the cost is upstream/downstream of the conversion |
| **R06** | "Use relatives' quotas" is expressly prohibited by Art.62 (watch list, year + 2) |
| **R07** | Nothing existed in the repo to review — recorded so the absence of a finding isn't misread as a clean bill of health |
| F01–F07 | 7 claims left blank/withheld: savings-interest exemption, 2021 No.19 announcement, 50%-of-balance willful FBAR measure, FinCEN 105, Form 3520 threshold/penalty, FATCA IGA, treaty benefit |

**Handoff / conflicts.** None. No other session committed to this repo during the run, so no rebase conflicts and no scope collisions occurred.

**Merge result.** Recorded below once the pull request is merged.

## PR record

| Item | Value |
|---|---|
| PR | _recorded post-merge_ |
| Merge SHA | _recorded post-merge_ |
| Pages deploy | _recorded post-merge_ |
