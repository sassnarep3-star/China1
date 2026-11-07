#!/usr/bin/env python3
"""Build a dependency-free, static evidence dashboard; all URLs are relative to the site root."""
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = {
 'salary': ('SAFE Tianjin · salary FX, 2026', 'https://www.safe.gov.cn/tianjin/2026/0713/3088.html'),
 'incomes': ('SAFE Tianjin · income and tax evidence', 'https://www.safe.gov.cn/tianjin/2021/1102/1777.html'),
 'rules': ('SAFE · individual FX rules, amended', 'https://www.safe.gov.cn/tianjin/2024/0430/2464.html'),
 'general': ('SAFE · individual FX measures', 'https://www.safe.gov.cn/tianjin/2024/0430/2465.html'),
 'residence': ('SAFE Tianjin · permanent residence card', 'https://www.safe.gov.cn/tianjin/2025/1113/2926.html'),
 'property': ('Shanghai government · property proceeds', 'https://english.shanghai.gov.cn/en-FAQHome/20240204/b4426264395b4fa3adfde73778c94ad4.html'),
 'inherit': ('SAFE · capital-account changes', 'https://www.safe.gov.cn/en/2014/0801/741.html'),
 'oldinherit': ('PBOC · provisional asset-transfer rules', 'https://www.pbc.gov.cn/english/130721/2025080815062856255/index.html'),
 'cards': ('SAFE · overseas card withdrawals', 'https://www.safe.gov.cn/guangdong/2018/0108/978.html'),
 'crypto': ('State Council · virtual currencies', 'https://www.gov.cn/zhengce/zhengceku/2021-10/08/content_5641404.htm'),
 'split': ('SAFE · splitting transactions', 'https://www.safe.gov.cn/xizang/2019/0916/378.html'),
 'tax': ('China State Taxation Administration · IIT law', 'https://www.chinatax.gov.cn/eng/c102962/c102967/c102997/c103004/c5245849/content.html'),
 'us': ('IRS · Publication 54', 'https://www.irs.gov/publications/p54'),
 'ftc': ('IRS · foreign tax credit', 'https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit'),
 'fx': ('IRS · foreign currency disposition', 'https://www.irs.gov/pub/fatca/int_practice_units/fcu_t_018_02_01_08.pdf'),
 'fbar': ('IRS · FBAR', 'https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar'),
 'fatca': ('IRS · Form 8938 reporting', 'https://www.irs.gov/businesses/corporations/summary-of-fatca-reporting-for-us-taxpayers'),
 'gift': ('IRS · foreign gifts and bequests', 'https://www.irs.gov/pub/irs-npl/2023ntf-15-foreign-gift-and-trust-reporting-on-form-3520-and-3520-a.pdf'),
 'treaty': ('IRS · U.S.–China tax treaty', 'https://www.irs.gov/pub/irs-trty/china.pdf'),
 'cash': ('CBP · currency reporting', 'https://www.cbp.gov/travel/international-visitors/applying-admission-united-states'),
 'fees': ('CFPB · remittance disclosures', 'https://www.consumerfinance.gov/rules-policy/regulations/1005/31/'),
 'filing': ('SAFE · external-payment filing', 'https://www.safe.gov.cn/en/2013/0724/736.html'),
 'enter': ('SAFE · investment profit remittances', 'https://www.safe.gov.cn/en/2017/0126/1248.html'),
}
# Entries consist of plain text and references, making every displayed table row traceable.
options = [
 ('Documented salary or other current-account income → own bank wire', 'Strong first route if funds are qualifying lawful income of an overseas individual. Bank reviews ID and transaction-amount source evidence, including tax evidence.', 'Direct, traceable; no need to assume an annual cap for this documented route.', 'Requires source-specific proof; bank may require resolution of unpaid tax. Rate and fees unverified.', 'salary,incomes'),
 ('Qualifying China permanent-residence ID → annual facilitation', 'SAFE says an overseas individual holding the foreign permanent-residence ID has an annual USD 50,000 equivalent purchase facilitation quota.', 'May simplify eligible purchases; not a tax exemption or permission for every capital transaction.', 'Card status unknown; bank must confirm allowed purpose, source and remittance.', 'residence,general'),
 ('Sale of mainland residence → FX purchase and remittance', 'Shanghai guidance says non-resident sellers can purchase FX and remit property-sale proceeds with ID, transfer documentation and tax voucher.', 'Dedicated documented route for qualifying property proceeds.', 'Property tax and filing requirements are transaction-specific; not a route for unrelated deposits.', 'property'),
 ('Inherited property → SAFE approval and bank', 'For eligible inheritance transfers, SAFE describes local approval and bank remittance; inheritance and title evidence are relevant.', 'Provides a specific capital-account process.', 'Eligibility, current local process, evidence and taxes need confirmation; not a general gift route.', 'inherit,oldinherit'),
 ('Unused original exchanged RMB → reverse exchange', 'SAFE rules describe converting back unused RMB with original exchange slip within 24 months, or limited ID-only cases.', 'Useful for genuine unspent exchanged travel funds.', 'Not a blanket way to convert salary or arbitrary savings; preserve original evidence.', 'rules,split'),
 ('Already-held foreign currency → outbound wire', 'SAFE rules describe remitting FX from an overseas individual’s FX savings account using valid ID for current-account remittance.', 'Avoids another CNY-to-USD conversion when funds already are foreign currency.', 'Not a solution for RMB alone; verify account nature, bank fees and compliance.', 'rules'),
 ('Domestic bank card → overseas ATM cash', 'SAFE describes annual per-person combined overseas cash withdrawals of RMB 100,000 equivalent and daily RMB 10,000 equivalent per card.', 'Provides cash abroad when the card and network work.', 'Not a wire; ATM, FX and deposit costs unknown; withdrawal ceiling and restrictions apply.', 'cards'),
 ('Domestic bank card → legitimate overseas purchases', 'SAFE says qualifying overseas card consumption is not affected by the overseas cash-withdrawal notice.', 'Pays genuine expenses without first wiring funds.', 'Does not put USD in a U.S. account; acceptance, FX rates and charges unverified.', 'cards'),
 ('Employer or business distribution → documented income', 'Where a real employer or investment pays qualifying income, SAFE describes documented current-account earnings and corporate profit remittance processes.', 'Can route genuine unpaid salary or eligible distributions through their proper channels.', 'Not a re-labeling of existing personal funds; corporate formalities and tax treatment differ.', 'incomes,enter'),
 ('Physical foreign-currency cash carried out', 'Possible only after lawful acquisition and subject to applicable China exit requirements and destination declarations.', 'May work for genuine travel cash.', 'Risk of loss and declaration issues; exact China allowance is not verified here. U.S. reporting applies above $10,000.', 'rules,cash'),
 ('Use another person’s quota or split purchases to evade limits', 'Not recommended. SAFE prohibits splitting to evade controls and warns repeated small conversions may be scrutinized.', 'No reliable compliance benefit.', 'Rejection, investigation or penalties are possible; do not misstate ownership or source.', 'general,split'),
 ('Cryptocurrency or underground FX exchange', 'Not recommended. China’s official notice prohibits specified virtual-currency exchange business and related services.', 'No verified lawful advantage for this use.', 'Legal, fraud, account-freeze and loss risks; do not use to bypass controls.', 'crypto'),
]
costs = [
 ('Chinese underlying income tax', 'Depends on source, tax residency, year, deductions, and applicable exemptions; not established by the account balance.', 'Unverified', 'tax'),
 ('U.S. federal and state tax on underlying income', 'U.S. citizens generally report worldwide income; credits, exclusions and state rules depend on facts. Do not assume the wire triggers a second income tax.', 'Unverified', 'us,ftc'),
 ('U.S. currency gain or loss', 'A disposition of nonfunctional currency can produce exchange gain or loss relative to dollar basis; individual personal-use rules and exceptions need separate review.', 'Unverified', 'fx'),
 ('FX spread', 'For the same CNY amount compare reference USD proceeds with quoted USD proceeds; the difference is economic cost, not automatically a tax.', 'Unverified', 'rules'),
 ('Outgoing, intermediary and receiving fees', 'Ask each bank for a written itemized quote, who pays, and exact expected USD receipt. Provider fee and exchange-rate disclosures may apply to covered U.S.-origin remittances; do not assume CFPB rules govern China-origin wires.', 'Unverified', 'fees'),
 ('Late tax / reporting penalties and interest', 'Only assess after examining filing years and facts; penalties are not a standard conversion charge.', 'Unverified', 'fbar,tax'),
 ('External payment tax filing', 'Shanghai’s property guidance says a filing form is required if the transaction exceeds USD 50,000. Filing is not a 50,000-dollar tax or a universal individual exemption.', 'Unverified for this account', 'property,filing'),
]
taxrows = [
 ('China income tax', 'Chinese tax law lists wages, services, interest, dividends, rent and asset transfers as taxable categories; rates and taxable base vary by category and facts.', 'tax'),
 ('Foreign tax credit', 'Eligible foreign income taxes may be credited against U.S. income tax subject to limits. Taxes allocable to income excluded under the foreign earned income exclusion cannot also be credited.', 'ftc,us'),
 ('Foreign earned income exclusion', 'Potentially available for qualified foreign earned income with a foreign tax home and qualifying residence or presence; investment income is not earned income.', 'us'),
 ('Currency gain', 'The IRS explains that disposition of nonfunctional currency can result in gain or loss based on amount realized and adjusted basis. Individual exceptions and character require specialist review.', 'fx'),
 ('U.S.–China treaty', 'Treaty benefits depend on residency, type of income, conditions and the saving clause. U.S. citizenship alone does not guarantee an exemption.', 'treaty'),
 ('FBAR', 'A U.S. person with required interest or authority files if the aggregate foreign financial account value exceeds $10,000 at any time during the calendar year. Annual due date is April 15 with automatic extension to October 15.', 'fbar'),
 ('Form 8938', 'Separate foreign financial asset reporting may apply; thresholds vary by residence and filing status. Filing it does not replace an FBAR.', 'fatca'),
 ('Foreign gift or inheritance', 'Form 3520 reporting can apply to gifts or bequests exceeding $100,000 from a nonresident alien individual or foreign estate, with aggregation rules. Reporting does not by itself establish a tax.', 'gift'),
 ('U.S. cash declaration', 'Currency and monetary instruments transported into or out of the United States over $10,000 require FinCEN Form 105; family declaration rules also apply.', 'cash'),
]
flags = [
 ('Source and ownership of funds', 'Unknown: salary, accumulated savings, inheritance, property proceeds, gift, business funds or other. Route and tax cannot be selected conclusively.', 'salary,inherit,property'),
 ('Amount and documentation', 'Unknown balance, transaction dates, USD basis, tax records, bank quote, account restrictions and recipient bank charges. No net amount or penalty can be calculated.', 'incomes,fx'),
 ('Residency and legal classification', 'Unknown Chinese FX classification, permanent-residence card, China tax residency, U.S. state and U.S. filing history. Citizenship alone does not decide these.', 'residence,tax,us'),
 ('Bank demand for taxes', 'The claimed tax amount and rationale are unverified; a requirement for evidence of payment or exemption is distinct from a newly assessed conversion tax.', 'incomes,tax'),
 ('Inheritance rules changed', 'The 2004 PBOC text contains older approval thresholds and staged remittances; SAFE’s 2014 circular cancels the specified threshold reporting and mandatory installments for emigrant transfers; inherited assets may be remitted in a lump sum or batches after approval. Confirm current implementation locally.', 'oldinherit,inherit'),
 ('Property filing threshold', 'Shanghai’s FAQ mentions a tax filing form over $50,000; it is specific guidance for that process, not proof of an automatic tax or a universal quota.', 'property,filing'),
 ('Older guidance and current practice', 'Rules and bank procedures may have changed; local SAFE and the handling bank should confirm current applicability, evidence, and any applicable taxes before execution.', 'rules,inherit'),
 ('Quotes and provider eligibility', 'No live bank or service-provider quote and no verified CNY-to-USD transfer availability for this specific account. Numeric fees, rates, and net proceeds are blank.', 'fees'),
]
nav = [('Overview','index.html'), ('Conversion routes','pages/routes.html'), ('Costs & taxes','pages/costs.html'), ('Reporting','pages/reporting.html'), ('Flagged for review','pages/review.html')]

