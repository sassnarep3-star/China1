"""Build the consolidated China Money dashboard from directly inspected sources.

Archived editions are read-only inputs. Legal/tax claims use government sources;
provider sources support only that provider's own tariffs or product terms.
Unknown personal and all-in values are emitted as blank + UNVERIFIED, never zero.
"""
from __future__ import annotations

import csv
from decimal import Decimal, ROUND_HALF_UP
from html import escape as e
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "integration"
CHECKED = "2026-11-10"
RATE = Decimal("6.6903")  # BOC USD100 telegraphic ask 669.03, 2026-11-10 07:32:39 China time.
TARGETS = list(range(10_000, 400_001, 10_000))

# Each record below was retrieved and its listed scope inspected on 2026-11-10.
# "provider" means first-party evidence of that provider's terms, not a regulator.
SOURCES = {
    "S01": {"title": "State Council Order 532 — Regulation on Foreign Exchange Administration", "url": "https://www.gov.cn/zhengce/2008-08/06/content_2602514.htm", "kind": "government", "locator": "Arts. 12, 22, 39–45, 52", "scope": "Real transaction basis; liquidation remittance; administrative violation bands; definitions."},
    "S02": {"title": "PBOC Order [2006] No. 3 — Individual Foreign Exchange Measures", "url": "https://www.safe.gov.cn/safe/2006/1225/5319.html", "kind": "government", "locator": "Arts. 3, 7, 9, 13, 22, 26, 28, 37", "scope": "Current/capital distinction; anti-splitting; overseas-person income and property rules; account identity classification."},
    "S03": {"title": "SAFE Huifa [2020] No. 14 — Current Account Guidelines", "url": "https://www.gov.cn/gongbao/content/2020/content_5560296.htm", "kind": "government", "locator": "Arts. 47–49, 54–65, 68, 86–89", "scope": "USD50,000 facilitation tier; documented purchases; Art. 59 tax/source evidence; existing-FX remittance; authenticity and cash rules."},
    "S04": {"title": "PBOC Announcement [2004] No. 16 — Individual Property Transfer Abroad", "url": "https://www.gov.cn/gongbao/content/2005/content_64294.htm", "kind": "government", "locator": "Arts. 2, 5–12", "scope": "Emigrant/inheritance definitions, evidence and own-account remittance. Historical staging in Art. 6 is modified by S05."},
    "S05": {"title": "SAFE Huifa [2014] No. 2 — amended republication", "url": "https://www.safe.gov.cn/tianjin/2024/0903/2594.html", "kind": "government", "locator": "Section VI", "scope": "Removes mandatory staged emigrant remittance; permits one or multiple remittances within approval; combines specified inheritance applications."},
    "S07": {"title": "SAFE Hebei — emigrant property transfer service guide", "url": "https://www.safe.gov.cn/hebei/file/file/20240816/86fd609207224d71b23cfda39ebe4bbb.pdf", "kind": "government", "locator": "Sections 3, 5, 7–9", "scope": "Pre-status property, identity/hukou, source/tax documents, approval procedure, 20-working-day statutory period and no administrative fee."},
    "S08": {"title": "SAFE Hebei — inheritance property transfer service guide", "url": "https://www.safe.gov.cn/hebei/file/file/20240816/186ef46ed22745009f16c6715f2a54f1.pdf", "kind": "government", "locator": "Sections 3, 5, 7–9", "scope": "Inheritance/property/tax documents and approval. Section 3 contains pre-status wording inconsistent with the inheritance definition; flagged."},
    "S12": {"title": "SAFE Henan — overseas insurance beneficiary Q&A", "url": "https://www.safe.gov.cn/henan/2022/0718/1245.html", "kind": "government", "locator": "Full Q&A", "scope": "Lawful compliant insurance proceeds may use the overseas-person lawful-RMB-income process with policy and insurer payment proof."},
    "S14": {"title": "Bank of China personal finance tariff, Chapter 3", "url": "https://pic.bankofchina.com/bocappd/pricelist/202511/P020251110646838136627.pdf", "kind": "provider", "locator": "Items 210101002, 210105008, 210108014; notes 4, 5, 10", "scope": "TT/draft 0.1%, min CNY50/max CNY260; international cable CNY150; actual overseas charges; USD15/25 conditional full-arrival; ATM and carry-permit terms."},
    "S16": {"title": "Bank of China indicative foreign-exchange board", "url": "https://www.boc.cn/sourcedb/whpj/", "kind": "provider", "locator": "USD row and disclaimer, captured 2026-11-10 07:32:39 China time", "scope": "USD100 bid CNY666.22 / telegraphic ask CNY669.03 / reference CNY671.88. Indicative only; actual channel/counter execution rate controls."},
    "S18": {"title": "HSBC China tariff of accounts and services (effective 2026-10-31)", "url": "https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-accouts-and-services.pdf", "kind": "provider", "locator": "Notes 3, 7, 10; items 2.2.4.1–2, 2.2.6.1, 2.2.16.7", "scope": "Private-individual TT commission/cable free; Premier/Advance 0.1%, min CNY100/max CNY500 + CNY120 cable; Global Transfer and ATM terms; exclusions."},
    "S20": {"title": "Wise — Guide to CNY transfers", "url": "https://wise.com/help/articles/2955298/guide-to-cny-transfers", "kind": "provider", "locator": "Sending from CNY", "scope": "Eligible non-mainland-Chinese people with China work/tax records; own-account destination; CNY300,000 bank-app / CNY50,000 Alipay per-transfer caps; after-tax-income overall limit."},
    "S25": {"title": "Western Union China — send money", "url": "https://www.westernunion.com/cn/en/send-money.html", "kind": "provider", "locator": "Availability notice and online/in-person instructions", "scope": "Bank-account payout temporarily unavailable; partner-bank cash-pickup route and local restrictions. No numeric fee schedule inferred."},
    "S28": {"title": "SAFE — overseas bank-card cash withdrawal explainer", "url": "https://www.safe.gov.cn/safe/2017/1230/8130.html", "kind": "government", "locator": "Full explainer for Huifa [2017] No. 29", "scope": "CNY100,000/person/year and CNY10,000/card/day overseas ATM caps; borrowed-card evasion prohibited."},
    "S30": {"title": "U.S. CBP — currency reporting reminder", "url": "https://www.cbp.gov/newsroom/local-media-release/cbp-encourages-travelers-plan-ahead-summer-travel-season-begins", "kind": "government", "locator": "Currency reporting paragraph", "scope": "More than USD10,000 in currency/monetary instruments entering or leaving the U.S. must be declared on FinCEN Form 105."},
    "S31": {"title": "PRC Individual Income Tax Law (2018 amendment)", "url": "https://guangdong.chinatax.gov.cn/gdsw/zjfg/2018-08/31/content_a735b4c382d94439b581054c32a4e7f4.shtml", "kind": "government", "locator": "Arts. 1–3, 6–7, 10, 13, 15–16", "scope": "Residence; nine income categories; 20% proportional categories; property gain net basis; foreign tax credit; emigration tax clearance."},
    "S33": {"title": "MOF/STA Announcement 2026 No. 27 — foreign-individual dividends", "url": "https://shanghai.chinatax.gov.cn/zzzb/zcwj/202609/t481448.html", "kind": "government", "locator": "Full text", "scope": "20% IIT on FIE dividends paid to foreign individuals from 2026-09-01; specified 1994 exemption repealed. Treaty/application facts remain separate."},
    "S37": {"title": "IRS — Foreign Tax Credit", "url": "https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit", "kind": "government", "locator": "Qualifying taxes and compliance issues", "scope": "Possible credit for qualifying foreign income taxes on the same income; treaty-reduced-tax and excluded-income limitations."},
    "S39": {"title": "26 U.S.C. §988 (2024 U.S. Code)", "url": "https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm", "kind": "government", "locator": "Subsections (a), (c)(1)(C), (e)", "scope": "Disposition of nonfunctional currency; ordinary-treatment default; personal-transaction exclusion does not apply when transaction gain exceeds USD200."},
    "S40": {"title": "IRS — Form 8938 and FBAR comparison", "url": "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", "kind": "government", "locator": "Reporting threshold and penalty table", "scope": "FBAR aggregate foreign-account threshold exceeds USD10,000 at any time; separate Form 8938 thresholds and filing mechanics."},
    "S42": {"title": "Bittner v. United States, No. 21-1195 (2023)", "url": "https://www.supremecourt.gov/opinions/22pdf/21-1195_h3ci.pdf", "kind": "government", "locator": "Syllabus and holding", "scope": "Nonwillful FBAR statutory penalty accrues per report, not per account. Willful account-based provisions are distinct."},
    "S43": {"title": "IRS — Gifts from foreign person", "url": "https://www.irs.gov/businesses/gifts-from-foreign-person", "kind": "government", "locator": "Reporting requirements", "scope": "Form 3520 above USD100,000 from nonresident alien/foreign estate; 2026 foreign-entity purported-gift threshold USD20,573; aggregation rules."},
    "S44": {"title": "IRS IR-2026-48 — remittance transfer tax proposed regulations", "url": "https://www.irs.gov/newsroom/treasury-irs-issue-proposed-regulations-on-the-new-remittance-transfer-tax-established-under-the-one-big-beautiful-bill", "kind": "government", "locator": "Full release", "scope": "1% tax from 2026-01-01 on specified physical-instrument-funded remittances sent from the United States, not China-to-U.S. transfers."},
    "S45": {"title": "PBOC et al. Yinfa [2026] No. 42 — virtual currency and RWA risks", "url": "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html", "kind": "government", "locator": "Sections 1, 3(6), 6 and final repeal clause", "scope": "Mainland virtual-currency exchange business prohibited; 2021 No. 237 expressly repealed."},
    "S53": {"title": "SAFE/Customs Huifa [2003] No. 102 — carrying foreign-currency cash", "url": "https://www.safe.gov.cn/tianjin/2024/0430/2466.html", "kind": "government", "locator": "Main notice paragraph 2", "scope": "USD5,000 no-permit tier; USD5,000–10,000 bank permit; above USD10,000 only specified special cases with SAFE permit."},
    "IRS-W": {"title": "IRS — U.S. citizens and resident aliens abroad", "url": "https://www.irs.gov/individuals/international-taxpayers/us-citizens-and-resident-aliens-abroad", "kind": "government", "locator": "Opening and reporting sections", "scope": "Worldwide taxable income; foreign-account reporting even without taxable income; Form 3520 overview."},
}

