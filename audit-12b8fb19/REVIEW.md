# Independent release audit — 2026-11-10 UTC

Scope: the consolidated portal at commit `93a6757745e2cb5912d36cd33eb71730be8695d6`, its automated verification, and the specific official sources below. This is a targeted audit, **not** an independent line-by-line legal or factual certification of every row, archived edition, or external link in the repository. The existing site contains earlier research logs and flags; those logs are not proof that this session independently rechecked each claim.

## Directly inspected official sources

| Subject | Check performed | Source | Limitation / review |
|---|---|---|---|
| Foreign-exchange quota | Read SAFE's 2007 English Q&A; its question distinguishes domestic individual foreign-exchange purchase from individual settlement and mentions a USD 50,000 annual quota. | [SAFE Q&A](https://www.safe.gov.cn/en/2007/0105/819.html) | Historical interpretation; not evidence that every U.S. citizen has an unconditional purchase quota. Confirm current classification and applicable rules with the bank. |
| Foreign permanent resident ID | Read the 2017 SAFE English circular: holders are eligible for the USD 50,000 annual quota for settlement and purchase. | [SAFE circular](https://www.safe.gov.cn/en/2017/1129/1365.html) | Whether this individual holds the required card is unknown; English text says Chinese prevails. |
| Foreign account reporting | Read IRS FBAR page: U.S. persons meeting its financial-interest/authority test file when aggregate foreign-account value exceeded USD 10,000 at any point during the year. | [IRS FBAR](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar) | Threshold applies to aggregate accounts and is not a transfer tax. Exceptions, filing history and any actual penalties are case-specific. |
| Business transaction authenticity | Read Articles 7 and 11 of the 2020 SAFE current-account guideline: genuine, lawful trade basis is required; banks review authenticity and transaction documentation. | [State Council Gazette, SAFE guidelines](https://www.gov.cn/gongbao/content/2020/content_5560296.htm) | Not a license to relabel personal funds as trade; subsequent amendments and local implementation require confirmation. |

## Automated checks run

- `python3 integration/verify.py`: PASS; 7 consolidated pages, 142 sourced rows, 40 target amounts, 160 independently recomputed fee values, 43 method links, 223 HTML files / 20,119 local references, deterministic rebuild.
- `python3 edition-i/build/verify.py`: 1,868 checks, 0 errors.
- `python3 assets/check.py`: PASS; 6 pages, 95 cited rows, 40 scenarios.
- `python3 edition-d/build/verify.py`: 19 checks, 0 failures.

These validators check their stated structural and arithmetic properties. They do not establish current external-link availability, legal effect of every source, actual eligibility, live FX execution, all-in price, tax liability, or user-specific penalty. Provider tariff citations are first-party pricing evidence, not official government confirmation of an executable quote. Some archived editions use scenario assumptions; review their caveats before relying on their estimates.

## Unresolved material items

- Source, ownership and tax history of the funds, Chinese FX classification, prior conversions, dates and destination account are unknown; no best personal route or final cost can be calculated honestly from the prompt alone. Published blanks are not zero costs.
- No contemporaneous binding quote from the banks or service providers was obtained. Published sender-fee illustrations exclude unknown FX execution and downstream charges, and do not establish a guaranteed net USD receipt.
- Full repository-wide line-by-line verification and independent checking of every cited external source were not completed by this session. The site already publishes its [Flagged for Review](../integration/review.html) and [Edition I flags](../edition-i/site/flagged.html); those flags remain open, not silently certified.
- GitHub Pages API reported `built` for the existing main-branch site at the start of this audit. A new deployment must be checked after this audit's merge.
