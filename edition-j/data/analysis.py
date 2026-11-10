"""Edition J findings, penalty decomposition and the flag register.

Nothing here is a new factual claim: each line restates something read in this
session and points at the source id that carries the text. Where the honest
answer is 'unknown', the value is None and the flag says why.
"""

# ---------- headline findings ----------
FINDINGS = [
    {
        "id": "J1",
        "title": "Converting CNY to USD is not a taxable event in either jurisdiction",
        "detail": "China taxes nine enumerated categories of income; currency exchange is not one of them "
                  "(IIT Law Art. 2). The US taxes your income, not the act of changing currency, and for an "
                  "individual's personal transaction §988(e)(2) disregards exchange-rate gain unless it exceeds "
                  "USD 200. So the 'tax on converting' in the brief does not exist as a separate charge.",
        "sources": ["CN-IIT", "US-988"],
    },
    {
        "id": "J2",
        "title": "What people experience as a conversion penalty is a bank spread, and it is small",
        "detail": "On the BOC board read for this edition, one USD costs CNY 6.6903 to buy and fetches CNY 6.6622 "
                  "to sell. The gap is 0.42% of the bid, so a round trip costs that much and a single conversion "
                  "costs about 0.21% - half the spread, measured against the bank's own mid. That is the entire "
                  "'penalty' at the currency layer. Note that comparing the ask to the PBOC central parity gives a "
                  "negative number on this snapshot, because the two are from different days; see the explanation "
                  "on the penalty page.",
        "sources": ["BOC-BOARD", "CFETS-FIX"],
    },
    {
        "id": "J3",
        "title": "The real barrier is convertibility, not tax",
        "detail": "Current-account items are convertible in principle; capital-account items follow a "
                  "'convertibility process' that means approval (Measures Art. 3). A balance with no documented "
                  "current-account source has no default lawful route, which is why it feels stuck.",
        "sources": ["CN-PBOC3"],
    },
    {
        "id": "J4",
        "title": "A US passport changes which quota applies - and usually helps",
        "detail": "The USD 50,000 annual facilitation quota is framed around 境内个人 (Chinese citizens with a "
                  "resident ID). For 境外个人 buying against documented lawful current-account income, Art. 59 of "
                  "the 2020 Guide states no annual cap. The binding constraint becomes evidence, not size.",
        "sources": ["CN-GUIDE2020"],
    },
    {
        "id": "J5",
        "title": "The largest number on this site is a US penalty, not a Chinese fee",
        "detail": "A willful FBAR violation carries a civil maximum of the greater of USD 165,353 or 50% of the "
                  "account balance at the time of the violation. At USD 400,000 that is USD 200,000 - roughly "
                  "46 times the entire bank cost of moving the money.",
        "sources": ["US-5321", "US-1010821"],
    },
    {
        "id": "J6",
        "title": "Chinese tax on the money can dwarf every fee, and one exemption just ended",
        "detail": "Interest, dividends, asset transfers and incidental income are taxed at a flat 20% "
                  "(IIT Law Art. 3(3)). The long-standing exemption for foreign individuals' FIE dividends was "
                  "repealed with effect from 2026-09-01, so any guide still calling those dividends tax-free is out "
                  "of date.",
        "sources": ["CN-IIT", "CN-DIV2026"],
    },
    {
        "id": "J7",
        "title": "Six of the thirty catalogued routes are prohibited, and one has a fresh legal basis",
        "detail": "Dealer intermediation, quota splitting, crypto, and false documents are joined by two more "
                  "structural traps. The crypto basis changed on 2026-02-06: 银发〔2026〕42号 replaced the 2021 "
                  "notice entirely.",
        "sources": ["CN-FXREG", "CN-VA2026", "CN-GUIDE2020"],
    },
    {
        "id": "J8",
        "title": "Staging rules you may find online for property transfers were cancelled in 2014",
        "detail": "The 2004 Measures required emigrant transfers in three stages over two years. 汇发〔2014〕2号 "
                  "Section VI cancelled the staging, the national-level filing above RMB 500,000, and the "
                  "notarisation duty. The 2026 SAFE Q&A still cites the 2004 Measures without restating the "
                  "amendment, which is how the stale version keeps circulating.",
        "sources": ["CN-PROPERTY2004", "CN-CAP2014", "CN-PROPERTYQA"],
    },
    {
        "id": "J9",
        "title": "No method in this catalogue can be given an exact all-in price today",
        "detail": "Two components are published and computed here: the FX spread and the BOC sender tariff. "
                  "Receiving-bank fees, intermediary charges, Chinese tax on the underlying income, and "
                  "notarisation or travel costs are all unknown for this account. Those cells are blank on "
                  "purpose and counted on the verification page.",
        "sources": ["BOC-TARIFF", "BOC-BOARD"],
    },
    {
        "id": "J10",
        "title": "The cheapest lawful route is the one that matches how the money was earned",
        "detail": "If the balance is documented salary or service income, R01 is lawful, uncapped and priced. If "
                  "it is pre-emigration savings, R08 needs an approval but no quota. If it is inherited, R09 does. "
                  "The choice is decided by evidence you already have, not by provider shopping.",
        "sources": ["CN-PBOC3", "CN-GUIDE2020", "CN-PROPERTY2004"],
    },
]

