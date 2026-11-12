# Independent re-verification, 2026-11-12 — session `arena-162b8707`

Branch: `arena/162b8707-china1`, base `main` `0e7ba08` (PR #82). This file records exactly what was opened, on which page, on 2026-11-12, and what changed as a result. Nothing here is inferred: a figure is listed only if it was read on the publisher's own page or returned by the publisher's own API during this session.

Two limits apply to this record and are repeated on the page:

1. **Thirteen of the thirty-four sources were re-read.** The other twenty-one were not opened today; this file makes no claim about them and their entries keep the read date of the session that read them.
2. **Re-reading a page confirms its text, not your facts.** Residence, source of funds, tax already paid and filings are personal and are not known to this audit.

## 1. Priced inputs — what was re-read and what moved

| Input | Publisher page opened 2026-11-12 | What the page said | Previous edition (2026-11-11) | Effect |
|---|---|---|---|---|
| CNY/USD board | [Bank of China 外汇牌价](https://www.boc.cn/sourcedb/whpj/), published 2026/11/13 00:15:11 Beijing time (= 2026-11-12 16:15:11 UTC) | USD per 100: 现汇买入价 666.16 · 现钞买入价 666.16 · 现汇卖出价 668.97 · 现钞卖出价 668.97 · 中行折算价 671.74 | 666.30 / 666.30 / 669.11 / 669.11 / 671.91 (published 2026/11/11 10:25:02) | Midpoint 6.67565; FX margin against the midpoint 0.2100%. All 760 ladder rows and 370 recomputed totals rebuilt. |
| BOC personal tariff | [Service tariff, ch. 3 (PDF)](https://pic.bankofchina.com/bocappd/pricelist/202511/P020251110646838136627.pdf) | 210105008 cross-border remittance 1‰, minimum CNY 50, maximum CNY 260 per item, international cable CNY 150; note 5 full-amount delivery USD 15 where the receiving bank holds an account at BOC's New York branch, otherwise USD 25; 210108014 cross-border ATM 12 yuan + 1% of the amount, maximum 112 yuan; 210101002 外币携带证 10 yuan, waived 2025-04-01 to 2026-12-31 | same | No change to the fee model. The ladder keeps the USD 25 rate, i.e. the rate for a receiving bank that does **not** hold an account at BOC New York. |
| Wise quotes | [Wise public comparison API](https://api.wise.com/v3/comparisons/?sourceCurrency=CNY&targetCurrency=USD&sendAmount=66756.5) | Five quotes collected 2026-11-12T16:20:14–16:20:20Z, rate 0.149897 USD per CNY, markup 0.0: 66,756.5 CNY → fee 435.11 → USD 9,941.38; 133,513 → 846.45 → 19,886.32; 200,269.5 → 1,225.74 → 29,836.06; 267,026 → 1,571.07 → 39,790.90; 300,000 → 1,741.65 → 44,708.03 | rate 0.149807; 66,770.5 → 435.20 → 9,937.49; 133,541 → 846.63 → 19,878.55; 200,311.5 → 1,226.05 → 29,824.39; 267,082 → 1,571.46 → 39,775.34; 300,000 → 1,741.74 → 44,681.18 | Wise's rate moved up; modelled shortfall fell from $62.51 to $58.62 at $10,000 and from $224.66 to $209.10 at $40,000. The send amounts had to be re-quoted because they are derived from the BOC midpoint. |
| Receiving wire | [Chase Total Checking fees](https://www.chase.com/personal/fees/total-checking) | "Incoming Wire … $15 per transfer or $0 if the transfer was originally sent with the help of a Chase banker or using chase.com or Chase Mobile app" | same | Unchanged; still included in every BOC total. |

### Resulting headline figures (Bank of China wire → Chase, all published charges)

| Amount | New total (2026-11-12) | Share | Previous total (2026-11-11) |
|---|---|---|---|
| $10,000 | $93.40 | 0.93% | $93.39 |
| $20,000 | $124.39 | 0.62% | $124.37 |
| $30,000 | $155.37 | 0.52% | $155.35 |
| $40,000 | $185.30 | 0.46% | $185.27 |
| $50,000 | $206.30 | 0.41% | $206.27 |
| $100,000 | $311.31 | 0.31% | $311.26 |
| $200,000 | $521.34 | 0.26% | $521.24 |
| $300,000 | $731.36 | 0.24% | $731.22 |
| $400,000 | $941.39 | 0.24% | $941.20 |

Wise (own quotes, receiving-bank fee excluded): $58.62 at $10,000, $113.68 at $20,000, $163.94 at $30,000, $209.10 at $40,000. Above $40,000 the amount held in CNY exceeds Wise's CNY 300,000 per-transfer limit, so no quote exists and the cells stay blank.

## 2. Rules re-read on 2026-11-12

| Source | Page opened | What it says (as read today) | Verdict |
|---|---|---|---|
| CN-ART59 | [SAFE Tianjin Q&A 2026-07-13](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) | 汇发〔2020〕14号 art. 59: a foreign individual buying FX with lawful current-account RMB income from work in China does so at a bank on ID plus source-and-amount materials (including tax documents). | Unchanged. It states the documents, **not** any cap. |
| CN-WORKFX2025 | [SAFE Tianjin Q&A 2025-07-15](https://www.safe.gov.cn/tianjin/2025/0715/2834.html) | (1) If the lawful current-account RMB income is not taxable under the rules, no tax voucher is needed to buy FX; (2) the purchased FX may be remitted, held in the person's own FX account, or carried out under the rules. | Unchanged. |
| CN-RULES | [汇发〔2007〕1号 implementing rules](https://www.safe.gov.cn/safe/2007/0105/5320.html) | Art. 2 annual total of USD 50,000 for 结汇 and for a **domestic** individual's 购汇; art. 13(1) foreign individual's lawful current-account income bought with ID + materials incl. tax documents; art. 13(2) 24-month re-conversion window; art. 14 domestic individual's outward remittance USD 50,000/day with ID, more with authenticity documents; art. 15 a foreign individual's outward remittance **from an FX savings account** on ID. | Unchanged. Art. 15 was not previously quoted on the page; it is a rule that a foreign individual remitting FX already held in their own FX account needs only ID. It is not added to the cost model. |
| CN-MEASURES | [PBOC Order 2006 No. 3](https://www.safe.gov.cn/safe/2006/1225/5319.html) | Art. 7 no splitting to evade limits and no false documents; art. 13 foreign individual's lawful current-account income may be bought and remitted; art. 22 house-sale proceeds may be bought and remitted with SAFE approval; art. 32 FX savings account scope; art. 37 definition of 境外个人. | Unchanged. |
| CN-FXREG | [State Council Order 532](https://www.gov.cn/zhengce/2008-08/06/content_2602514.htm) | Art. 5 no restriction on current international payments and transfers; art. 12 real and lawful transaction basis; art. 39 evasion fine up to 30%, 30%–100% if serious; art. 40 illegal FX arbitrage same scale; art. 42 illegal carrying in/out up to 20%; art. 45 private FX trading up to 30%, 30%–100% if serious; art. 48 false documents up to CNY 50,000 for an individual; art. 52 definitions. | Unchanged. |
| CN-CASH | [汇发〔2003〕102号](https://www.safe.gov.cn/tianjin/2024/0430/2466.html) | Up to USD 5,000 no permit; above USD 5,000 to USD 10,000 a bank-issued permit; in principle no more than USD 10,000 equivalent may be carried out. | Unchanged. |
| CN-CARD | [汇发〔2017〕29号 notice](https://www.safe.gov.cn/safe/2017/1230/8130.html) | Overseas cash withdrawal on mainland cards: CNY 100,000 equivalent per person per calendar year; CNY 10,000 equivalent per card per day; borrowing or lending cards to circumvent is prohibited. | Unchanged. |
| US-8938FBAR | [IRS 8938 vs FBAR](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements) | FBAR threshold aggregate over USD 10,000 at any time; due 15 April with automatic extension to 15 October; 8938 thresholds by residence and filing status; 8938 penalty up to USD 10,000 plus USD 10,000 per 30 days, maximum USD 60,000. | Unchanged. The page also states the willful FBAR alternative "greater of $100,000 or 50 percent of account balances" **for assessments before 2016-08-01**, which is why F14 stays open for current assessments. |
| US-FBARPEN | [31 CFR 1010.821](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821) | Table: 31 U.S.C. 5321(a)(5)(B)(i) non-willful USD 10,000 → USD 16,536; 31 U.S.C. 5321(a)(5)(C)(i)(I) willful USD 100,000 → USD 165,353. | Unchanged (eCFR title 31 last amended 11/06/2026). |

## 3. Irregularities found today

| ID | What | Why it matters | What this session did |
|---|---|---|---|
| V-01 | The Bank of China board moved between editions (buy 666.30 → 666.16, sell 669.11 → 668.97), and it publishes on Beijing time, so its "2026/11/13" date is 2026-11-12 in UTC. | Every CNY figure and every cost total is derived from this one reading. A date read without the time zone looks like tomorrow's rate. | Refreshed `prices.json`; the page now prints both the Beijing time and the UTC equivalent; F20 re-worded. |
| V-02 | Wise's own rate moved (0.149807 → 0.149897) and the quote is only valid at the exact send amount asked, which is derived from the BOC midpoint. | Re-using yesterday's quotes against today's rate would silently drop the Wise column to blank or overstate its cost. | Five quotes re-taken at the new amounts; figures recorded in `sources.json`. |
| V-03 | The Wise help article on CNY eligibility returned `{"response":"block"}` to this session's reader on both the `/help/` and `/us/help/` URLs. | The eligibility conditions (not a mainland national, China work history, tax record within three years, send only to your own account, CNY 300,000 per transfer) are decision-critical and were **not** confirmed today. | Added **F25** and attached it to method M10. No wording changed, because nothing contradicted the earlier read. |
| V-04 | The BOC full-amount delivery charge is USD 15 only where the receiving bank holds an account at BOC's New York branch, otherwise USD 25, and the service applies only when the remittance has to pass through at least one intermediary bank. | Using USD 15 for a normal US account would understate the cost by USD 10 per wire. | No change: the ladder already uses USD 25. Recorded here so the assumption is visible. |
| V-05 | One prose figure ("$93.39 at $10,000 and $941.20 at $400,000" on the Decide page) was hard-coded text, not generated from the ladder. | It would have gone stale the moment the rate moved — which is exactly what happened today. | Replaced with build-time tokens (`{boc10k}`, `{boc400k}`) that `guide/build/build.py` fills from the same ladder the tables use. |
| V-06 | `guide/build/verify.py` only accepted read dates 2026-11-10 and 2026-11-11. | A genuine re-read today would have failed the build. | Allowed 2026-11-12 as a valid read date. The date is still required, so a source cannot silently lose its provenance. |

## 4. Not verified today

These twenty-one sources were **not** opened in this session. Their entries keep the read date shown on the Sources page; nothing in this audit should be read as confirming them:

CN-BOCFEE, PR-HSBC, PR-WISE, PR-WU, CN-PR, CN-TAXFILING, CN-PROPTRANS, CN-CAP2014, CN-SHPROP, CN-CRYPTO, CN-RMBX, CN-IIT, CN-TAXCOLL, CN-CNYCASH, US-ABROAD, US-FTC, US-FX, US-988, US-3520, US-CBP, US-REMIT.

Also open after today:

- The IRS page's willful-FBAR wording is limited to assessments before 2016-08-01; 31 U.S.C. 5321(a)(5) itself was still not opened here (F14).
- No bank other than Bank of China and HSBC China has a published tariff in this guide (F03), and HSBC China's CNY/USD rate was not obtained (F02).
- No channel limit on a single large wire was verified with the bank (F22), and the commission base is the remittance amount, not the CNY held (F19).
- Whether a US person's personal conversion produces a reportable §988 gain above USD 200, or a deductible loss, is still unverified (F13).

## 5. How to reproduce

```sh
python3 guide/build/build.py
python3 guide/build/verify.py
```

`verify.py` re-runs the build, fails if the committed pages differ, checks that every table row links an official host, that every blank cell carries a Flagged link, that the board and Wise figures appear verbatim in the quoted source text, and recomputes all 370 totals with exact fractions. It does **not** verify that a cited page still supports its quote — that is what section 1 and 2 above record, page by page, for the thirteen sources re-read today.

This is research, not legal or tax advice.