FINDINGS = [
    ("Best first route if the money is documented current income", "For a U.S. passport holder classified as an overseas individual, SAFE Article 13 and Guideline Article 59 support purchasing/remitting lawful China-source current-account RMB income with identity, transaction-amount source evidence and tax records. This is the first route to investigate—not a conclusion that the whole balance qualifies.", ["S02", "S03"]),
    ("Match capital assets to their own approval route", "Pre-emigration property and inheritance are not salary. Use the applicable SAFE property-transfer process. The 2014 amendment removed mandatory staged emigrant releases; approved amounts may go once or in installments. Emigrant property is limited to qualifying pre-status assets.", ["S04", "S05", "S07", "S08"]),
    ("Tax follows the income and currency basis—not the wire", "A remittance fee is not an income tax, and moving existing principal is not automatically new income. Underlying salary, rent, dividends or property gains can be taxable. U.S. citizens report worldwide income; §988 and foreign-tax-credit rules require transaction records. No personal tax bill can be calculated from citizenship alone.", ["S31", "S39", "S37", "IRS-W"]),
    ("Known sender fees are only one cost layer", "BOC and HSBC publish usable tariff formulas. Their scenarios below exclude the executable FX difference, correspondent/receiving charges, documents, underlying tax and U.S. tax. A provider rail never creates the legal right to export the balance.", ["S14", "S16", "S18", "S20"]),
    ("FBAR/FATCA and Form 3520 are separate from conversion", "Aggregate foreign accounts exceeding USD10,000 at any time can trigger FBAR even without taxable income. Form 8938 has separate thresholds. Qualifying foreign gifts/bequests can trigger Form 3520. Emptying the account does not erase historical duties.", ["S40", "S43", "IRS-W"]),
    ("Reject evasion, not merely its price", "Do not split quotas, borrow cards, fabricate trade, use underground settlement or use a crypto bridge. These are not tax-saving methods. The consolidated catalog names risks but gives no operational instructions for prohibited schemes.", ["S01", "S02", "S03", "S28", "S45"]),
]

