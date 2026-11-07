# Executive summary

**Question.** A US citizen holds CNY in a mainland Chinese bank account and reports being unable to convert it to USD "without paying a considerable amount of taxes."

**Answer in one sentence.** There is no tax on converting or transferring your own money in either jurisdiction; the real cost of a lawful conversion is a bank spread of about **0.42%**; the real barrier is China's *capital-account* inconvertibility, not tax; and the only genuinely large exposure in the whole picture is **US non-reporting**, where the willful-FBAR penalty is the greater of USD 100,000 or **50% of the account balance, per year**.

Evidence for every claim below, with links to the instrument, is in [`scripts/data_sources.py`](scripts/data_sources.py) and on the live site's *Sources* page. Values that could not be confirmed from an official page are left **blank** and published on the *Flagged for review* page.

---

## 1. The premise is the most expensive part of the problem

The brief assumes a large Chinese or US tax on the conversion. Tested against the instruments, no such tax exists:

| Proposition | Position | Source |
|---|---|---|
| China taxes the exchange of CNY for USD | **No.** The Individual Income Tax Law charges nine enumerated categories of *income*; a currency exchange is not one of them. | 个人所得税法 Arts. 2–3 — [CN-14](https://tianjin.chinatax.gov.cn/11200000000/0300/030004/03000418/20260727143202317.shtml) |
| China taxes remitting your own principal abroad | **No.** Remittance is regulated by the FX Regulations (permits, quotas, authenticity review) which impose *administrative penalties for evasion* — not a levy. | 外汇管理条例 (State Council Order 532) — [CN-08](https://www.gov.cn/zhengce/2008-08/06/content_2602514.htm) |
| The US taxes money arriving in your own US account | **No.** A transfer between accounts you own is not income, not a gift, not an inheritance. | IRC §988(e)(2) — [US-04](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section988&num=0&edition=prelim) |
| The US taxes the FX gain on conversion | **No**, for a personal transaction: gain is not recognised unless it would exceed USD 200. Losses are not deductible. | IRC §988(e)(2) — [US-04](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section988&num=0&edition=prelim) |

Where the 20% that people actually encounter comes from: **Chinese IIT on the underlying income** — property transfer gains (20% of the gain), interest and dividends (20%), already withheld at source. If the balance in the account came from selling a Chinese property, that 20% was always owed and no remittance channel avoids it. If it came from salary, the tax was already paid in China — which is precisely why remitting it later is not a second taxable event.

## 2. The real conversion cost is about 0.42%

Bank of China's published board on 2026-11-08 quoted USD at 现汇买入价 666.48 and 现汇卖出价 669.29 CNY per 100 USD ([CN-11](https://www.boc.cn/sourcedb/whpj/)). The spread is:

> (669.29 − 666.48) ÷ 669.29 = **0.4199%**

On CNY 1,000,000 that is about **CNY 4,200**. Wire charges are additional and are small relative to a large balance. Four cost lines — outbound commission, correspondent charges, the receiving bank's inbound fee, and notarisation cost — could not be verified from an official page, so they are left blank rather than estimated.

## 3. The binding constraint is legal, not fiscal

`个人外汇管理办法` Art. 3 splits individual FX business into:
- **Current account** — administered on the *convertibility* principle. Freely convertible.
- **Capital account** — administered "according to the process of convertibility", i.e. gradually, by approval. ([CN-01](http://m.safe.gov.cn/safe/2006/1225/5319.html))

Using the annual USD 50,000 quota is a *current-account convenience*. Parking savings abroad is a *capital-account act*. That distinction, not tax, is why the money is stuck.

## 4. One fact decides everything: how the bank classifies the holder

| | 境内个人 (PRC resident ID) | 境外个人 (US passport) |
|---|---|---|
| USD 50,000 annual purchase quota | **Applies** | **Does not appear in the rule text** for purchases against lawful China-source RMB income (汇发[2020]14号 Art. 59) |
| Documentation | ID only within quota; purpose documents above it | ID **plus source-of-funds materials including tax vouchers** |
| Remitting FX already held | USD 50,000/day, then documents (Art. 64) | ID alone (Art. 65) |
| Whole-balance exit | Capital-account route only | Capital-account route only |

Sources: [CN-01](http://m.safe.gov.cn/safe/2006/1225/5319.html) (Art. 37 defines the two categories), [CN-02](https://www.safe.gov.cn/hebei/2015/0514/422.html), [CN-03](https://www.gov.cn/gongbao/content/2020/content_5560296.htm).

**Irregularity worth flagging (F02):** a naturalised US citizen often still holds an un-cancelled 户口 and a live 居民身份证. Chinese nationality is lost automatically on voluntary acquisition of another nationality while settled abroad (`国籍法` Art. 9, confirmed by the National Immigration Administration — [CN-17](https://www.nia.gov.cn/Enquiry/publish/showQuestion.jsp?MZ=9PQAMhZWr6Zk9fibcZHJMA%3D%3D)). An account still classified as 境内个人 is therefore both a compliance problem *and* the reason the holder is trapped behind the USD 50,000 quota.

## 5. The five routes that matter

| Route | What it is | Cap in the rule text | Best for |
|---|---|---|---|
| **A3 / A4** | 境外个人 buys FX against lawful China-source RMB income, then remits | **No annual cap in the rule text**; ID + source documents | A US citizen whose balance is already-taxed Chinese income |
| **B1** | 移民转移 — emigration asset transfer (PBOC Announcement [2004] No. 16) | Whole declared balance, staged: 50%, then half the remainder after a year, the rest after two; ≤ CNY 200,000 may go in one release | A whole balance, for someone who has genuinely emigrated and can produce hukou cancellation + a consular settlement certificate |
| **A7** | 境外个人 repatriates property-sale proceeds | The sale proceeds, with SAFE approval | A property-funded balance (20% IIT on the gain is unavoidable) |
| **B2** | 继承转移 — inheritance transfer | The whole estate, declared once | Inherited assets |
| **C3 / E3** | Spend it abroad on a mainland-issued card | No stated cap; consumes no quota | Recurring USD expenses — often the highest-value practical move |

Sources: [CN-03](https://www.gov.cn/gongbao/content/2020/content_5560296.htm), [CN-06](https://www.gov.cn/gongbao/content/2005/content_64294.htm), [CN-07](https://www.safe.gov.cn/safe/2004/1116/4134.html), [CN-12](https://www.bankofchina.com/custserv/cs5/201712/t20171231_11032383.html).

## 6. Two facts that are commonly missed

- **The USD 50,000 line is per *day*, not per year, for *remitting* FX you already hold.** 汇发[2020]14号 Art. 64 sets a USD 50,000/day cumulative threshold on ID alone. The USD 50,000 *annual* figure is the *purchase* quota. These are different limits and are routinely conflated. ([CN-03](https://www.gov.cn/gongbao/content/2020/content_5560296.htm), [CN-04](https://www.safe.gov.cn/tianjin/2026/0422/3039.html))
- **Above the annual quota, a current-account purchase is still possible** with genuine purpose documents. SAFE restated this in 2026: the quota is a *convenience tier*, not an absolute ceiling, for current-account uses. ([CN-05](https://www.safe.gov.cn/tianjin/2026/0706/3085.html))

## 7. The penalty ladder

| Conduct | Penalty | Source |
|---|---|---|
| 逃汇 — evading FX controls to move capital abroad | Fine ≤ 30% of the amount; **30%–100%** if serious; criminal referral where the threshold is met | 条例 Art. 39 — [CN-08](https://www.gov.cn/zhengce/2008-08/06/content_2602514.htm) |
| Underground banks / mirror trades | Warning, confiscation, fine ≤ 30% of the amount or 30%–100% if serious | 条例 Art. 45 — [CN-08](https://www.gov.cn/zhengce/2008-08/06/content_2602514.htm) |
| Splitting across relatives' quotas | Prohibited by name; 关注名单 watch-listing, written risk notice at the counter | 汇发[2020]14号 Arts. 62–63 — [CN-03](https://www.gov.cn/gongbao/content/2020/content_5560296.htm) |
| Crypto / stablecoin bridge | Illegal financial activity — prohibited outright | 银发〔2021〕237号 — [CN-16](http://www.news.cn/2021-09/24/c_1127898838.htm) |
| Undeclared cash at the US border | **Entire** amount exposed to seizure, not just the excess; structuring is a separate offence | 31 U.S.C. §5316/5317 — [USB-12](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title31-section5316&num=0&edition=prelim) |
| **Willful FBAR failure** | **Greater of USD 100,000 or 50% of the account balance**, per year | 31 U.S.C. §5321(a)(5)(C) — [US-03](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title31-section5321&num=0&edition=prelim) |
| Non-willful FBAR failure | Up to USD 10,000 per report, inflation-adjusted | [US-01](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements) |

Note the asymmetry: the Chinese exposure is a percentage of *what you moved*; the US exposure is a percentage of *the whole balance*. That is why the reporting question must be resolved **before** the transfer question.

## 8. The US reporting stack — four parallel obligations

| Filing | Trigger | Penalty ceiling |
|---|---|---|
| FinCEN Form 114 (FBAR) | Aggregate foreign accounts > USD 10,000 at any point in the year | Non-willful USD 10,000; willful greater of USD 100,000 or 50% of balance |
| Form 8938 | Specified foreign financial assets above the filing-status threshold | USD 10,000 + USD 10,000 per 30 days after notice, max USD 60,000 |
| Schedule B, Part III | Any foreign financial account | Accuracy-related exposure |
| Form 3520, Part IV | Gifts/bequests from foreign persons above the threshold | 5% per month, capped at 25% |

Sources: [US-01](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements), [US-05](https://www.irs.gov/forms-pubs/about-form-3520), [US-07](https://www.irs.gov/forms-pubs/about-form-schedule-b-form-1040).

**A trap specific to the *form* of the holding:** if the CNY is not in a deposit but in a Chinese fund or investment-linked insurance policy, it is very likely a PFIC for a US person, and the US tax cost can far exceed everything else in this document ([US-09](https://www.irs.gov/individuals/international-taxpayers/foreign-investment-entities)). Identify the product before doing anything.

## 9. Recommended sequence

1. **Establish the classification.** Ask the bank, in writing, for the account's 账户主体类别 and which ID document is on file. *(Flag F01)*
2. **Fix the US filing position first.** Confirm the FBAR / Form 8938 / Schedule B history before any large inbound transfer. *(Flag F04)*
3. **Identify the source of funds, tranche by tranche.** Salary → A3/C3. Property → A7 (+ 20% IIT on the gain). Inheritance → B2. Unused inward remittance → A6. Untraceable → nothing moves. *(Flag F03)*
4. **Choose the route that matches the source**, not the route that is cheapest in spread — because the spread is 0.42% and the wrong route is 30%–100%.
5. **Convert once and wire directly.** Never convert twice. Avoid cash: it is the most expensive form and triggers a US reporting duty above USD 10,000.
6. **Report the arrival year.** The Chinese account stays reportable for every year it exists, including the year it is emptied.
7. **Do not use group D.** Splitting, underground banking, stablecoins, fabricated invoices and undeclared cash convert a 0.42% cost into a 30%–100% or 50%-of-balance loss.

## 10. What remains unverified

Twenty items are published on the *Flagged for review* page rather than filled in. The ones that change the answer:

- **F01** — how the bank classifies the account holder *(determines whether the USD 50,000 quota applies at all)*
- **F02** — whether a PRC resident identity is still in use by a US citizen *(a compliance problem and the likely cause of the trap)*
- **F03** — the source of the funds *(determines which route is even available)*
- **F04** — whether prior FBAR / 8938 filings were made *(the only 50%-of-balance exposure)*
- **F05** — whether the balance is a deposit or a fund/insurance product *(PFIC)*
- **F06** — wire, correspondent and inbound fees *(deliberately blank; no official tariff retrieved)*
- **F07** — the exact "prohibited uses" wording for quota purchases *(not retrieved from a tier-A page, so not quoted)*

## 11. Scope and limits

- This is a **research dossier, not legal, tax or investment advice**. Application to a person's facts requires a PRC-qualified lawyer for the China side and a US CPA or tax attorney for the US side — routinely done as a pair.
- Criminal, as distinct from administrative, exposure for individuals is **outside scope**. The administrative fine bands above are ceilings, not predictions; the Regulations leave the amount to the authority's discretion.
- 35 routes are mapped, including 8 unlawful ones. Documenting a prohibited route and its statutory penalty is not an endorsement of it.
- The FX spread is a **snapshot dated 2026-11-08**; the structure of the cost is stable, the number is not.

---

*Published site: <https://sassnarep3-star.github.io/China1/> · Method: [methodology](docs/methodology.html) · Full route table: [channels](docs/channels.html) · Unverified items: [flagged](docs/flagged.html)*
