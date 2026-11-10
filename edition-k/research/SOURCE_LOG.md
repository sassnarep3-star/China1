# Retrieval log — Edition K, 2026-11-10

Every page below was requested directly from its publisher during this session. Where a
URL failed, the failure and the replacement are recorded — a 404 is evidence about the
source, and hiding it would make the register look cleaner than the research was.

Legend: **OK** = retrieved and read; **404** = publisher returned not found, not used;
**SHELL** = retrieved but the content is generated client-side, so no figure could be
read from it.

## Chinese official sources

| URL | Result | What was extracted |
|---|---|---|
| `pbc.gov.cn/zhengcehuobisi/125207/125217/125925/2026111008593664671/index.html` | OK | Central parity for 2026-11-10: 1 USD = 6.7167 CNY, plus the whole currency table |
| `pbc.gov.cn/zhengcehuobisi/125207/125217/125925/index.html` | OK | Confirms the 2026-11-10 announcement is the latest and lists 3,021 historical announcements |
| `boc.cn/sourcedb/whpj/index.html` | OK | USD row, stamp 2026/11/10 17:39:58: bid 665.71, ask 668.51, cash bid/ask identical, 折算价 671.67 per 100 USD |
| `boc.cn/ebanking/service/cs1/200905/t20090506_990712.html` | OK | Cross-border telegraphic transfer 1‰, min CNY 50, max CNY 260, cable CNY 150 (non-HK/Macau/Taiwan); note 1 on local variation |
| `safe.gov.cn/safe/2007/0105/5320.html` | OK | Huifa [2007] No.1 in full: Art. 2 annual total, Arts. 10/11/12/13/14/15, Art. 30 cash withdrawal filing, and the note that Art. 39 was repealed by Huifa [2023] No.8 |
| `safe.gov.cn/safe/2004/1116/4133.html` | OK | 2004 interim measures: emigrant and inheritance transfer definitions, evidence lists, Art. 6 staged release |
| `safe.gov.cn/tianjin/2024/0903/2594.html` | OK | Huifa [2014] No.2 §6: staged release, CNY 500,000 filing and notarisation requirements all cancelled |
| `gov.cn/flfg/2008-08/06/content_1066336.htm` | OK (chunk 2) | State Council Order 532 Arts. 39, 40, 41, 42, 43, 44, 45, 46, 47, 48 and the Art. 52 definitions |
| `m.safe.gov.cn/safe/2003/0828/22157.html` | OK | Huifa [2003] No.102: USD 5,000 permit-free, 5,000–10,000 bank certificate, above 10,000 in principle prohibited |
| `chinatax.gov.cn/eng/c102962/c102967/c102997/c103004/c5245849/content.html` | OK | IIT Law Arts. 1, 2, 3 and 4 |
| `chinamoney.com.cn/chinese/bkccpr/` | SHELL | Navigation only; the rate table is script-rendered, so the PBOC announcement page was used instead |

## US official sources

| URL | Result | What was extracted |
|---|---|---|
| `irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar` | OK | FBAR who/threshold ($10,000 aggregate), due 15 April, automatic extension to 15 October, penalty note |
| `irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements` | OK | 8938 thresholds for US-resident and abroad filers; penalty structure up to $60,000 |
| `irs.gov/businesses/gifts-from-foreign-person` | OK | $100,000 aggregate threshold for nonresident-alien gifts; $20,116 for 2025 and $20,573 for 2026 for foreign corporations/partnerships; due dates |
| `irs.gov/individuals/international-taxpayers/foreign-tax-credit` | OK | Credit vs deduction, Form 1116, limitation caveats |
| `irs.gov/individuals/international-taxpayers/us-citizens-and-resident-aliens-abroad` | OK | Worldwide income; Form 3520 triggers; virtual-currency reporting |
| `govinfo.gov/.../USCODE-2024-title26-...-sec988.htm` | OK (chunks 0, 2, 3) | §988(a), (c), and (e) including the $200 personal-transaction threshold. Retrieved from GPO after noting that the 2024 edition is the current published compilation. |
| `fincen.gov/resources/statutes-regulations/administrative-rulings/fincen-form-105-currency-and-other-monetary` | OK | CMIR requirement above $10,000 in aggregate at one time, in either direction |
| `cbp.gov/travel/international-visitors/know-before-you-visit/currency` | 404 | Not used. Replaced by the FinCEN ruling above. |
| `fincen.gov/sites/default/files/shared/FinCEN105.pdf` | 404 | Moved; the administrative-ruling page was used instead of the blank form |

## Provider sources

| URL | Result | What was extracted |
|---|---|---|
| `hsbc.com.cn/.../tariff-of-accouts-and-services.pdf` | OK (6 chunks; fee tables in chunks 2–3) | Effective 2026-10-31. Outward TT 0.1% min CNY 100 max CNY 500; cable CNY 120; Global Transfers free for Premier; inbound TT free for Premier; FX drafts discontinued 2019-12-01 |
| `wise.com/help/articles/2955298/guide-to-cny-transfers` | OK | Eligibility (non-mainland-Chinese, China work history, tax record showing tax paid within 3 years), CNY 300,000 per transfer from the bank app, CNY 50,000 from Alipay, own-account only, overall limit = net salary |
| `chase.com/personal/fees/secure-checking` | OK | "$15 per transfer" for incoming domestic and international wires |
| `chase.com/content/dam/chase-ux/documents/personal/checking/chase-deposit-account-agreement.pdf` | 404 | Not used |
| `irs.gov/individuals/international-taxpayers/foreign-currency-and-foreign-currency-transactions` | 404 | Not used; §988 and the FBAR/8938 pages cover the same ground |

## How the numbers were built

1. `SELL = 6.6851` (BOC ask, S02) converts a USD target into the CNY that must be raised.
2. `HALF_SPREAD = ((6.6851 − 6.6571) / 2) / 6.6711 = 0.2098604%` — both quotes from the
   same BOC snapshot, so no timing mismatch enters the figure. Checked independently in
   `verify.py` against the two published quotes.
3. BOC commission `= min(max(0.001 × CNY, 50), 260)`, cable `= CNY 150`, US receiving
   `= $15`, all converted at `SELL`.
4. All-in `= (spread cost in USD) + commission + cable + receiving`.
5. Tax is never added to all-in, because it is a function of the underlying event rather
   than of the transfer. It is presented separately with its statutory rate.

## What was deliberately not done

- No figure was taken from a blog, forum, news article, comparison site or AI summary.
- No provider fee was invented where the provider publishes only a quote-time price.
- No FX spread was borrowed from one bank and applied to another.
- No tax amount was computed by applying a rate to a balance whose basis is unknown.
