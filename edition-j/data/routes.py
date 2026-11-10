"""Edition J route catalog: 30 candidates, pros and cons, steps and cost basis.

Rules enforced by build/verify.py:
  * every route carries at least one law source id and one limit basis source
    unless the limit genuinely does not exist (then `limit_basis` is empty and
    the route is marked `limit_known=False`);
  * `estimate.mode` decides whether a 40-row ladder is computed; a computed
    ladder requires a source in `cost_basis`;
  * prohibited routes carry no execution steps - only what is prohibited, the
    instrument, and the exposure.

`verifiability` is deliberately conservative:
  verified   - the operative rule and the price basis were both read in full
  partly     - the rule was read but the price or the local practice was not
  unverified - known only from secondary sources or not confirmable at all
"""

LAWFUL = "lawful"
CONDITIONAL = "conditional"
PROHIBITED = "prohibited"

ROUTES = [
    # =================== A. CURRENT ACCOUNT: DOCUMENTED INCOME ===================
    {
        "id": "R01",
        "name": "Bank purchase and TT remittance against documented current-account income",
        "zh": "境外个人凭经常项目合法人民币收入购汇汇出",
        "category": "A",
        "lawful": LAWFUL,
        "law_basis": ["CN-PBOC3", "CN-GUIDE2020"],
        "law_text": "个人外汇管理办法 Art. 13; 经常项目指引(2020) Art. 59",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "No annual cap stated for 境外个人 purchasing against documented income "
                 "(Art. 59). Above USD 50,000 per payment the bank applies enhanced documentary review.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "verified",
        "pros": [
            "The only route that is unrestricted in size once the income trail is documented.",
            "Priced from a published bank tariff, so the fee is knowable before you commit.",
            "Leaves a clean audit trail for both SAFE and the IRS.",
        ],
        "cons": [
            "Requires an evidence chain linking each CNY to specific lawful income.",
            "Banks may still refuse or escalate; the rule gives them discretion on documentary adequacy.",
            "Does not remove Chinese income tax already due on the underlying income.",
        ],
        "steps": [
            "Classify the balance by source and period; separate documented income from pre-emigration savings.",
            "Ask the bank to confirm you are booked as 境外个人 (foreign individual) on the account, because the quota rules differ.",
            "Assemble the documentary set: passport, China tax record or withholding slips, employment or service contract, and bank statements showing the credits.",
            "Submit the purchase (购汇) application; above USD 50,000 the bank performs enhanced review under Art. 59.",
            "Settle the FX at the counter/online rate, request the TT, and keep the 结售汇 slip and the remittance receipt.",
            "Report the account and the transfer on your US return: FBAR if the aggregate exceeded USD 10,000 at any point, Form 8938 if the threshold applies.",
        ],
        "estimate": {"mode": "boc_tt"},
    },
    {
        "id": "R02",
        "name": "Annual facilitation-quota purchase (USD 50,000 per person per year)",
        "zh": "年度便利化额度购汇",
        "category": "A",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-GUIDE2020", "CN-PBOC3"],
        "law_text": "经常项目指引(2020) Art. 54; 个人外汇管理办法 Art. 9",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "USD 50,000 equivalent per person per calendar year, for 个人结汇 and 境内个人购汇.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "partly",
        "pros": [
            "Fast and largely documentary-free inside the quota.",
            "Can be done online or on the mobile app at most banks.",
        ],
        "cons": [
            "The purchase quota is framed for 境内个人 (Chinese citizens with a resident ID); a US citizen holding a foreign passport is generally 境外个人, so this quota is the wrong lane and a bank may refuse it.",
            "USD 50,000 a year cannot move USD 400,000 quickly; you would need eight years, and stacking relatives to speed it up is prohibited (see R28).",
            "Using it to disguise a capital-account transfer is the classic violation.",
        ],
        "steps": [
            "Confirm with the bank whether you are recorded as 境内个人 or 境外个人 - this determines whether the quota is even available to you.",
            "If available, submit the purchase application with your valid ID inside the annual quota.",
            "Record the quota usage; it is aggregated per person across all banks.",
            "Remit and retain the slips.",
        ],
        "estimate": {"mode": "boc_tt"},
    },
    {
        "id": "R03",
        "name": "Salary, bonus and severance paid from a mainland employer",
        "zh": "工资薪金及离职补偿购汇汇出",
        "category": "A",
        "lawful": LAWFUL,
        "law_basis": ["CN-PBOC3", "CN-GUIDE2020", "CN-IIT"],
        "law_text": "个人外汇管理办法 Art. 13; 经常项目指引(2020) Art. 59; IIT Law Art. 2(1)",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "No annual cap for 境外个人 against documented income; documentary review above USD 50,000.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "verified",
        "pros": [
            "The strongest documentary position available: payroll records and withholding slips already exist.",
            "Chinese individual income tax has usually been withheld monthly, so no fresh Chinese tax event arises on the transfer.",
        ],
        "cons": [
            "Only covers the salary portion of the balance, not savings accumulated from other sources.",
            "Severance may need the termination agreement and the tax treatment confirmed locally.",
        ],
        "steps": [
            "Obtain the employment contract, the payroll history and the annual 个人所得税 withholding record.",
            "Have the employer or the tax bureau confirm the tax-paid position for the period.",
            "Present the package to the bank with the purchase application.",
            "Convert, remit, and reconcile the gross and net amounts in USD on your US return.",
        ],
        "estimate": {"mode": "boc_tt"},
    },
    {
        "id": "R04",
        "name": "Service-trade income: consulting, freelance, royalties",
        "zh": "服务贸易项下收入购汇汇出",
        "category": "A",
        "lawful": LAWFUL,
        "law_basis": ["CN-GUIDE2020", "CN-PBOC3"],
        "law_text": "经常项目指引(2020) Art. 49 and Art. 59",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "Payments up to USD 50,000: the bank may waive documentary review (Art. 49). "
                 "Above that: full documentary review, plus the external-payment tax filing form where applicable.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "verified",
        "pros": [
            "Fits consultants, contractors and royalty owners who invoiced from China.",
            "Below USD 50,000 per payment the documentary burden is at the bank's discretion, which is usually faster.",
        ],
        "cons": [
            "Requires genuine contracts and invoices - fabricating them is the offence in R30.",
            "Above USD 50,000 the tax filing form requirement adds a step at the tax bureau.",
        ],
        "steps": [
            "Gather contracts, invoices, payment receipts and the tax treatment of the service income.",
            "Confirm whether the payment needs the 服务贸易等项目对外支付税务备案表.",
            "Apply at the bank for purchase and remittance.",
            "Retain everything; report the income and the account in the US.",
        ],
        "estimate": {"mode": "boc_tt"},
    },
    {
        "id": "R05",
        "name": "Rent collected from mainland property you own",
        "zh": "自有房产租金收入汇出",
        "category": "A",
        "lawful": LAWFUL,
        "law_basis": ["CN-PBOC3", "CN-IIT"],
        "law_text": "个人外汇管理办法 Art. 13; IIT Law Art. 2(7) and Art. 3(3)",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "Current-account treatment with no annual cap; documentary review applies.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "partly",
        "pros": [
            "Recurring, well documented, and small enough to stay inside simple documentary review.",
            "Chinese IIT on rental income is a flat 20% category with a computable base.",
        ],
        "cons": [
            "Moves only the rental yield, not the property's capital value.",
            "Requires a lease, tax-paid evidence and often a property-rights document.",
        ],
        "steps": [
            "Register or confirm the lease and the rental tax payments.",
            "Present the lease, the tax record and the bank statements showing rent credits.",
            "Apply for purchase and remittance of the net rent.",
        ],
        "estimate": {"mode": "boc_tt"},
    },
    {
        "id": "R06",
        "name": "Deposit interest and dividends (bank deposits, fund distributions, FIE dividends)",
        "zh": "利息、股息、红利所得购汇汇出",
        "category": "A",
        "lawful": LAWFUL,
        "law_basis": ["CN-IIT", "CN-DIV2026", "CN-PBOC3"],
        "law_text": "IIT Law Art. 2(6) and Art. 3(3); 财政部 税务总局公告2026年第27号",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "Current-account treatment; documentary review applies.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "verified",
        "pros": [
            "Flat 20% Chinese rate makes the tax arithmetic simple and predictable.",
            "Withholding is usually done by the payer, so the net amount is already clean.",
        ],
        "cons": [
            "The 1994 exemption for foreign individuals' FIE dividends was repealed for payments from 2026-09-01; older guides still claim it is tax-free.",
            "20% is a real cost on the income itself, and it dominates bank fees for large balances.",
        ],
        "steps": [
            "Identify each distribution and whether 20% was withheld at source.",
            "Obtain the withholding certificates.",
            "Apply at the bank for purchase and remittance of the net amount.",
            "Claim the Chinese tax as a foreign tax credit on the US return where eligible.",
        ],
        "estimate": {"mode": "boc_tt", "tax_rate": 0.20, "tax_basis": "CN-DIV2026"},
    },

    # =================== B. CAPITAL ACCOUNT: PROPERTY, INHERITANCE, EXIT ===================
    {
        "id": "R07",
        "name": "Sale of mainland residential property by a non-resident owner",
        "zh": "境外个人出售境内房产购汇汇出",
        "category": "B",
        "lawful": LAWFUL,
        "law_basis": ["CN-PBOC3", "CN-SHFAQ", "CN-IIT"],
        "law_text": "个人外汇管理办法 Art. 22; IIT Law Art. 2(8) and Art. 6(5)",
        "limit_basis": ["CN-GUIDE2020", "CN-SHFAQ"],
        "limit": "No cap on the proceeds themselves; each outward payment above USD 50,000 needs the "
                 "external-payment tax filing form.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "verified",
        "pros": [
            "The single most common way a large balance legitimately leaves China: real asset, real contract, real tax receipt.",
            "Chinese capital-gains tax is computed on gain, not gross proceeds (Art. 6(5)).",
        ],
        "cons": [
            "Requires the property to actually be sold, at market price, with the tax settled first.",
            "The tax filing form and the title documents create real lead time.",
            "You must not rely on the seller-side cash discount stories; the bank checks the tax voucher.",
        ],
        "steps": [
            "Sign the sale contract and complete the ownership-transfer registration at the real-estate authority.",
            "Settle property transfer taxes at the local tax bureau and obtain the tax-payment proof.",
            "Obtain the 服务贸易等项目对外支付税务备案表 for amounts above USD 50,000.",
            "Present passport, contract, registration certificate and tax voucher to the bank.",
            "Purchase FX and remit to your own overseas account; keep the 结售汇 slip.",
        ],
        "estimate": {"mode": "boc_tt", "tax_note": "Capital-gains tax is on gain, not gross; amount unknown."},
    },
    {
        "id": "R08",
        "name": "Emigrant property transfer with SAFE approval (移民财产转移)",
        "zh": "移民财产对外转移",
        "category": "B",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-PROPERTY2004", "CN-CAP2014", "CN-PBOC3"],
        "law_text": "PBOC公告〔2004〕16号 Arts. 2, 8, 10; 汇发〔2014〕2号 Section VI",
        "limit_basis": ["CN-PROPERTY2004"],
        "limit": "No amount cap; approval is required. The original staged-release rule (50%, then 50%, then "
                 "the rest over two years) was cancelled by 汇发〔2014〕2号 Section VI-二, so an approved amount "
                 "may be remitted once or in instalments.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "partly",
        "pros": [
            "The designed route for pre-emigration savings that are not documented income.",
            "Since 2014 there is no mandatory staging and no notarisation duty for property-rights documents.",
        ],
        "cons": [
            "Conditional on having emigrated and cancelled Chinese household registration, with consular proof of settlement abroad.",
            "The local branch still applies its own checklist; the 2014 cancellation of staging is not restated on every branch page.",
            "Requires a Chinese tax certificate or tax-paid evidence for the property.",
        ],
        "steps": [
            "Confirm eligibility: settled abroad and Chinese household registration cancelled.",
            "File the written application and the two prescribed forms with the FX bureau at your former household-registration location.",
            "Provide identity documents, the consular certificate of settlement abroad, and the property-rights and realisation documents.",
            "Provide the Chinese tax certificate or tax-paid vouchers for the property being transferred.",
            "Obtain the approval and 核准件, then apply at the designated bank to purchase FX and remit.",
            "Keep the approval, the 核准件 and each remittance receipt for the US side.",
        ],
        "estimate": {"mode": "boc_tt"},
    },
    {
        "id": "R09",
        "name": "Inheritance transfer with SAFE approval (继承财产转移)",
        "zh": "继承财产对外转移",
        "category": "B",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-PROPERTY2004", "CN-CAP2014"],
        "law_text": "PBOC公告〔2004〕16号 Arts. 2, 9, 10; 汇发〔2014〕2号 Section VI-三",
        "limit_basis": ["CN-PROPERTY2004"],
        "limit": "No amount cap; approval required. Inheritances from different decedents may now be merged "
                 "into one application (2014 Section VI-三).",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "partly",
        "pros": [
            "The only lawful route for inherited mainland assets that were never your own income.",
            "Merging applications from multiple decedents removes a duplication burden.",
        ],
        "cons": [
            "Requires proof of inheritance and evidence of the decedent's property rights.",
            "The decedent's tax-paid position must be demonstrated.",
            "US side: a foreign gift or bequest above USD 100,000 triggers Form 3520.",
        ],
        "steps": [
            "Obtain the inheritance documentation and the decedent's property-rights documents.",
            "Obtain the decedent's Chinese tax certificate or tax-paid vouchers.",
            "File the application at the FX bureau where the decedent's household was registered.",
            "Receive approval, then purchase and remit at the designated bank.",
            "File Form 3520 on the US side if the bequest exceeded USD 100,000.",
        ],
        "estimate": {"mode": "boc_tt", "tax_note": "US Form 3520 information return, not a tax on the bequest."},
    },
    {
        "id": "R10",
        "name": "Company liquidation, capital reduction or equity-sale proceeds",
        "zh": "外商投资企业清算、减资、股权转让所得汇出",
        "category": "B",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-FXREG", "CN-PBOC3"],
        "law_text": "外汇管理条例 Art. 22 final paragraph; 个人外汇管理办法 Art. 31",
        "limit_basis": ["CN-FXREG"],
        "limit": "No cap; requires the liquidation/tax clearance and the capital-account registration to be in order.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "partly",
        "pros": [
            "A statutory entitlement: after lawful liquidation and tax payment, the foreign investor's share may be purchased and remitted.",
            "Scales to any size because it is a capital-account transaction, not a quota transaction.",
        ],
        "cons": [
            "Requires an actual corporate event - you cannot manufacture a liquidation.",
            "Multiple authorities in sequence: tax clearance, market regulator, bank, FX registration.",
        ],
        "steps": [
            "Complete the liquidation or capital reduction and obtain the tax clearance.",
            "Update the capital-account registration with the FX bureau.",
            "Present the liquidation documents, tax clearance and registration to the bank.",
            "Purchase FX and remit the distributable amount.",
        ],
        "estimate": {"mode": "boc_tt"},
    },
    {
        "id": "R11",
        "name": "Sell the mainland asset to a non-resident buyer who pays you offshore",
        "zh": "向境外买方转让资产并在境外收款",
        "category": "B",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-FXREG", "CN-PBOC3"],
        "law_text": "外汇管理条例 Art. 22; 个人外汇管理办法 Art. 26",
        "limit_basis": ["CN-FXREG"],
        "limit": "No FX cap, because no CNY-to-USD conversion inside China occurs - the consideration is "
                 "already in foreign currency offshore.",
        "cost_basis": [],
        "verifiability": "unverified",
        "pros": [
            "If it is a genuine arm's-length offshore sale, the conversion problem disappears because the "
            "proceeds never enter the mainland banking system.",
            "No Chinese FX purchase fee applies.",
        ],
        "cons": [
            "Only workable where the asset can lawfully change hands to a non-resident without an onshore settlement.",
            "Restrictions on foreigners buying mainland property, and capital-account registration duties, may block it.",
            "Pricing the deal to keep the money offshore while the asset stays in China is evasion, not structuring.",
        ],
        "steps": [
            "Confirm with a Chinese lawyer whether the specific asset class can be transferred to a non-resident with offshore settlement.",
            "Complete any required capital-account or real-estate registration.",
            "Settle offshore in USD and document the arm's-length price.",
        ],
        "estimate": {"mode": "not_applicable"},
    },

    # =================== C. BUSINESS, DIVIDENDS AND INVESTMENT ===================
    {
        "id": "R12",
        "name": "FIE dividend distribution to a foreign individual shareholder",
        "zh": "外商投资企业向外籍个人股东分配股息",
        "category": "C",
        "lawful": LAWFUL,
        "law_basis": ["CN-DIV2026", "CN-IIT"],
        "law_text": "财政部 税务总局公告2026年第27号; IIT Law Art. 2(6), Art. 3(3)",
        "limit_basis": ["CN-FXREG"],
        "limit": "No cap; distribution must come from distributable profits.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "verified",
        "pros": [
            "The 20% rate is now unambiguous and the withholding obligation sits with the company.",
            "Scales without a quota and is a routine bank transaction once the tax is paid.",
        ],
        "cons": [
            "20% withholding is the dominant cost - far larger than any bank fee.",
            "The old 'foreign individuals are exempt' claim is dead for payments from 2026-09-01.",
            "Needs genuine distributable profit and a board resolution.",
        ],
        "steps": [
            "Pass the profit-distribution resolution.",
            "The company withholds 20% and files within 15 days of the month after payment.",
            "Obtain the withholding certificate.",
            "The company or you apply at the bank to remit the net dividend.",
        ],
        "estimate": {"mode": "boc_tt", "tax_rate": 0.20, "tax_basis": "CN-DIV2026"},
    },
    {
        "id": "R13",
        "name": "Foreign-investor special account (资本金/外投) after approval",
        "zh": "外国投资者专用外汇账户",
        "category": "C",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-PBOC3"],
        "law_text": "个人外汇管理办法 Art. 31",
        "limit_basis": ["CN-PBOC3"],
        "limit": "No cap stated; account conversion requires FX-bureau approval.",
        "cost_basis": ["BOC-TARIFF"],
        "verifiability": "partly",
        "pros": [
            "Lets a genuine foreign direct investor hold and convert FX inside China lawfully.",
        ],
        "cons": [
            "Requires an approved direct-investment project - not available for personal savings.",
            "Approval-gated and slow.",
        ],
        "steps": [
            "Obtain the direct-investment approval from the competent authority.",
            "Apply to the FX bureau to open the special account.",
            "Apply for approval to convert the account balance.",
        ],
        "estimate": {"mode": "quote_only", "reason": "Approval-gated; no published fee applies to the approval step."},
    },
    {
        "id": "R14",
        "name": "Licensed outbound investment product bought while still resident (QDII and similar)",
        "zh": "合格境内机构投资者（QDII）等境外投资产品",
        "category": "C",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-PBOC3", "CN-FXREG"],
        "law_text": "个人外汇管理办法 Art. 17; 外汇管理条例 Art. 17",
        "limit_basis": ["CN-PBOC3"],
        "limit": "Subject to the individual product quota; not an unrestricted personal channel.",
        "cost_basis": [],
        "verifiability": "unverified",
        "pros": [
            "A lawful way to hold foreign-currency exposure without moving cash out yourself.",
        ],
        "cons": [
            "Only works if you are still 境内个人 at purchase time; once you are 境外个人 most domestic financial products are closed to you (Art. 23).",
            "The money stays inside the domestic custody chain - it does not become spendable USD abroad.",
        ],
        "steps": [
            "Confirm your 境内/境外 classification at the time of purchase.",
            "Buy through a licensed domestic institution within its approved quota.",
        ],
        "estimate": {"mode": "quote_only", "reason": "Product-specific fees; no published government schedule."},
    },
    {
        "id": "R15",
        "name": "Domestic FX deposit account inside China (convert now, remit later)",
        "zh": "境内个人外币存款账户",
        "category": "C",
        "lawful": LAWFUL,
        "law_basis": ["CN-PBOC3"],
        "law_text": "个人外汇管理办法 Arts. 27, 32",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "Account may hold FX. Outward remittance from the account: USD 50,000 per day with ID only; "
                 "above that documentary review (Art. 64).",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "partly",
        "pros": [
            "Converts CNY exposure into USD exposure immediately, using the same bank spread.",
            "Lets you choose the remittance timing separately from the conversion.",
            "Remittance from an FX account up to USD 50,000 a day needs only ID.",
        ],
        "cons": [
            "The money is still in China and remains reportable as a foreign account.",
            "You pay the spread now and again on any later conversion.",
            "Does not create a right to remit capital-account money later.",
        ],
        "steps": [
            "Open or confirm the 外币储蓄账户 at the bank.",
            "Purchase FX into the account and keep the 结售汇 slip.",
            "Remit later within the Art. 64 rules, or convert back if needed.",
        ],
        "estimate": {"mode": "boc_tt"},
    },
    {
        "id": "R16",
        "name": "B-share or cross-border securities account for a foreign individual",
        "zh": "境外个人B股及跨境证券账户",
        "category": "C",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-PBOC3"],
        "law_text": "个人外汇管理办法 Arts. 17, 23",
        "limit_basis": ["CN-PBOC3"],
        "limit": "Securities-specific; not a remittance channel for existing cash.",
        "cost_basis": [],
        "verifiability": "unverified",
        "pros": [
            "A recognised lawful investment channel for foreign individuals.",
        ],
        "cons": [
            "Converts savings into market exposure, which is a different decision from moving money.",
            "Capital is then subject to securities repatriation rules, not personal remittance rules.",
        ],
        "steps": [
            "Confirm eligibility for the specific account type.",
            "Open through a licensed domestic securities institution.",
        ],
        "estimate": {"mode": "quote_only", "reason": "Brokerage-specific; no published government schedule."},
    },

    # =================== D. CASH, CARDS, WALLETS, RETAIL CHANNELS ===================
    {
        "id": "R17",
        "name": "Spend on a mainland-issued card abroad (no conversion by you)",
        "zh": "境内银行卡境外消费",
        "category": "D",
        "lawful": LAWFUL,
        "law_basis": ["CN-CARDS2017", "CN-GUIDE2020"],
        "law_text": "SAFE 汇发〔2017〕29号 Q&A; 经常项目指引(2020) Art. 76(3)",
        "limit_basis": ["CN-CARDS2017"],
        "limit": "Card spending abroad does not consume the USD 50,000 facilitation quota. The CNY 100,000 "
                 "annual cap applies to cash withdrawals, not to purchases.",
        "cost_basis": [],
        "verifiability": "partly",
        "pros": [
            "Legitimate, quota-free, and the card network does the conversion.",
            "Useful for travel, tuition and genuine consumption.",
        ],
        "cons": [
            "Purchases, not cash: it cannot fund a US bank account.",
            "The card conversion rate and any card FX fee are set by the issuer and are not published in a way "
            "that can be modelled here.",
            "Spending down USD 400,000 of consumption you do not need is not a transfer strategy.",
        ],
        "steps": [
            "Use the card for genuine consumption abroad.",
            "Keep the statements for US reporting and for the foreign-account question.",
        ],
        "estimate": {"mode": "limit_only", "reason": "Issuer card FX fee is not published as a schedule."},
    },
    {
        "id": "R18",
        "name": "Overseas ATM cash withdrawal on a mainland card",
        "zh": "境内银行卡境外提取现金",
        "category": "D",
        "lawful": LAWFUL,
        "law_basis": ["CN-CARDS2017"],
        "law_text": "SAFE 汇发〔2017〕29号",
        "limit_basis": ["CN-CARDS2017", "CN-GUIDE2020"],
        "limit": "CNY 10,000 equivalent per card per day; CNY 100,000 equivalent per person per calendar year "
                 "across all cards. Exceeding it suspends overseas cash access for this year and next.",
        "cost_basis": [],
        "verifiability": "verified",
        "pros": [
            "Small, lawful, and simple.",
        ],
        "cons": [
            "CNY 100,000 a year is roughly USD 14,000 - nowhere near USD 400,000.",
            "Attracts ATM and issuer fees plus a spread that is not published as a schedule.",
            "Breaching the annual cap triggers an automatic suspension and possible penalties.",
            "Carrying cash into the US above USD 10,000 requires a FinCEN 105 report.",
        ],
        "steps": [
            "Withdraw within the per-card daily and per-person annual limits.",
            "If carrying more than USD 10,000 into the US, file FinCEN 105.",
        ],
        "estimate": {"mode": "limit_only", "reason": "ATM and issuer fees are not published as a schedule."},
    },
    {
        "id": "R19",
        "name": "Carry cash across the border within the permit band",
        "zh": "携带外币现钞出境",
        "category": "D",
        "lawful": LAWFUL,
        "law_basis": ["CN-GUIDE2020", "CN-FXREG"],
        "law_text": "经常项目指引(2020) Arts. 86-89; 外汇管理条例 Art. 42",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "Inbound: declare above USD 5,000. Outbound: USD 5,000-10,000 needs a 携带外汇出境许可证 from "
                 "the bank; above USD 10,000 needs one from the FX bureau. Withdrawal of cash above USD 10,000 a "
                 "day needs prior FX-bureau filing.",
        "cost_basis": [],
        "verifiability": "verified",
        "pros": [
            "Lawful inside the bands, and no bank wire fee.",
        ],
        "cons": [
            "Physically impractical and unsafe at scale, and the permit ceiling is low.",
            "Unapproved breach is an offence under Art. 42 (warning, up to 20% of the amount) and can become smuggling.",
            "US side: more than USD 10,000 at one time requires a FinCEN 105 report; structuring to avoid it is itself an offence.",
            "No insurance, no trace, no receipt.",
        ],
        "steps": [
            "Withdraw with prior FX-bureau filing if above USD 10,000 a day.",
            "Obtain the 携带外汇出境许可证 in the applicable band.",
            "Declare to China Customs and, on entry to the US, file FinCEN 105 if above USD 10,000.",
        ],
        "estimate": {"mode": "limit_only", "reason": "No published per-item fee; permit issuance fee not verified."},
    },
    {
        "id": "R20",
        "name": "Alipay or WeChat cross-border remittance",
        "zh": "支付宝/微信跨境汇款",
        "category": "D",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-GUIDE2020"],
        "law_text": "经常项目指引(2020) Arts. 120-137 (payment institutions)",
        "limit_basis": ["CN-GUIDE2020", "WISE-CNY"],
        "limit": "Payment institutions: USD 50,000 equivalent single-transaction cap (Art. 132). Wallet-side "
                 "limits vary; Wise publishes CNY 50,000 per Alipay transfer.",
        "cost_basis": [],
        "verifiability": "partly",
        "pros": [
            "Fast and app-based; familiar.",
            "Uses the same regulated payment-institution framework as larger providers.",
        ],
        "cons": [
            "Tight per-transaction caps make a large balance a long series of small moves.",
            "Fees and the FX rate are set in the app and are not published as a schedule you can audit.",
            "Eligibility is usually tied to documented purpose.",
        ],
        "steps": [
            "Confirm the wallet's eligibility and per-transfer and annual limits.",
            "Complete identity and purpose verification.",
            "Send and keep the electronic receipts.",
        ],
        "estimate": {"mode": "quote_only", "reason": "App-quoted; no published schedule."},
    },
    {
        "id": "R21",
        "name": "Licensed remittance provider with a China tax record (e.g. Wise from-CNY)",
        "zh": "持牌跨境汇款机构（凭完税记录）",
        "category": "D",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-GUIDE2020", "WISE-CNY"],
        "law_text": "经常项目指引(2020) Art. 120-137; provider terms",
        "limit_basis": ["WISE-CNY"],
        "limit": "Provider-published: CNY 300,000 per transfer from the China bank app; CNY 50,000 via Alipay; an "
                 "overall limit equal to after-tax salary evidenced by tax records.",
        "cost_basis": [],
        "verifiability": "verified",
        "pros": [
            "Transparent, licensed, and reaches a US account you own.",
            "Fees are shown before you send; no bank branch visit.",
        ],
        "cons": [
            "Eligibility is narrow: you must have worked in China and hold a China tax record showing tax paid "
            "in the last three years.",
            "The overall limit is your after-tax salary - savings outside that formula do not qualify.",
            "The recipient must be an account you own.",
        ],
        "steps": [
            "Collect China tax records covering the last three years.",
            "Complete provider verification (1-2 working days).",
            "Link your Chinese bank account or Alipay as the funding source.",
            "Send to your own overseas account and download the receipt.",
        ],
        "estimate": {"mode": "quote_only", "reason": "Provider prices per quote; no published schedule."},
    },
    {
        "id": "R22",
        "name": "International postal money order or courier of a monetary instrument",
        "zh": "国际邮政汇款/邮寄支付凭证",
        "category": "D",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-FXREG", "US-1010340"],
        "law_text": "外汇管理条例 Art. 42; 31 CFR 1010.340",
        "limit_basis": [],
        "limit": "No reliable published FX limit for personal outbound postal remittance of CNY was located. "
                 "What is published is the reporting duty: mailing or shipping monetary instruments above "
                 "USD 10,000 into or out of the US requires a FinCEN 105 report.",
        "cost_basis": [],
        "limit_known": False,
        "verifiability": "unverified",
        "pros": [
            "Historically used for small family remittances.",
        ],
        "cons": [
            "No official CNY-outbound limit was found, which means the risk cannot be bounded - the safest "
            "reading is that this is not a lawful large-value channel.",
            "Mailing instruments above USD 10,000 without a report is a US offence.",
            "Loss and fraud exposure with no recourse.",
        ],
        "steps": [
            "Do not use for material amounts without written guidance from the bank and the FX bureau.",
        ],
        "estimate": {"mode": "quote_only", "reason": "No published limit or fee; deliberately left blank."},
    },

    # =================== E. KEEP IN PLACE / AVOID CONVERSION ===================
    {
        "id": "R23",
        "name": "Leave the CNY on deposit and spend it on future trips to China",
        "zh": "保留人民币存款、境内消费",
        "category": "E",
        "lawful": LAWFUL,
        "law_basis": ["CN-PBOC3"],
        "law_text": "个人外汇管理办法 Arts. 27-36 (accounts); no conversion occurs",
        "limit_basis": ["CN-PBOC3"],
        "limit": "Not applicable - nothing crosses the border.",
        "cost_basis": [],
        "verifiability": "verified",
        "pros": [
            "Zero conversion cost, zero remittance fee, no FX evidence burden.",
            "Keeps optionality if you return to China.",
        ],
        "cons": [
            "The money stays exposed to CNY/USD movement and to Chinese deposit rates.",
            "Still reportable to the US every year while it is a foreign account.",
            "Consuming it requires being in China.",
        ],
        "steps": [
            "Keep the account compliant and file FBAR/8938 as applicable.",
        ],
        "estimate": {"mode": "not_applicable"},
    },
    {
        "id": "R24",
        "name": "Convert inside China into USD and hold the USD in a mainland bank",
        "zh": "境内购汇后持有外币存款",
        "category": "E",
        "lawful": LAWFUL,
        "law_basis": ["CN-PBOC3", "CN-GUIDE2020"],
        "law_text": "个人外汇管理办法 Art. 32; 经常项目指引(2020) Art. 64",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "Same as R15: remittance from an FX account up to USD 50,000 a day on ID alone.",
        "cost_basis": ["BOC-TARIFF", "BOC-BOARD", "CFETS-FIX"],
        "verifiability": "partly",
        "pros": [
            "Removes CNY exposure at a known spread.",
            "Splits the conversion decision from the remittance decision.",
        ],
        "cons": [
            "Two spreads instead of one if it is later converted back.",
            "Chinese USD deposit rates are typically lower than US rates, and the deposit remains a reportable foreign account.",
        ],
        "steps": [
            "Purchase FX into the foreign-currency savings account.",
            "Hold or remit later under Art. 64.",
        ],
        "estimate": {"mode": "boc_tt"},
    },
    {
        "id": "R25",
        "name": "Buy a globally priced asset in China (e.g. gold) and sell it abroad",
        "zh": "境内购入黄金等全球定价资产、境外出售",
        "category": "E",
        "lawful": CONDITIONAL,
        "law_basis": ["CN-PBOC3", "CN-FXREG"],
        "law_text": "个人外汇管理办法 Art. 30; 外汇管理条例 Arts. 8, 39",
        "limit_basis": [],
        "limit": "Not verified. Cross-border movement of gold and of the sale proceeds engages customs, FX and "
                 "capital-account rules that were not read in this session.",
        "cost_basis": [],
        "limit_known": False,
        "verifiability": "unverified",
        "pros": [
            "Gold is globally priced, so in theory the conversion is embedded in the asset.",
        ],
        "cons": [
            "Taking the metal out of China is itself a customs and FX event with its own limits.",
            "The purchase premium, the assay and resale discount, and the insurance usually exceed the FX spread you were avoiding.",
            "Carrying value out inside an asset without declaration is evasion if the purpose is to defeat FX controls.",
        ],
        "steps": [
            "Do not treat this as a conversion channel without written customs and FX advice specific to the asset.",
        ],
        "estimate": {"mode": "quote_only", "reason": "No published end-to-end cost; left blank."},
    },
    {
        "id": "R26",
        "name": "Use the balance for genuine obligations that are payable in CNY",
        "zh": "用于境内应付的人民币义务",
        "category": "E",
        "lawful": LAWFUL,
        "law_basis": ["CN-FXREG"],
        "law_text": "外汇管理条例 Art. 5, Art. 12 (genuine current-account payments)",
        "limit_basis": [],
        "limit": "Bounded only by the genuine obligation itself.",
        "cost_basis": [],
        "verifiability": "partly",
        "pros": [
            "No conversion at all: paying a Chinese supplier, tuition, medical bills or taxes in CNY is a "
            "current-account payment, not a capital transfer.",
            "Often the cheapest way to get value out of a trapped balance - you get the goods or services.",
        ],
        "cons": [
            "You receive value, not dollars; it does not fund a US account.",
            "Paying a non-existent obligation to move money to a related party offshore is evasion.",
        ],
        "steps": [
            "Identify genuine CNY obligations and pay them from the account.",
            "Keep the invoices and contracts.",
        ],
        "estimate": {"mode": "not_applicable"},
    },

    # =================== F. PROHIBITED / UNLAWFUL ===================
    {
        "id": "R27",
        "name": "Underground bank / private FX dealer (地下钱庄, 对敲)",
        "zh": "地下钱庄、变相买卖外汇",
        "category": "F",
        "lawful": PROHIBITED,
        "law_basis": ["CN-FXREG", "CN-PBOC3"],
        "law_text": "外汇管理条例 Art. 45; 个人外汇管理办法 Art. 7",
        "limit_basis": ["CN-FXREG"],
        "limit": "Not applicable - the activity is unlawful at any size.",
        "cost_basis": [],
        "risk_basis": ["CN-FXREG"],
        "verifiability": "verified",
        "pros": [],
        "cons": [
            "Warning, confiscation of the illegal gain, and a fine of up to 30% of the amount, or 30%-100% if serious (Art. 45); criminal liability follows where it constitutes a crime.",
            "The counterparty usually holds the funds, and there is no legal recourse when they disappear.",
            "You become a participant in the counterparty's money-laundering chain, which is a separate exposure.",
        ],
        "steps": [],
        "estimate": {"mode": "prohibited"},
    },
    {
        "id": "R28",
        "name": "Splitting the quota across family, friends or staff (分拆)",
        "zh": "分拆结售汇",
        "category": "F",
        "lawful": PROHIBITED,
        "law_basis": ["CN-PBOC3", "CN-GUIDE2020"],
        "law_text": "个人外汇管理办法 Art. 7; 经常项目指引(2020) Art. 62",
        "limit_basis": ["CN-GUIDE2020"],
        "limit": "Zero - the conduct is prohibited in any amount.",
        "cost_basis": [],
        "risk_basis": ["CN-PBOC3", "CN-GUIDE2020", "CN-FXREG"],
        "verifiability": "verified",
        "pros": [],
        "cons": [
            "Lending your quota to someone else brings a risk warning the first time and a place on the 'watch list' the second; borrowing someone else's puts you on it directly (Art. 62).",
            "Watch-list status lasts the current year plus two more, and every subsequent transaction then needs full documentary review.",
            "Penalties under the FX Regulations follow, and the receiving bank may close the relationship.",
        ],
        "steps": [],
        "estimate": {"mode": "prohibited"},
    },
    {
        "id": "R29",
        "name": "Crypto or stablecoin conversion (USDT intermediation)",
        "zh": "虚拟货币/稳定币兑换",
        "category": "F",
        "lawful": PROHIBITED,
        "law_basis": ["CN-VA2026", "CN-FXREG"],
        "law_text": "银发〔2026〕42号; 外汇管理条例 Art. 45",
        "limit_basis": ["CN-VA2026"],
        "limit": "Prohibited as business activity in mainland China at any size.",
        "cost_basis": [],
        "risk_basis": ["CN-VA2026", "CN-FXREG"],
        "verifiability": "verified",
        "pros": [],
        "cons": [
            "Virtual-currency business activity is characterised as illegal financial activity and strictly prohibited; the 2021 notice it replaced has been repealed, so older guides are out of date.",
            "Financial and payment institutions may not provide account, transfer or settlement services for it, so the CNY leg usually has to go through an unlawful intermediary anyway.",
            "Where a court treats the token as the medium for converting CNY into FX, it is analysed as disguised FX dealing under Art. 45.",
        ],
        "steps": [],
        "estimate": {"mode": "prohibited"},
    },
    {
        "id": "R30",
        "name": "False or inflated trade and service documents",
        "zh": "虚构贸易背景、虚假单证",
        "category": "F",
        "lawful": PROHIBITED,
        "law_basis": ["CN-FXREG", "CN-GUIDE2020", "CN-PBOC3"],
        "law_text": "外汇管理条例 Arts. 12, 39, 40; 经常项目指引(2020) Art. 47",
        "limit_basis": ["CN-FXREG"],
        "limit": "Zero - prohibited.",
        "cost_basis": [],
        "risk_basis": ["CN-FXREG"],
        "verifiability": "verified",
        "pros": [],
        "cons": [
            "Using false or invalid documents to buy FX is 非法套汇: refund of the funds and a fine of up to 30%, or 30%-100% if serious (Art. 40).",
            "Moving funds abroad by deception is 逃汇 under Art. 39 with the same ladder.",
            "The bank is separately penalised (Art. 47), which is why it audits the underlying documents.",
        ],
        "steps": [],
        "estimate": {"mode": "prohibited"},
    },
]

CATEGORY_NAMES = {
    "A": "Current account - income you can document",
    "B": "Capital account - property, inheritance and business exit",
    "C": "Business, dividends and investment",
    "D": "Cash, cards, wallets and retail channels",
    "E": "Keep in place, or avoid converting at all",
    "F": "Prohibited - do not use",
}

CATEGORY_BLURB = {
    "A": "The only family of routes without a hard amount ceiling, but each requires an evidence chain from the "
         "CNY to specific lawful income. Start here if any part of the balance is documented earnings.",
    "B": "The lawful home for pre-emigration savings and inherited assets. All of these are approval-gated, and "
         "none of them is a way to relabel income you cannot document.",
    "C": "Company-level and investment routes. Real costs here are Chinese taxes, not bank fees.",
    "D": "Small, fast and capped. Useful for genuine consumption; incapable of moving a six-figure balance.",
    "E": "Sometimes the right answer is not to convert. These rows exist so the comparison is honest about the "
         "zero-cost option and about the routes that only look clever.",
    "F": "Listed because they are what people are actually offered. They carry the largest expected cost of any "
         "row on this site, and no execution steps are published here.",
}