def refs(keys):
 return ' '.join('<a class="source" href="%s" target="_blank" rel="noopener noreferrer">%s ↗</a>' % (e(S[k][1], quote=True), e(S[k][0])) for k in keys.split(','))
def table(headers, rows):
 return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th scope="col">%s</th>' % e(h) for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>%s</td>' % e(v) for v in row[:-1]) + '<td>%s</td></tr>' % refs(row[-1]) for row in rows) + '</tbody></table></div>'
def page(title, eyebrow, desc, body, current, base):
 links=''.join('<a%s href="%s%s">%s</a>' % (' class="active" aria-current="page"' if p==current else '',base,p,e(n)) for n,p in nav)
 return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Evidence-led guide to lawful CNY to USD conversion and cross-border transfers."><title>{e(title)} · China Money</title><link rel="stylesheet" href="{base}assets/style.css"></head><body><a class="skip" href="#main">Skip to content</a><div class="layout"><aside class="sidebar"><a class="brand" href="{base}index.html"><span class="brand-icon">¥</span><span>China Money<small>RESEARCH DASHBOARD</small></span></a><div class="nav-label">EXPLORER</div><nav aria-label="Main navigation">{links}</nav><div class="sidebar-note"><span class="status-dot"></span> Source-led research<br><small>Reviewed 07 Nov 2026</small></div></aside><main id="main"><div class="topline"><span>RESEARCH BRIEF / {e(eyebrow.upper())}</span><span class="top-date">UPDATED 07 NOV 2026</span></div><header class="page-header"><div class="eyebrow">{e(eyebrow)}</div><h1>{e(title)}</h1><p>{e(desc)}</p></header>{body}<footer>Research as of 7 November 2026 · Educational information, not individualized legal or tax advice.<br>Source links open in a new tab. Chinese-language official sources may require translation.</footer></main></div></body></html>'''