FLAGS = [
    ("J01 · Root summary corrected", "The inherited root EXECUTIVE_SUMMARY.md called a roughly 0.42% bid/ask gap the one-way conversion cost, repeated superseded emigrant staging, and described willful FBAR exposure as per year. Those statements are not carried into the consolidated summary. A bid/ask gap is not a measured one-way customer loss; the 2014 amendment controls staging; penalty application depends on the violation.", ["S05", "S16", "S42"]),
    ("J02 · Exact personal all-in cost remains unverified", "Source-of-funds, bank classification, CNY basis/acquisition dates, PRC and U.S. tax history, receiving bank, actual transfer count, executable FX and document quotes were not supplied. All-in and personal-tax cells remain blank. Blank never means zero.", ["S03", "S14", "S18", "S31", "S39"]),
    ("J03 · Indicative quote, not an execution offer", f"The consolidated scenario uses BOC's USD100 ask CNY669.03 at 2026-11-10 07:32:39 China time. BOC says actual transaction-channel rates control. The ask was below its displayed reference rate, so no positive FX 'spread cost' is inferred. Edition H's prior-day grids use CNY669.19 and are retained unchanged.", ["S16"]),
    ("J04 · Known sender fee is not a total", "BOC overseas charges are actual; its full-arrival option is conditional. HSBC excludes other institutions' and government charges. Intermediate and U.S. receiving fees are unknown. Scenario values cover only published sender commission/cable and a comparison-rate conversion.", ["S14", "S18"]),
    ("J05 · Identity classification can conflict", "The 2006 individual measures use ID-based domestic/overseas categories, while the broader FX regulation has a separate residence-based definition. A U.S. citizen with legacy PRC identity documents must resolve the bank's classification rather than assume quota eligibility.", ["S01", "S02"]),
    ("J06 · Official inheritance-guide irregularity", "SAFE Hebei's inheritance guide repeats emigrant pre-status wording in its eligibility section even though its definition and document checklist concern inherited property. It is flagged verbatim rather than silently rewritten; the competent SAFE office must confirm the current local checklist.", ["S04", "S08"]),
    ("J07 · Wise eligibility and grid limitations", "Wise from-CNY requires qualifying non-mainland status, China work/tax history, own-account destination and an after-tax-income overall limit. Its bank-app and Alipay caps can force multiple transfers. No current 40-point fee schedule was verified, so Wise grid values remain blank in Edition H.", ["S20"]),
    ("J08 · Provider corridors can change", "Western Union's checked China page says bank-account payout is temporarily unavailable and offers cash pickup through partner banks. No fee or FX amount is inferred. MoneyGram/PayPal and other unsupported own-account CNY corridors stay unverified in the inherited catalog.", ["S25"]),
    ("J09 · Cash is not a large-balance workaround", "China generally restricts carrying more than USD10,000 cash abroad to specified special cases with SAFE permission; U.S. entry/exit above USD10,000 requires declaration. ATM caps and transport/deposit risks apply. No splitting instructions are provided.", ["S28", "S30", "S53"]),
    ("J10 · Archived editions are evidence, not certification", "The consolidated method catalog links Edition H's 43 candidates, steps and 1,720 amount rows. This integration directly re-read the load-bearing sources listed in its evidence log and ran all edition checkers. It does not claim a fresh legal opinion on every archived line or guarantee external-link uptime.", ["S02", "S03"]),
    ("J11 · Current dividend rule", "MOF/STA 2026 No. 27 applies 20% IIT to foreign individuals' FIE dividends from 2026-09-01 and repeals the specified old exemption. Older archived exemptions are stale. Treaty and beneficial-owner analysis remains case-specific.", ["S33"]),
    ("J12 · Prohibited-route authority updated", "PBOC Yinfa [2026] No. 42 expressly repealed the 2021 virtual-currency notice. Older archives citing only the 2021 instrument retain historical text but are not the consolidated authority.", ["S45"]),
]

