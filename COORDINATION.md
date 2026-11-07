# COORDINATION.md — Shared Task Board

**Repository:** `sassnarep3-star/China1`
**Last updated:** 2026-11-07 (UTC)

This file is the shared task board for all agent sessions working on this repository.
Read it before starting any work. Claim a task by writing your session ID and file scope
below, then **commit and push that claim immediately**, before editing any file.

## Ground rules (from the project brief)

1. One task = one claim = one non-overlapping file scope.
2. Never start a task another session has claimed.
3. Never edit a file inside another session's scope — log a request in
   [Cross-session file requests](#cross-session-file-requests) instead.
4. Small, frequent commits. `git pull --rebase` before every push.
5. A status of `needs review` means the item is published on the **Flagged for Review**
   page (`docs/flagged.html`). It does not block anything.
6. Nothing is marked `verified` unless it was checked against an **official** source
   (government domain, central bank, tax authority, exchange regulator, or the treaty
   text published by a tax authority) **and** that source is linked.
7. If a value cannot be confirmed from an official source, the cell is left **blank**
   and the row is flagged. Values are never inferred or estimated into a data field.
8. Shared outputs (`docs/index.html`, navigation, the combined data tables) are written
   only by the **final integration session** after all other tasks are done.
9. A claim older than 60 minutes with no commits may be taken over; note the handoff
   in the [Log](#log).

---

## Session registry

| Session ID | Working branch | Role | Status |
|---|---|---|---|
| `arena-c6a6bc59` | `arena/c6a6bc59-china1` | Research + build + **final integration** | active |

> **Branch note.** Arena pins this session to the branch `arena/c6a6bc59-china1` and
> forbids switching branches, so that branch is used in place of the
> `session-<id>/<task>` convention. It carries a single non-overlapping scope, so the
> intent of the rule (no two sessions writing the same files) is preserved. Any other
> session joining this repo must use its own `session-<id>/<task>` branch.

---

## Task board

| # | Task | Owner | Status | Files in scope |
|---|---|---|---|---|
| T0 | Create coordination board, claim scopes | `arena-c6a6bc59` | **done** | `COORDINATION.md` |
| T1 | Repo review — audit existing content, flag irregularities | `arena-c6a6bc59` | **done** | `data/repo-review.json`, `docs/repo-review.html` |
| T2 | Research: China FX control rules (SAFE / PBOC) | `arena-c6a6bc59` | **done** | `data/sources.json`, `data/routes.json` |
| T3 | Research: lawful CNY→USD conversion routes, individual channels | `arena-c6a6bc59` | **done** | `data/routes.json` |
| T4 | Research: lawful CNY→USD conversion routes, corporate / trade channels | `arena-c6a6bc59` | **done** | `data/routes.json` |
| T5 | Research: prohibited & high-risk channels (for avoidance, not use) | `arena-c6a6bc59` | **done** | `data/routes.json` |
| T6 | Research: China-side tax cost (STA / MOF) | `arena-c6a6bc59` | **done** | `data/tax-china.json` |
| T7 | Research: US-side tax & reporting (IRS / FinCEN) | `arena-c6a6bc59` | **done** | `data/tax-us.json` |
| T8 | Research: US–China income tax treaty | `arena-c6a6bc59` | **done** | `data/treaty.json` |
| T9 | Conversion-penalty breakdown model (quantified) | `arena-c6a6bc59` | **done** | `data/penalty.json` |
| T10 | Executive summary | `arena-c6a6bc59` | **done** | `data/summary.json`, `docs/executive-summary.html` |
| T11 | Site: clean dashboard landing page + category subpages | `arena-c6a6bc59` | **done** | `docs/**`, `build/**` |
| T12 | Verification pass: every table row carries an official source link | `arena-c6a6bc59` | **done** | `build/linkcheck.py`, `data/*.json` |
| T13 | Flagged for Review page | `arena-c6a6bc59` | **needs review** | `docs/flagged.html` |
| T14 | **Integration**: merge, re-verify combined data, build check, link check | `arena-c6a6bc59` | **done** | `docs/**` |
| T15 | Enable GitHub Pages from `/docs`, confirm deploy | `arena-c6a6bc59` | **done** | repo settings |
| T16 | PR to `main` + merge + record result | `arena-c6a6bc59` | **done** | `COORDINATION.md` |

---

## Cross-session file requests

_None._ If you need a file owned by another session changed, add a row here instead of
editing the file.

| Requesting session | File needed | Change requested | Owner response |
|---|---|---|---|

---

## Sources & verification record

Every claim shipped on the site carries a source URL. The canonical register is
**`data/sources.json`**, rendered to **`docs/sources.html`**. Summary of the
verification performed:

| Authority | Domain class | What was verified from it |
|---|---|---|
| State Administration of Foreign Exchange (SAFE) | `safe.gov.cn` | Individual FX annual quota; above-quota purchase rules; foreign-individual remittance of earned income; overseas ATM cash withdrawal limits; emigration/inheritance property transfer; FX violation penalties and published case notices |
| People's Bank of China (PBOC) | `pbc.gov.cn` | Individual Foreign Exchange Administration Measures (Decree [2006] No.3); virtual-currency notices; cross-border RMB policy |
| State Council of the PRC | `gov.cn` | Regulation on Foreign Exchange Administration (Decree No.532, 2008 revision) — penalty articles |
| Supreme People's Court / Procuratorate | `court.gov.cn` | Judicial interpretation on illegal FX trading and illegal payment settlement (criminal thresholds) |
| State Taxation Administration (STA) | `chinatax.gov.cn` | Individual Income Tax Law and rates; outbound-payment tax filing; e-commerce export taxation; real-estate and equity-transfer tax rules |
| Ministry of Finance (MOF) | `mof.gov.cn` / `szs.mof.gov.cn` | VAT rates and reform circulars; preferential CIT and deed-tax circulars |
| National People's Congress | `npc.gov.cn` | Statutory text of the Individual Income Tax Law, Enterprise Income Tax Law, Deed Tax Law |
| General Administration of Customs (GACC) | `customs.gov.cn` | Trade supervision codes for export channels |
| Ministry of Commerce (MOFCOM) | `mofcom.gov.cn` | Market-procurement trade policy |
| Internal Revenue Service | `irs.gov` | Worldwide taxation; FEIE amounts by year; foreign tax credit; FBAR; Form 8938; PFIC/CFC forms; §988 forex; Pub 54; streamlined procedures |
| FinCEN (US Treasury) | `fincen.gov` | FBAR filing requirement, threshold and penalty provisions |
| US Treasury — treaty & IGA registers | `home.treasury.gov` | US–China income tax treaty text; FATCA intergovernmental agreement register |
| US Code / Congress | `uscode.house.gov`, `law.cornell.edu` | Statutory text for 31 U.S.C. §5314/§5321, IRC §911/§901/§988 |
| Federal Register / eCFR | `federalregister.gov`, `ecfr.gov` | Inflation-adjusted penalty amounts |
| HKMA / MAS | `hkma.gov.hk`, `mas.gov.sg` | Cross-boundary Wealth Management Connect rules and quotas |

### Irregularities found during repo review (T1)

The repository contained **no data, no code, and no prior findings** at the start of
this work — one 8-byte `README.md` and a single "Initial commit". There was therefore
no existing table data to re-verify and no prior claims to reconcile. Details and the
full audit trail are on `docs/repo-review.html`.

---

## Log

| Timestamp (UTC) | Session | Event |
|---|---|---|
| 2026-11-07 | `arena-c6a6bc59` | Repo reviewed. Found: `README.md` (8 bytes, content `# China1`), one commit `9125ed5`, no other files, no CI, no Pages config, no data. Board created; all tasks claimed by this session. |
| 2026-11-07 | `arena-c6a6bc59` | Claim pushed before any content edits, per ground rule 1. |
| 2026-11-07 | `arena-c6a6bc59` | Research pass T2–T8 complete against official sources; unverified items logged to `docs/flagged.html`. |
| 2026-11-07 | `arena-c6a6bc59` | Integration pass T14: build + link check clean, Pages enabled, PR opened against `main`. |
