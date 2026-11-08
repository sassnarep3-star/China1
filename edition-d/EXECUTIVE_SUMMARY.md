# Executive Summary — Converting CNY to USD as a US Citizen

**Edition D · 2026-11-08 (UTC) · Official-source research, not legal/tax advice**

**Scope.** A US citizen holds RMB in a China bank account and wants it as USD. Question: the cheapest lawful way to convert/remit, what each method costs, at every USD 10,000 increment from $10,000 to $400,000. Verified against Chinese law (State Council Gazette, SAFE, STA, GACC), US law (26/31 USC, 31 CFR), IRS/FinCEN guidance, and bank-published boards/fee tables. 28 sources, each linked in `data/sources.json` and rendered in `docs/sources.html`.

---

## 1. The answer in one table

| Route (lawful) | $10k | $50k | $100k | $200k | $400k |
|---|---|---|---|---|---|
| L1 境内个人 quota (PRC resident) — 1 wire/$50k/yr | $53 (1 yr) | $166 (1 yr) | $333 (2 yrs) | $666 (4 yrs) | $1,332 (8 yrs) |
| L2 境外个人 documented-income — no cap | $53 | $166 | $272 | $482 | **$903** |
| L3 移民转移 emigrant exit (staged ≤50%/yr) | $85 (1 stage) | $237 (3 stages) | $366 | $651 | $1,025 |
| L4 继承转移 inheritance exit (1 application) | $53 | $166 | $272 | $482 | $903 |
| L5 Property-sale proceeds (SAFE approval) | $53 | $166 | $272 | $482 | $903 |

Fees are BoC counter standard (1‰, ¥50–260 cap + ¥150 telegraph per wire); spread is the measured one-way BoC board cost (0.2104%; full bid–ask 0.4206%); US receiving-bank fee **excluded — unverified (F-D03)**; L5 excludes disposition taxes (F-D07). Every increment $10k→$400k lives in `docs/ladder.html` / `data/ladder.json`.

**If you remember one number: at $400k, the lawful cost is ≈$900–$1,300 — about 0.23–0.33% of the amount — plus whatever your US adviser charges.**

## 2. The reframe — three beliefs, three facts

1. **“Converting CNY→USD is taxed.”** No. No Chinese or US tax applies to the exchange itself. China's IIT on savings interest has been exempt since 2008-10-09 （财税〔2008〕132号， via STA national tax library, `fgk.chinatax.gov.cn/zcfgk/c100012/c5193326/content.html`). US taxes the CNY account like any foreign asset — on income, not on the transfer.
2. **“The penalty is big.”** No. It is the bank spread (≈0.21% measured one-way, verify on trade date) plus a capped ¥410 (~$61) wire per remittance — legally capped by the bank's published fee table, whatever the amount.
3. **“It is possible if you just find the right trick.”** The blocker is **capital-account control**, not penalties: RMB only exits for capital purposes through narrow statutory gates (emigrant/inheritance/property-sale approval, SAFE-gated). The USD 50,000/yr facilitation quota is a *current-account* meter for **境内个人** (PRC residents with ID cards). A naturalized Chinese citizen is 境外个人 by operation of Nationality Law §9 — the quota route that takes 8 years for $400k **does not bind a foreign passport holder**, who buys against documented China-source income (S02 Art.13; S03 Art.59).

## 3. The status fork — determine this first