CSS = r"""
:root{--navy:#102a43;--blue:#1769aa;--teal:#087f5b;--ink:#172b3a;--muted:#5c6f7c;--bg:#f4f7fa;--line:#d9e2ec;--warn:#8a4b00;--warnbg:#fff4d6}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.58 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}a{color:var(--blue);text-underline-offset:2px}a:focus-visible{outline:3px solid #b57600;outline-offset:2px}.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:20}header{background:var(--navy);color:#fff;padding:18px 16px}header a{color:#fff;text-decoration:none}.brand{font-weight:800;font-size:1.15rem}.subtitle{display:block;color:#d9eaf7;font-size:.84rem;margin-top:3px}nav{display:flex;gap:6px;overflow-x:auto;padding:10px 12px;background:#fff;border-bottom:1px solid var(--line);white-space:nowrap}nav a{text-decoration:none;padding:7px 10px;border-radius:8px;font-size:.88rem}nav a[aria-current]{background:var(--navy);color:#fff}main{max-width:1180px;margin:auto;padding:20px 14px 64px}h1{font-size:clamp(1.7rem,4vw,2.5rem);line-height:1.16;margin:.15em 0 .45em}h2{font-size:1.35rem;line-height:1.25;margin-top:1.8em}h3{font-size:1.08rem}p{max-width:88ch}.hero{padding:26px 20px;background:linear-gradient(135deg,#102a43,#1769aa);color:#fff;border-radius:16px}.hero p{max-width:78ch}.hero a{color:#fff}.lead{font-size:1.08rem}.muted,small{color:var(--muted)}small{display:block;font-size:.78rem}.notice{border-left:5px solid #d97706;background:var(--warnbg);padding:13px 15px;border-radius:8px;margin:14px 0}.good{border-left-color:var(--teal);background:#e7f6ef}.danger{border-left-color:#9b1c1c;background:#fee2e2}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:12px}.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0}.cards .card{margin:0;text-decoration:none;color:inherit}.card strong{color:var(--teal)}.card p{margin:.45em 0 0}.kpi{font-size:1.65rem;font-weight:800;color:var(--teal)}.button{display:inline-block;background:var(--navy);color:#fff;text-decoration:none;padding:9px 13px;border-radius:8px;margin:3px 5px 3px 0}.steps li{margin:.5em 0}.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:10px;margin:12px 0;-webkit-overflow-scrolling:touch}table{border-collapse:collapse;width:100%;font-size:.86rem}th,td{text-align:left;vertical-align:top;padding:10px;border-top:1px solid var(--line)}th{background:#eaf0f5;font-size:.73rem;text-transform:uppercase;letter-spacing:.035em}tbody tr:hover{background:#f8fafc}.num{white-space:nowrap;font-variant-numeric:tabular-nums}.source{display:inline-block;margin:2px 7px 2px 0;font-size:.75rem;white-space:nowrap}.badge{display:inline-block;border-radius:5px;padding:2px 6px;font-size:.68rem;font-weight:800;background:#e5e7eb;color:#374151}.unverified{background:var(--warnbg);color:var(--warn)}.blank{display:inline-block;width:2.8em;border-bottom:2px dotted var(--warn);height:1em;margin-right:5px}.archive{columns:2;column-gap:24px}.archive a{display:block;break-inside:avoid;padding:4px 0}footer{border-top:1px solid var(--line);padding:20px 14px;text-align:center;color:var(--muted);font-size:.83rem}code{overflow-wrap:anywhere}@media(max-width:680px){main{padding:14px 10px 48px}.hero{padding:20px 15px}.archive{columns:1}.responsive thead{position:absolute;left:-9999px}.responsive,.responsive tbody,.responsive tr,.responsive td{display:block;width:100%}.responsive tr{border-top:8px solid var(--line);padding:8px 0}.responsive tr:first-child{border-top:0}.responsive td{border:0;padding:6px 10px 6px 44%;position:relative;min-height:29px}.responsive td::before{content:attr(data-label);position:absolute;left:10px;top:6px;width:32%;font-size:.69rem;font-weight:800;text-transform:uppercase;color:var(--muted)}.responsive td:first-child{font-size:1.04rem;background:#f1f5f9}.table-wrap{border:0;overflow:visible;background:transparent}.num{white-space:normal}}@media print{header,nav,footer{display:none}main{max-width:none}.table-wrap{overflow:visible}.responsive thead{position:static}.responsive tr{display:table-row}.responsive td{display:table-cell}.responsive td::before{display:none}}
"""

NAV = [
    ("index.html", "Overview"), ("integration/costs.html", "Cost ladder"),
    ("integration/methods.html", "Methods & steps"), ("integration/tax.html", "Tax & reporting"),
    ("integration/evidence.html", "Sources"), ("integration/review.html", "Flagged for Review"),
]


def q2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(value: Decimal, currency: str) -> str:
    return f"{currency} {q2(value):,.2f}"


def blank(label="Unverified") -> str:
    return f'<span class="blank" aria-label="Blank, {e(label)}"></span><span class="badge unverified">UNVERIFIED</span>'


def links(ids) -> str:
    return " ".join(f'<a class="source" href="{e(SOURCES[i]["url"])}" rel="noopener noreferrer" title="{e(SOURCES[i]["title"])} — {e(SOURCES[i]["locator"])}">{e(i)} ↗</a>' for i in ids)


