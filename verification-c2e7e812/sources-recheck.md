# Per-source re-check notes — arena-c2e7e812, 2026-11-11 ~12:55–13:05 UTC

Method: each official page was looked up with web search restricted to official
domains, and the returned official-page excerpts were compared with the text stored in
`guide/data/sources.json`. Excerpts below are the text the check was based on.

## CN-FXBOARD — Bank of China FX board (PASS, time-specific)

- Official board page reachable at `boc.cn/sourcedb/whpj/`.
- Reading observed in search index: USD 现汇买入价 666.41 / 现汇卖出价 669.22,
  published 2026/11/09 10:04:51. Guide uses its own dated reading of
  2026-11-11 10:25:02 Beijing (buy 666.30, sell 669.11). Both are snapshots of a
  continuously moving board; the site labels its snapshot and flags it (F20). The
  board note ("the rate at the actual transaction applies") matches the recorded quote.
- https://www.boc.cn/sourcedb/whpj/

## CN-ART59 — SAFE Tianjin Q&A, 2026-07-13 (PASS)

- Official page text: 「境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇」 quoting 汇发〔2020〕14号 第五十九条. Identical to the recorded quote.
- https://www.safe.gov.cn/tianjin/2026/0713/3088.html

## SAFE Tianjin Q&A, 2026-05-11 (PASS)

- Foreign Permanent Resident ID Card holders get the annual facilitation quota per
  art. 59. Matches CN-PR usage.
- https://www.safe.gov.cn/tianjin/2026/0511/3051.html

## CN-FXREG — FX Regulation, State Council Order 532 (PASS)

- Official gazette text observed at `gov.cn/gongbao/content/2008/content_1071846.htm`
  and `gov.cn/flfg/2008-08/06/content_1066336.htm` (same regulation the guide cites at
  `gov.cn/zhengce/2008-08/06/content_2602514.htm`):
  - Art. 39 逃汇: 责令限期调回 + 处逃汇金额30%以下的罚款; 情节严重 30%以上等值以下; 犯罪追究刑事责任.
  - Art. 40 骗购外汇 (false/invalid documents): 30%以下; 严重 30%以上等值以下.
  - Art. 42 违反规定携带外汇出入境: 警告 + 20%以下.
  - Art. 45 私自买卖外汇/变相买卖外汇: 没收违法所得 + 30%以下; 严重 30%以上等值以下.
- Matches every `china_penalties` row in `guide/data/taxes.json`.

## CN-MEASURES / CN-RULES — PBOC Order 2006 No. 3 + 2007 implementation rules (PASS)

- Art. 7: 「不得以分拆等方式逃避限额监管，也不得使用虚假商业单据或者凭证逃避真实性管理」 — splitting *to evade limits* is banned; this is the only splitting wording the guide uses.
- Implementation rules art. 2: annual totals of USD 50,000 equivalent per person per year for both sale and (domestic individual) purchase of FX; art. 13: foreign individual's purchase is document-driven.
- https://www.safe.gov.cn/safe/2006/1225/5319.html · https://www.safe.gov.cn/safe/2007/0105/5320.html

## US-FBARPEN — 31 CFR 1010.821 + 31 USC 5321 (PASS)

- Penalties assessed on/after 2025-01-17: non-willful up to $16,536; willful = greater
  of $165,353 or 50% of the account balance (statute: 31 USC 5321(a)(5)(C)–(D)).
- Matches the taxes page figures plus flag F14 (the 50% alternative).
- https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821 · https://www.govinfo.gov/link/uscode/31/5321

## US-8938FBAR — IRS comparison page (PASS)

- FBAR: aggregate value exceeds $10,000 at any time in the calendar year; filed with
  FinCEN, not with the tax return. Form 8938 thresholds (US resident / abroad,
  single / joint): $50k/$75k, $100k/$150k, $200k/$300k, $400k/$600k — as recorded.
- https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements

## US-988 — 26 USC 988 (PASS)

- §988(a): FX gain/loss on a §988 transaction is ordinary. §988(e)(2): personal
  transaction — no gain recognized by reason of rate changes unless the gain exceeds
  $200. Matches the taxes page row and flag F13 (character above $200 / loss
  deductibility unverified).
- https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm

