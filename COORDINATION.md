# Coordination

Session: arena-3e9a7b87 (sole active session observed). All work remains on the Arena-required branch `arena/3e9a7b87-china1`; this overrides the requested alternate branch naming.

| Task | Status | Owner | Scope |
|---|---|---|---|
| Repository audit, official-source research, dashboard, verification and integration | in progress | arena-3e9a7b87 | COORDINATION.md, README.md, docs/**, scripts/**, .github/** |

## Log
- 2026-11-07: Initial repository contains only README.md, with no existing analysis, source data, site, or competing claims. Claimed integrated scope before implementation. No user-specific tax/account facts supplied; these must remain unknown rather than inferred.
- Initial claim push: remote session branch did not yet exist, so `pull --rebase origin <session-branch>` failed. Rebased against origin/main instead, then published the required session branch. No conflicts and no other work discarded.
- Research inspected 2026-11-07: PBOC Decree [2006] No.3 Articles 3, 7, 9, 13–15; HSBC China Individual FX Services Guide (purchase/property/outbound sections); Wise CNY guide (outbound eligibility and limits); IRS worldwide-income, FX translation, foreign tax credit and FBAR/8938 guidance; GPO 2024 section 988; China Customs passenger guide. Direct links and inspection scopes are in docs/sources.html and docs/data.json.
- Evidence irregularities are published in docs/review.html: quota wording/classification, missing personal facts/quotes, source age, incompletely retrieved Shenzhen filing page (official search excerpt only), unverified alternative services/crypto/cash permit rules. No numerical personal fees, taxes, or exchange rates invented.
- Local verification: `python scripts/build.py` and `python scripts/verify.py` passed; 6 pages and 60 table rows, each with official-source reference; relative links and source domains validated; unknown cost values blank. External source retrieval is recorded, not claimed as continuous live-link uptime verification.

| Task update | Status | Owner | Scope |
|---|---|---|---|
| Research and dashboard implementation | done | arena-3e9a7b87 | docs/**, scripts/**, README.md |
| Published evidence uncertainties | needs review | arena-3e9a7b87 | docs/review.html (non-blocking) |
| CI, PR, merge and Pages deployment | in progress | arena-3e9a7b87 | .github/**, COORDINATION.md |

## Preserved concurrent session board

# Coordination board

Last updated: 2026-11-07 (UTC)

| Task | Status | Owner | File scope |
|---|---|---|---|
| Research, verify, build and integrate China money dashboard; publish and merge | needs review | e6269551-china1 | COORDINATION.md, README.md, index.html, pages/, assets/, .github/workflows/ |

## Log

- 2026-11-07: Repository inspected; no existing board or project files beyond README. This session claims the integrated task. The Arena-assigned branch is `arena/e6269551-china1`; its name is fixed by the environment. Other sessions should claim non-overlapping scopes here before starting.

- 2026-11-07: Research and integration complete; unresolved case facts and older-rule issues are published on Flagged for Review. Reviewed each displayed data row against its linked official source or marked the account-specific value unverified. Major sources: [SAFE salary and source evidence](https://www.safe.gov.cn/tianjin/2026/0713/3088.html), [SAFE individual measures](https://www.safe.gov.cn/tianjin/2024/0430/2464.html), [SAFE inheritance revisions](https://www.safe.gov.cn/en/2014/0801/741.html), [Shanghai property FAQ](https://english.shanghai.gov.cn/en-FAQHome/20240204/b4426264395b4fa3adfde73778c94ad4.html), [Chinese income tax law](https://www.chinatax.gov.cn/eng/c102962/c102967/c102997/c103004/c5245849/content.html), [IRS FBAR](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar), [IRS foreign tax credit](https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit), and other official authorities linked per row. Official pages and search-indexed official PDF text were examined; an official citation does not establish individual eligibility. Notable irregularity: 2004 asset-transfer provisions differ from 2014 SAFE changes; current local implementation needs confirmation. Source, amount, status, rates and tax demands remain unknown. No case-specific numeric penalty was invented.
- Validation: `python3 assets/check.py` checks deterministic generation, 46 cited rows and local links; all five pages and stylesheet returned HTTP 200 locally. External source availability is not guaranteed by the local checker. The existing GitHub Pages configuration publishes `main` from the repository root. First pull of the newly created session branch failed because the remote branch did not yet exist; rebased against `main` before its initial push. No conflict occurred.
- Integration PR: https://github.com/sassnarep3-star/China1/pull/1. Initial branch and pull-request verification jobs passed; merge and new Pages deployment are pending. GitHub Actions warned that `actions/checkout@v4` is being run on Node.js 24 after Node.js 20 deprecation; this did not fail the job.
- Concurrent integration discovered after initial implementation: origin/main advanced to ef153cb (PR #1, owner e6269551-china1). Its completed/needs-review scope and site were not visible in the original checkout. Stopped to inspect that board, then merged origin/main on the fixed session branch. Add/add conflicts in workflow and coordination and README content conflict were resolved by preserving both coordination histories, preserving all prior pages/assets, retaining the prior checker and adding supplemental checks. No session branch was switched or deleted.
- Pages-settings API update denied HTTP 403 (`Resource not accessible by integration`). Used the already-configured `main:/` publication instead. Original dashboard retained at site root; supplemental dashboard at `/docs/`; reciprocal landing-page links added by final integration. This avoids needing a Pages-setting permission change. Prior edition retains its own source log; supplemental audit does not independently certify every prior-edition claim.

## Concurrent deployment completion update (preserved)
- Integration PR: https://github.com/sassnarep3-star/China1/pull/1. Initial branch and pull-request verification jobs passed; merge and new Pages deployment are pending. GitHub Actions warned that `actions/checkout@v4` is being run on Node.js 24 after Node.js 20 deprecation; this did not fail the job.

- Integration PR [#1](https://github.com/sassnarep3-star/China1/pull/1) merged successfully at 2026-11-07 20:28 UTC, merge commit `ef153cbfe24a9444090ea85818d4fcd49274622b`. [Pages build and deploy](https://github.com/sassnarep3-star/China1/actions/runs/42411230797) succeeded; the [live landing page](https://sassnarep3-star.github.io/China1/index.html?deployment=ef153cb) served the new dashboard. Case-specific unknowns and historical guidance remain on the Flagged for Review page.
- PR #3: https://github.com/sassnarep3-star/China1/pull/3. Combined checks passed at https://github.com/sassnarep3-star/China1/actions/runs/42411327202 (5 original pages/46 rows and 6 supplemental pages/60 rows). Merge initially refused because concurrent PR #4 updated main; preserved its deployment log and re-integrated. Initial flattening `pull --rebase` attempts were aborted without loss; `pull --rebase=merges` preserves the integration graph and succeeds.
- Integration completed: PR https://github.com/sassnarep3-star/China1/pull/3 merged 2026-11-07T20:30:28Z, merge commit 51fbb7ee25daade6742753c2be93387c8919b82e. Post-merge verification succeeded: https://github.com/sassnarep3-star/China1/actions/runs/42411379679. GitHub Pages build and deployment succeeded: https://github.com/sassnarep3-star/China1/actions/runs/42411379641; Pages API reports `built` at that exact merge commit, no error.
- Published URLs: https://sassnarep3-star.github.io/China1/ (preserved original dashboard) and https://sassnarep3-star.github.io/China1/docs/ (supplemental six-page dashboard). Browser-level public HTTP retrieval was not independently tested from this network-restricted shell; deployment confirmation is GitHub's successful deployment/API result.
- Final task status: research/dashboard/integration/deployment **done**; evidence uncertainties **needs review**, published and non-blocking. Workflow runtime deprecation notices were informational, not failed checks. This final log update is submitted in a follow-up documentation PR from the same fixed branch.