overview='''<section class="hero"><div><span class="pill">EXECUTIVE SUMMARY</span><h2>Start with the source,<br>not a workaround.</h2><p>For documented, lawful China-source current-account income, the first route to assess is a bank purchase of foreign exchange followed by a remittance. A tax receipt can prove the status of the underlying income; it does not, by itself, establish a new tax on conversion.</p><a class="button" href="pages/routes.html">Compare the routes <span>↗</span></a></div><div class="hero-side"><span class="hero-mark">¥ <span>→</span> $</span><div>THE DECISION</div><strong>Evidence first.<br>Transfer second.</strong><p>Eligibility and actual costs remain case-specific.</p></div></section><section class="stats" aria-label="Key findings"><div><small>BEST FIRST ROUTE</small><strong>Documented bank FX</strong><span>For eligible income, not all funds</span></div><div><small>CONVERSION TAX</small><strong>Not established</strong><span>Separate underlying tax from fees</span></div><div><small>NET PROCEEDS</small><strong>Unverified</strong><span>No balance or bank quote supplied</span></div></section><section><div class="section-head"><div><span class="eyebrow">THE SHORT VERSION</span><h2>What matters most</h2></div><a class="text-link" href="pages/costs.html">See cost breakdown →</a></div>'''+table(['Finding','Implication','Official source'],[
 ('1 · Classify the money', 'SAFE’s documented income route and inheritance/property routes are different. Identify the true source and ownership before choosing.', 'salary,inherit,property'),
 ('2 · Distinguish tax from proof', 'Tax vouchers can establish payment or exemption for a relevant transaction. Do not treat a document request as proof of a new tax on the whole balance.', 'incomes,tax'),
 ('3 · Compare total cost', 'Request the actual FX rate, outgoing fee, intermediary and recipient fees, and any separately assessed tax. No actual quote is available here.', 'rules,fees'),
 ('4 · Check both jurisdictions', 'Assess U.S. worldwide income and foreign account reporting separately from the mechanics of the wire.', 'us,fbar'),
 ('5 · Avoid evasion', 'Do not split transactions to bypass controls or use virtual-currency exchanges as a workaround.', 'general,crypto'),
 ])+'''</section><section class="two-cards"><a class="feature" href="pages/routes.html"><span>01 / ROUTES</span><h3>Explore the options →</h3><p>See documented bank routes, alternatives and approaches to avoid.</p></a><a class="feature" href="pages/review.html"><span>02 / OPEN QUESTIONS</span><h3>Review the unknowns →</h3><p>See every material uncertainty and conflicting historical guidance.</p></a></section><div class="notice"><strong>Important:</strong> No one can identify the lowest-tax lawful route or calculate a penalty from the facts supplied. A China-qualified tax adviser and a U.S. international tax professional should verify the transaction before execution.</div>'''
