"""Edition J — verified CNY→USD research dashboard (session arena-3843fb62).

Every legal/tax claim cites a government/regulator/court source fetched and read
2026-11-10. Provider sources support only that provider's own tariffs/terms.
Unknown personal and all-in values are emitted as blank + UNVERIFIED, never zero.
Prohibited routes carry risk information only — no execution steps.
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = ROOT / "data"
CHECKED = "2026-11-10"
SNAPSHOT = "2026-11-10 13:49:58 China time"

# ---- Cost model (inputs read from fetched sources, see SOURCES) ----
SELL = Decimal("6.6866")          # BOC USD100 telegraphic ask 668.66 (S07)
BUY = Decimal("6.6586")           # BOC USD100 telegraphic buy 665.86 (S07)
MID = Decimal("6.6726")           # (665.86+668.66)/2
FX_MARGIN = (Decimal("668.66") - Decimal("667.26")) / Decimal("667.26")  # one-way vs midpoint
BOC_MIN, BOC_MAX, BOC_CABLE = Decimal("50"), Decimal("260"), Decimal("150")
HSBC_MIN, HSBC_MAX, HSBC_CABLE = Decimal("100"), Decimal("500"), Decimal("120")
TARGETS = list(range(10_000, 400_001, 10_000))


def q2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def boc_sender(target: int) -> Decimal:
    p = Decimal(target) * SELL
    return min(BOC_MAX, max(BOC_MIN, Decimal("0.001") * p)) + BOC_CABLE


def hsbc_sender(target: int) -> Decimal:
    p = Decimal(target) * SELL
    return min(HSBC_MAX, max(HSBC_MIN, Decimal("0.001") * p)) + HSBC_CABLE


def fx_margin_usd(target: int) -> Decimal:
    return q2(Decimal(target) * FX_MARGIN)


def boc_subtotal_usd(target: int) -> Decimal:
    return q2(fx_margin_usd(target) + boc_sender(target) / SELL)


def hsbc_subtotal_usd(target: int) -> Decimal:
    return q2(fx_margin_usd(target) + hsbc_sender(target) / SELL)


def tranches(target: int, per: int = 50_000) -> list[int]:
    out, rem = [], target
    while rem > 0:
        take = min(per, rem)
        out.append(take)
        rem -= take
    return out


def boc_tranche_subtotal_usd(target: int) -> Decimal:
    return q2(sum((fx_margin_usd(t) + boc_sender(t) / SELL) for t in tranches(target)))


def hsbc_tranche_subtotal_usd(target: int) -> Decimal:
    return q2(sum((fx_margin_usd(t) + hsbc_sender(t) / SELL) for t in tranches(target)))


def atm_per_withdrawal_cny(amount_cny: Decimal) -> Decimal:
    return min(Decimal("112"), Decimal("12") + Decimal("0.01") * amount_cny)


# ---- Source registry (all fetched/read 2026-11-10 unless noted) ----
SOURCES = {
    "S01": {"title": "PBOC Order [2006] No. 3 — Individual Foreign Exchange Measures",
            "url": "https://www.safe.gov.cn/safe/2006/1225/5319.html", "kind": "government",
            "locator": "Arts. 3, 7, 9, 13, 14, 22, 26, 33–35, 37",
            "scope": "Current/capital distinction; anti-splitting; overseas-person income; property sale/transfer; cash carry; 境内/境外 definitions."},
    "S02": {"title": "SAFE Huifa [2020] No. 14 — Current Account Guidelines (2020 edition)",
            "url": "https://www.gov.cn/gongbao/content/2020/content_5560296.htm", "kind": "government",
            "locator": "Arts. 47–49, 54–65, 68, 86–88",
            "scope": "USD50,000/yr facilitation tier; Art. 59 overseas-person income purchase; Art. 64–65 remittance; Art. 62 watchlist; cash rules."},
    "S03": {"title": "SAFE Huifa [2014] No. 2 — amended republication (capital account)",
            "url": "https://www.safe.gov.cn/tianjin/2024/0903/2594.html", "kind": "government",
            "locator": "Section VI",
            "scope": "Removes mandatory staged emigrant remittance; combines inheritance applications; removes notarisation requirement."},
    "S04": {"title": "SAFE — overseas bank-card cash withdrawal explainer (Huifa [2017] No. 29)",
            "url": "https://www.safe.gov.cn/safe/2017/1230/8130.html", "kind": "government",
            "locator": "Full explainer",
            "scope": "CNY100,000/person/year and CNY10,000/card/day overseas ATM caps; borrowed-card evasion prohibited."},
    "S05": {"title": "PRC Individual Income Tax Law (2018 amendment)",
            "url": "https://guangdong.chinatax.gov.cn/gdsw/zjfg/2018-08/31/content_a735b4c382d94439b581054c32a4e7f4.shtml",
            "kind": "government", "locator": "Arts. 1–3, 6–7, 10, 13, 15–16",
            "scope": "Residence; nine income categories; 20% proportional categories; property gain net basis; foreign tax credit; emigration clearance."},
    "S06": {"title": "Bank of China personal finance tariff, Chapter 3 (2025-11)",
            "url": "https://pic.bankofchina.com/bocappd/pricelist/202511/P020251110646838136627.pdf",
            "kind": "provider", "locator": "Items 210105008, 210108014; notes 4, 5, 10",
            "scope": "TT/draft 0.1% min CNY50/max CNY260 + CNY150 international cable; ATM (12 + 1%, max CNY112); USD15/25 conditional full-arrival; overseas charges at cost."},
    "S07": {"title": "Bank of China indicative foreign-exchange board",
            "url": "https://www.boc.cn/sourcedb/whpj/", "kind": "provider",
            "locator": "USD row and disclaimer, captured 2026-11-10 13:49:58 China time",
            "scope": "USD100 buy CNY665.86 / telegraphic ask CNY668.66 / reference CNY671.67. Indicative only; actual channel/counter rate controls."},
    "S08": {"title": "HSBC China tariff of accounts and services (effective 2026-10-31)",
            "url": "https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-accouts-and-services.pdf",
            "kind": "provider", "locator": "Items 2.2.4.1–2; notes 3, 7, 10",
            "scope": "Premier/Advance TT 0.1% min CNY100/max CNY500 + CNY120 cable; private-banking personal free; SHA/BEN/OUR charge options; exclusions."},
    "S09": {"title": "Wise — Guide to CNY transfers",
            "url": "https://wise.com/help/articles/2955298/guide-to-cny-transfers", "kind": "provider",
            "locator": "Sending from CNY",
            "scope": "Eligible non-mainland people with China work/tax records; own-account destination; CNY300,000 bank-app / CNY50,000 Alipay per-transfer caps; after-tax-income overall limit."},
    "S10": {"title": "26 U.S.C. §988 (2024 U.S. Code, GPO)",
            "url": "https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm",
            "kind": "government", "locator": "Subsections (a), (c)(1)(C), (e)",
            "scope": "Disposition of nonfunctional currency; ordinary-treatment default; personal-transaction exclusion fails when gain exceeds USD200."},
    "S11": {"title": "IRS — Form 8938 and FBAR comparison",
            "url": "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements",
            "kind": "government", "locator": "Threshold and penalty table",
            "scope": "FBAR aggregate >USD10,000 at any time; Form 8938 $50k/$75k (US-resident single) tiers; penalty table."},
    "S12": {"title": "IRS — Gifts from foreign person",
            "url": "https://www.irs.gov/businesses/gifts-from-foreign-person", "kind": "government",
            "locator": "Reporting requirements",
            "scope": "Form 3520 above USD100,000 from nonresident alien/foreign estate; 2026 foreign-entity purported-gift threshold USD20,573; aggregation."},
    "S13": {"title": "IRS — Foreign Tax Credit",
            "url": "https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit",
            "kind": "government", "locator": "Qualifying taxes and compliance issues",
            "scope": "Possible credit for qualifying foreign income taxes on the same income; treaty-reduced-tax and excluded-income limitations."},
    "S14": {"title": "PBOC et al. Yinfa [2026] No. 42 — virtual currency and RWA risks",
            "url": "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html",
            "kind": "government", "locator": "Sections 1, 3(6), 6 and final repeal clause",
            "scope": "Mainland virtual-currency exchange business prohibited; 2021 No. 237 expressly repealed."},
    "S15": {"title": "PBOC Announcement [2004] No. 16 — Individual Property Transfer Abroad",
            "url": "https://www.gov.cn/gongbao/content/2005/content_64294.htm", "kind": "government",
            "locator": "Arts. 2, 5–12",
            "scope": "Emigrant/inheritance definitions, evidence and own-account remittance. Staging in Art. 6 modified by S03. Inherited from integration evidence log; not re-fetched this session — see flag F12."},
    "S16": {"title": "IRS IR-2026-48 — remittance transfer tax proposed regulations",
            "url": "https://www.irs.gov/newsroom/treasury-irs-issue-proposed-regulations-on-the-new-remittance-transfer-tax-established-under-the-one-big-beautiful-bill",
            "kind": "government", "locator": "Full release",
            "scope": "1% tax from 2026-01-01 on specified physical-instrument-funded remittances sent from the United States, not China-to-U.S. Inherited from integration evidence log; not re-fetched this session — see flag F12."},
}

# ---- Methods: (id, category, name, status, when, pros, cons, steps, source_ids) ----
METHODS = [
    ("M01", "Current account", "Overseas-person lawful RMB income — purchase + remittance",
     "Lawful (conditional)",
     "You are a 境外个人 (passport holder) with lawful China-source RMB income (salary, labour, royalties, etc.).",
     ["No annual purchase cap in the rule text for this route (Art. 59); tax/source evidence is the gate, not a quota.",
      "Single documented wire; BOC/HSBC sender fees are small and capped (see costs)."],
     ["Requires genuine income + tax records; bank reviews authenticity (Art. 68).",
      "Cannot be used for unrelated savings — relabelling principal as salary is prohibited."],
     ["Confirm your bank classifies you as 境外个人 (passport) and will accept the income category.",
      "Gather: passport, employment/labour contract, payroll records, China IIT payment records (Art. 59 requires tax vouchers).",
      "At the bank: apply to purchase FX against the income, then remit to your own overseas account (Art. 65: ID only for existing FX).",
      "Keep purchase slip, SWIFT copy and tax records; reconcile U.S. reporting (FBAR/8938, worldwide income)."],
     ["S01", "S02"]),
    ("M02", "Current account", "Existing FX remittance (FX already held)",
     "Lawful (conditional)",
     "You already hold USD/FX in a China FX account (e.g. prior lawful purchase, remittance received).",
     ["Overseas-person FX remittance needs only ID (Art. 65) — no purchase quota involved.",
      "No conversion spread if already in USD."],
     ["Does not solve the CNY-conversion problem; only helps if FX is already held.",
      "Account identity (境内/境外) still controls; bank may still review source."],
     ["Confirm FX balance is in an FX account under your own name.",
      "Instruct remittance to your own overseas account; 境内个人 over USD50,000/day needs transaction evidence (Art. 64).",
      "Retain remittance receipt for U.S. reporting reconciliation."],
     ["S01", "S02"]),
    ("M03", "Current account", "境内个人 annual facilitation quota (USD50,000/yr)",
     "Lawful only if classified 境内个人",
     "You are classified 境内个人 (Chinese citizen holding a resident ID) — normally NOT a U.S. citizen with a U.S. passport.",
     ["Within quota: ID only, no transaction evidence (Arts. 54–55).",
      "Simple bank purchase + remittance."],
     ["A U.S. citizen holding a U.S. passport is 境外个人 under Art. 37 — this quota route does not apply.",
      "Splitting across people/years to evade limits is prohibited (Art. 7; Art. 62 watchlist)."],
     ["Confirm classification with the bank first — do not assume it.",
      "If 境内个人: purchase within USD50,000/yr, remit; over quota needs transaction evidence (Art. 56).",
      "Never borrow another person's quota."],
     ["S01", "S02"]),
    ("M04", "Current account", "Return of unused prior conversion",
     "Lawful (conditional)",
     "You previously converted FX to RMB and did not use the RMB.",
     ["Direct return path (Art. 14) with ID; no new purchase needed."],
     ["Only covers the unused converted amount; needs original exchange slip within 24 months (Art. 60)."],
     ["Bring passport + original exchange slip.",
      "Apply at bank for return conversion and remittance."],
     ["S01", "S02"]),
    ("M05", "Rails", "Wise from-CNY transfer",
     "Lawful (conditional)",
     "Non-mainland person with China work history and China tax records within the last 3 years; destination must be your own account.",
     ["Designed for exactly this profile; own-account rule keeps it compliant.",
      "Per-transfer caps are clear: CNY300,000 (bank app) / CNY50,000 (Alipay)."],
     ["Overall limit = after-tax China salary — cannot move unrelated principal.",
      "Fee is quote-time only; no 40-point schedule verified — cost cells stay blank."],
     ["Verify identity + tax records with Wise (1–2 working days first time).",
      "Start transfer from China bank app or Alipay; confirm remaining overall limit covers the amount.",
      "Destination must be your own overseas account/Wise account."],
     ["S09"]),
    ("M06", "Rails", "Bank telegraphic transfer (BOC / HSBC China)",
     "Rail — needs an entitlement first",
     "Any lawful entitlement (M01, M07–M11) executed as a bank wire.",
     ["Published capped sender fees (BOC max CNY410 all-in sender; HSBC max CNY620).",
      "SWIFT record; full-arrival option available (BOC note 5: USD15/25)."],
     ["Rail only — does not create entitlement; bank still reviews the underlying transaction.",
      "Intermediary/receiving charges excluded from tariff; FX execution rate is the real variable."],
     ["Present entitlement documents to the bank (see the entitlement method's steps).",
      "Choose SHA/BEN/OUR charge option; consider full-arrival if intermediary deductions are a concern.",
      "Confirm the executed FX rate and all deductions on the receipt."],
     ["S06", "S08"]),
    ("M07", "Capital account", "Emigrant property transfer",
     "Lawful (conditional)",
     "You have emigrated / are emigrating and transfer pre-emigration property abroad.",
     ["The only general capital-account exit for personal property; own-account remittance.",
      "2014 reform: no mandatory staged releases — one or multiple remittances within approval."],
     ["Requires emigration status + approval by the original household-registration SAFE office.",
      "Evidence-heavy (identity, hukou, property, tax); approval timelines apply."],
     ["Apply to SAFE at original hukou location with identity/property/tax evidence.",
      "Obtain approval; remit to your own overseas account within the approved amount (one or multiple times)."],
     ["S01", "S03", "S15"]),
    ("M08", "Capital account", "Inheritance property transfer",
     "Lawful (conditional)",
     "You inherit China property/funds as a 境外个人 heir.",
     ["Capital-account entitlement; 2014 reform allows combined applications across estates."],
     ["Needs notarised entitlement + tax/document review; bank/SAFE approval required.",
      "Inheritance-guide wording inconsistencies flagged (F11) — confirm locally."],
     ["Collect death/relationship/entitlement documents and tax records.",
      "Apply for approval; remit to your own account."],
     ["S01", "S03", "S15"]),
    ("M09", "Capital account", "Sale of China property (境外个人)",
     "Lawful (conditional)",
     "You actually sell China property held for own use.",
     ["Sale proceeds are an approved capital-account exit (Art. 22)."],
     ["Needs a real sale, IIT on net gain (Art. 6(5)), registration and bank review.",
      "No generic tax rate inferred — basis/proceeds records control."],
     ["Complete a genuine sale; pay/evidence IIT on net gain; register transfer.",
      "Apply for SAFE approval to purchase FX and remit proceeds."],
     ["S01", "S05"]),
    ("M10", "Capital account", "Insurance proceeds",
     "Lawful (conditional)",
     "You receive lawful insurance proceeds in China.",
     ["May use the overseas-person lawful-income process with policy + insurer payment proof."],
     ["Needs genuine policy/proceeds; bank reviews authenticity."],
     ["Gather policy and insurer payment proof.",
      "Apply via the M01 income process."],
     ["S01", "S02"]),
    ("M11", "Business", "Genuine trade / service settlement",
     "Lawful (conditional)",
     "You have real export/service income with contracts, invoices and customs/tax records.",
     ["Current-account settlement for real transactions; no personal quota involved."],
     ["Cannot be used to relabel personal savings — fictitious trade is prohibited (Arts. 7, 47).",
      "Bank reviews transaction documents; service payments over USD50,000 need tax filing records."],
     ["Maintain genuine contracts/invoices/customs records.",
      "Settle through the bank with transaction documents."],
     ["S01", "S02"]),
    ("M12", "Rails", "Bank draft / cashier's order",
     "Rail — needs an entitlement first",
     "Same entitlement as M06, executed as a draft instead of a wire.",
     ["BOC draft tariff is identical to TT (item 210105008).",
      "Useful where wire rails are unavailable."],
     ["Slower; overseas charges still apply; same entitlement review."],
     ["Present entitlement documents; request draft issuance at the same tariff as TT (item 210105008).",
      "Mail or present the draft per the bank's instructions; confirm overseas charges and delivery time before issuing."],
     ["S06"]),
    ("M13", "Rails", "Overseas ATM cash withdrawal (China card)",
     "Lawful but capped — not a bulk exit",
     "Small amounts only; you hold a China bank card and travel abroad.",
     ["No conversion decision needed at the China bank; cash in hand."],
     ["SAFE caps: CNY100,000/person/year and CNY10,000/card/day; suspension beyond annual cap.",
      "BOC tariff (12 + 1%, max CNY112) plus possible overseas surcharge; card network/issuer limits also apply."],
     ["Withdraw within CNY10,000/day and CNY100,000/year across all your cards.",
      "Never use another person's card (prohibited).",
      "Declare cash over USD10,000 entering the U.S. (FinCEN 105) — see flag F08."],
     ["S04", "S06"]),
    ("M14", "Rails", "Physical cash carry + customs declaration",
     "Lawful but capped — not a bulk exit",
     "Small amounts only; you travel with cash.",
     ["No bank FX spread on carried cash."],
     ["Carry limits, customs declaration and U.S. declaration rules apply; permits needed above thresholds.",
      "Not scalable to USD100,000+; security/AML scrutiny."],
     ["Check carry limits and permit requirements before travel.",
      "Declare on both sides as required; keep declarations."],
     ["S01", "S02"]),
    ("M15", "Prohibited", "Underground bank / hawala / informal settlement",
     "Prohibited — risk only, no steps",
     "—",
     ["None claimed."],
     ["Illegal FX settlement; administrative fines and possible criminal liability; funds at risk."],
     [],
     ["S01"]),
    ("M16", "Prohibited", "Quota splitting / nominee quotas",
     "Prohibited — risk only, no steps",
     "—",
     ["None claimed."],
     ["Art. 7 prohibits splitting to evade limits; Art. 62 watchlist (3-year enhanced review); fines under FX Regulation."],
     [],
     ["S01", "S02"]),
    ("M17", "Prohibited", "Falsified trade / invoices",
     "Prohibited — risk only, no steps",
     "—",
     ["None claimed."],
     ["False commercial documents to evade authenticity review; fines, account closure, criminal referral."],
     [],
     ["S01", "S02"]),
    ("M18", "Prohibited", "Virtual-currency / stablecoin bridge",
     "Prohibited — risk only, no steps",
     "—",
     ["None claimed."],
     ["PBC 2026 No. 42: mainland virtual-currency exchange business strictly prohibited; 2021 notice repealed and replaced."],
     [],
     ["S14"]),
    ("M19", "Prohibited", "Sham asset sale / gift relabelling",
     "Prohibited — risk only, no steps",
     "—",
     ["None claimed."],
     ["Creating a fake sale/gift to move unrelated principal misstates the transaction; tax and FX penalties."],
     [],
     ["S01", "S05"]),
    ("M20", "Prohibited", "Structuring around bank review thresholds",
     "Prohibited — risk only, no steps",
     "—",
     ["None claimed."],
     ["Deliberately splitting to avoid review is the Art. 7 violation pattern; watchlist and fines apply."],
     [],
     ["S01", "S02"]),
]

# ---- Taxes: (id, jurisdiction, item, position, sources) ----
TAXES = [
    ("T01", "China", "Conversion itself", "No conversion tax. The nine IIT categories (Art. 2) do not include currency exchange; the blocker is capital-account inconvertibility (Measures Art. 3), not a tax.", ["S05", "S01"]),
    ("T02", "China", "Salary / labour income", "Comprehensive income 3–45% progressive (Art. 3(1)); non-resident monthly deduction CNY5,000 (Art. 6(2)). Withholding + annual reconciliation (Arts. 11–13).", ["S05"]),
    ("T03", "China", "Interest / dividends / royalties", "20% proportional rate (Art. 3(3)).", ["S05"]),
    ("T04", "China", "Property transfer gain", "20% on (proceeds − basis − reasonable fees) (Arts. 3(3), 6(5)). Registration requires tax-payment proof (Art. 15).", ["S05"]),
    ("T05", "China", "Foreign tax credit", "Residents may credit foreign IIT paid, capped at the China tax on that income (Art. 7).", ["S05"]),
    ("T06", "China", "Emigration clearance", "Cancelling hukou on emigration requires prior tax settlement (Arts. 10(5), 13).", ["S05"]),
    ("T07", "U.S.", "Own principal", "Moving your own already-taxed principal is not automatically new U.S. income — but characterise the original income, interest, dividends and gains separately. No blanket exemption claimed.", ["S13"]),
    ("T08", "U.S.", "§988 currency gain/loss", "Disposition of nonfunctional currency is a §988 transaction, ordinary by default (a)(1), (c)(1)(C). Personal-transaction exclusion fails if gain exceeds USD200 (e)(2) — not a universal USD200 deduction.", ["S10"]),
    ("T09", "U.S.", "FBAR (FinCEN 114)", "Aggregate foreign accounts >USD10,000 at any time. Separate from the tax return; automatic extension to Oct 15.", ["S11"]),
    ("T10", "U.S.", "Form 8938 (FATCA)", "US-resident single: >USD50,000 year-end or >USD75,000 intra-year; higher tiers abroad. Filed with the return.", ["S11"]),
    ("T11", "U.S.", "Form 3520 (foreign gifts)", "Report gifts/bequests from a nonresident alien/foreign estate above USD100,000 (aggregate, related parties). Foreign corp/partnership purported gifts: USD20,573 for 2026.", ["S12"]),
    ("T12", "U.S.", "Foreign tax credit", "Credit for qualifying foreign income taxes on the same income (Form 1116); treaty-reduced-tax and excluded-income limits apply.", ["S13"]),
    ("T13", "U.S.", "1% remittance transfer tax", "Applies to specified physical-instrument-funded remittances sent FROM the U.S. (from 2026-01-01), not China-to-U.S. transfers. Inherited source — see F12.", ["S16"]),
    ("T14", "Penalty exposure", "China FX violations", "Administrative fines under the FX Administration Regulation for splitting/false documents; watchlist consequences (2020 Art. 62). Criminal referral possible — not quantified here.", ["S01", "S02"]),
    ("T15", "Penalty exposure", "U.S. reporting penalties", "FBAR civil penalties inflation-adjusted; willful up to the greater of USD100,000 or 50% of balances (pre-2016 figures on IRS table; current amounts adjusted annually). Form 8938 up to USD60,000. Criminal penalties may apply.", ["S11"]),
]

# ---- Flags: (id, finding, disposition, sources) ----
FLAGS = [
    ("F01", "Source of funds, 境内/境外 classification, China tax history and destination bank are unknown. No personal all-in total or 'best route' is certified.", "Blank + flagged; conditional decision order published instead.", ["S01"]),
    ("F02", "Executable FX rate, intermediary/receiving charges, document costs and personal tax are unknown. Sender tariffs are partial, not all-in quotes.", "All-in cells blank + UNVERIFIED in every ladder.", ["S06", "S07", "S08"]),
    ("F03", "BOC board is indicative; the ask moved from CNY669.03 (07:32) to CNY668.66 (13:49) on 2026-11-10. Edition J uses the 13:49 snapshot only.", "Dated snapshot; never mixed with Edition H/I observations.", ["S07"]),
    ("F04", "Wise fee for a personal from-CNY transfer is quote-time only; no 40-point schedule verified.", "Wise ladder blank + UNVERIFIED.", ["S09"]),
    ("F05", "BOC tariff note 1: local branches may vary; electronic-channel discounts possible.", "Tariff shown as published national schedule; confirm at the handling branch.", ["S06"]),
    ("F06", "HSBC Premier/Advance eligibility (balance/relationship) is not established for the reader.", "HSBC ladder labelled Premier/Advance only; other tiers differ.", ["S08"]),
    ("F07", "ATM/cash routes are capped (CNY100,000/yr; CNY10,000/day) and cannot scale to USD100,000+.", "Shown as capped rails with feasibility flag, not bulk exits.", ["S04"]),
    ("F08", "U.S. physical-currency declaration (FinCEN 105, >USD10,000) and China carry permits are separate from FX rules.", "Flagged; cash methods carry declaration steps.", ["S01", "S02"]),
    ("F09", "2004 staged-emigrant text vs 2014 §VI conflict: 2014 removed mandatory staging.", "2014 controls; 2004 cited only for definitions/evidence.", ["S03", "S15"]),
    ("F10", "Emigrant/inheritance approval timelines and local SAFE practice vary by province.", "Confirm with the handling SAFE office; no timeline inferred.", ["S03"]),
    ("F11", "Inheritance service-guide wording (pre-status language) is inconsistent across provincial guides.", "Flagged; confirm entitlement documents locally.", ["S03"]),
    ("F12", "S15 and S16 are inherited from the integration evidence log (retrieved 2026-11-10 by that session) and were not re-fetched by this session.", "Marked inherited; load-bearing figures do not depend on them.", ["S15", "S16"]),
    ("F13", "No wholesale re-certification of editions B–I rows was performed; disagreements are in edition-i/audit/REPO_AUDIT.md.", "Edition J certifies only its own rows.", ["S01"]),
    ("F14", "Criminal (as distinct from administrative) exposure is outside quantified scope.", "Penalty bands quoted as administrative; criminal referral noted, not quantified.", ["S01"]),
    ("F15", "Provider availability and tariffs can change without notice; live uptime is not certified.", "Dated 2026-11-10; re-check before executing.", ["S06", "S08", "S09"]),
]


def src_links(ids: list[str]) -> str:
    out = []
    for i in ids:
        s = SOURCES[i]
        out.append(f'<a class="source" href="{e(s["url"])}" rel="noopener noreferrer" title="{e(s["title"])} — {e(s["locator"])}">{i} ↗</a>')
    return " ".join(out)


CSS = """
:root{--navy:#102a43;--blue:#1769aa;--teal:#087f5b;--ink:#172b3a;--muted:#5c6f7c;--bg:#f4f7fa;--line:#d9e2ec;--warn:#8a4b00;--warnbg:#fff4d6}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.58 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
a{color:var(--blue);text-underline-offset:2px}a:focus-visible{outline:3px solid #b57600;outline-offset:2px}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:20}
header{background:var(--navy);color:#fff;padding:18px 16px}header a{color:#fff;text-decoration:none}
.brand{font-weight:800;font-size:1.15rem}.subtitle{display:block;color:#d9eaf7;font-size:.84rem;margin-top:3px}
nav{display:flex;gap:6px;overflow-x:auto;padding:10px 12px;background:#fff;border-bottom:1px solid var(--line);white-space:nowrap}
nav a{text-decoration:none;padding:7px 10px;border-radius:8px;font-size:.88rem}nav a[aria-current]{background:var(--navy);color:#fff}
main{max-width:1180px;margin:auto;padding:20px 14px 64px}h1{font-size:clamp(1.7rem,4vw,2.5rem);line-height:1.16;margin:.15em 0 .45em}
h2{font-size:1.35rem;line-height:1.25;margin-top:1.8em}h3{font-size:1.08rem}p{max-width:88ch}
.hero{padding:26px 20px;background:linear-gradient(135deg,#102a43,#1769aa);color:#fff;border-radius:16px}.hero p{max-width:78ch}.hero a{color:#fff}
.lead{font-size:1.08rem}.muted,small{color:var(--muted)}small{display:block;font-size:.78rem}
.notice{border-left:5px solid #d97706;background:var(--warnbg);padding:13px 15px;border-radius:8px;margin:14px 0}
.good{border-left-color:var(--teal);background:#e7f6ef}.danger{border-left-color:#9b1c1c;background:#fee2e2}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:12px}.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0}
.cards .card{margin:0;text-decoration:none;color:inherit}.card strong{color:var(--teal)}.card p{margin:.45em 0 0}
.kpi{font-size:1.65rem;font-weight:800;color:var(--teal)}
.button{display:inline-block;background:var(--navy);color:#fff;text-decoration:none;padding:9px 13px;border-radius:8px;margin:3px 5px 3px 0}
.steps li{margin:.5em 0}
.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:10px;margin:12px 0;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.86rem}th,td{text-align:left;vertical-align:top;padding:10px;border-top:1px solid var(--line)}
th{background:#eaf0f5;font-size:.73rem;text-transform:uppercase;letter-spacing:.035em}tbody tr:hover{background:#f8fafc}
.num{white-space:nowrap;font-variant-numeric:tabular-nums}
.source{display:inline-block;margin:2px 7px 2px 0;font-size:.75rem;white-space:nowrap}
.badge{display:inline-block;border-radius:5px;padding:2px 6px;font-size:.68rem;font-weight:800;background:#e5e7eb;color:#374151}
.unverified{background:var(--warnbg);color:var(--warn)}
.blank{display:inline-block;width:2.8em;border-bottom:2px dotted var(--warn);height:1em;margin-right:5px}
footer{border-top:1px solid var(--line);padding:20px 14px;text-align:center;color:var(--muted);font-size:.83rem}
code{overflow-wrap:anywhere}
@media(max-width:760px){main{padding:14px 10px 48px}.hero{padding:20px 15px}
.responsive thead{position:absolute;left:-9999px}.responsive,.responsive tbody,.responsive tr,.responsive td{display:block;width:100%}
.responsive tr{border-top:2px solid var(--line);padding:6px 0}.responsive td{border-top:0;padding:4px 10px}
.responsive td::before{content:attr(data-label);display:block;font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
"""

NAV = [("index.html", "Dashboard"), ("executive-summary.html", "Executive summary"),
       ("methods.html", "Methods"), ("steps.html", "Steps"), ("costs.html", "Costs"),
       ("taxes.html", "Tax & penalties"), ("sources.html", "Sources"), ("flagged.html", "Flagged for Review")]


def page(title: str, current: str, body: str) -> str:
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{href}"{cur if href == current else ""}>{label}</a>' for href, label in NAV)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="description" content="Source-linked CNY to USD routes, conditional sender-fee estimates, China and U.S. tax analysis">'
            f'<title>{e(title)} · China Money — Edition J</title><style>{CSS}</style></head><body>'
            f'<a class="skip" href="#main">Skip to content</a>'
            f'<header><a class="brand" href="index.html">China Money<span class="subtitle">Edition J — verified 2026-11-10 · CNY → USD for a U.S. citizen</span></a></header>'
            f'<nav aria-label="Sections">{nav}</nav><main id="main">{body}</main>'
            f'<footer>Blank = unverified, never zero · Partial estimates are not all-in quotes.<br>'
            f'Educational research, not individualized legal, tax, investment or immigration advice. '
            f'<a href="../../index.html">Portal</a> · <a href="sources.html">Sources</a></footer></body></html>\n')


def table(headers: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f'<td data-label="{e(h)}">{c}</td>' for h, c in zip(headers, row)) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table class="responsive"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def blank_cell() -> str:
    return '<span class="blank" aria-label="Blank, value unavailable"></span><span class="badge unverified">UNVERIFIED</span>'


def money_usd(x: Decimal) -> str:
    return f"USD {x:,.2f}"


def money_cny(x: Decimal) -> str:
    return f"CNY {x:,.2f}"


# ---- Cost ladders ----
LADDERS = [
    ("L1", "BOC TT — single wire (FX margin + sender fee)", "priced"),
    ("L2", "HSBC Premier/Advance TT — single wire", "priced"),
    ("L3", "BOC TT — USD50,000 tranches (repeated fees)", "priced"),
    ("L4", "HSBC TT — USD50,000 tranches", "priced"),
    ("L5", "BOC draft (same tariff as TT)", "priced"),
    ("L6", "BOC overseas ATM cash (capped rail)", "atm"),
    ("L7", "Wise from-CNY", "blank"),
    ("L8", "Emigrant / inheritance transfer (entitlement-dependent)", "blank"),
]


def build_cost_rows() -> dict[str, list[list[str]]]:
    out: dict[str, list[list[str]]] = {}
    for lid, _name, kind in LADDERS:
        rows = []
        for t in TARGETS:
            fx = fx_margin_usd(t)
            if kind == "priced" and lid in ("L1", "L5"):
                sender = boc_sender(t)
                sub = boc_subtotal_usd(t)
                rows.append([f"<strong>USD {t:,}</strong>",
                             f"{money_cny(sender)}<small>≈ {money_usd(q2(sender / SELL))} at ask</small>",
                             f"{money_usd(fx)}<small>vs midpoint, indicative</small>",
                             f"{money_usd(sub)}<small>partial, not all-in</small>",
                             blank_cell(),
                             src_links(["S06", "S07"])])
            elif kind == "priced" and lid == "L2":
                sender = hsbc_sender(t)
                sub = hsbc_subtotal_usd(t)
                rows.append([f"<strong>USD {t:,}</strong>",
                             f"{money_cny(sender)}<small>≈ {money_usd(q2(sender / SELL))} at ask</small>",
                             f"{money_usd(fx)}<small>vs midpoint, indicative</small>",
                             f"{money_usd(sub)}<small>partial, not all-in</small>",
                             blank_cell(),
                             src_links(["S07", "S08"])])
            elif kind == "priced" and lid == "L3":
                sub = boc_tranche_subtotal_usd(t)
                n = len(tranches(t))
                rows.append([f"<strong>USD {t:,}</strong>",
                             f"{n} × wire<small>USD50,000 tranches</small>",
                             f"{money_usd(fx)}<small>vs midpoint, indicative</small>",
                             f"{money_usd(sub)}<small>partial, not all-in</small>",
                             blank_cell(),
                             src_links(["S06", "S07"])])
            elif kind == "priced" and lid == "L4":
                sub = hsbc_tranche_subtotal_usd(t)
                n = len(tranches(t))
                rows.append([f"<strong>USD {t:,}</strong>",
                             f"{n} × wire<small>USD50,000 tranches</small>",
                             f"{money_usd(fx)}<small>vs midpoint, indicative</small>",
                             f"{money_usd(sub)}<small>partial, not all-in</small>",
                             blank_cell(),
                             src_links(["S07", "S08"])])
            elif kind == "atm":
                p = Decimal(t) * SELL
                per = atm_per_withdrawal_cny(p)
                n_with = -(-t // 10_000)  # ceil to USD10k/day-equivalent withdrawals (illustrative count)
                rows.append([f"<strong>USD {t:,}</strong>",
                             f"{money_cny(per)}/withdrawal<small>max CNY112; SAFE caps apply</small>",
                             f"{money_usd(fx)}<small>vs midpoint, indicative</small>",
                             blank_cell(),
                             f"≥ {n_with} withdrawals<small>CNY100k/yr cap binds</small>",
                             src_links(["S04", "S06", "S07"])])
            else:
                rows.append([f"<strong>USD {t:,}</strong>", blank_cell(), blank_cell(), blank_cell(), blank_cell(),
                             src_links(["S09"] if lid == "L7" else ["S01", "S03"])])
        out[lid] = rows
    return out


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(exist_ok=True)
    costs = build_cost_rows()

    # ---- index.html (dashboard) ----
    b10, b400 = boc_subtotal_usd(10_000), boc_subtotal_usd(400_000)
    h10, h400 = hsbc_subtotal_usd(10_000), hsbc_subtotal_usd(400_000)
    idx = f"""
<h1>CNY → USD: what it costs and what blocks it</h1>
<div class="hero"><p class="lead">There is <strong>no conversion tax</strong> in China or the U.S. The blocker is <strong>capital-account inconvertibility</strong> — you need a lawful entitlement first, then a rail. Sender fees are small and capped; the FX execution rate and downstream charges are the real variables.</p>
<p><a class="button" href="executive-summary.html">Read the executive summary</a><a class="button" href="costs.html">Open the $10K–$400K cost ladders</a></p></div>
<div class="cards">
<div class="card"><span class="kpi">{money_usd(b10)}</span><p><strong>BOC single wire at USD 10,000</strong> — FX margin vs midpoint + published sender fee. Partial, not all-in. {src_links(['S06','S07'])}</p></div>
<div class="card"><span class="kpi">{money_usd(b400)}</span><p><strong>BOC single wire at USD 400,000</strong> — same machinery; capped commission dominates. {src_links(['S06','S07'])}</p></div>
<div class="card"><span class="kpi">{money_usd(h400)}</span><p><strong>HSBC Premier/Advance at USD 400,000</strong> — higher cap (CNY500) + CNY120 cable. {src_links(['S08'])}</p></div>
<div class="card"><span class="kpi">0.2098%</span><p><strong>One-way FX margin vs midpoint</strong> (BOC board {SNAPSHOT}). Round-trip spread 0.4187%. Indicative only. {src_links(['S07'])}</p></div>
</div>
<div class="notice"><strong>Decision order:</strong> (1) identify the true source of funds and your 境内/境外 classification; (2) pick the matching entitlement (M01, M07–M11); (3) only then compare same-time executable quotes (BOC, HSBC, Wise if eligible). Never split quotas, falsify trade, or use crypto bridges — see M15–M20. {src_links(['S01','S02'])}</div>
<h2>Headline cost preview (partial sender-side only)</h2>
{table(["USD target", "BOC known sender fee", "HSBC P/A known sender fee", "All-in", "Sources"],
       [[f"<strong>USD {t:,}</strong>", f"{money_cny(boc_sender(t))}<small>≈ {money_usd(q2(boc_sender(t)/SELL))} at ask</small>", f"{money_cny(hsbc_sender(t))}<small>≈ {money_usd(q2(hsbc_sender(t)/SELL))} at ask</small>", blank_cell(), src_links(["S06","S07","S08"])] for t in (10_000, 50_000, 100_000, 400_000)])}
<p><a class="button" href="costs.html">Every $10,000 increment, every method</a><a href="methodology.html">Formula and limits</a></p>
<h2>Findings</h2>
<table(["#", "Finding", "Sources"],
       [["1", "Converting CNY→USD is not taxed in either jurisdiction. The nine China IIT categories do not include exchange; U.S. §988 taxes currency <em>gains</em>, not principal movement.", src_links(["S05","S10"])],
        ["2", "A U.S. citizen with a U.S. passport is 境外个人 (Measures Art. 37). The USD50,000/yr purchase quota is for 境内个人; overseas-person lawful income purchase (Art. 59) has no annual cap in the rule text.", src_links(["S01","S02"])],
        ["3", "The 'conversion penalty' is a bank FX margin of ~0.21% one-way (0.42% round-trip), plus capped sender fees — not a tax. At USD400,000 the BOC partial subtotal is " + money_usd(b400) + ".", src_links(["S06","S07"])],
        ["4", "The real penalty exposure is reporting: willful FBAR up to 50% of balances; Form 8938/3520 duties are separate from tax.", src_links(["S11","S12"])],
        ["5", "Prohibited workarounds (underground banks, quota splitting, fake trade, crypto) carry fines, watchlist and criminal risk — documented, never instructed.", src_links(["S01","S02","S14"])]])
"""
    (SITE / "index.html").write_text(page("Dashboard", "index.html", idx))

    # ---- executive-summary.html ----
    b400s = f"<strong>{money_usd(b400)}</strong> partial subtotal (FX margin + CNY410 sender). Receiver/intermediary/tax unknown — all-in stays blank."
    b10s = f"<strong>{money_usd(b10)}</strong> partial subtotal (FX margin + CNY216.87 sender). Fixed cable fee dominates at small sizes."
    summ = f"""
<h1>Executive summary</h1>
<p><strong>Reader:</strong> a U.S. citizen with CNY in a Chinese bank account. <strong>Decision date:</strong> {CHECKED}. <strong>Currency controls depend on immigration/residence and the money's source, not U.S. citizenship alone.</strong></p>
<div class="notice good"><strong>Most important result:</strong> there is <strong>no verified universal cheapest route</strong>. First establish that the bank can document the transaction, source of funds and tax treatment. Then request executable quotes for the same settled amount from every eligible provider and compare the FX rate plus every sending, intermediary and receiving fee — not just a headline commission.</div>
<h2>The numbers that matter</h2>
{table(["Question", "Answer", "Sources"],
       [["Is converting CNY→USD taxed?", "No, in either jurisdiction. China IIT Art. 2 lists nine income categories; exchange is not one. U.S. §988 taxes currency <em>gains</em> (ordinary by default), not the movement of principal.", src_links(["S05","S10"])],
        ["What does one lawful conversion cost?", "FX margin <strong>0.2098%</strong> one-way vs midpoint (BOC board {SNAPSHOT}: sell 668.66 / buy 665.86 per 100), plus capped sender fees.", src_links(["S07"])],
        ["All-in at USD 400,000 (BOC single wire)?", b400s, src_links(["S06","S07"])],
        ["All-in at USD 10,000 (BOC single wire)?", b10s, src_links(["S06","S07"])],
        ["What is the 0.42% figure?", "The <strong>round-trip</strong> spread (buy vs sell). A single conversion costs the one-way margin. Both are shown so the two are never confused.", src_links(["S07"])]])}
<h2>Decision order</h2>
<ol class="steps">
<li><strong>Classify first.</strong> Confirm with the bank whether you are 境内个人 or 境外个人 and which income/property category the balance belongs to. {src_links(['S01'])}</li>
<li><strong>Match the entitlement.</strong> Lawful RMB income (M01), emigrant/inheritance transfer (M07–M08), property sale (M09), insurance (M10), or genuine trade (M11). {src_links(['S01','S02','S03'])}</li>
<li><strong>Pick a rail.</strong> Bank TT (M06), draft (M12), or Wise if eligible (M05). Compare executable quotes. {src_links(['S06','S08','S09'])}</li>
<li><strong>Keep evidence.</strong> Purchase slips, SWIFT receipts, tax records; reconcile FBAR/Form 8938/3520. {src_links(['S11','S12'])}</li>
<li><strong>Never use prohibited workarounds</strong> (M15–M20). {src_links(['S01','S02','S14'])}</li>
</ol>
<h2>Tax and reporting — do not assume zero</h2>
<p>Moving your own already-taxed principal is not automatically new U.S. income, but characterise the original income, interest, dividends, asset gains and any currency disposition separately. §988's personal-transaction exclusion fails when gain exceeds USD200 — it is not a universal USD200 deduction. FBAR and Forms 8938/3520 are separate reporting duties. The new 1% U.S. remittance tax concerns remittances sent <em>from</em> the U.S., not this direction. {src_links(['S10','S11','S12','S13','S16'])}</p>
<p><a class="button" href="methods.html">All 20 methods with pros &amp; cons</a><a class="button" href="steps.html">Step-by-step procedures</a><a class="button" href="costs.html">Cost ladders</a></p>
"""
    (SITE / "executive-summary.html").write_text(page("Executive summary", "executive-summary.html", summ))

    # ---- methods.html ----
    mrows = []
    for mid, cat, name, status, when, pros, cons, _steps, sids in METHODS:
        mrows.append([f"<strong>{mid}</strong><small>{e(cat)}</small>", f"<strong>{e(name)}</strong><small>{e(status)}</small>",
                      e(when), "<br>".join(f"✓ {e(p)}" for p in pros) + "<br>" + "<br>".join(f"✗ {e(c)}" for c in cons),
                      src_links(sids)])
    meth = f"""
<h1>Methods — 20 routes, pros &amp; cons</h1>
<div class="notice"><strong>An entitlement is not a rail.</strong> M01/M07–M11 establish <em>what may be remitted</em>; M06/M12/M05 are <em>how</em>. Do not add their costs together. Prohibited routes (M15–M20) have risk information only — no execution steps.</div>
{table(["ID / category", "Method / status", "When it applies", "Pros & cons", "Sources"], mrows)}
"""
    (SITE / "methods.html").write_text(page("Methods", "methods.html", meth))

    # ---- steps.html ----
    srows = []
    for mid, cat, name, status, _when, _pros, _cons, steps, sids in METHODS:
        if steps:
            lis = "".join(f"<li>{e(s)}</li>" for s in steps)
            srows.append([f"<strong>{mid}</strong><small>{e(cat)}</small>", f"<strong>{e(name)}</strong>", f'<ol class="steps">{lis}</ol>', src_links(sids)])
        else:
            srows.append([f"<strong>{mid}</strong><small>{e(cat)}</small>", f"<strong>{e(name)}</strong>",
                          '<span class="badge unverified">PROHIBITED — no steps provided</span>', src_links(sids)])
    steps_html = f"""
<h1>Step-by-step procedures</h1>
<div class="notice">Every lawful procedure remains subject to the handling bank's and competent authority's current review. Large or complex capital transactions need advice from the bank, a China tax adviser and a U.S. international tax adviser before execution.</div>
{table(["ID / category", "Method", "Steps (provision to cite)", "Sources"], srows)}
"""
    (SITE / "steps.html").write_text(page("Steps", "steps.html", steps_html))

    # ---- costs.html ----
    ladder_sections = []
    for lid, name, _kind in LADDERS:
        ladder_sections.append(f"<h2>{lid} — {e(name)}</h2>" + table(
            ["USD target", "Sender / rail fee", "FX margin (indicative)", "Partial subtotal", "All-in", "Sources"], costs[lid]))
    costs_html = f"""
<h1>Costs — every $10,000 increment, every method</h1>
<div class="notice"><strong>Read this first.</strong> Targets are gross USD-equivalent principal before fees, not guaranteed net receipt. P = target × CNY6.6866 (BOC ask, {SNAPSHOT}). BOC sender = min(CNY260, max(CNY50, 0.1%×P)) + CNY150 cable. HSBC Premier/Advance sender = min(CNY500, max(CNY100, 0.1%×P)) + CNY120 cable. FX margin is vs the BOC midpoint and is indicative only — the executed channel rate controls. <strong>All-in stays blank + UNVERIFIED</strong> because receiver/intermediary charges, documents and personal tax are unknown. Blank never means zero. {src_links(['S06','S07','S08'])}</div>
<p><a href="methodology.html">Formula, worked example and limits</a> · <a href="costs.csv">Download all ladders (CSV)</a></p>
{''.join(ladder_sections)}
"""
    (SITE / "costs.html").write_text(page("Costs", "costs.html", costs_html))

    # ---- taxes.html ----
    trows = [[f"<strong>{tid}</strong>", e(jur), f"<strong>{e(item)}</strong>", e(pos), src_links(sids)] for tid, jur, item, pos, sids in TAXES]
    taxes_html = f"""
<h1>Tax &amp; penalty breakdown</h1>
<div class="notice">Conversion is not taxed; <em>income</em> is. Characterise the original income separately from the movement. Penalty bands below are administrative; criminal referral is noted, not quantified (F14).</div>
{table(["ID", "Jurisdiction", "Item", "Position", "Sources"], trows)}
"""
    (SITE / "taxes.html").write_text(page("Tax & penalties", "taxes.html", taxes_html))

    # ---- sources.html ----
    srows = [[f"<strong>{sid}</strong><small>{e(s['kind'])}</small>",
              f'<a href="{e(s["url"])}" rel="noopener noreferrer">{e(s["title"])} ↗</a>',
              e(s["locator"]), e(s["scope"]), CHECKED] for sid, s in SOURCES.items()]
    sources_html = f"""
<h1>Sources — 16 official/primary sources</h1>
<p>Each source was retrieved and its listed scope inspected on {CHECKED} UTC. Government/regulator/court sources support legal and tax propositions. Provider-first-party sources support only that provider's own prices or product rules. Retrieval does not prove account eligibility or continuous future availability.</p>
{table(["ID / type", "Source", "Inspected locator", "What was confirmed", "Checked"], srows)}
"""
    (SITE / "sources.html").write_text(page("Sources", "sources.html", sources_html))

    # ---- flagged.html ----
    frows = [[f"<strong>{fid}</strong>", e(finding), e(disp), src_links(sids)] for fid, finding, disp, sids in FLAGS]
    flagged_html = f"""
<h1>Flagged for Review</h1>
<div class="notice"><strong>These items are published and non-blocking.</strong> Unverified values stay blank. A citation verifies the cited rule or provider term, not personal eligibility, a bank's acceptance, or an all-in price.</div>
{table(["Flag", "Finding", "Disposition", "Sources"], frows)}
<h2>Repository audit</h2>
<p><a href="../audit/REPO_AUDIT.md">Edition J repository audit (line-by-line)</a> · <a href="../../index.html">Portal</a> · <a href="../../integration/review.html">Consolidated review</a></p>
"""
    (SITE / "flagged.html").write_text(page("Flagged for Review", "flagged.html", flagged_html))

    # ---- methodology.html ----
    ex10_boc = boc_subtotal_usd(10_000)
    meth_html = f"""
<h1>Methodology and limitations</h1>
<h2>Source hierarchy</h2>
<ol class="steps"><li>Government, regulator, statute, court and official tax guidance for legal/tax claims.</li>
<li>A bank or provider's own tariff/help page for its own prices and product terms only.</li>
<li>No blog, forum, aggregator or law-firm summary supports a numeric or legal row.</li></ol>
<h2>Cost model (worked example: USD 10,000, BOC single wire)</h2>
<ul><li>P = 10,000 × 6.6866 = CNY66,866.00.</li>
<li>Commission = 0.1% × P = CNY66.87 (within CNY50–260). Sender fee = 66.87 + 150 = <strong>CNY216.87</strong>.</li>
<li>FX margin = 10,000 × 0.209813% = <strong>USD 20.98</strong> vs midpoint (indicative).</li>
<li>Partial subtotal = 20.98 + 216.87/6.6866 = <strong>{money_usd(ex10_boc)}</strong>. All-in remains blank (receiver/intermediary/tax unknown).</li>
<li>One transfer assumed. Tranche ladders (L3/L4) repeat the fee per USD50,000 wire — shown to expose the cost of splitting, not to recommend it.</li></ul>
<p>{src_links(['S06','S07','S08'])}</p>
<h2>What verification proves (and does not)</h2>
<p>Mechanical verification proves deterministic arithmetic, source presence, blank semantics and local-link integrity. It does not establish legal correctness, personal eligibility, bank acceptance, an executable quote, or future external-link uptime. Earlier editions are preserved for provenance and are not re-certified here (F13).</p>
<h2>Safety and legality</h2>
<p>Quota splitting, underground settlement, fabricated trade and crypto/stablecoin bridges are not tax-saving recommendations. Prohibited candidates have no operational steps. Business, investment and cash routes require real underlying transactions and cannot be used to relabel an unrelated personal balance.</p>
"""
    (SITE / "methodology.html").write_text(page("Methodology", "methodology.html", meth_html))

    # ---- machine-readable exports ----
    (DATA / "sources.json").write_text(json.dumps(SOURCES, indent=2, ensure_ascii=False) + "\n")
    (DATA / "methods.json").write_text(json.dumps(
        [{"id": m[0], "category": m[1], "name": m[2], "status": m[3], "when": m[4], "pros": m[5], "cons": m[6], "steps": m[7], "sources": m[8]} for m in METHODS],
        indent=2, ensure_ascii=False) + "\n")
    (DATA / "taxes.json").write_text(json.dumps(
        [{"id": t[0], "jurisdiction": t[1], "item": t[2], "position": t[3], "sources": t[4]} for t in TAXES],
        indent=2, ensure_ascii=False) + "\n")
    (DATA / "flags.json").write_text(json.dumps(
        [{"id": f[0], "finding": f[1], "disposition": f[2], "sources": f[3]} for f in FLAGS],
        indent=2, ensure_ascii=False) + "\n")
    (DATA / "costs.json").write_text(json.dumps(
        {"checked": CHECKED, "snapshot": SNAPSHOT, "sell_rate": str(SELL), "buy_rate": str(BUY),
         "fx_margin_pct": str(FX_MARGIN),
         "targets": TARGETS,
         "boc_sender_cny": {str(t): str(boc_sender(t)) for t in TARGETS},
         "hsbc_sender_cny": {str(t): str(hsbc_sender(t)) for t in TARGETS},
         "boc_subtotal_usd": {str(t): str(boc_subtotal_usd(t)) for t in TARGETS},
         "hsbc_subtotal_usd": {str(t): str(hsbc_subtotal_usd(t)) for t in TARGETS},
         "boc_tranche_subtotal_usd": {str(t): str(boc_tranche_subtotal_usd(t)) for t in TARGETS},
         "hsbc_tranche_subtotal_usd": {str(t): str(hsbc_tranche_subtotal_usd(t)) for t in TARGETS}},
        indent=2) + "\n")

    with (SITE / "costs.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ladder", "usd_target", "sender_fee_cny", "fx_margin_usd", "partial_subtotal_usd", "all_in", "sources"])
        for lid, _name, kind in LADDERS:
            for t in TARGETS:
                if kind == "priced" and lid in ("L1", "L5"):
                    w.writerow([lid, t, boc_sender(t), fx_margin_usd(t), boc_subtotal_usd(t), "", "S06;S07"])
                elif kind == "priced" and lid == "L2":
                    w.writerow([lid, t, hsbc_sender(t), fx_margin_usd(t), hsbc_subtotal_usd(t), "", "S07;S08"])
                elif kind == "priced" and lid == "L3":
                    w.writerow([lid, t, "", fx_margin_usd(t), boc_tranche_subtotal_usd(t), "", "S06;S07"])
                elif kind == "priced" and lid == "L4":
                    w.writerow([lid, t, "", fx_margin_usd(t), hsbc_tranche_subtotal_usd(t), "", "S07;S08"])
                elif kind == "atm":
                    w.writerow([lid, t, atm_per_withdrawal_cny(Decimal(t) * SELL), fx_margin_usd(t), "", "", "S04;S06;S07"])
                else:
                    w.writerow([lid, t, "", "", "", "", "S09" if lid == "L7" else "S01;S03"])

    print(f"Edition J: {len(METHODS)} methods, {len(TAXES)} tax rows, {len(FLAGS)} flags, "
          f"{len(LADDERS)} ladders x {len(TARGETS)} targets = {len(LADDERS)*len(TARGETS)} cost rows")
    print(f"BOC 10k={boc_subtotal_usd(10_000)} 400k={boc_subtotal_usd(400_000)} | "
          f"HSBC 10k={hsbc_subtotal_usd(10_000)} 400k={hsbc_subtotal_usd(400_000)} | "
          f"FX margin={FX_MARGIN*100}%")


if __name__ == "__main__":
    main()
