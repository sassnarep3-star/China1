# Independent targeted review — 2026-11-11

This is a targeted review, not a new line-by-line certification of the entire repository, every historic edition, or every external link. The automated verifier checks link syntax and local targets, arithmetic and presence of source links; it does not prove each cited source supports each assertion or remains current.

## Checked against official sources

- [SAFE Tianjin](https://www.safe.gov.cn/tianjin/2026/0713/3088.html): the cited salary answer requires identification and evidence of the amount and source, including tax vouchers, for eligible foreign individuals' lawful current-account CNY income. It does not establish the user's funds qualify or guarantee a particular bank will process the transaction.
- [IRS foreign tax credit](https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit): credit or deduction may be available for qualifying foreign taxes; eligibility, limits and exclusions matter. Prior text implying an automatic credit was corrected.
- [26 USC 988](https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm): nonfunctional-currency disposition and the personal-transaction exception have statutory conditions. Earlier unconditional phrasing was qualified. Individual currency gain or loss and basis remain unknown.
- [IRS FBAR and Form 8938 comparison](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements): FBAR generally uses aggregate account value exceeding $10,000; Form 8938 thresholds vary by residence and filing status. Earlier summary wording was qualified.
- [Bank of China foreign exchange board](https://www.boc.cn/sourcedb/whpj/): on 2026-11-11 the displayed USD selling rate was 669.11 CNY per 100 USD at 10:25:02 Beijing time. The guide uses the explicitly dated 2026-11-10 snapshot of 668.51; it is not a quote for this user's transaction. The board itself says the actual transaction rate applies. No personal executable quote was obtained.

## Remaining irregularities

F23 is published in the guide's Flagged for Review page. The user's residency, source and amount of funds, past tax treatment, exchange-rate basis, receiving bank and executable fees are unknown; consequently no personalized best route, all-in cost or tax liability can be confirmed. Existing costs are scenario estimates with exclusions, not confirmed prices; blank costs should remain blank. Penalty numbers depend on applicable law and assessment dates. The archival editions are preserved and were not re-certified in this session. External source links were not exhaustively checked. Site-wide source-link presence does not establish line-by-line factual verification.

## Verification

`python3 guide/build/build.py && python3 guide/build/verify.py`: 10 pages; 1,018 sourced rows, 19 methods × 40 ladder amounts, 370 totals independently recomputed; 278 HTML files and 22,546 internal links checked; deterministic rebuild. This verifies only what the checker implements.