routes='<div class="notice"><strong>Read this first:</strong> These are conditional pathways, not a claim that all are available to this account. Costs and approvals depend on the facts and current bank practice.</div><div class="section-head"><div><span class="eyebrow">ROUTE COMPARISON</span><h2>Ways to move or use funds</h2></div><span class="count">12 pathways</span></div>'+table(['Route','What official guidance supports','Potential advantage','Limitations & risk','Official source'], options)
routes += '<section><div class="section-head"><div><span class="eyebrow">PRACTICAL SEQUENCE</span><h2>From documents to delivery</h2></div></div>' + table(['Step','What to establish','Official source'], [
 ('1 · Identify and document','Match the balance to its true legal owner and source; collect identity, account statements and source-specific evidence.','salary,inherit'),
 ('2 · Resolve the tax position','Obtain payment or exemption evidence as applicable; ask the bank to explain any requested amount in writing.','incomes,tax'),
 ('3 · Obtain the right approval','For eligible inheritances, check the SAFE procedure; for property proceeds, verify the local bank requirements.','inherit,property'),
 ('4 · Compare written quotes','Compare like-for-like expected USD received, including the spread and separately charged fees; obtain written intermediary and recipient fee information.','rules,fees'),
 ('5 · Complete and retain records','Use the correct channel and preserve transaction records for U.S. tax and applicable account reporting.','rules,us,fbar'),
 ]) + '</section>'