# ---------- conversion-penalty decomposition ----------
# kind: unavoidable | avoidable | tax-on-income | penalty-risk | baseline
PENALTY_LINES = [
    {
        "id": "P01",
        "component": "Bank FX spread (bid/ask)",
        "kind": "unavoidable",
        "value": "computed",
        "basis": "BOC board 666.22 / 669.03; half of the 0.4218% bid/ask spread",
        "sources": ["BOC-BOARD"],
        "note": "Paid on every conversion, at every size, and not deductible anywhere. Measured against the bank's "
                "own mid, not against the PBOC parity, because the two are published at different times.",
    },
    {
        "id": "P02",
        "component": "Bank commission on cross-border TT",
        "kind": "unavoidable",
        "value": "computed",
        "basis": "BOC tariff: 1 per mille, min CNY 50, max CNY 260",
        "sources": ["BOC-TARIFF"],
        "note": "Caps out at CNY 260, so it shrinks to rounding at large sizes.",
    },
    {
        "id": "P03",
        "component": "Cable / postage charge",
        "kind": "unavoidable",
        "value": "computed",
        "basis": "BOC tariff: CNY 150 non-HK/Macau/Taiwan, CNY 80 for HK/Macau/Taiwan",
        "sources": ["BOC-TARIFF"],
        "note": "Flat per transfer, so splitting a transfer into pieces multiplies it.",
    },
    {
        "id": "P04",
        "component": "Correspondent and receiving-bank charges",
        "kind": "unavoidable",
        "value": None,
        "basis": "Not published by any bank read in this session",
        "sources": ["BOC-TARIFF"],
        "note": "Typically deducted by the receiving bank; the amount depends on your US bank. Left blank.",
    },
    {
        "id": "P05",
        "component": "Chinese tax on the underlying income",
        "kind": "tax-on-income",
        "value": "20% on the enumerated categories",
        "basis": "IIT Law Art. 3(3); dividends from 2026-09-01 under 2026 No. 27",
        "sources": ["CN-IIT", "CN-DIV2026"],
        "note": "Not a conversion tax. It is due whether or not you move the money, and it is the largest "
                "legitimate cost for income-type balances.",
    },
    {
        "id": "P06",
        "component": "Chinese tax on asset-transfer gain",
        "kind": "tax-on-income",
        "value": "20% of gain after original value and reasonable expenses",
        "basis": "IIT Law Art. 2(8), Art. 6(5)",
        "sources": ["CN-IIT"],
        "note": "Property and equity sales. Computed on gain; the basis is unknown here, so no amount is shown.",
    },
    {
        "id": "P07",
        "component": "US income tax on the same income",
        "kind": "tax-on-income",
        "value": None,
        "basis": "Worldwide taxation; foreign tax credit against it",
        "sources": ["US-IRS-ABROAD"],
        "note": "Depends on your bracket and on the credit for Chinese tax already paid. Not calculable from the "
                "facts supplied.",
    },
    {
        "id": "P08",
        "component": "US §988 exchange gain on the currency itself",
        "kind": "tax-on-income",
        "value": "excluded for personal transactions up to USD 200 of gain",
        "basis": "26 U.S.C. §988(e)(2)-(3)",
        "sources": ["US-988"],
        "note": "For an individual's personal transaction the gain is disregarded; above USD 200 the exclusion "
                "withdraws. Basis and holding period are unknown.",
    },
    {
        "id": "P09",
        "component": "SAFE fine for evasion or illegal FX purchase",
        "kind": "penalty-risk",
        "value": "up to 30%, or 30%-100% if serious",
        "basis": "外汇管理条例 Arts. 39, 40",
        "sources": ["CN-FXREG"],
        "note": "The real 'conversion penalty' people describe. It is a punishment, not a fee: zero if the route "
                "is lawful.",
    },
    {
        "id": "P10",
        "component": "SAFE fine for cash or private dealing",
        "kind": "penalty-risk",
        "value": "up to 20% (cash), up to 30% (private dealing)",
        "basis": "Arts. 42, 45",
        "sources": ["CN-FXREG"],
        "note": "Applies to unapproved cash movement and to dealer transactions.",
    },
    {
        "id": "P11",
        "component": "Watch-list consequence of splitting",
        "kind": "penalty-risk",
        "value": "current year plus two more years of enhanced review",
        "basis": "经常项目指引(2020) Art. 62",
        "sources": ["CN-GUIDE2020"],
        "note": "A non-monetary cost with a long tail: every transaction afterwards is document-heavy.",
    },
    {
        "id": "P12",
        "component": "FBAR civil penalty",
        "kind": "penalty-risk",
        "value": "USD 16,536 non-willful / USD 165,353 or 50% willful",
        "basis": "31 U.S.C. §5321(a)(5); 31 CFR 1010.821",
        "sources": ["US-5321", "US-1010821"],
        "note": "Per violation, inflation-adjusted. This is the only component that can exceed the balance.",
    },
    {
        "id": "P13",
        "component": "Form 8938 penalty",
        "kind": "penalty-risk",
        "value": "USD 10,000 plus up to USD 50,000 more",
        "basis": "26 U.S.C. §6038D(d)",
        "sources": ["US-6038D"],
        "note": "Capped, and unlike the FBAR it is tied to the filed return.",
    },
    {
        "id": "P14",
        "component": "Form 3520 late information return",
        "kind": "penalty-risk",
        "value": None,
        "basis": "Instructions for Form 3520 penalties section",
        "sources": ["US-3520"],
        "note": "The 25%/35% figures circulating are not stated on the page read here, so no number is shown.",
    },
    {
        "id": "P15",
        "component": "Chinese tax already withheld on the income",
        "kind": "baseline",
        "value": "not a conversion cost",
        "basis": "Sunk at the moment the income arose",
        "sources": ["CN-IIT"],
        "note": "Listed so it is not double-counted as a cost of moving the money.",
    },
    {
        "id": "P16",
        "component": "Time value of the money while it is stuck",
        "kind": "baseline",
        "value": None,
        "basis": "Requires your alternative USD return",
        "sources": ["US-IRS-FX"],
        "note": "Honest answer is a range from zero to substantial; not computable without your opportunity cost.",
    },
    {
        "id": "P17",
        "component": "Round-trip spread if converted twice",
        "kind": "avoidable",
        "value": "double P01",
        "basis": "Arithmetic on the same board",
        "sources": ["BOC-BOARD"],
        "note": "Avoided by converting once, in the right direction, at the right time.",
    },
    {
        "id": "P18",
        "component": "Extra cable fees from splitting into many transfers",
        "kind": "avoidable",
        "value": "CNY 150 x number of extra transfers",
        "basis": "BOC tariff",
        "sources": ["BOC-TARIFF"],
        "note": "The one fee that is entirely within your control.",
    },
    {
        "id": "P19",
        "component": "Notarisation, translation and agent fees",
        "kind": "avoidable",
        "value": None,
        "basis": "Notarisation duty for property-rights documents was cancelled in 2014",
        "sources": ["CN-CAP2014"],
        "note": "Still charged in practice by some agents. No official schedule exists, so blank.",
    },
    {
        "id": "P20",
        "component": "Travel and time to attend in person",
        "kind": "avoidable",
        "value": None,
        "basis": "No published figure",
        "sources": ["CN-SHFAQ"],
        "note": "Real but personal; left blank rather than estimated.",
    },
    {
        "id": "P21",
        "component": "Provider fees (Wise, Alipay, banks other than BOC)",
        "kind": "avoidable",
        "value": None,
        "basis": "Quote-based; no published schedule on the pages read",
        "sources": ["WISE-CNY"],
        "note": "The Wise page says to check live pricing, so there is nothing to transcribe.",
    },
    {
        "id": "P22",
        "component": "Penalty for a false declaration on entry to the US",
        "kind": "penalty-risk",
        "value": None,
        "basis": "31 CFR 1010.340 (reporting duty); penalty amount not read in this session",
        "sources": ["US-1010340"],
        "note": "The duty is verified; the penalty figure is not, so it is blank.",
    },
    {
        "id": "P23",
        "component": "Cost of doing nothing",
        "kind": "baseline",
        "value": "zero fees, full currency and country exposure",
        "basis": "Arithmetic",
        "sources": ["CN-PBOC3"],
        "note": "The comparison baseline. Not free, but no cash leaves.",
    },
    {
        "id": "P24",
        "component": "Bank spread on a CNY-USD-CNY round trip",
        "kind": "avoidable",
        "value": "computed",
        "basis": "Same board, both directions",
        "sources": ["BOC-BOARD"],
        "note": "Shown so the 0.42%-style figures quoted elsewhere can be reconciled: they are round-trip numbers.",
    },
]