def table(headers, rows, class_name="responsive") -> str:
    head = "".join(f'<th scope="col">{e(h)}</th>' for h in headers)
    body = []
    for row in rows:
        cells = "".join(f'<td data-label="{e(label)}">{cell}</td>' for label, cell in zip(headers, row))
        body.append(f"<tr>{cells}</tr>")
    return f'<div class="table-wrap"><table class="{class_name}"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def shell(slug, title, body) -> str:
    depth = 1 if slug.startswith("integration/") else 0
    prefix = "../" if depth else ""
    nav_items = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == slug else ""
        nav_items.append(f'<a href="{prefix}{href}"{current}>{e(label)}</a>')
    nav = "".join(nav_items)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Source-linked CNY to USD routes, conditional sender-fee estimates, China and U.S. tax analysis"><title>{e(title)} · China Money</title><style>{CSS}</style></head><body><a class="skip" href="#main">Skip to content</a><header><a class="brand" href="{prefix}index.html">China Money</a><span class="subtitle">CNY → USD · consolidated official/primary-source review · {CHECKED} UTC</span></header><nav aria-label="Main navigation">{nav}</nav><main id="main">{body}</main><footer>Blank = unverified, never zero · Partial estimates are not all-in quotes.<br>Educational research, not individualized legal, tax, investment or immigration advice. <a href="{prefix}COORDINATION.md">Coordination</a> · <a href="{prefix}integration/methodology.html">Methodology</a></footer></body></html>'''


def cost_rows():
    rows = []
    for amount in TARGETS:
        usd = Decimal(amount)
        principal = RATE * usd
        boc = q2(min(Decimal(260), max(Decimal(50), principal * Decimal("0.001"))) + 150)
        hsbc = q2(min(Decimal(500), max(Decimal(100), principal * Decimal("0.001"))) + 120)
        rows.append({
            "target_usd": amount,
            "cny_scenario": float(q2(principal)),
            "boc_sender_cny": float(boc), "boc_sender_usd_comparison": float(q2(boc / RATE)),
            "hsbc_sender_cny": float(hsbc), "hsbc_sender_usd_comparison": float(q2(hsbc / RATE)),
            "fx_cost_usd": None, "downstream_usd": None, "documentation_usd": None,
            "tax_usd": None, "all_in_usd": None,
            "sources": ["S14", "S16", "S18"],
        })
    return rows


def fee_cells(row):
    boc = f'{money(Decimal(str(row["boc_sender_cny"])), "CNY")}<small>≈ {money(Decimal(str(row["boc_sender_usd_comparison"])), "USD")} at comparison ask</small>'
    hsbc = f'{money(Decimal(str(row["hsbc_sender_cny"])), "CNY")}<small>≈ {money(Decimal(str(row["hsbc_sender_usd_comparison"])), "USD")} at comparison ask</small>'
    return boc, hsbc


def build_index(rows):
    cards = [
        ("integration/costs.html", "40-amount cost ladder", "Amount-specific BOC and HSBC sender-fee scenarios; unknown all-in values stay blank."),
        ("integration/methods.html", "43 candidates, steps, pros & cons", "Personal, bank/provider, business, adjacent and rejected options; every row has primary-source links."),
        ("edition-h/site/costs.html", "Every method × every amount", "Edition H's 1,720 rows and downloadable CSV, including per-transaction formulas and unavailable routes."),
        ("integration/tax.html", "Tax & U.S. reporting", "Separate underlying tax, personal FX gain, FBAR/FATCA, gifts and penalty exposure."),
        ("integration/evidence.html", "Evidence log", "Directly inspected clauses, provider/government classification and retrieval dates."),
        ("integration/review.html", "Flagged for Review", "Material irregularities, stale archived claims and unresolved personal facts."),
    ]
    for href, _, _ in cards:
        assert (ROOT / href).is_file() or href.startswith("integration/"), href
    quick = []
    for row in [rows[0], rows[1], rows[3], rows[9], rows[-1]]:
        boc, hsbc = fee_cells(row)
        quick.append(([f'<strong>USD {row["target_usd"]:,}</strong>', boc, hsbc, blank("All-in components unavailable"), links(["S14", "S16", "S18"])]))
    body = f'''<section class="hero"><h1>Move CNY to USD lawfully—with the costs separated.</h1><p class="lead">The best available first route is <strong>documented lawful current income</strong>, if that is what the balance contains. Otherwise, match property, inheritance, insurance or business proceeds to their own legal route. Do not choose a provider before establishing eligibility.</p><p><a class="button" href="integration/methods.html">Find your route</a><a class="button" href="integration/costs.html">See all 40 amounts</a></p></section>
<div class="notice"><strong>Bottom line:</strong> no universal “conversion tax” or exact personal tax penalty is verified. Bank tariffs can be estimated; a lawful entitlement and an executable all-in quote cannot be inferred from U.S. citizenship or a stuck bank balance.</div>
<div class="cards">{"".join(f'<a class="card" href="{href}"><strong>{e(title)} →</strong><p>{e(desc)}</p></a>' for href,title,desc in cards)}</div>
<h2>Decision summary</h2>{table(["Priority", "What the evidence supports", "Official / primary sources"], [[e(a),e(b),links(c)] for a,b,c in FINDINGS])}
<h2>Known sender-fee comparison</h2><p>One transfer of gross USD-equivalent principal. BOC: min(CNY260, max(CNY50, 0.1% × CNY principal)) + CNY150 cable. HSBC Premier/Advance: min(CNY500, max(CNY100, 0.1% × CNY principal)) + CNY120 cable. CNY principal and USD fee comparisons use BOC's indicative ask CNY6.6903/USD1; HSBC's own executable FX was not captured.</p><p><strong>These are not all-in totals.</strong> HSBC Private Banking individual TT commission/cable is published as free for eligible clients, but FX, third-party and relationship costs are not thereby zero.</p>{table(["USD target", "BOC known sender fee", "HSBC P/A known sender fee", "All-in", "Sources"], quick)}<p><a class="button" href="integration/costs.html">Open every $10,000 increment</a><a href="integration/methodology.html">Formula and limitations</a></p>
<h2>Recommended order of work</h2><ol class="steps"><li>Classify each tranche by its true source and confirm the bank's individual-FX identity classification.</li><li>Collect transaction-amount source evidence and applicable PRC tax records. Do not relabel savings as salary, trade, a gift or a dividend.</li><li>Use the matching entitlement: current income, pre-emigration property, inheritance, property sale, insurance, unused prior conversion, or genuine business transaction.</li><li>Only then compare same-time executable BOC, HSBC and eligible provider quotes, including FX and every downstream charge.</li><li>Keep purchase slips, SWIFT/receipt records and tax evidence; reconcile U.S. worldwide-income, FBAR/FATCA and any Form 3520 duties.</li></ol><p>{links(['S02','S03','S04','S05','S14','S18','S20','S37','S40'])}</p>
<h2>Preserved research archive</h2><p>Edition H is the latest broad catalog. Older editions are preserved for traceability and can contain stale or conflicting claims; inclusion is not re-certification.</p><div class="archive">'''
    archive = [
        ("edition-h/site/index.html", "Edition H — latest 43-candidate dashboard"),
        ("pages/estimates.html", "Original USD scenario table"), ("overview.html", "Original overview"),
        ("docs/index.html", "Supplemental dashboard"), ("dossier/index.html", "Dossier"),
        ("edition-b/index.html", "Edition B"), ("edition-c/docs/index.html", "Edition C"),
        ("edition-d/docs/index.html", "Edition D — historical scenario model"),
        ("edition-e/site/index.html", "Edition E"), ("edition-f/site/index.html", "Edition F"),
        ("edition-g/docs/index.html", "Edition G"),
    ]
    for href, title in archive:
        assert (ROOT / href).is_file(), href
        body += f'<a href="{href}">{e(title)}</a>'
    body += "</div>"
    (ROOT / "index.html").write_text(shell("index.html", "Overview", body), encoding="utf-8")


