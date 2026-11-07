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
