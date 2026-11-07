# Verification and repository audit

Evidence date: **2026-11-07 UTC**. This document records how the repository was reviewed, what was verified, what remains unverified, and how to reproduce the checks.

## 1. Repository audit

The checkout began at commit `9125ed5` with only `README.md` (`# China1`). There were no pre-existing substantive entries, data files, site pages or task claims to audit line by line. All research, analysis, site and validation files were created in this session on the fixed branch `arena/489b75a1-china1`.

| Area | Files | Review result |
|---|---|---|
| Coordination | `COORDINATION.md` | Sequential claims T0–T6, branch adaptation, verification logs and publication record. |
| China evidence | `research/china.json`, `research/china-notes.md` | 21 official sources; 41 linked requirements/findings/unknowns/flags. Historical provisions labeled; amendments applied. |
| US evidence | `research/us.json`, `research/us-notes.md` | 25 official sources; 40 linked rows. Income tax, FX gain, reporting and remittance-excise scope separated. |
| Route evidence | `research/routes.json` | 29 routes; 12 additional official/primary provider sources; 33 linked rows including flags. Commercial costs null. |
| Synthesis | `research/analysis.json`, `EXECUTIVE_SUMMARY.md` | 35 linked decision/cost/scenario/myth/flag rows; conditional recommendations only; no cheapest-provider ranking. |
| Generated site | `scripts/build_site.py`, `site/`, `site/public/` | Deterministic static build; 10 pages; every rendered data row has an external source link; no remote assets. |
| Flat exports | `scripts/export_data.py`, `data/evidence.csv`, `data/sources.csv` | 165 evidence rows and 58 sources, each with source IDs and URLs. |
| Checks | `tests/test_site.py`, `.github/workflows/pages.yml` | Offline acceptance tests, deterministic rebuild, CSV integrity, Pages build/deploy workflow. |

## 2. Source policy

- **Legal/regulatory claims:** government, regulator, central-bank, tax-authority, customs, consular, IRS, FinCEN, CBP, SSA, FTC or official US Code sources.
- **Provider product claims:** the provider's own official page is primary evidence for that product only. It does not establish legal eligibility, tax treatment or availability to this user.
- **Historical rules:** labeled and read together with identified amendments. Superseded rules are not presented as current.
- **Unknowns:** user balance, income source, Chinese/US tax residence, inside/outside classification, asset history, filings, bank, destination and live quotes remain blank/null and flagged.
- **No inference:** missing prices, eligibility or tax amounts are not replaced with zero, estimates or generic marketing claims.

## 3. Key irregularities and corrections

| Issue | Resolution | Evidence location |
|---|---|---|
| Old foreign-individual FIE dividend exemption | Repealed for distributions on/after 2026-09-01; current individual rule is 20% IIT under Announcement 2026 No.27. Corporate 10% withholding is a different category. | `CN15`–`CN17`, flag `C-X01` |
| Old staged immigration/inheritance property-transfer schedule | 2014 amendment removed staged schedule; current approval guides used. | `CN07`–`CN10`, flag `C-X02` |
| USD 50,000 treated as absolute ceiling | It is a facilitation quota; documented qualifying current income and separate capital/approval routes differ. | `CN01`–`CN04`, `A-Y01` |
| Stale FEIE overview amounts | Use current IRS figuring page: 2026 maximum USD 132,900, with eligibility/proration/timing. | `US05`–`US07`, flag `U-X01` |
| Section 988 live US Code URL unavailable | Read official archived 2024 US Code PDF; currentness flag retained. | `US09`, flag `U-X02` |
| China cash-exit thresholds initially not exposed by retrieved Customs page | Resolved with PBOC RMB notice, foreign-cash rule, SAFE withdrawal Q&A and 2024 consular confirmation. Failed alternates not used. | `RT01`–`RT03`, `RT06`–`RT08`, flag `A-X03` |
| MoneyGram/Remitly outbound-China availability | MoneyGram page generic; Remitly page is US→China. Outbound products remain unverified candidates. | `PR03`, `PR04`, `R07`, `R08`, flag `R-X01` |
| Western Union delivery method | Official China page says direct bank-account delivery temporarily unavailable; cash pickup via partner bank only. | `PR02`, `R06` |
| Wise eligibility | Non-mainland-Chinese origin, work/tax-record and own-account conditions; overall limit tied to documented after-tax salary. User eligibility unverified. | `PR01`, `R05` |
| FDI detailed checklist | Amended 2012 notice main text supports genuine equity-sale/reduction/liquidation payments, but old operational attachments were repealed; no current detailed checklist inferred. | `RT05`, `R14`, `R15`, flag `R-X03` |
| New US 1% remittance excise | Verified scope concerns specified physical-instrument-funded outbound-from-US transfers, not inbound China→US wires by default. | `US25`, `A-Y09` |
| Mixed-language typo in R22 | Corrected “payment额度” to “payment quota” and rebuilt. | `research/routes.json` R22 |

## 4. Failed or insufficient retrievals (not used as evidence)

- `uscode.house.gov` section 988 URLs returned Page Not Found; wrong govinfo path 404. Correct archived 2024 govinfo PDF recorded in `US09`.
- IRS FBAR/FATCA URLs under `/individuals/international-taxpayers/` 404; correct `/businesses/...` pages fetched and recorded.
- Shenzhen口岸办 cash articles returned HTTP 500; Guangzhou Customs guide returned 404. Customs online procedure omitted collapsed thresholds. These were not cited as substantive evidence.
- PBOC PDF URL contains a 2025-looking path segment but the document is 2018 No.2; direct read confirmed attachment 2 current list. Search snippet alone was not trusted.
- Remitly `/us/en/china` redirected to a US→China sending page; generic MoneyGram agent steps did not verify outbound-China eligibility/pricing.

## 5. Reproduce the checks

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/export_data.py
.venv/bin/python -m unittest discover -s tests -v
node --check site/app.js
```

The tests are offline. They validate JSON/source integrity, blank unverified values, rendered row coverage, source links on every data row, internal link resolution, absence of remote assets/placeholders, CSV exports and deterministic rebuild. They do **not** re-fetch external government/provider pages; source verification was performed during research and recorded with URLs, locators, access notes and verification dates.

## 6. Publication rule

Flagged/unverified items are published on `flagged.html` and do not block integration. The site must still pass build and structural checks before merge/deploy. No broken site is merged.
