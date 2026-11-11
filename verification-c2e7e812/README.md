# Verification record — session arena-c2e7e812 (2026-11-11)

Independent re-verification of the canonical guide on `main` after PR #69, under the
takeover of stale claims noted in `COORDINATION.md` (session board arena-c2e7e812).
Nothing here is legal or tax advice.

## What was run

| Step | Result |
|---|---|
| `python3 guide/build/build.py` deterministic rebuild | PASS — 19 methods × 40 amounts, 33 sources, 23 flagged items; output identical to committed pages before any data change |
| `python3 guide/build/verify.py` (every table row has an official source link; every blank cell links to Flagged for Review; 370 totals recomputed; whole-repository link crawl; quoted-text cross-check of every priced figure) | PASS — 11 pages; 1,057 table rows; 288 blank-cell rows; 760 ladder rows; 280 HTML files / 22,600 internal links, none broken |

## Sources re-opened in this session (web_search, 2026-11-11 ~12:55–13:05 UTC)

The sandbox cannot open arbitrary URLs directly, so each page was re-checked through
independent search results that quote the official text. PASS below means the official
page is still published and its quoted text matches what `guide/data/sources.json`
records. Details per source: [sources-recheck.md](sources-recheck.md).

| Source | Guides uses it for | Result 2026-11-11 |
|---|---|---|
| Bank of China FX board `boc.cn/sourcedb/whpj/` | CN-FXBOARD — dated USD buy/sell snapshot | PASS — board live, USD rows published (reading of 2026-11-09 seen: 666.41/669.22; guide's own reading is the 2026-11-11 10:25:02 Beijing snapshot, flagged F20 as time-specific) |
| SAFE Tianjin Q&A 2026-07-13 (`safe.gov.cn/tianjin/2026/0713/3088.html`) | CN-ART59 — art. 59 Huifa〔2020〕No. 14 lawful current-account income purchase of FX | PASS — page live, art. 59 quoted verbatim as recorded |
| SAFE Tianjin Q&A 2026-05-11 (`safe.gov.cn/tianjin/2026/0511/3051.html`) | foreign permanent-resident quota Q&A | PASS — page live, matches PR-quota wording |
| FX Regulation, State Council Order 532 (`gov.cn`) | CN-FXREG — penalty table | PASS — arts. 39/40/42/45: up to 30%, serious 30%–100%; carrying breach up to 20%; private FX dealing confiscation + fines |
| PBOC Order 2006 No. 3 + SAFE 2007 implementation rules (`safe.gov.cn/safe/2006/1225/5319.html`, `/2007/0105/5320.html`) | CN-MEASURES, CN-RULES — USD 50,000 annual totals, splitting ban, art. 13 | PASS — art. 7 splitting-to-evade prohibition; USD 50,000 equivalents per person per year confirmed |
| 31 CFR 1010.821 (eCFR) + 31 USC 5321 (govinfo) | US-FBARPEN — FBAR penalty figures | PASS — $16,536 non-willful; willful = greater of $165,353 or 50% of the balance (adjustments for penalties assessed on/after 2025-01-17) |
| IRS "Comparison of Form 8938 and FBAR" | US-8938FBAR — thresholds | PASS — FBAR > $10,000 aggregate any time; 8938 thresholds $50k/$75k, $100k/$150k, abroad $200k/$300k, $400k/$600k as recorded |
| 26 USC 988 (govinfo) | US-988 — exchange gain/loss, $200 personal-transaction exclusion | PASS — §988(e)(2) verbatim match |
| IRS/Treasury proposed regs on the 1% remittance transfer tax (OBBBA, IRC §4475) | US-REMIT — inbound transfers not taxed | PASS — 1% applies to US-outbound remittances funded with cash/money order/cashier's check from 2026-01-01; account/card-funded exempt |
| Wise "Guide to CNY transfers" (article 2955298) | PR-WISE — eligibility and limits | PASS — non-mainland-Chinese who worked in China with tax records ≤ 3 years; personal accounts only; Alipay 50,000 CNY/transfer; overall limit = after-tax China salary |
| STA/SAFE Announcement 2013 No. 40 (`fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html`) | CN-TAXFILING — tax filing above USD 50,000 | PASS — page live, filing requirement text as recorded; art. 4 carve-out noted in F01 |
| SAFE 汇发〔2017〕29号 (overseas ATM cash) (`safe.gov.cn/safe/2017/1230/8130.html`) | CN-CARD — ATM caps | PASS — 10,000 CNY/card/day; 100,000 CNY/person/year; suspension on breach |
| IRS "Gifts from foreign person" (Form 3520) | US-3520 — gift/bequest reporting | PASS — > $100,000 from nonresident alien individuals/foreign estates |
| BOC personal tariff PDF (2025-11 price list) | CN-BOCTARIFF — wire commission 1‰ (min 50/max 260), cable 150, full-amount $25/$15, ATM 12 + 1% max 112 | CONSISTENT with the recorded quote in `sources.json` (the PDF itself is served from `pic.bankofchina.com`; figures re-checked against the stored quote, not re-downloaded) — see sources-recheck.md |
| Wise comparison API quotes (PR-WISEFEE) | M10 cost rows | Snapshot data from 2026-11-11T02:35Z; unchanged by definition of a snapshot; flagged F06 for re-quote before acting |

## Corrections applied in this session

1. **Open integration request (from QA session arena-713a97b7, carried over by the
   stale takeover of arena-dc298e7a):** added `quality-713a97b7/index.html` to
   `guide/data/archive.json` so the independent QA report is reachable from the
   canonical Archive page. Regenerated `guide/archive.html`; no other guide page
   changes. Build + verify PASS after the change.

## Items deliberately NOT changed

- `guide/data/prices.json` dated snapshots (BOC board 2026-11-11 10:25:02 Beijing;
  Wise quotes 02:35Z): re-reading minutes-old snapshots from search-index caches
  would mix timestamps; they are flagged (F06, F20) and dated on the site.
- Historical session-board blocks in `COORDINATION.md`, including stale figures in
  older boards (e.g. $93.36/$939.01 quoted by arena-f766722d before the
  2026-11-11 repricing) — preserved verbatim as log entries per the coordination
  rules; they are not site data.
- Open PRs #39 and #45 (owned by other sessions, listed on Flagged for Review).

## QA wording requests vs current guide text (re-checked)

| # | Request | State in current guide | Action |
|---|---|---|---|
| 1 | FBAR willful ceiling must show the 50%-of-balance alternative and reasonable-cause exception | Figure cell lists the fixed amounts; flag **F14** documents the 50% alternative; statute + eCFR both linked | OK — flagged, not overstated |
| 2 | China tax voucher ≠ proof conversion adds only fees; §988/FTC conditional | Taxes page says the FTC "may be available, subject to limitations"; exchange-gain row cites §988(e) with $200 exception; F13 open | OK |
| 3 | Wise-vs-BOC not a fully priced winner | Summary states Wise figures exclude any receiving-bank fee; Wise rows stop at its CNY 300,000 quote cap; F06 open | OK |
| 4 | Full-amount service and fee conversion assumptions (BOC tariff notes 1 and 5) | M01 step 5 presents full-amount delivery as an option; F04 (intermediary deductions), F19 (commission base/discounts) open | OK |
| 5 | No blanket ban on all split transactions | Guide prohibits only splitting *to avoid review/evade limits* (steps and X01); matches PBOC Order 2006-3 art. 7 | OK |
| 6 | Wage route quoted as conditional | M01 "who" limits it to lawful current-account income with documents; ART59 quote is verbatim | OK |