def build_costs(rows):
    rendered = []
    for row in rows:
        boc, hsbc = fee_cells(row)
        rendered.append([
            f'<strong>USD {row["target_usd"]:,}</strong>',
            money(Decimal(str(row["cny_scenario"])), "CNY"), boc, hsbc,
            blank("FX, downstream, documents and tax unknown"), links(row["sources"]),
        ])
    body = f'''<h1>$10,000–$400,000 cost ladder</h1><div class="notice"><strong>Most important:</strong> these are amount-specific <em>sender-fee scenarios</em>, not quotes or totals. All-in remains blank because executable FX, intermediary/receiving charges, documents and personal taxes are unknown. One transfer is assumed; multiple transfers can repeat fees.</div>
<h2>Formula and quote timestamp</h2><p>Gross principal P = USD target × CNY6.6903. BOC = min(CNY260, max(CNY50, 0.001×P)) + CNY150. HSBC Premier/Advance = min(CNY500, max(CNY100, 0.001×P)) + CNY120. USD fee equivalents = CNY fee ÷ 6.6903. BOC board captured at 2026-11-10 07:32:39 China time: USD100 telegraphic ask CNY669.03; actual transaction rate controls.</p><p>{links(['S14','S16','S18'])}</p>
{table(["USD target", "CNY principal scenario", "BOC sender fee", "HSBC P/A sender fee", "All-in total", "Sources"], rendered)}
<h2>How to use the comparison</h2><ol class="steps"><li>First establish the legal entitlement in the <a href="methods.html">method catalog</a>.</li><li>Ask each eligible provider for an executable quote for the same CNY amount and same guaranteed USD outcome, at the same time.</li><li>Add FX difference, optional full-arrival/correspondent charges, receiving fee, documents and actual underlying tax. Do not add both a personal-entitlement scenario and a separate rail fee twice.</li><li>Prefer the lowest verified total among eligible routes—not the smallest advertised sender fee. At USD20,000–40,000 in this scenario, HSBC P/A's published sender fee is lower; at USD10,000 and from USD50,000 upward, BOC's is lower. This says nothing about FX or eligibility.</li></ol>
<p><a class="button" href="../edition-h/site/costs.html">All 43 methods at lowest/highest amounts</a><a class="button" href="../edition-h/site/cost-ladder.csv">Edition H full 1,720-row CSV</a><a href="costs.csv">Download this 40-row comparison</a></p>'''
    (OUT / "costs.html").write_text(shell("integration/costs.html", "Cost ladder", body), encoding="utf-8")


def build_methods():
    doc = json.loads((ROOT / "edition-h/data/methods.json").read_text(encoding="utf-8"))
    h_sources = {s["id"]: s for s in json.loads((ROOT / "edition-h/data/sources.json").read_text(encoding="utf-8"))["sources"]}
    rows = []
    for m in doc["methods"]:
        source_html = " ".join(f'<a class="source" href="{e(h_sources[s]["url"])}" rel="noopener noreferrer" title="{e(h_sources[s]["title"])}">{e(s)} ↗</a>' for s in m["sources"])
        method_link = f'<a href="../edition-h/site/method-{e(m["id"])}.html"><strong>{e(m["id"])} · {e(m["name"])}</strong></a><small>{e(m["category"])} · {e(m["status"])}</small>'
        analysis = f'<strong>Pros:</strong> {e(" ".join(m["pros"]))}<br><strong>Cons:</strong> {e(" ".join(m["cons"]))}'
        action = f'<a href="../edition-h/site/method-{e(m["id"])}.html">Steps / disposition</a><br><a href="../edition-h/site/method-{e(m["id"])}.html">40-row cost grid</a>'
        rows.append([method_link, e(m["summary"]), analysis, action, source_html])
    body = f'''<h1>Methods, pros, cons and steps</h1><div class="notice"><strong>43 candidates, not 43 interchangeable ways to export the same savings.</strong> A legal entitlement, an execution rail, an adjacent alternative and a rejected scheme are different objects. Select the true source-of-funds route first, then one execution rail. Prohibited schemes have risk information only—no execution instructions.</div><p>This consolidated register links Edition H's candidate inventory and per-method pages. Government/provider-primary links appear on every row. The integration's direct re-verification scope is in the <a href="evidence.html">evidence log</a>; inherited claims are not presented as new legal opinions.</p>{table(["Candidate", "When it applies / verified disposition", "Pros & cons", "Steps & costs", "Primary sources"], rows)}<p><a class="button" href="../edition-h/site/flagged.html">Edition H's 52 detailed flags</a><a class="button" href="../edition-h/site/cost-ladder.csv">All 1,720 cost rows (CSV)</a></p>'''
    (OUT / "methods.html").write_text(shell("integration/methods.html", "Methods and steps", body), encoding="utf-8")