## US-REMIT — 1% remittance transfer tax (PASS)

- IRC §4475 (One Big Beautiful Bill Act, enacted 2025-07-04, effective 2026-01-01):
  1% on remittance transfers sent FROM the US when the sender provides cash, money
  order, cashier's check or similar physical instrument; not when funded from an
  account or US-issued card; proposed regulations 2026-04-10. The guide's row
  "Does not apply to money arriving" stands.
- https://www.irs.gov/newsroom/treasury-irs-issue-proposed-regulations-on-the-new-remittance-transfer-tax-established-under-the-one-big-beautiful-bill

## PR-WISE — Wise "Guide to CNY transfers" (PASS)

- Sending from CNY: sender must not be mainland Chinese (TW/HK/MO eligible), works or
  worked in China, valid China tax record showing taxes paid within the last 3 years;
  personal accounts only. Alipay funding: 50,000 CNY per transfer. Overall limit based
  on after-tax China salary. Matches M10's `who` and `limit`.
- https://wise.com/help/articles/2955298/guide-to-cny-transfers

## PR-WISEFEE — Wise comparison API quotes (SNAPSHOT, flagged F06)

- Quotes stored in `sources.json` (collected 2026-11-11T02:35:43–02:35:50Z) match
  `prices.json` exactly (fees 435.20 / 846.63 / 1,226.05 / 1,571.46 / 1,741.74 CNY;
  no quote at CNY 2,668,440). A snapshot is re-checkable only against its own record;
  the site tells the reader to re-quote at deal time.
- https://api.wise.com/v3/comparisons/?sourceCurrency=CNY&targetCurrency=USD&sendAmount=66770.5

## CN-TAXFILING — STA/SAFE Announcement 2013 No. 40 (PASS)

- Single outward payment above USD 50,000 equivalent by domestic institutions or
  individuals for listed items (incl. a foreign individual's China work pay received
  in China — per the guide's F01 framing) requires a tax filing with the local tax
  authority; art. 4 routes a foreign individual's outward payments to the individual
  FX rules. Page live at the recorded URL.
- https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html

## CN-CARD — SAFE 汇发〔2017〕29号 (PASS)

- Overseas ATM cash with mainland bank cards: 10,000 CNY per card per day; 100,000 CNY
  per person per natural year across all own cards; breach suspends the right for the
  current and next year. Matches `prices.json` ATM caps.
- https://www.safe.gov.cn/safe/2017/1230/8130.html

## US-3520 — IRS "Gifts from foreign person" (PASS)

- Form 3520 needed when gifts/bequests from a nonresident alien individual or foreign
  estate aggregate more than $100,000 in a year (related parties aggregated). Matches
  the guide's use in M07/X01 context.
- https://www.irs.gov/businesses/gifts-from-foreign-person

## CN-BOCTARIFF — BOC personal service tariff PDF (CONSISTENT, not re-downloaded)

- The recorded quote contains: 电汇 commission 1‰ min 50 max 260 CNY; international
  cable 150 CNY; full-amount delivery USD 15 (payee's bank at BOC New York) or USD 25
  (all others); cross-border ATM 12 + 1% max 112 CNY. These match `prices.json`
  figures one-to-one. The PDF sits behind `pic.bankofchina.com`, which the sandbox
  cannot fetch directly; no contrary official figure was found in search excerpts.
  Kept as-is; F19 (commission base/discounts) and F04 (intermediary deductions) stay
  open on Flagged for Review.
- https://pic.bankofchina.com/bocappd/pricelist/202511/P020251110646838136627.pdf

## Sources not re-opened in this pass

CN-BOCFEE (2009 BOC fee page), PR-HSBC, PR-WU, CN-PR (2024 Q&A), CN-PROPTRANS,
CN-SHPROP, CN-CASH page, CN-CRYPTO (PBOC 2026 No. 42), CN-RMBX, CN-IIT page,
CN-TAXCOLL, CN-CNYCASH, US-ABROAD, US-FTC, US-FX, US-CBP, US-CHASE — these were each
opened within the last 48 hours by the sessions recorded on the board
(arena-db079cfc, arena-f766722d), their quoted text is stored in `sources.json`, and
none drives a figure that changed in this session. They are listed here so a future
session knows the exact coverage boundary of this pass.