costbody='''<div class="notice"><strong>Do not equate a tax document with a tax bill.</strong> Separate tax on the underlying income, possible U.S. FX gain, exchange-rate spread, bank fees, and any actual penalties. The user’s purported tax rate is unverified.</div><div class="section-head"><div><span class="eyebrow">THE COST STACK</span><h2>What can reduce the proceeds</h2></div></div>'''+table(['Component','Analysis','Case-specific value','Official source'],costs)+'''<section class="formula"><span class="eyebrow">COMPARISON METHOD</span><h2>Measure the economic conversion cost</h2><p>For an identical amount of CNY, calculate <strong>reference USD = CNY ÷ reference rate</strong> and <strong>quoted USD = CNY ÷ quoted rate</strong> when both rates are expressed as CNY per USD. Spread cost = reference USD − quoted USD. Add separately charged outbound, intermediary and receiving fees to obtain a transfer-cost estimate. Avoid double-counting fees already deducted from the quote.</p><p>Then separately compare any applicable unpaid underlying tax, interest, penalties and U.S. FX consequences. A reference rate is a benchmark, not necessarily an obtainable price. No actual rates, fees, taxes or amounts are known, so no numeric result is presented.</p></section>'''
reportbody='<div class="section-head"><div><span class="eyebrow">TAX & COMPLIANCE</span><h2>Obligations to check</h2></div></div>'+table(['Topic','Finding','Official source'],taxrows)
reviewbody='<div class="notice"><strong>Needs review ≠ verified case fact.</strong> These open items are deliberately visible and do not imply a violation. Get written confirmation from the bank or a qualified adviser for the actual transaction.</div><div class="section-head"><div><span class="eyebrow">REVIEW QUEUE</span><h2>Unverified and irregular items</h2></div><span class="count">8 flags</span></div>'+table(['Issue','Why it matters','Official source'], flags)
for path,title,eyebrow,desc,body in [
 ('index.html','Make a clear move','Cross-border money guide','An evidence-led guide to converting yuan and moving funds from mainland China to the United States.',overview),
 ('pages/routes.html','Conversion routes','Compare your options','Understand what each pathway actually does, when it may apply, and where the risks lie.',routes),
 ('pages/costs.html','Costs & taxes','Follow the money','A practical breakdown of tax, exchange-rate costs, transfer fees and possible penalties.',costbody),
 ('pages/reporting.html','Reporting & tax','Stay compliant','The Chinese and U.S. obligations that may matter independently of the transfer itself.',reportbody),
 ('pages/review.html','Flagged for review','Open questions','Important unknowns and historical inconsistencies, kept visible for manual review.',reviewbody),
]:
 (ROOT/path).write_text(page(title,eyebrow,desc,body,path,'' if path=='index.html' else '../'),encoding='utf-8')