| | 境内个人 (PRC ID) | 境外个人 (foreign passport / naturalized US citizen) |
|---|---|---|
| Who | PRC residents incl. Chinese nationals with ID | Foreign citizens (naturalization abroad lapses Chinese nationality automatically), HK/MO/TW residents |
| Route | USD 50,000/person/**year**, ID only; remittance ≤$50k/day same-day with ID, above that documents | **No annual cap in the rule text** — buy FX against lawful China-source RMB income incl. tax vouchers; FX already in your FX account remits out on ID alone (S03 Art.65(一）) |
| Whole capital balance | Emigrant (L3) / inheritance (L4) / property-sale proceeds (L5), SAFE-approved | Same L3/L4/L5 capital gates |
| Reporting | FBAR/8938 regardless | FBAR/8938 same |

## 4. Recommended sequence (least cost first)

1. **Fix US reporting now.** If the China account exceeded $10,000 aggregate any time since you had US-person status, you owe an FBAR (FinCEN 114, free; due April 15, auto-extended Oct 15) and possibly Form 8938 ($10,000 + $10,000/30d after notice, max $60,000(S16)). Delinquency — not the wire — is where money dies. Use Streamlined procedures if delinquent.
2. **Confirm your 境内/境外 status** (passport vs PRC ID; naturalized abroad → 境外个人）.
3. **Locate the money's character**: (a) documented China-source income → L2 (uncapped, cheapest — 0.53% of amount at $10k falling to 0.23% at $400k); (b) legacy savings/capital balance → L3/L4/L5 (emigrant or inheritance; whole amount, staged for L3); (c) small balance (≤$50k × years you can wait) → L1; (d) not destined for the US → keep it in China / pay US obligations directly from China (K1/K3).
4. **Execute and document**: bank purchase voucher → wire receipt → FBAR for the receiving foreign account. Get the bank to confirm single-release processing for >$100k L2 purchases (F-D05).
5. **Never**: splitting across relatives' quotas, underground banks, false invoices, crypto — each ends at 30%–100% of the amount (外汇管理条例 Art.39/45) and potentially a criminal file, plus US willful-FBAR 50%/yr on top ($200k per $400k per year).

## 5. The cost of the shortcut, at every $100k

| Amount | CN fine (30%→100% band) | FBAR willful, 1 year (max($165,353, 50%·A)) |
|---|---|---|
| $100,000 | $30,000 → $100,000 | greater of $165,353 or 50% = **$165,353** |
| $200,000 | $60,000 → $200,000 | greater of $165,353 or $100,000 = **$165,353** |
| $300,000 | $90,000 → $300,000 | greater of $165,353 or $150,000 = **$165,353** |
| $400,000 | $120,000 → $400,000 | greater of $165,353 or $200,000 = **$200,000** |

(Full $10k-step table: `docs/penalties.html`. These are statutory exposures, not fees, and stack across unreported years. Per eCFR, amounts are those assessed on/after 2025-01-17; see Flag F-D11 re reported 2026 non-adjustment.)

## 6. Cost ladder, most important rows

Per $10k across the whole $10k→$400k range, totals equal *(spread + wire)*: e.g., $20k→$74; $60k→$194 (L1 2nd yr/… or L2); $150k→$377; $250k→$588; $350k→$790 (all L2-type single-wire). The complete 40× increments × 5 routes with years/wires/percent columns are in `docs/ladder.html` Table 0–H and `data/ladder.json`. Time is the real cost of L1: 8 calendar years for $400k.

## 7. Limits and honesty box

- US receiving bank fee: **unknown** — excluded from every total (F-D03). SAFE permit fees for L3/L4: unpublished — omitted (F-D08). L5 excludes ~5–20% of proceeds in disposition taxes (F-D07). L3 staging text is the 2004 Announcement (still the published instrument); 2014 SAFE changes to inheritance handling not re-verified line-by-line (F-D04). FBAR 2026 COLA not independently verified against the OMB memo; regulation table shows $16,536/$165,353 (F-D11). FX figures are a dated measurement — re-capture on trade date (F-D01). Two repo-wide citation defects found in review (F-D16 superseded crypto notice; F-D17 dead OLRC links). **Nothing in this document is personalized advice.**

## 8. Where to read more

- `docs/ladder.html` — every increment, every route
- `docs/methods.html` — 20 entries, eligibility/docs/steps/pros/cons
- `docs/penalties.html` — statutory exposure
- `docs/repo-review.html` — what was run/verified/flagged in the repo
- `docs/flagged.html` — 20 flagged items; `docs/sources.html` — 28 sources
- Sister editions: `/dossier/` (35 routes), `/edition-b/` (22), `/edition-c/` (33) at `https://sassnarep3-star.github.io/China1/`
