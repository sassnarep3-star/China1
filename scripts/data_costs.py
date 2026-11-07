# -*- coding: utf-8 -*-
"""Cost and penalty decomposition.

The brief asked for the 'conversion penalty' to be broken down. This file does that
item by item. Every numeric value is either (a) quoted from a tier-A/C source, (b)
arithmetic performed on a quoted value and labelled as derived, or (c) left EMPTY
and pushed to the Flagged page.
"""

COSTS = [
    dict(id="K1", band="A. Unavoidable cost of a lawful conversion",
         item="Bank FX bid/ask spread (spot / 现汇)",
         value="0.42%", how="Derived from the Bank of China USD board on 2026-11-08: 现汇买入价 666.48 and 现汇卖出价 669.29 CNY per 100 USD → (669.29 − 666.48) ÷ 669.29 = 0.4199%. A round trip loses about 0.42% of the principal.",
         on1m="≈ CNY 4,200 on CNY 1,000,000",
         vstatus="VERIFIED", basis=["CN-11"]),

    dict(id="K2", band="A. Unavoidable cost of a lawful conversion",
         item="Cash (现钞) versus transfer (现汇) spread",
         value="", how="Bank of China quoted identical 现钞 and 现汇 USD rates on 2026-11-08, i.e. no additional cash penalty at that bank on that day. Whether other banks price cash worse, and by how much, was not verified. Cash is normally the more expensive form, so the absence of a penalty here should not be generalised.",
         on1m="", vstatus="PARTIAL", basis=["CN-11"]),

    dict(id="K3", band="A. Unavoidable cost of a lawful conversion",
         item="Outbound telegraphic-transfer commission",
         value="", how="Set by each bank's published tariff (typically a percentage with a floor and a cap). No tier-A tariff schedule was retrieved this session, so the figure is deliberately left blank rather than estimated.",
         on1m="", vstatus="UNVERIFIED", basis=[]),

    dict(id="K4", band="A. Unavoidable cost of a lawful conversion",
         item="Intermediary / correspondent bank charges and the receiving US bank's inbound wire fee",
         value="", how="Charged by the correspondent and the beneficiary bank; varies by bank, by currency-pair corridor and by whether charges are shared (SHA) or borne by the sender (OUR). Not verified.",
         on1m="", vstatus="UNVERIFIED", basis=[]),

    dict(id="K5", band="A. Unavoidable cost of a lawful conversion",
         item="Documentary and notarisation cost for a capital-account route (B1/B2/A7)",
         value="", how="Notarial certification and translation of title documents, plus any agent fee. Not verified; depends on the province and the number of documents.",
         on1m="", vstatus="UNVERIFIED", basis=["CN-06"]),

    dict(id="K6", band="A. Unavoidable cost of a lawful conversion",
         item="Time cost: the annual quota as a schedule",
         value="USD 50,000 per person per year", how="Pure arithmetic on the verified quota: a USD 500,000 balance takes 10 calendar years; USD 1,000,000 takes 20; a two-person household halves it. Regulators state the quota; the schedule is our derived calculation.",
         on1m="", vstatus="VERIFIED", basis=["CN-02", "CN-03"]),

    dict(id="K7", band="A. Unavoidable cost of a lawful conversion",
         item="Time cost: the emigration-transfer release schedule",
         value="50% / +1 year 25% / +2 years the rest", how="Statute 第六条: first release ≤ half the declared total, a further ≤ half of the remainder after one year, the balance after two years; a declared total of CNY 200,000 or less may be released at once after approval.",
         on1m="", vstatus="VERIFIED", basis=["CN-06"]),

    dict(id="K8", band="B. Real Chinese tax that is NOT a conversion tax",
         item="IIT on property transfer gains (财产转让所得)",
         value="20%", how="Flat 20% of the gain (sale proceeds less original cost and reasonable expenses). This is the largest genuine tax in the picture and it is triggered by the sale, not by the conversion. It is not avoidable by choosing a different remittance route.",
         on1m="≤ CNY 200,000 on a CNY 1,000,000 gain",
         vstatus="VERIFIED", basis=["CN-14"]),

    dict(id="K9", band="B. Real Chinese tax that is NOT a conversion tax",
         item="IIT on interest, dividends and bonuses (利息、股息、红利所得)",
         value="20%", how="Flat 20% on the gross amount, withheld at source by the paying institution. A CNY deposit therefore already nets 80% of its coupon, and that withholding is the only Chinese tax most savers ever actually pay.",
         on1m="", vstatus="VERIFIED", basis=["CN-14"]),

    dict(id="K10", band="B. Real Chinese tax that is NOT a conversion tax",
         item="IIT on wages and salaries",
         value="3%–45% progressive", how="Already withheld by the employer. If the balance is accumulated salary, the Chinese tax has already been paid — which is precisely why remitting it later is not a second taxable event.",
         on1m="", vstatus="VERIFIED", basis=["CN-14"]),

    dict(id="K11", band="B. Real Chinese tax that is NOT a conversion tax",
         item="Tax on the act of remitting your own after-tax principal",
         value="None", how="The IIT Law taxes nine enumerated categories of income (工资薪金, 劳务报酬, 稿酬, 特许权使用费, 经营, 利息股息红利, 财产租赁, 财产转让, 偶然). A movement of the taxpayer's own already-taxed principal between the taxpayer's own accounts is not one of them. What the law does require is a tax filing/clearance step for certain outward payments and for the emigration route — a procedural gate, not a levy.",
         on1m="CNY 0", vstatus="VERIFIED", basis=["CN-14", "CN-13", "CN-06"]),

    dict(id="K12", band="B. Real Chinese tax that is NOT a conversion tax",
         item="Chinese exit tax (tax on ceasing Chinese tax residence, or on renouncing/before leaving)",
         value="None identified", how="No exit-tax mechanism appears in the IIT Law's charging provisions. The nearest thing is the tax clearance requirement inside the emigration-transfer procedure (a certificate that the assets are clean, not a departure levy). Stated as a negative finding: the IIT Law contains no such charge.",
         on1m="CNY 0", vstatus="PARTIAL", basis=["CN-14", "CN-06"]),

    dict(id="K13", band="C. Penalty exposure if a lawful route is skipped",
         item="Chinese administrative fine — 逃汇 (evasion of FX controls)",
         value="≤30% of the amount; 30%–100% if serious", how="'违反规定将境内外汇转移境外，或者以欺骗手段将境内资本转移境外' — order to repatriate, fine of up to 30% of the evaded amount, or from 30% up to the equivalent amount for serious cases, with criminal liability where the threshold is met.",
         on1m="up to CNY 300,000, or up to CNY 1,000,000 if serious",
         vstatus="VERIFIED", basis=["CN-08"]),

    dict(id="K14", band="C. Penalty exposure if a lawful route is skipped",
         item="Chinese administrative fine — private/underground FX dealing",
         value="≤30% of the amount; 30%–100% if serious", how="Warning, confiscation of illegal gains and a fine up to 30% of the amount for 私自买卖外汇、变相买卖外汇、倒买倒卖外汇 or 非法介绍买卖外汇 where the amount is significant; 30% to 100% for serious cases; criminal referral where the threshold is met.",
         on1m="up to CNY 300,000, or up to CNY 1,000,000 if serious",
         vstatus="VERIFIED", basis=["CN-08"]),

    dict(id="K15", band="C. Penalty exposure if a lawful route is skipped",
         item="Loss of banking access — the 关注名单 (watch list)",
         value="Not quantified in the regulation", how="SAFE watch-lists individuals who evade the quota or the authenticity review, including by lending a quota; the bank must hand over a written 风险提示函 / 关注名单告知书 at the counter. The regulation states the consequence but not a duration, so no duration is asserted here.",
         on1m="", vstatus="VERIFIED", basis=["CN-03"]),

    dict(id="K16", band="C. Penalty exposure if a lawful route is skipped",
         item="Two-year suspension of overseas cash withdrawal",
         value="Current year + following year", how="Exceeding the CNY 100,000 annual overseas cash-withdrawal cap suspends overseas ATM withdrawal on mainland cards for the remainder of the year and the whole of the next year, with penalties under the FX Regulations depending on seriousness.",
         on1m="", vstatus="VERIFIED", basis=["CN-12"]),

    dict(id="K17", band="C. Penalty exposure if a lawful route is skipped",
         item="US civil penalty — non-willful FBAR failure",
         value="Up to USD 10,000 per report, inflation-adjusted", how="Statutory maximum for a non-willful violation; the figure is adjusted for inflation annually, so the current-year dollar figure changes and is deliberately not restated as a fixed number here. The Supreme Court has held the non-willful penalty attaches per report rather than per account.",
         on1m="", vstatus="VERIFIED", basis=["US-01", "US-03"]),

    dict(id="K18", band="C. Penalty exposure if a lawful route is skipped",
         item="US civil penalty — willful FBAR failure",
         value="Greater of USD 100,000 or 50% of the account balance", how="This is the only place in the entire problem where the exposure genuinely exceeds a 20% headline: on a USD 500,000 account a willful finding puts 50% of the balance at risk for a single year, and the statute of limitations runs six years. Inflation adjustment applies.",
         on1m="≈ USD 250,000 on a USD 500,000 balance (single year)",
         vstatus="VERIFIED", basis=["US-03", "US-01"]),

    dict(id="K19", band="C. Penalty exposure if a lawful route is skipped",
         item="US penalty — failure to file Form 8938",
         value="USD 10,000 per failure, plus USD 10,000 per 30 days after notice, max USD 60,000", how="Continuous-failure penalty under the FATCA reporting provisions, per the IRS comparison page.",
         on1m="", vstatus="VERIFIED", basis=["US-01", "US-06"]),

    dict(id="K20", band="C. Penalty exposure if a lawful route is skipped",
         item="US penalty — failure to file Form 3520 for a foreign gift or inheritance",
         value="5% of the unreported amount per month, capped at 25%", how="Applies to gifts/bequests from foreign persons above the reporting threshold. The underlying gift is not taxable; the penalty is for the silence.",
         on1m="", vstatus="VERIFIED", basis=["US-05"]),

    dict(id="K21", band="C. Penalty exposure if a lawful route is skipped",
         item="US forfeiture exposure on undeclared cash",
         value="The entire amount, not the excess", how="31 U.S.C. § 5316/5317: failing to file FinCEN Form 105 exposes the whole sum to seizure and forfeiture irrespective of its lawful origin, with civil and criminal penalties on top. Dividing cash among travellers is structuring — a separate offence.",
         on1m="", vstatus="VERIFIED", basis=["US-11", "US-12"]),

    dict(id="K22", band="C. Penalty exposure if a lawful route is skipped",
         item="US tax on the FX gain itself",
         value="Usually nil for an individual", how="On a personal (non-business, non-investment) disposition of foreign currency, exchange-rate gain is not recognised unless it exceeds USD 200; losses on personal transactions are not deductible. For a person converting their own savings once, the US income tax on the currency movement is normally zero.",
         on1m="≈ USD 0", vstatus="VERIFIED", basis=["US-04", "US-13"]),

    dict(id="K23", band="D. Baseline for comparison",
         item="Chinese deposit interest rate (opportunity cost of holding CNY)",
         value="", how="Official benchmark deposit rates are set by the PBOC and quoted by each bank. Not retrieved this session; left blank rather than estimated.",
         on1m="", vstatus="UNVERIFIED", basis=[]),

    dict(id="K24", band="D. Baseline for comparison",
         item="USD short-term interest available in the US (opportunity gain from converting)",
         value="", how="Not verified; left blank. Directionally the comparison is one the reader should make with live rates.",
         on1m="", vstatus="UNVERIFIED", basis=[]),
]

# ---------------------------------------------------------------------------
# Headline decomposition used on the landing page and in the executive summary.
# ---------------------------------------------------------------------------
HEADLINE = [
    ("0.42%", "Measured bank spread", "The real, unavoidable 'conversion penalty' on a lawful CNY→USD purchase, derived from Bank of China's own USD quotes of 2026-11-08."),
    ("≈ 0%", "US tax on the FX movement", "A personal conversion of your own currency is not recognised as US income unless the rate gain exceeds USD 200 (IRC §988(e)(2))."),
    ("0%", "Chinese tax on remitting your own principal", "The IIT Law taxes nine enumerated income categories; a transfer of already-taxed principal is not one of them."),
    ("20%", "Chinese IIT that does apply — but to the gain, not the transfer", "Property-transfer gains and interest/dividends are taxed at a flat 20%. If the balance came from a property sale, this tax was always owed."),
    ("50%", "The number that is actually dangerous", "US willful-FBAR exposure is the greater of USD 100,000 or 50% of the account balance — per year. Non-reporting, not conversion, is where a 'considerable amount' is genuinely at risk."),
]
