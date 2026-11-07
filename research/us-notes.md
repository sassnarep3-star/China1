# US federal evidence notes — T2

Verified 2026-11-07 UTC by `arena-489b75a1-china1`. Structured evidence: `research/us.json`.

## Core distinction

Do not calculate a "repatriation tax" by multiplying an unknown CNY balance by a guessed rate. Analyze:

1. Tax on the income or asset disposition that originally generated the funds, in the correct year.
2. Any later foreign-currency gain/loss under the applicable functional-currency and transaction rules.
3. Any separate transfer excise actually within scope (the verified 2026 US excise concerns specified outbound-from-US funding, not an inbound China-to-US wire by default).
4. Account/asset/gift/trust/entity information reporting, which is not itself a tax on principal.
5. Commercial FX spread and transfer charges, which require quotes and are not tax rates.

No reviewed official source was used to assert that every international transfer is universally tax-free. The legal analysis is deliberately bounded to the cited rules and missing facts.

## What was read directly

- Publication 54 chapter 1, including the actual **Blocked Income** section, not just a search snippet. It describes a specific nonconvertibility condition, an information-return election, unblocking events and accounting-method permissions. Being "stuck" is not enough to establish eligibility.
- IRS foreign-tax-credit overview and computation pages; Publication 514's currency/translation section.
- FEIE eligibility, income classification and the separate current **Figuring the foreign earned income exclusion** page giving the 2026 USD 132,900 maximum. The overview's old amounts through 2023 are not used as current.
- US–China treaty articles and Protocol paragraph 2, including the saving clause preserving US citizen taxation and the exchanged notes excluding tax sparing at signing.
- Official 2024 US Code section 988 PDF, including nonfunctional-currency deposits, ordinary treatment and the personal-transaction exclusion condition. The live US Code site is in a temporary format and the attempted section URLs returned Page Not Found. The edition/currentness limitation is published rather than hidden.
- IRS and FinCEN FBAR pages; IRS FATCA thresholds; current Form 3520 instructions and foreign-gift page; Forms 8621/5471 overviews.
- Streamlined overview and the separate foreign/domestic procedure pages, including conditions, covered years and penalty bases. No assumption is made that the user is delinquent or non-willful.
- IRS NIIT, main-home exclusion and self-employment pages; SSA's current agreement-country table (China is not listed).
- CBP's current money/monetary-instruments page and the IRS April 2026 release on the new outbound US remittance excise.

All URLs, source dates where published, locators and access limitations are recorded in `us.json`.

## Important corrections

- **USD 200 is not a currency-gain allowance:** section 988(e)'s exclusion does not apply if the otherwise recognized personal-transaction gain exceeds USD 200. Do not describe only the excess as taxable. Do not assume business/investment currency transactions are personal transactions.
- **FEIE is not a savings exclusion:** it applies to qualifying earned income for the relevant work year, subject to tax-home/residence/presence and timing rules. Dividends, interest, capital gains and pensions are not foreign earned income.
- **FTC is not automatic dollar-for-dollar relief:** qualification, categories, source adjustments and the limitation matter. No credit for the tax allocable to excluded income.
- **FBAR and FATCA are different:** the former uses an aggregate account maximum above USD 10,000; the latter uses different assets, year-end/any-time values, filing status and residence conditions.
- **Form 3520 is not a way to relabel own savings as a gift.** Foreign trusts have separate reporting rules. A company/PFIC wrapper can add US reporting and tax complexity rather than solve exchange controls.
- **Streamlined is conditional compliance relief, not a transfer channel or amnesty.** The domestic 5% base is a defined covered-asset base, not necessarily the entire current balance.
- **US cash reporting is not a carrying cap:** CBP requires a report above USD 10,000; it does not establish China's exit permission. China-side cash thresholds remain unresolved in T1.
- **Do not import the new US 1% outbound excise into an inbound wire:** the IRS release's direction and physical-instrument funding scope matter. Its April 2026 regulatory details were proposed; final details were not verified here.

## Unverified / review items

- No state or locality was supplied. State tax is blank, not zero.
- No income source, year, tax home, travel days, treaty residence, CNY basis, functional currency, other-account values or filing history was supplied. Personal liability and penalty amounts are blank.
- The current live section 988 consolidation could not be retrieved. The official 2024 statutory text is cited with an explicit review flag, not represented as a verified 2026 consolidated page.
- Specialized pension/trust/PFIC/entity treatment cannot be determined without the actual instruments. No such holdings are inferred.
- Failed old IRS FBAR/FATCA URLs and unsuccessful US Code/GovInfo path variants are not used as evidence. Working official replacements are in the JSON.

## Integration instructions

Render requirements, findings, unknowns and flags with their source links. Keep null values blank and visibly unverified. Do not collapse federal reporting thresholds into transfer limits or imply that changing the money-transfer provider changes the underlying income tax. T3 owns cross-jurisdiction synthesis and route comparisons.