def build_tax():
    entries = [
        ("PRC underlying income", "IIT applies to enumerated income, not a flat remittance charge. Salary, rent, interest/dividends and property gains follow their own rules; property-transfer taxable income is proceeds less original value and reasonable expenses. The listed proportional categories use 20%, but the base and exemptions matter.", "Rate depends on income; personal amount blank", ["S31"]),
        ("Foreign-individual FIE dividend", "MOF/STA 2026 No. 27 imposes 20% IIT on FIE dividends to foreign individuals from 2026-09-01 and repeals the specified 1994 exemption. Do not use an older blanket exemption.", "20% statutory rate; treaty/application facts separate", ["S33"]),
        ("U.S. worldwide income", "U.S. citizens generally report worldwide taxable income whether living in the U.S. or abroad. A transfer of existing principal is not by itself a new income category, but original earnings/gains and account reporting still matter.", "Personal tax blank", ["IRS-W"]),
        ("U.S. personal foreign-currency gain", "§988 treats disposition of nonfunctional currency as a §988 transaction. For a personal transaction, no gain is recognized unless the gain on that transaction exceeds USD200; exceeding USD200 disapplies the exclusion for the transaction—it is not a USD200 deduction. Basis, dates and transaction character are required.", "USD200 transaction threshold; personal gain blank", ["S39"]),
        ("U.S. foreign tax credit", "Qualifying foreign income taxes on the same income may support a credit or deduction. The credit is limited; treaty-reduced tax and foreign-earned-income-exclusion interactions matter. It is not an automatic dollar-for-dollar elimination of U.S. tax.", "Case-specific", ["S37"]),
        ("FBAR and Form 8938", "FBAR applies when aggregate foreign financial accounts exceed USD10,000 at any time in the calendar year. Form 8938 has separate asset, residence and filing-status thresholds. One does not replace the other; reporting can apply without taxable income.", "FBAR >USD10,000 aggregate; Form 8938 varies", ["S40", "IRS-W"]),
        ("FBAR penalty characterization", "Bittner holds that the nonwillful statutory FBAR penalty accrues per report, not per account. Willful account-based provisions are distinct. Penalty maxima and inflation adjustments are not predicted transfer costs or automatic annual assessments.", "Case- and violation-specific", ["S40", "S42"]),
        ("Foreign gift or bequest", "Form 3520 Part IV generally applies above USD100,000 from a nonresident alien/foreign estate, with related-party aggregation. The 2026 foreign-corporation/partnership purported-gift threshold is USD20,573. Do not relabel your own balance as a gift.", ">USD100,000 individual/estate; USD20,573 entity (2026)", ["S43"]),
        ("U.S. 1% remittance tax", "The 2026 tax covers specified remittances sent from the United States when funded with cash, a money order, cashier's check or similar physical instrument. It is not a China-to-U.S. conversion charge.", "Not applicable to China→U.S. direction", ["S44"]),
        ("Physical cash declaration", "More than USD10,000 in currency/monetary instruments entering or leaving the U.S. must be declared to CBP on FinCEN Form 105. This is separate from China's cash-export permit tiers.", ">USD10,000 physical currency/instruments", ["S30", "S53"]),
    ]
    body = f'''<h1>China and U.S. tax & reporting</h1><div class="notice"><strong>Tax follows the income, not the wire.</strong> There is no verified universal CNY→USD conversion penalty. Underlying income, property gain, dividends, currency-basis gain and reporting failures are separate issues. A foreign tax credit is not an automatic full offset.</div>{table(["Topic", "Verified position", "Rate / threshold / unknown", "Official sources"], [[e(a),e(b),e(c),links(s)] for a,b,c,s in entries])}<h2>Practical compliance sequence</h2><ol class="steps"><li>Reconstruct annual maximum foreign-account balances and review FBAR for every year the Chinese account existed, including the year it is emptied.</li><li>Test Form 8938 separately using residence, filing status and asset values.</li><li>Trace each income tranche and its PRC tax record; analyze U.S. worldwide income and any limited foreign tax credit.</li><li>For CNY disposition, reconstruct acquisition dates/basis and personal versus investment/business character before applying §988.</li><li>For genuine foreign gifts/bequests or trusts, analyze Form 3520. Keep bank, conversion and remittance evidence.</li></ol><p>{links(['S31','S37','S39','S40','S43'])}</p>'''
    (OUT / "tax.html").write_text(shell("integration/tax.html", "Tax and reporting", body), encoding="utf-8")