# ---------- flag register ----------
# severity: high | medium | low
FLAGS = [
    {
        "id": "FJ01",
        "severity": "high",
        "title": "Account-specific facts are unknown",
        "detail": "Bank, account holder classification (境内个人 vs 境外个人), balance, source of funds, residency "
                  "status, filing history and receiving bank are all unknown. Every all-in cost and every tax "
                  "figure that depends on them is blank on this site, including whether FBAR is owed at all.",
        "sources": ["CN-PBOC3", "US-IRS-ABROAD", "US-FBAR"],
    },
    {
        "id": "FJ02",
        "severity": "high",
        "title": "Rates move; the board and parity are snapshots",
        "detail": "The BOC board is timestamped 2026/11/10 07:32:39 and the parity 2026-11-09 09:15. The board "
                  "itself states the counter/online rate governs, so every computed FX figure is illustrative of "
                  "that timestamp, not a quote.",
        "sources": ["BOC-BOARD", "CFETS-FIX"],
    },
    {
        "id": "FJ03",
        "severity": "high",
        "title": "Form 3520 penalty percentages left blank",
        "detail": "Widely quoted 25%/35% late-filing percentages were not found in the instructions chunk read here. "
                  "The row stays blank rather than repeating an unverified figure.",
        "sources": ["US-3520", "US-8938"],
    },
    {
        "id": "FJ04",
        "severity": "medium",
        "title": "Two SAFE property-transfer texts conflict on staging",
        "detail": "The 2004 Measures still contain staged release. 汇发〔2014〕2号 Section VI cancelled it, and the "
                  "2026 Tianjin Q&A cites the 2004 text without mentioning the amendment. Read together, single or "
                  "instalment release after approval is correct; a branch applying the old text would not be.",
        "sources": ["CN-PROPERTY2004", "CN-CAP2014", "CN-PROPERTYQA"],
    },
    {
        "id": "FJ05",
        "severity": "medium",
        "title": "Virtual-currency notice read from a government reprint",
        "detail": "银发〔2026〕42号 was read on a Shenzhen district government portal because the PBOC page did not "
                  "load from this sandbox. The content is consistent across the reprints located, but the canonical "
                  "PBOC URL is the one to cite in a filing.",
        "sources": ["CN-VA2026"],
    },
    {
        "id": "FJ06",
        "severity": "medium",
        "title": "US Code read via Cornell, not uscode.house.gov",
        "detail": "uscode.house.gov granule links returned 404 and govinfo was unreachable from this sandbox, so "
                  "§988, §5321 and §6038D were read on the Legal Information Institute's republication. The IRS and "
                  "eCFR pages used for FBAR and the inflation table are primary.",
        "sources": ["US-988", "US-5321", "US-6038D"],
    },
    {
        "id": "FJ07",
        "severity": "medium",
        "title": "Facilitation quota may not be available to a foreign passport holder",
        "detail": "Art. 54 frames the USD 50,000 quota around 个人结汇 and 境内个人购汇. Whether a US citizen holding a "
                  "Chinese account is booked as 境内个人 or 境外个人 is an account-level fact. R02 is marked "
                  "conditional for this reason and should not be planned around.",
        "sources": ["CN-GUIDE2020", "CN-PBOC3"],
    },
    {
        "id": "FJ08",
        "severity": "medium",
        "title": "Only one bank's tariff could be read",
        "detail": "ICBC's fee schedule page did not expose a readable tariff table and the HSBC PDF returned 404. "
                  "All fee arithmetic therefore uses BOC alone; other banks may differ in either direction, and "
                  "BOC's own note 1 allows agreed or local pricing.",
        "sources": ["BOC-TARIFF"],
    },
    {
        "id": "FJ09",
        "severity": "low",
        "title": "Postal remittance limit unverified",
        "detail": "No official CNY-outbound limit or fee for international postal money orders could be confirmed. "
                  "The row carries no limit and no price, and is not recommended for material amounts.",
        "sources": ["US-1010340"],
    },
    {
        "id": "FJ10",
        "severity": "low",
        "title": "Receiving-bank fees are blank everywhere",
        "detail": "No US bank's incoming wire fee was read in this session, so no receiver cost is included in any "
                  "row. Adding one would change every all-in total, which is why the totals stay blank rather than "
                  "half-complete.",
        "sources": ["BOC-TARIFF"],
    },
    {
        "id": "FJ11",
        "severity": "low",
        "title": "Gold and offshore-asset routes are unverified",
        "detail": "R25 and R11 rest on rules read only in outline (customs, capital registration, foreign buyer "
                  "restrictions). They are listed for completeness with no estimate and no limit.",
        "sources": ["CN-FXREG", "CN-PBOC3"],
    },
    {
        "id": "FJ12",
        "severity": "medium",
        "title": "Chinese tax on the underlying income is not modelled per route",
        "detail": "Only the flat 20% categories can be computed from a published rate; whether that tax has already "
                  "been withheld, and on what base, is unknown. R06 and R12 show a 20% figure for the withholding "
                  "case only, and no figure is claimed for capital gains because the basis is unknown.",
        "sources": ["CN-IIT", "CN-DIV2026"],
    },
]
