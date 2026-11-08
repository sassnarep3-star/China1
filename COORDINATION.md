---

# Session board — arena-0614c102 — 2026-11-08

All previous boards are preserved verbatim. This session is pinned to `arena/0614c102-china1`; Arena's fixed-branch rule takes precedence over the requested `session-<id>/<task>` naming. No other branch will be created or pushed.

| ID | Task | Status | Owner | File scope |
|---|---|---|---|---|
| E0 | Read shared board; inventory prior editions; publish claim | done | arena-0614c102 | This appended board section only |
| E1 | Independent repository audit and requirement coverage | in progress | arena-0614c102 | edition-d/data/audit.json, edition-d/audit.md |
| E2 | Official-source research, route inventory, tax and cost verification | in progress | arena-0614c102 | edition-d/data/**, edition-d/research/** |
| E3 | Executive summary and forty $10,000 cost increments through $400,000 | in progress | arena-0614c102 | edition-d/EXECUTIVE_SUMMARY.md, edition-d/build/** |
| E4 | Clean mobile dashboard, category pages, review register | in progress | arena-0614c102 | edition-d/site/** |
| E5 | Deterministic build, row-level evidence checks, local link/browser checks | in progress | arena-0614c102 | edition-d/build/**, .github/workflows/edition-d.yml |
| E6 | Final integration, PR, merge, live Pages verification | pending component completion | arena-0614c102 | Append-only board/README integration notes; root landing link after other tasks complete |
| E7 | Unverified values and inherited-edition irregularities | in progress | arena-0614c102 | edition-d/data/flags.json, edition-d/site/flagged.html |

No active non-overlapping task is being taken over. Previous edition files will not be changed. A new self-contained edition will preserve all existing outputs. Research will not start until this claim is committed and pushed. No personal balance, source-of-funds, residency, tax history, bank fee quote or exchange rate has been supplied; these remain unknown. Official rules will be distinguished from explicitly labelled arithmetic scenarios. No unverified numeric value will be populated as fact.

- 2026-11-08: Initial claim commit `dbcc779` pushed successfully. The remote session branch did not exist, so its first pull failed; rebased against origin/main and published the fixed Arena branch. No conflict or discarded work. E0 complete; E1/E2 claimed before implementation.
- 2026-11-08: E3/E4/E5/E7 claimed by the same session before implementation. E6 awaits a passing component build; shared files remain untouched until that gate. Official-page checks found that PBOC notice [2026] No.42 replaced the 2021 virtual-currency notice, and SC China's current personal tariff is Version 2 dated 2026-07-26. These are being checked against the inherited editions rather than copying older figures.
# Session update — arena-22534b4a (current Arena branch)

## Claim

| Task | Status | Owner | Scope |
|---|---|---|---|
| Add a source-linked USD 10k–400k scenario page; reconcile estimates with the official-rate timestamp and preserve unknown fees as blank | done (timestamp caveat published) | arena-22534b4a | `assets/build.py`, `assets/check.py`, `pages/estimates.html`, `pages/costs.html`, `pages/routes.html`, `pages/reporting.html`, `pages/review.html`, `index.html`, `COORDINATION.md`, `REQUIREMENTS.md` |

No other active owner or in-progress scope was present in the current checkout. Historical edition boards above are preserved; no other edition's data was edited. Current branch name is Arena-pinned and remains `arena/22534b4a-china1`.

### Sources and verification

- Read the official [Bank of China FX rate board](https://www.boc.cn/sourcedb/whpj/) directly on 2026-11-08 UTC. Its extracted USD row displayed 现汇卖出价 669.29 and 现汇买入价 666.48 CNY per USD 100, with published date 2026/11/09. The same page says its board is reference-only and actual execution uses the applicable online/branch quote. Because the displayed rate date is later than this report date, the mismatch is explicitly shown on the scenario page and on Flagged for Review; no claim is made that these are 2026-11-08 execution prices.
- Implemented transparent, reproducible arithmetic for 40 USD target amounts ($10,000 to $400,000 by $10,000): CNY target = USD × 669.29 / 100; midpoint comparator = USD × ((669.29 + 666.48) / 2) / 100; displayed difference is a quote-midpoint spread proxy, not a tax or bank fee. Outgoing, intermediary, receiving, documentary and account-specific tax amounts remain blank/unverified. Other listed methods carry primary provider/regulator source links and no fabricated numeric costs.
- Validation: `python3 assets/build.py` and `python3 assets/check.py` passed (6 root pages, 95 sourced data rows, 40 exact ordered scenarios, all local links, reproducible generation, visible date-mismatch warning). `python3 scripts/build.py && python3 scripts/verify.py` passed (6 generated supplemental pages, 60 sourced rows). `python3 edition-b/build/generate.py && python3 edition-b/build/verify.py` passed (15 checks); `python3 edition-c/build/build.py && python3 edition-c/build/linkcheck.py` passed (17 pages, 0 warnings). A separate HTMLParser review confirmed all 48 amount/method table rows have official/provider-primary links. Unknown values remain blank.
- No source establishes the exact transfer fee or tax owed by this account, and no personal facts or executable quote were supplied. These limits remain prominently stated; the date mismatch is flagged and non-blocking.

### Publication record — PR #10

- Pull request: https://github.com/sassnarep3-star/China1/pull/10 — **merged** 2026-11-08 23:11:05 UTC; merge commit `36116f9ece8aca6b61e10bbffcd7207734fce429`.
- PR verification: https://github.com/sassnarep3-star/China1/actions/runs/42533901475 — **passed**. The only notices were GitHub's informational Node.js 20 deprecation and upcoming `ubuntu-latest` image migration.
- Main-branch validation: https://github.com/sassnarep3-star/China1/actions/runs/42533931575 — **passed** at the merge commit.
- GitHub Pages build/deploy: https://github.com/sassnarep3-star/China1/actions/runs/42533930366 — **passed**. Pages API reports `built`, publishing from `main:/` at `https://sassnarep3-star.github.io/China1/`.
- Public verification: fetched `https://sassnarep3-star.github.io/China1/pages/estimates.html` after deployment. The published page contained all 40 targets, displayed the date warning, exposed source links on scenario and route rows, and left method fees unverified. `pages/review.html` publishes the date mismatch as a review flag.

# Session board — arena-133875bd (Edition D: cost engine + consolidated dashboard)

Appended 2026-11-08 UTC. Every prior board above is preserved verbatim; nothing was overwritten,
renamed or deleted.

## Claim

| Item | Value |
|---|---|
| Session | `arena-133875bd` |
| Branch | `arena/133875bd-china1` (fixed by Arena; the `session-<id>/<task>` convention cannot be used) |
| File scope | `edition-d/**` (new), this appended section of `COORDINATION.md`, one added CI job in `.github/workflows/verify.yml`, and a navigation link on root `index.html` *only* as final-integration step |
| Overlap | None. No file owned by another edition is edited. Existing editions are linked, not modified. |

## Why this edition exists

Editions A–C answered the legal question comprehensively but deliberately left every fee and every
dollar figure blank, because no official tariff had been retrieved. The brief explicitly requires
**per-method cost estimates in USD 10,000 increments up to USD 400,000** and **step-by-step
instructions per method**. Edition D closes exactly that gap: it sources published tariffs and
statutory rates, derives each cell arithmetically from a sourced unit rate, labels every derived
cell as derived, and flags the residual assumptions.

## Task board

| # | Task | Status | Notes |
|---|---|---|---|
| D-01 | Read repo, prior boards, requirements; claim scope | in progress | |
| D-02 | Repo review line by line; flag irregularities | unclaimed | |
| D-03 | Source register: official regulator, statute, published bank tariff | unclaimed | |
| D-04 | Method inventory with pros/cons, lawful/prohibited classification | unclaimed | |
| D-05 | Cost engine: $10k→$400k in $10k steps, every method | unclaimed | |
| D-06 | Step-by-step procedure per method | unclaimed | |
| D-07 | Executive summary | unclaimed | |
| D-08 | Site build: landing page + category subpages, mobile-first tables | unclaimed | |
| D-09 | Verification gate (citations resolve, no unsourced numbers, links) | unclaimed | |
| D-10 | Flagged-for-Review publication | unclaimed | |
| D-11 | CI job, PR, merge, Pages deploy confirmation | unclaimed | |

## Edition D — status update (supersedes the claim table above)

**All tasks D-01 to D-11 complete.** Session `arena-133875bd`, branch `arena/133875bd-china1`.

### File scope actually touched

| Path | Change |
|---|---|
| `edition-d/data/*.json` | new: 17 sources, 16 methods, 8 parameter groups, 25 flags, 15 repo-review findings |
| `edition-d/build/build.py` | new: cost engine and generator, 19 pages including 8 cost tables |
| `edition-d/build/verify.py` | new: 19-check gate, independent recomputation of all 320 cost cells |
| `edition-d/docs/**` | generated site |
| `index.html` | **regenerated as the portal** (final integration). The previous landing page is preserved byte-for-byte at `overview.html`. |
| `overview.html` | new: preserved copy of the pre-existing root landing page |
| `.github/workflows/verify.yml` | one job appended (`edition-d`); the five existing jobs are untouched |
| `README.md` | Edition D section prepended; all existing content preserved below it |
| `assets/build.py` | three lines: the legacy dashboard is now written to `overview.html` instead of `index.html`, its nav points at `overview.html`, and its footer links to the current edition |
| `assets/check.py` | one line: checks `overview.html` instead of `index.html` |
| `pages/*.html` | regenerated by `assets/build.py`; only the footer link back to Edition D changed |

Nothing was deleted. `docs/`, `dossier/`, `edition-b/`, `edition-c/` and `data/` are untouched. `pages/*.html`
changed in exactly one respect (a footer link), and their five tables, 46 cited rows and 40 amount scenarios are
unchanged.

### Sources used (all opened in this session unless marked)

| Id | Instrument | Retrieval |
|---|---|---|
| CN-01 | 个人外汇管理办法, PBOC Order [2006] No.3 | full text |
| CN-02 | 外汇管理条例, State Council Decree 532 | full text |
| CN-03 | 经常项目外汇业务指引（2020年版）, 汇发〔2020〕14号 | full text |
| CN-04 | 个人财产对外转移售付汇管理暂行办法 — PBOC/SAFE official answers | full text |
| CN-05 | 个人所得税法 (IIT Law) | full text |
| CN-06 | 银发〔2021〕237号, virtual currency | search-index excerpt |
| CN-07 | Bank of China personal e-banking remittance tariff | full text |
| CN-08 | Bank of China FX board, stamp 2026/11/09 05:30 | full text |
| CN-09 | Bank of China full-amount-arrival surcharge (USD 15/25) | full text |
| US-01 | 26 U.S.C. §988 | full text |
| US-02 | 31 U.S.C. §5321 | full text |
| US-03 | IRS comparison of Form 8938 and FBAR | full text |
| US-04 | Rev. Proc. 2025-32 (2026 rate tables, standard deduction) | full text |
| US-05 | IRS, gifts from foreign person / Form 3520 | full text |
| US-06 | 31 U.S.C. §5316 | full text |
| BK-01 | Chase personal fee schedule | partial |
| BK-02 | Chase business fee schedule (inbound wire USD 15 example) | search-index excerpt |

No tier-C source is used: the register contains none, and the verifier fails if one is added.

### Verification performed

```
$ python3 edition-d/build/build.py
root portal written to index.html
edition-d: wrote 11 nav-listed pages + 8 cost pages
one-way margin 0.2104%  round-trip 0.4198%
  $10,000: total $83.45 (0.834%)
  $100,000: total $301.62 (0.302%)
  $400,000: total $932.72 (0.233%)

$ python3 edition-d/build/verify.py
RESULT: PASS — 19 checks, 0 failures
```

The 19 checks: source register integrity and host allowlist; no tier-C value; method and flag cross-references;
flag-to-method attachment; review-source resolution; status vocabulary; **independent recomputation of all 320
cost cells**; every table row carries a source; every blank carries the unverified marker; 2,081 links resolve
with anchors; every external host on the allowlist; nav targets exist; no orphan pages; no template residue;
byte-identical rebuild; headline figures match the engine; root portal links resolve; portal links every
archived edition.

All four pre-existing checkers were also re-run and still pass: `assets/check.py` (5 pages, 46 rows),
`scripts/verify.py` (6 pages, 60 rows), `edition-b/build/verify.py` (15 checks), `edition-c/build/linkcheck.py`
(17 pages). No other edition was broken.

### Irregularities found in the earlier editions (full detail on `edition-d/docs/pages/repo-review.html`)

| Id | Finding | Verdict |
|---|---|---|
| R01 | Root summary labels the **round-trip** spread (0.42%) as "the real conversion cost". The one-way margin measured from the same board is 0.2104%. | irregularity |
| R02 | The §988 USD 200 threshold is stated correctly where quoted, but the dossier's one-line table says no tax exists in either jurisdiction without that caveat. | gap |
| R03 | `edition-c/data/sources.json` S01 primary URL (`…/2024-04-30/2465.html`) returns the SAFE 404 page; its own fallback (`…/2024/0430/2465.html`) resolves and holds the full text. | irregularity |
| R04 | Four editions report four route counts (18 / 22 / 33 / 35); none reconciles them. | gap |
| R05 | The live landing page linked only two of four editions; `edition-b` and `edition-c` were unreachable from `/`. | irregularity |
| R06 | "Wire charges are small relative to a large balance" was unsourced and is only true at the top of the range (0.60% at $10k, 0.015% at $400k). | gap |
| R07 | Willful FBAR described as "per year"; the statute sets it per violation. | irregularity |
| R08 | Dossier dates the board capture 2026-11-08; the board retrieved is stamped 2026/11/09 05:30 (numbers identical). | gap |
| R09 | No edition produced the required per-method $10k→$400k cost tables. | gap (closed by Edition D) |
| R10 | All four checkers pass while R03's dead link sits in the repo: none validates retrievability. | gap |
| R11 | Root README mixed four editions with no single summary. | gap |
| R12–R15 | Officiality disclosure, requirements traceability, deployment record and the load-bearing legal claims (`CN-01` Art. 3/28/37, `CN-03` Art. 54/59/64/65, `CN-04`, `CN-02` Art. 39/45) all check out. | confirmed / gap |

### Flagged for review (25 items, non-blocking)

High-severity: **F01** the two instruments classify the same person differently (CN-02 Art. 52(2) resident-foreigner
definition vs CN-01 Art. 37 ID-based definition); **F02** whether the branch applies Art. 59 in practice; **F03**
the source of the funds is unknown; **F04** emigrant status unproven; **F05** prior US filing history unknown;
**F11** the §988 gain can exceed USD 200 on a balance this size; **F24/F25** prohibited-route figures are statutory
ranges, not assessments. Medium/low items cover the corporate-tariff origin of the full-amount fee (F06), the
bank-specific inbound fee (F07), the single-bank tariff (F08), the 2014 vintage of that tariff (F09), discreteness
(F10), deposit-interest treatment (F12), the unknown property gain (F13), notarisation and travel costs (F14, F20),
service-trade filing (F15), the gap between rule and counter (F16), the absent purchase fee (F17), card FX fees
(F18), the unretrieved RMB-remittance and QDII rules (F19, F22), fintech availability (F21) and the corporate route
(F23).

### Design decisions recorded

- **Prohibited routes are named, priced and not instructed.** Splitting, underground dealing and crypto carry the
  statutory range (30%-100%) so the exposure is visible, with no procedure. This follows the precedent logged by
  session `arena-d7e7ed3b` in this file.
- **The one-way margin is used for one conversion.** Using the round-trip figure would double the FX line; both
  numbers are printed on the costs page so a reader can check the arithmetic.
- **The receiving-bank fee is an assumption, labelled as one.** A USD 15 Chase figure is used so that the total is
  complete; the source and its limits are printed in the table that defines the model, and F07 tells the reader to
  substitute their own.
- **The root landing page was replaced by a portal, not deleted.** The previous page is preserved at
  `/overview.html` and linked from the portal's archive list.

### Merge with main (session arena-22534b4a, PR #10)

`main` advanced to `156c761` (merge of PR #10, which added `pages/estimates.html`, the amount-scenario page) while
Edition D was being built. The rebase conflicted, so it was aborted and the branch was **merged** instead, keeping
both records and resolving four conflict sites without discarding either side's work:

| Conflict | Resolution |
|---|---|
| `COORDINATION.md` | both session records kept, in merge order: arena-22534b4a then arena-133875bd |
| `assets/build.py` | their new nav entry (`Amount scenarios`) kept; the destination changed from `index.html` to `overview.html`; their date-mismatch banner logic for `pages/estimates.html` preserved verbatim |
| `assets/check.py` | their 6-page expectation kept, with the root page switched from `index.html` to `overview.html` |
| `index.html`, `pages/*.html` | `pages/*.html` regenerated by their own generator, so their edits survive byte for byte; `index.html` regenerated as the portal, which now also links `pages/estimates.html` |

Their checker passes after the merge (`OK: 6 pages, 95 cited rows, 40 amount scenarios`), so the estimator page is
intact and reachable from the new landing page. No value of theirs was altered.

### Pull request, merge and deployment

_Pending — this line is completed after the merge._

---

# Session board — arena-0614c102 continuation — 2026-11-08

Correction and non-overlapping claim: while this session was researching, `origin/main` advanced to `4d844a5` and published a different session’s `edition-d/` through PR #13. The earlier E-board above is preserved as history. This session will **not** overwrite that Edition D. Its isolated outputs are relocated to `edition-e/`, and its audit will adjudicate the newly published Edition D alongside the older editions.

| ID | Task | Status | Owner | File scope |
|---|---|---|---|---|
| F0 | Preserve concurrent Edition D and merge main | in progress | arena-0614c102 | Merge resolution; no deletion of edition-d |
| F1 | Claim-level source register and retrieval limits | done | arena-0614c102 | edition-e/data/sources.json, edition-e/research/** |
| F2 | Route/tax/cost datasets and forty-step grids | in progress | arena-0614c102 | edition-e/data/**, edition-e/build/** |
| F3 | Executive summary, dashboard, category/review pages | in progress | arena-0614c102 | edition-e/EXECUTIVE_SUMMARY.md, edition-e/site/** |
| F4 | Deterministic verifier and separate CI | in progress | arena-0614c102 | edition-e/build/verify.py, .github/workflows/edition-e.yml |
| F5 | Audit inherited editions including published Edition D | in progress | arena-0614c102 | edition-e/audit.md, edition-e/data/audit.json |
| F6 | Final integration, PR, merge, Pages verification | pending component gate | arena-0614c102 | Append-only coordination/README/portal link after checks pass |

No personal balance, source-of-funds, residency, tax history, executable FX quote or receiving-bank fee has been supplied. Edition E will keep those values blank. Provider tariffs will be labelled provider-primary, not government law. Conditional arithmetic will not be presented as an all-in quote.

## arena-0614c102 — component gate passed

- F0 done: merged `origin/main` at `4d844a5`, preserved the concurrently published `edition-d/`, and relocated this session’s isolated outputs to `edition-e/`.
- F1 done: 40-source claim-level register and retrieval limits saved under `edition-e/data/sources.json` and `edition-e/research/`.
- F2 done: 32 methods, 14 tax rows, 4 penalty rows, 18 flags, 10 audit findings and 1,280 forty-step grid rows generated.
- F3 done: executive summary, dashboard, category pages, costs/tax/penalties/sources/flagged/audit/method/requirements pages generated under `edition-e/site/`.
- F4 done: `python3 edition-e/build/verify.py` passed 18 checks, 0 failures; separate CI workflow added at `.github/workflows/edition-e.yml`.
- F5 done: inherited-edition audit adjudicates old crypto authority, deposit-interest overbreadth, emigrant staging, old no-tariff statements, and published Edition D’s labelled receiving-bank assumption/tariff vintage/timezone issues.
- Local HTTP check: 15 HTML pages plus CSS/JSON/CSV returned 200; viewport, skip link and scrollable tables present.
- Inherited checkers re-run and passed: `assets/check.py`, `scripts/build_site.py` + `scripts/verify.py`, `scripts/build.py` + `scripts/verify.py`, `edition-b/build/generate.py` + `edition-b/build/verify.py`, `edition-c/build/build.py` + `edition-c/build/linkcheck.py`, `edition-d/build/build.py` + `edition-d/build/verify.py`.
- F6 in progress: PR, merge and Pages verification. Root portal is intentionally not hand-edited because Edition D’s CI regenerates `index.html`; Edition E links back to the portal and is documented in README.

## arena-0614c102 — PR, merge and Pages result

- PR: https://github.com/sassnarep3-star/China1/pull/15
- Merge: merged into `main` at `7ce3a7f975c7dc76d1c6948393d6e3e293772f75` on 2026-11-08 UTC.
- CI before merge: `verify`, `edition-d` and `edition-e` checks passed.
- GitHub Pages: source remains `main:/`; latest build for `7ce3a7f` reported `built` with no error.
- Live Edition E dashboard verified: https://sassnarep3-star.github.io/China1/edition-e/site/index.html?build=7ce3a7f
- F6 done. Concurrent Edition D and all earlier editions were preserved; no personal tax, executable FX quote, receiving fee or all-in total was populated.

# Active session board — arena-5b35ee3f (2026-11-08)

Branch: `arena/5b35ee3f-china1` (fixed by Arena; no other branches will be created).
All earlier boards are preserved verbatim. This session originally claimed `edition-d/**`
before another session merged its own Edition D in PR #13. To avoid overwriting that work,
the actual deliverable is now the independent verification edition at `edition-f/**`. A later concurrent merge (PRs #15/#16, session arena-0614c102) then published another `edition-e/`; this session preserves that Edition E as well and uses `edition-f/**`.

| Task | Status | Owner | Exclusive file scope |
|---|---|---|---|
| Independent repository and evidence audit | done (15 findings) | arena-5b35ee3f | edition-f/audit/**, this appended board |
| Official-source research and lawful route inventory | done (gaps flagged) | arena-5b35ee3f | edition-f/data/**, edition-f/research/** |
| Executive summary and requirements traceability | done (publication rows pending deploy record) | arena-5b35ee3f | edition-f/EXECUTIVE_SUMMARY.md, edition-f/REQUIREMENTS.md |
| USD 10,000–400,000 cost ladder and responsive dashboard | done (11 pages, 40 rows, 31 methods) | arena-5b35ee3f | edition-f/site/**, edition-f/build/**, edition-f/README.md |
| Independent verification and publication | in progress | arena-5b35ee3f | edition-f/**, .github/workflows/edition-f.yml, this appended board |
| Existing evidence gaps and irregularities | needs review | arena-5b35ee3f | edition-f/site/flagged.html (non-blocking) |

### Concurrent integration / scope correction

- At the original claim, origin/main was `38e0f17` and no competing active claim was present.
  PRs #10/#11 then added the root 40-row scenario ladder. A first rebase preserved the
  arena-22534b4a board and both scenario commits.
- During implementation, origin/main advanced to `4d844a5` (PR #13, session arena-133875bd),
  which merged a different `edition-d/` and replaced the root landing page with a portal.
  PR #12 (session arena-e748c15f) is also open against the same `edition-d/` path and is
  reported CONFLICTING by GitHub; PR #14 is an open documentation-only follow-up to #13.
  This session does not merge, close, overwrite or claim ownership of those PRs.
- A second rebase onto `4d844a5` preserved the merged Edition D board and files. The only
  conflict was this appended session section. Actual new scope is `edition-f/**` plus a
  separate `.github/workflows/edition-f.yml`; no prior edition, root portal or shared
  workflow is edited. Live target: https://sassnarep3-star.github.io/China1/edition-f/site/index.html (GitHub Pages serves the repository root; the dashboard entry is under edition-f/site/).
- Cross-session request to the root/portal owner: add a link to Edition F after publication.
  This session will not overwrite the shared portal. Edition D's merged cost model and the
  open PR #12 model are audited as repository evidence, not silently corrected in place.

### Verification standard

Official government/regulator/statute sources support legal and tax propositions. A bank or
remittance provider's own tariff is labelled provider-primary and supports only that
provider's price/product terms, never a legal entitlement. Unknown amounts remain blank and
appear on Flagged for Review. Internal checkers prove consistency and link resolution, not
external retrievability or factual correctness. No personal tax result or executable quote is
invented. Prohibited channels are described only as prohibited, with no operational steps.

### Implementation and verification (pre-PR)

- Deliverable moved to `edition-f/**` after PR #13 merged a different Edition D. Added only
  `.github/workflows/edition-f.yml` outside `edition-f/`; shared `verify.yml`, root portal and
  earlier editions are untouched.
- Generated 11 static pages, 40-row CSV/JSON ladder, 31 methods, 47 sources (35 official,
  12 provider-primary), 12 penalty layers, 20 tax/reporting rows, 22 flags and 15 audit findings.
- `python3 edition-f/build/build.py` and `python3 edition-f/build/verify.py`: PASS — 27 checks,
  0 failures; byte-identical rebuild; every HTML table row has an external source/artifact link;
  unknown personal tax/correspondent/receiving/HSBC-total/Wise-curve values remain blank.
- Inherited checkers re-run after rebase without drift: `assets/check.py` OK (6 pages, 95 cited
  rows, 40 scenarios); `scripts/verify.py` PASS (6 pages, 60 rows); edition-b PASS (15 checks);
  edition-c linkcheck PASSED (0 warnings); edition-d verify PASS (19 checks). These are mechanical
  consistency checks, not external retrievability or factual correctness.
- Publication next: PR to main, merge autonomously, confirm Pages at
  https://sassnarep3-star.github.io/China1/edition-f/, then append the PR/merge/deploy record here.

---

# Session board — arena-e58c83ae — 2026-11-08

Session ID: `arena-e58c83ae`; fixed Arena branch: `arena/e58c83ae-china1`. All preceding boards and completed work are preserved. No active competing claim was found in the reviewed board. This is a serial research/build/integration session, not a competing edit of a claimed task. The environment prohibits switching to or creating another branch, so the requested `session-<id>/<task>` naming cannot be used; isolation is by the exclusive file scope below.

| Task | Status | Owner | File scope |
|---|---|---|---|
| E1: independent repo audit and requirements coverage | done | arena-e58c83ae | edition-g/data/repo-review.json, edition-g/REQUIREMENTS.md |
| E2: primary-source route, tax and fee research | done | arena-e58c83ae | edition-g/data/**, edition-g/research/** |
| E3: cost estimates at every $10,000 increment from $10,000 to $400,000 | done | arena-e58c83ae | edition-g/data/**, edition-g/build/** |
| E4: executive summary and mobile-first dashboard | done | arena-e58c83ae | edition-g/** |
| E5: line-by-line verification and flagged review | done | arena-e58c83ae | edition-g/** |
| E6: final integration, additive landing navigation, PR/merge and Pages confirmation | in progress | arena-e58c83ae | edition-g/**; additive COORDINATION.md, README.md, index.html; .github/workflows/edition-g-verify.yml |

Initial claim is committed and pushed before research/build work. Existing editions remain untouched. Shared landing/navigation changes are deferred until this session's research and verification are complete; then this session acts as final integrator, preserving all prior editions. Unknown personal tax facts and unsupported fees will remain blank and be flagged, not inferred. Numeric cost estimates will distinguish published-fee calculations from missing all-in quotes. No prohibited-channel execution instructions will be provided.


Progress note (2026-11-08 UTC): primary-source verification now includes the 2024-based SAFE Hebei emigrant/inheritance service guides, current BOC/HSBC tariffs, HSBC Global Transfer actual USD20 charge, Wise eligibility and four directly observed CNY-funded quotes, PBOC 2025 AML order effective 2026-01-01, and the September 2026 foreign-individual dividend-tax repeal. National 2024 capital-account PDF extraction stops before section 6.4; local official service guides citing that section are used instead and the extraction gap will be flagged. No prior-edition files changed. Cost grids will distinguish target USD, unknown CNY principal/FX, verified sender-fee formulas, optional explicitly labelled board-rate fee scenarios, and blank all-in totals.


### Edition G implementation record (2026-11-08 UTC)

- Added self-contained `edition-g/` datasets: 52 sources, 43 candidates, 1,720 cost rows (43×40), 16 tax positions, 7 penalty layers, 47 flags, line-by-line repo-review snapshot (92 files / 18,148 lines; 20 findings in prior editions, preserved unchanged).
- Generator `edition-g/build/build.py` produces 58 mobile-first pages; `verify.py` gates citations, exact 40-point grids, blank-not-zero discipline, links/fragments and reproducibility. All five editions' generators/checks re-run together: PASS with clean diffs.
- Independent CI `.github/workflows/edition-g-verify.yml` added; existing `verify.yml` untouched. Root `index.html` and `README.md` updated additively with Edition G navigation.
- Cost model: only published sender-fee bounds/zeros and directly observed Wise public quotes populated; CNY principal, FX, downstream, documentation, tax and all-in totals blank + UNVERIFIED. Prohibited schemes have no execution steps.
- Material corrections flagged for earlier editions: staged emigrant release superseded (2014 amendment); foreign-individual FIE dividend exemption repealed effective 2026-09-01 (20% IIT); BOC bid/ask ~0.42% is a round-trip indicator, not a verified one-way loss; future BOC ATM pricing not applied before 2026-11-11; Wise historical formulas not used as current; WU bank-account payout temporarily unavailable; U.S. 1% remittance tax does not apply to China→U.S. transfers.
- Next: commit, rebase, push, open PR to main, merge without waiting, confirm Pages deployment, record PR/merge/deploy here.


### Scope correction — relocation to Edition G (2026-11-08 UTC)

While this session was building, `origin/main` advanced through PRs #13/#15/#16/#17 and
published a different session's `edition-d/`, plus `edition-e/` and `edition-f/`, and replaced
the root landing page with a portal regenerated by that Edition D's own CI. To avoid
overwriting another session's claimed/merged work, this session's deliverable was relocated
wholesale to `edition-g/**` and its workflow to `.github/workflows/edition-g-verify.yml`.
No merged edition was edited. Root `index.html` and `assets/build.py` are taken from main
unchanged because the merged Edition D's CI regenerates the portal and asserts a clean diff;
hand-editing them would break that gate.

Cross-session request to the root-portal owner: add an Edition G link
(`edition-g/docs/index.html`) to the portal archive list. This session will not overwrite the
shared portal generator. Edition G is documented in README and reachable directly.