def build_review():
    rows = [[e(a), e(b), links(c)] for a,b,c in FLAGS]
    body = f'''<h1>Flagged for Review</h1><div class="notice"><strong>These items are published and non-blocking.</strong> Unverified values stay blank. A citation verifies the cited rule or provider term, not personal eligibility, a bank's acceptance, or an all-in price.</div>{table(["Flag", "Finding / disposition", "Official / primary sources"], rows)}<h2>Detailed inherited review registers</h2><p><a href="../edition-h/site/flagged.html">Edition H — 52 flags</a> · <a href="../edition-h/site/repo-review.html">Edition H repository audit</a> · <a href="../edition-g/docs/flagged.html">Edition G flags</a> · <a href="../edition-f/site/flagged.html">Edition F flags</a> · <a href="../edition-d/docs/pages/flagged.html">Edition D flags</a></p>'''
    (OUT / "review.html").write_text(shell("integration/review.html", "Flagged for Review", body), encoding="utf-8")


def build_evidence():
    rows = []
    for sid, source in SOURCES.items():
        label = f'<strong>{e(sid)}</strong><small>{e(source["kind"])}</small>'
        link = f'<a href="{e(source["url"])}" rel="noopener noreferrer">{e(source["title"])} ↗</a>'
        rows.append([label, link, e(source["locator"]), e(source["scope"]), e(CHECKED)])
    body = f'''<h1>Evidence and direct-inspection log</h1><p>Each source below was retrieved and the listed operative scope inspected on {CHECKED} UTC using the page-retrieval tool. Government/regulator/court sources support legal and tax propositions. Provider-first-party sources support only that provider's own prices or product rules. Retrieval does not prove account eligibility or continuous future availability.</p>{table(["ID / type", "Source", "Inspected locator", "What was confirmed", "Checked UTC"], rows)}<h2>Scope of final verification</h2><ul><li>Consolidated legal, tax, fee and review rows use the sources above.</li><li>All 40 BOC/HSBC rows are independently recomputed from the displayed formulas and timestamped indicative rate.</li><li>Edition H supplies the broad 43-candidate inventory and 1,720-row per-method grids; its source register and checkers remain linked.</li><li>All prior-edition builders/checkers and an independent whole-repository internal-link crawl are run before publication.</li></ul><p><strong>Not claimed:</strong> exact personal tax, net USD receipt, bank approval, executable FX, or independent legal certification of every inherited archived line.</p>'''
    (OUT / "evidence.html").write_text(shell("integration/evidence.html", "Evidence log", body), encoding="utf-8")


def build_methodology():
    body = f'''<h1>Methodology and limitations</h1><h2>Source hierarchy</h2><ol class="steps"><li>Government, regulator, statute, court and official tax guidance for legal/tax claims.</li><li>A bank or provider's own tariff/help page for its own prices and product terms only.</li><li>No blog, forum, aggregator or law-firm summary supports a consolidated numeric or legal row.</li></ol><h2>Cost model</h2><ul><li>Targets are gross USD-equivalent principal before fees, not guaranteed net receipt.</li><li>P = target × CNY6.6903, using BOC's {CHECKED} 07:32:39 China-time indicative telegraphic ask. The actual execution rate controls.</li><li>BOC sender = min(CNY260, max(CNY50, 0.1%×P)) + CNY150 international cable. Overseas charges are separate; full-arrival is optional and conditional.</li><li>HSBC Premier/Advance sender = min(CNY500, max(CNY100, 0.1%×P)) + CNY120 cable. Other institutions' charges and taxes are excluded. The USD equivalent uses BOC's ask only for comparison; HSBC's own executable FX was not captured.</li><li>One transfer is assumed. No quota splitting or repeated-fee estimate is invented. Wise, ATM, cash, drafts and other methods retain their own formulas or blank values in Edition H.</li><li>FX cost, intermediary/receiver charges, documents, personal tax and all-in totals remain blank where unknown. N/A means not applicable, not zero.</li></ul><p>{links(['S03','S14','S16','S18','S20','S31','S39'])}</p><h2>Repository and archive policy</h2><p>Earlier editions remain unchanged. Material inconsistencies are disclosed on Flagged for Review rather than silently rewritten in archives. Mechanical verification proves deterministic arithmetic, source presence, blank semantics and local-link integrity; it does not establish legal correctness or future external-link uptime.</p><h2>Safety and legality</h2><p>Quota splitting, underground settlement, fabricated trade and crypto/stablecoin bridges are not tax-saving recommendations. Prohibited candidates have no operational steps. Business, investment and cash routes require real underlying transactions and cannot be used to relabel an unrelated personal balance.</p>'''
    (OUT / "methodology.html").write_text(shell("integration/methodology.html", "Methodology", body), encoding="utf-8")


def build():
    rows = cost_rows()
    # Files generated later in this function are valid link destinations.
    build_costs(rows)
    build_methods()
    build_tax()
    build_review()
    build_evidence()
    build_methodology()
    build_index(rows)
    (OUT / "costs.json").write_text(json.dumps({
        "checked_utc": CHECKED,
        "amount_definition": "Gross USD-equivalent principal before fees; one transfer; not guaranteed net receipt.",
        "boc_observation": {"usd100_bid_cny": 666.22, "usd100_ask_cny": 669.03, "usd100_reference_cny": 671.88, "published_china_time": "2026-11-10 07:32:39", "cny_per_usd_ask": float(RATE), "source": "S16"},
        "policy": "Known sender fees only. Null is blank/unverified, never zero.",
        "rows": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (OUT / "costs.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "sources": " ".join(row["sources"])})
    evidence = {
        "checked_utc": CHECKED,
        "method": "Direct fetch_page retrieval and listed operative-scope inspection",
        "sources": SOURCES,
        "flags": FLAGS,
        "inherited_catalog": {"edition": "H", "methods": 43, "cost_rows": 1720, "independently_recertified": False},
    }
    (OUT / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
