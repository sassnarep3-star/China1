"""Edition J source registry.

Every entry was retrieved and read in this session (2026-11-10 UTC) unless
`retrieved` says otherwise. `scope` records what was actually inspected, so a
claim is never wider than the text that was read. `tier` distinguishes
government/statute sources from provider-primary schedules: a provider page can
only establish that provider's own price or terms, never the law.
"""

SOURCES = {
    # ---------------- China: statutes, regulator rules ----------------
    "CN-FXREG": {
        "tier": "A",
        "publisher": "State Council of the PRC (国务院令第532号)",
        "title": "中华人民共和国外汇管理条例 (Foreign Exchange Administration Regulations)",
        "url": "https://www.gov.cn/gongbao/content/2008/content_1071846.htm",
        "scope": "Full text retrieved; Articles 5, 12, 21, 22, 39, 40, 41, 42, 45, 48, 52 read.",
        "supports": "The statutory penalty ladder: 逃汇 (Art. 39) up to 30% then 30%-100%; "
                    "非法套汇 (Art. 40) same; cash carried in/out of the border (Art. 42) up to 20%; "
                    "private/illegal FX dealing (Art. 45); and Art. 5 free current-account payments.",
        "retrieved": "2026-11-10",
    },
    "CN-PBOC3": {
        "tier": "A",
        "publisher": "People's Bank of China (中国人民银行令[2006]第3号), published by SAFE",
        "title": "个人外汇管理办法 (Measures for the Administration of Individual Foreign Exchange)",
        "url": "https://www.safe.gov.cn/safe/2006/1225/5319.html",
        "scope": "Full instrument retrieved; Articles 2, 3, 7, 9, 12-15, 16-26, 27-36, 37 read.",
        "supports": "The 境内个人 / 境外个人 split (Art. 2, Art. 37 definitions), current-account "
                    "convertibility versus capital-account 'convertibility process' (Art. 3), the "
                    "no-splitting rule (Art. 7), the quota/over-quota structure (Art. 9), the overseas "
                    "individual documented-income route (Art. 13), property-sale remittance (Art. 22) "
                    "and outward property transfer (Art. 26).",
        "retrieved": "2026-11-10",
    },
    "CN-GUIDE2020": {
        "tier": "A",
        "publisher": "SAFE, 汇发〔2020〕14号, republished in State Council Gazette 2020 No. 31",
        "title": "经常项目外汇业务指引（2020年版） (Current-Account FX Business Guide, 2020 edition)",
        "url": "https://www.gov.cn/gongbao/content/2020/content_5560296.htm",
        "scope": "All six chunks of the Gazette page retrieved; Articles 47-49, 54-63, 64-67, "
                 "76-79, 86-89, 132, 137, 177-179 read in the operative text.",
        "supports": "Annual facilitation quota of USD 50,000 per person per year for 个人结汇 and "
                    "境内个人购汇 (Art. 54); 境外个人 purchases against documented current-account "
                    "income with no stated annual cap (Art. 59); service-trade documentary threshold of "
                    "USD 50,000 (Art. 49); splitting/'watch list' rules (Art. 62); the USD 50,000 "
                    "outward-remittance documentary threshold (Art. 64); cash rules: USD 10,000 per day "
                    "withdrawal/deposit and the USD 5,000 inbound declaration and USD 5,000-10,000 "
                    "carry-permit bands (Arts. 86-89); payment-institution single-transaction cap of "
                    "USD 50,000 (Art. 132).",
        "retrieved": "2026-11-10",
    },
    "CN-PROPERTY2004": {
        "tier": "A",
        "publisher": "People's Bank of China 公告〔2004〕第16号, published by SAFE",
        "title": "个人财产对外转移售付汇管理暂行办法 (Interim Measures on Sale and Payment of FX for "
                 "Outward Transfer of Personal Property)",
        "url": "http://m.safe.gov.cn/safe/2004/1116/5461.html",
        "scope": "Full instrument retrieved; Articles 2-15 read, including Art. 6 staging and Art. 10 "
                 "approval split.",
        "supports": "Defines emigrant transfer and inheritance transfer (Art. 2); original staging "
                    "(Art. 6); document list including the tax certificate/完税凭证 (Arts. 8-9); the "
                    "RMB 500,000 approval threshold (Art. 10); ban on taking out cash in China (Art. 11).",
        "retrieved": "2026-11-10",
    },
    "CN-CAP2014": {
        "tier": "A",
        "publisher": "SAFE, 汇发〔2014〕2号, amended republication on the Tianjin branch site",
        "title": "国家外汇管理局关于进一步改进和调整资本项目外汇管理政策的通知 (Section VI: personal "
                 "property transfer)",
        "url": "https://www.safe.gov.cn/tianjin/2024/0903/2594.html",
        "scope": "Full notice retrieved; Section VI paragraphs (一)-(四) read, plus the 汇发〔2023〕28号 "
                 "amendment note for Section III.",
        "supports": "Cancels the RMB 500,000 national-level filing (VI-一), cancels mandatory staged "
                    "emigrant releases so an approved amount may be remitted once or in instalments "
                    "(VI-二), allows merged applications from different decedents (VI-三), and removes "
                    "the notarisation requirement for property-rights documents (VI-四). This supersedes "
                    "the staging in CN-PROPERTY2004 Art. 6.",
        "retrieved": "2026-11-10",
    },
    "CN-PROPERTYQA": {
        "tier": "A",
        "publisher": "SAFE Tianjin branch (国家外汇管理局天津市分局)",
        "title": "个人财产转移购付汇业务问答（六） (Q&A on outward transfer of personal property, part 6)",
        "url": "http://www.safe.gov.cn/tianjin/2026/0318/3017.html",
        "scope": "Full item retrieved (published 2026-03-18).",
        "supports": "Confirms, as of March 2026, that the operative definition of 个人财产对外转移 still "
                    "rests on PBOC Announcement [2004] No. 16 and covers emigrant and inheritance "
                    "transfers. It does not restate the 2014 staging removal, so the two must be read "
                    "together.",
        "retrieved": "2026-11-10",
    },
    "CN-IIT": {
        "tier": "A",
        "publisher": "State Taxation Administration (English translation of the statute)",
        "title": "Individual Income Tax Law of the PRC",
        "url": "https://www.chinatax.gov.cn/eng/c102962/c102967/c102997/c103004/c5245849/content.html",
        "scope": "Chunks 0 and 1 retrieved; Articles 1-13 read.",
        "supports": "Nine taxable income categories (Art. 2) - a currency exchange is not among them; "
                    "20% flat rate on interest/dividends, asset leasing, asset transfer and incidental "
                    "income (Art. 3(3)); 3%-45% progressive on comprehensive income (Art. 3(1)); "
                    "taxable-income computation for asset transfers net of original value and reasonable "
                    "expenses (Art. 6(5)); the exit filing trigger when emigrating and cancelling "
                    "household registration (Art. 10(5)).",
        "retrieved": "2026-11-10",
    },
    "CN-DIV2026": {
        "tier": "A",
        "publisher": "Ministry of Finance & STA, 财政部 税务总局公告2026年第27号 (Shanghai STA reprint)",
        "title": "关于外籍个人股息红利个人所得税政策有关事项的公告",
        "url": "https://shanghai.chinatax.gov.cn/zzzb/zcwj/202609/t481448.html",
        "scope": "Full announcement retrieved; paragraphs 1-3 read.",
        "supports": "From 2026-09-01, dividends paid by a foreign-invested enterprise to a foreign "
                    "individual are taxed at 20% under 'interest, dividends and bonuses', withholding "
                    "applies, and the 1994 exemption in 财税字〔1994〕20号 Art. 2(8) is repealed.",
        "retrieved": "2026-11-10",
    },
    "CN-SHFAQ": {
        "tier": "B",
        "publisher": "Shanghai Municipal Government English portal, sourced to Bank of China",
        "title": "Can I buy foreign exchange using the proceeds from selling my house?",
        "url": "https://english.shanghai.gov.cn/en-FAQHome/20240204/b4426264395b4fa3adfde73778c94ad4.html",
        "scope": "Full FAQ retrieved (5 steps, 4 document items).",
        "supports": "The operational sequence for a non-resident selling mainland property: ownership "
                    "transfer, tax settlement and tax-payment proof, the external-payment tax filing form "
                    "above USD 50,000, then purchase and remittance. Government-hosted but content "
                    "attributed to a commercial bank, so it evidences procedure, not statute.",
        "retrieved": "2026-11-10",
    },
    "CN-CARDS2017": {
        "tier": "B",
        "publisher": "SAFE, 汇发〔2017〕29号, via the State Council portal Q&A reprint",
        "title": "规范银行卡境外大额提取现金交易 (Overseas card cash-withdrawal limits)",
        "url": "https://www.gov.cn/zhengce/2017-12/31/content_5251958.htm",
        "scope": "Official Q&A reprint retrieved; the four operative points and the consumption carve-out read.",
        "supports": "Aggregate overseas cash withdrawal on a person's domestic bank cards is capped at "
                    "CNY 100,000 per calendar year; per-card daily limit is CNY 10,000 equivalent; exceeding "
                    "it suspends overseas cash access for the current and following year; card spending "
                    "abroad does not consume the USD 50,000 facilitation quota.",
        "retrieved": "2026-11-10",
    },
    "CN-VA2026": {
        "tier": "B",
        "publisher": "Eight ministries incl. PBOC and SAFE, 银发〔2026〕42号; full text as republished by a "
                     "Shenzhen district government portal",
        "title": "关于进一步防范和处置虚拟货币等相关风险的通知",
        "url": "https://www.szns.gov.cn/ztzl/ffjzxsjb/zcfg/content/post_12958317.html",
        "scope": "Full notice retrieved; Parts I-VI read including the repeal clause.",
        "supports": "Virtual-currency business activity in mainland China is characterised as illegal "
                    "financial activity and strictly prohibited; financial and payment institutions may not "
                    "provide account, transfer or settlement services for it; it took effect 2026-02-06 and "
                    "repealed 银发〔2021〕237号. The PBOC original is the primary source; this government "
                    "portal reprint was used because the PBOC page was not retrievable from this sandbox.",
        "retrieved": "2026-11-10",
    },
    # ---------------- China: provider-primary price and channel pages ----------------
    "BOC-BOARD": {
        "tier": "P",
        "publisher": "Bank of China (中国银行) - 外汇牌价",
        "title": "中国银行外汇牌价 (BOC foreign-exchange board)",
        "url": "https://www.boc.cn/sourcedb/whpj/",
        "scope": "Live board retrieved 2026-11-10; USD row read: 现汇买入价 666.22, 现钞买入价 666.22, "
                 "现汇卖出价 669.03, 现钞卖出价 669.03, 中行折算价 671.88, published 2026/11/10 07:32:39. "
                 "Board note 1 states the table is indicative and the actual transaction rate at the "
                 "counter/online/mobile channel governs.",
        "supports": "Only the published bid/ask numbers on that timestamp. It is not a quote for any "
                    "particular customer, amount or date after the timestamp.",
        "retrieved": "2026-11-10",
    },
    "BOC-TARIFF": {
        "tier": "P",
        "publisher": "Bank of China (中国银行) - 电子银行个人服务转账汇款费率表",
        "title": "中国银行电子银行个人服务转账汇款费率表 (personal e-banking transfer tariff, effective "
                 "2014-11-01)",
        "url": "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
        "scope": "Full tariff page retrieved; the cross-border TT row, the domestic interbank tiered row, "
                 "the intra-bank foreign-currency transfer row and notes 1-3 read.",
        "supports": "Cross-border telegraphic transfer: 1 per mille of the remittance, minimum CNY 50, "
                    "maximum CNY 260, plus cable CNY 80 (Hong Kong/Macau/Taiwan) or CNY 150 (elsewhere). "
                    "Domestic interbank: tiered CNY 2/5/10/15 up to CNY 50,000, then 0.03% capped at CNY 50. "
                    "Intra-bank foreign-currency transfer: 1 per mille capped at CNY 200. Note 1 allows "
                    "separate agreements, discounts and local differences.",
        "retrieved": "2026-11-10",
    },
    "CFETS-FIX": {
        "tier": "A",
        "publisher": "China Foreign Exchange Trade System / 中国货币网, authorised by the PBOC",
        "title": "人民币汇率中间价 (RMB central parity)",
        "url": "https://www.chinamoney.com.cn/chinese/bkccpr/",
        "scope": "Live page retrieved 2026-11-10; the USD/CNY quote block read: 6.7188 at 2026-11-09 09:15, "
                 "with the October 2026 monthly average 6.7223.",
        "supports": "The PBOC-authorised central parity, and the published methodology (market-maker "
                    "quotes, highest and lowest dropped, weighted average).",
        "retrieved": "2026-11-10",
    },
    "WISE-CNY": {
        "tier": "P",
        "publisher": "Wise - Help Centre",
        "title": "Guide to CNY transfers",
        "url": "https://wise.com/help/articles/2955298/guide-to-cny-transfers",
        "scope": "First chunk retrieved; 'Sending from CNY' section read (eligibility, limits, verification).",
        "supports": "Eligibility for sending from CNY is limited to non-mainland-Chinese senders who work "
                    "or have worked in China and hold a China tax record showing tax paid in the last three "
                    "years; the recipient must be an account the sender owns; CNY 300,000 per transfer via "
                    "a China bank app, CNY 50,000 via Alipay; an overall limit based on after-tax salary. "
                    "Fees are quote-based, not a published schedule - the page says to check live pricing.",
        "retrieved": "2026-11-10",
    },
    # ---------------- United States: statutes and agency guidance ----------------
    "US-988": {
        "tier": "A",
        "publisher": "Legal Information Institute, Cornell Law School (26 U.S.C. §988)",
        "title": "26 U.S. Code §988 - Treatment of certain foreign currency transactions",
        "url": "https://www.law.cornell.edu/uscode/text/26/988",
        "scope": "Chunks 0, 2 and 3 retrieved; subsection (e) 'Application to individuals' read in full.",
        "supports": "§988(e)(2): for an individual's personal transaction in nonfunctional currency, no gain "
                    "is recognised from exchange-rate movement between acquisition and disposition, and "
                    "§988(e)(3) defines 'personal transaction'. §988(e)(2) withdraws that relief when the "
                    "gain would exceed USD 200. Cornell is a republication of the Code, used here because "
                    "the uscode.house.gov granule URLs returned HTTP 404 and govinfo was unreachable.",
        "retrieved": "2026-11-10",
    },
    "US-5321": {
        "tier": "A",
        "publisher": "Legal Information Institute, Cornell Law School (31 U.S.C. §5321)",
        "title": "31 U.S. Code §5321 - Civil penalties",
        "url": "https://www.law.cornell.edu/uscode/text/31/5321",
        "scope": "First chunk retrieved; subsection (a)(5) foreign financial agency transaction violation read.",
        "supports": "FBAR civil penalty structure: non-willful capped at USD 10,000 per violation with a "
                    "reasonable-cause exception; willful raised to the greater of USD 100,000 or 50% of the "
                    "account balance at the time of the violation, and the reasonable-cause defence is "
                    "unavailable for willful violations. Statutory caps are inflation-adjusted annually.",
        "retrieved": "2026-11-10",
    },
    "US-1010821": {
        "tier": "A",
        "publisher": "eCFR (Office of the Federal Register), 31 CFR 1010.821",
        "title": "§1010.821 Penalty adjustment and table",
        "url": "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
        "scope": "Chunks 0 and 1 retrieved; the penalty table rows for 31 U.S.C. 5321(a)(5)(B)(i) and (C)(i) read.",
        "supports": "Current inflation-adjusted FBAR maxima for penalties assessed on or after 2025-01-17: "
                    "non-willful USD 16,536; willful USD 165,353 (and the 50%-of-balance alternative in the "
                    "statute continues to apply).",
        "retrieved": "2026-11-10",
    },
    "US-6038D": {
        "tier": "A",
        "publisher": "Legal Information Institute, Cornell Law School (26 U.S.C. §6038D)",
        "title": "26 U.S. Code §6038D - Information with respect to foreign financial assets",
        "url": "https://www.law.cornell.edu/uscode/text/26/6038D",
        "scope": "Full section retrieved; subsections (a), (d) and (g) read.",
        "supports": "Form 8938 attachment duty above USD 50,000 aggregate; USD 10,000 penalty for failure to "
                    "disclose plus USD 10,000 per 30-day period after notice, capped at USD 50,000 additional; "
                    "reasonable-cause exception in (g).",
        "retrieved": "2026-11-10",
    },
    "US-FBAR": {
        "tier": "A",
        "publisher": "Internal Revenue Service",
        "title": "Report of Foreign Bank and Financial Accounts (FBAR)",
        "url": "https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar",
        "scope": "First chunk retrieved; who-must-file, due date, recordkeeping and penalties sections read.",
        "supports": "USD 10,000 aggregate reporting trigger, April 15 due date with automatic October 15 "
                    "extension, five-year record retention, and confirmation that producing no taxable income "
                    "does not remove the filing duty.",
        "retrieved": "2026-11-10",
    },
    "US-8938": {
        "tier": "A",
        "publisher": "Internal Revenue Service",
        "title": "Comparison of Form 8938 and FBAR requirements",
        "url": "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements",
        "scope": "First chunk retrieved; the full threshold and penalty comparison table read.",
        "supports": "Form 8938 thresholds by filing status and residence (USD 50,000/75,000 single in the US, "
                    "100,000/150,000 joint, 200,000/300,000 and 400,000/600,000 abroad) and the USD 10,000 plus "
                    "USD 10,000/30-days to a USD 60,000 maximum penalty description.",
        "retrieved": "2026-11-10",
    },
    "US-3520": {
        "tier": "A",
        "publisher": "Internal Revenue Service",
        "title": "Instructions for Form 3520 (12/2025)",
        "url": "https://www.irs.gov/instructions/i3520",
        "scope": "Chunks 0 and 2 retrieved; the who-must-file items and the gifts/bequests threshold read.",
        "supports": "Form 3520 is required on receipt of more than USD 100,000 from a nonresident alien "
                    "individual or foreign estate treated as a gift or bequest, and for foreign-trust "
                    "transactions; it is an information return filed apart from the income tax return.",
        "retrieved": "2026-11-10",
    },
    "US-1010340": {
        "tier": "A",
        "publisher": "eCFR (Office of the Federal Register), 31 CFR 1010.340",
        "title": "§1010.340 Reports of transportation of currency or monetary instruments",
        "url": "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-C/section-1010.340",
        "scope": "Full section retrieved; paragraphs (a), (b) and (d) read.",
        "supports": "A FinCEN 105 report is required to transport, mail or ship more than USD 10,000 in "
                    "currency or monetary instruments into or out of the United States at one time; "
                    "paragraph (d) confirms a funds transfer through normal banking channels that involves no "
                    "physical transport is outside this section.",
        "retrieved": "2026-11-10",
    },
    "US-IRS-FX": {
        "tier": "A",
        "publisher": "Internal Revenue Service",
        "title": "Foreign currency and currency exchange rates",
        "url": "https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates",
        "scope": "Full page retrieved.",
        "supports": "US-dollar functional currency, translation at the rate prevailing when an item is "
                    "received/paid/accrued, and the IRS's list of governmental rate resources.",
        "retrieved": "2026-11-10",
    },
    "US-IRS-ABROAD": {
        "tier": "A",
        "publisher": "Internal Revenue Service",
        "title": "U.S. citizens and resident aliens abroad",
        "url": "https://www.irs.gov/individuals/international-taxpayers/us-citizens-and-resident-aliens-abroad",
        "scope": "First chunk retrieved; worldwide-income, FBAR and Form 3520 paragraphs read.",
        "supports": "US citizens are taxed on worldwide income regardless of residence, and must report "
                    "foreign accounts even where no taxable income arises.",
        "retrieved": "2026-11-10",
    },
}

# Source ids that may legitimately appear in a published table row.
GOVERNMENT_TIERS = {"A", "B"}
PROVIDER_TIERS = {"P"}
