# COORDINATION.md — Shared Task Board

**Repo:** `sassnarep3-star/China1`
**Protocol owner:** integration session
**Last updated:** 2026-11-07

## Session registry

| Session ID | Branch | Role | Status |
|---|---|---|---|
| `arena-fb9ad5f3` | `arena/fb9ad5f3-china1` | Research + build + integration (single active session) | active |

> **Note on parallelism:** at the time this board was created, `git branch -a` showed only
> `main` and `arena/fb9ad5f3-china1`, and no other session had written to `COORDINATION.md`.
> This session therefore claimed *all* tasks in one scope and is acting as its own final
> integration session. Any later session that sees a claim older than 60 minutes with no
> commits may take over per the protocol.

## Task board

| # | Task | Status | Owner | File scope |
|---|---|---|---|---|
| T1 | Repo review + irregularity log | in progress | `arena-fb9ad5f3` | `COORDINATION.md`, `research/00-repo-review.md` |
| T2 | China-side legal framework: capital controls, FX quotas, outbound-transfer channels | in progress | `arena-fb9ad5f3` | `research/10-china-framework/` |
| T3 | Channel inventory: every legal CNY→USD route, pros/cons, with official sources | in progress | `arena-fb9ad5f3` | `data/channels.json`, `research/20-channels/` |
| T4 | Penalty & cost decomposition (FX spread, fees, tax, fines) | in progress | `arena-fb9ad5f3` | `data/costs.json`, `research/30-costs/` |
| T5 | US-side tax & reporting obligations (FBAR, 8938, §988, 3520, §6038D) | in progress | `arena-fb9ad5f3` | `data/us-tax.json`, `research/40-us-tax/` |
| T6 | Illegal / high-risk routes (must-not-do list) | in progress | `arena-fb9ad5f3` | `data/prohibited.json`, `research/50-prohibited/` |
| T7 | Executive summary | in progress | `arena-fb9ad5f3` | `research/90-executive-summary.md` |
| T8 | Static site build (landing + category subpages + tables) | unclaimed | — | `site/`, `docs/` |
| T9 | Link + data validation (no broken links, every row sourced) | unclaimed | — | `scripts/verify.py` |
| T10 | PR → main, merge, Pages deploy confirmation | unclaimed | — | git only |

## Log

### 2026-11-07 — session `arena-fb9ad5f3`
- Created this board. Repo contained only a one-line `README.md` (`# China1`) at commit `9125ed5`;
  nothing to review, no prior work to merge. Recorded in `research/00-repo-review.md`.
- Claimed T1–T7. T8–T10 will be claimed by this session once content tasks are `needs review`/`done`.
- GitHub Pages already enabled on `main` (`build_type: legacy`, source `/`, public),
  html_url `https://sassnarep3-star.github.io/China1/`.
