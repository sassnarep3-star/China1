# Edition D — CNY → USD for a US citizen

**Live site:** https://sassnarep3-star.github.io/China1/edition-d/docs/

A self-contained research edition under `edition-d/`. It does not modify the four earlier editions in
this repository (root, `dossier/`, `edition-b/`, `edition-c/`); it answers the same brief with a
different emphasis: a dollar cost at every $10,000 step from $10,000 to $400,000, a step-by-step
sequence for every route, and a mechanical verifier that re-derives every published number from the
model before the site can be committed.

> Research, not legal, tax or investment advice. Every legal proposition is cited to an article of an
> official instrument. Where a price could not be found on an official source it is either left blank
> and flagged, or used as an explicitly labelled assumption and stress-tested. Nothing is silently
> estimated.

---

## Executive summary

### The answer in one paragraph

The cheapest lawful way to move a balance out of mainland China is a **bank FX purchase followed by a
SWIFT wire**, executed as an *overseas individual* against documented, lawful **current-account income
earned in China**. On a **$400,000** balance the total cost is **≈ $941 — 0.235% of the money**. There
is no Chinese tax on converting CNY into USD and no US tax on repatriating your own after-tax
principal. The "considerable amount of taxes" in the brief is almost certainly one of three different
things: (a) Chinese tax on the event that created the money, which was owed whether or not you moved
it; (b) the commercial spread and wire charges; or (c) the penalty for a route that is not lawful.

### The cost table (condensed)

Bank FX purchase + one wire, from the model in `build/model.py`:

| Amount | Total cost | % of amount |
|---|---|---|
| $10,000 | $93.40 | 0.934% |
| $25,000 | $143.90 | 0.576% |
| $50,000 | $206.22 | 0.412% |
| $100,000 | $311.18 | 0.311% |
| $200,000 | $521.11 | 0.261% |
| $300,000 | $731.03 | 0.244% |
| $400,000 | $940.95 | 0.235% |

The full 40-row table, the seven-column route comparison and the stress test are on the site under
*Cost tables*. The percentage falls as the amount rises because fixed wire charges do not scale — the
opposite of how a tax behaves.

### Why it is not automatic

| Gate | What the rule says | What it means |
|---|---|---|
| Character of the money | Current-account business is convertible; capital-account business follows a phased process (PBOC Measures 2006, Art. 3) | Salary, fees, rent and interest are easy. A property gain needs SAFE approval. |
| Who you are | A passport holder is an *overseas individual* (Art. 37(2)); the USD 50,000 annual quota applies only to a *domestic* individual (Art. 9) and, per SAFE's 2024 answer, to an overseas individual only if they hold a Chinese permanent-residence ID | You are not necessarily limited to USD 50,000 a year |
| Evidence | ID plus source-of-funds evidence **including tax vouchers** (Detailed Rules Art. 13(1); Current-Account Guide Art. 59) | Without the tax paper the branch falls back on the quota |
| Who decides | The bank reviews authenticity; the regulator sets only the exchange-rate regime | The branch is the gatekeeper — get its position in writing |

### The five layers of the "conversion penalty"

1. **FX spread** — the bank's own buy/sell gap is 0.4199% (BOC board, 2026-11-09 05:30 Beijing time);
   one-way, about 0.21% of principal.
2. **Bank commission and cable** — a percentage fee with a floor and a cap, plus a fixed charge.
3. **Correspondent and receiving bank** — about $40 per wire.
4. **Tax on the event** — Chinese IIT at 20% flat on interest, dividends and transfers of assets;
   3–45% on wages. This is owed because the income arose, not because the money moves.
5. **Penalty** — only if the route is unlawful: 0–30% of the amount, 30–100% in serious cases.

On $400,000, layers 1–3 total **$940.95**. Layer 4 is a percentage of a *gain*, not of the balance.
Layer 5 starts at $120,000 and runs to $400,000 on the same balance. That is the real subject of the
brief.

### The routes

Eleven lawful or conditional routes, six prohibited, two that do not exist as personal repatriation
routes. Each has a page with the legal basis, the 40-row cost table and a step-by-step sequence:

| Route | What it is | Status |
|---|---|---|
| M01 | Bank FX purchase + SWIFT wire, documented current-account income | Lawful — cheapest |
| M02 | The same, drip-fed under the USD 50,000 annual quota | Conditional — 8 years for $400k |
| M03 | Emigration transfer (移民转移), whole balance in three releases over two years | Conditional |
| M04 | Inheritance transfer (继承转移) | Conditional |
| M05 | Sale proceeds of your own Chinese property | Conditional — SAFE approval + 20% IIT on the gain |
| M06 | Remit USD you already hold — no conversion at all | Lawful — zero spread |
| M07 | RMB to Hong Kong, convert offshore, wire onward | Conditional — costs unverified |
| M08 | Withdraw RMB abroad with a Chinese card | Conditional — ≈ $14,942/year cap |
| M09 | Carry foreign cash out | Conditional — $10,000 per exit with a permit |
| M10 | Company dividend remittance | Conditional — withholding tax unverified |
| M11 | Liquidation / capital reduction of a foreign-invested enterprise | Conditional — express statutory entitlement |
| P01–P06 | Splitting, underground banks, false documents, crypto, oversized cash, FX bought for overseas property | Prohibited, with the statutory fine band applied to each $10,000 step |
| X01–X02 | Wise/Revolut-style services; QDII funds | Not available as personal repatriation routes |

### The US side

Repatriating principal is not a taxable event, and §988(e)(2) switches off foreign-currency gain on a
personal transaction unless the gain exceeds **$200**. The exposure that matters is reporting: **FBAR**
above $10,000 in aggregate at any time in the year, and **Form 3520 Part IV** for a foreign gift or
bequest above $100,000. A willful FBAR penalty is the greater of $100,000 (inflation-adjusted) or 50%
of the account balance, per violation.

---

## What is verified, what is assumed, what is blank

- **Verified** — every legal proposition, the exchange rate used (with its timestamp), the receiving
  bank's incoming-wire fee, the quota, the cash and ATM limits, the US reporting thresholds.
- **Assumption, labelled and stress-tested** — the Chinese bank commission and cable charge (A2), the
  correspondent deduction (A3), and the decision to treat the one-way spread as half the round-trip gap (A1).
- **Blank and flagged** — the offshore CNH spread and Hong Kong wire fees (U03), overseas ATM fees
  (U04), notarisation and translation costs (U05), non-IIT taxes on a property sale (U06), the Chinese
  withholding rate on a corporate dividend (U07), and whether third-party transfer apps work at all (U08).
- **A genuine conflict, not resolved** — whether a foreigner resident in China for a year is a
  "domestic individual": the 2008 Regulation says yes, the 2006 Measures and SAFE's 2024 answer say the
  passport decides. Published as **U09**.

## Build and verify

```sh
python3 edition-d/build/build.py     # regenerates edition-d/docs
python3 edition-d/build/verify.py    # 36 mechanical checks, exits non-zero on failure
```

The verifier re-derives every published cost from the model, checks that all 40 rows exist for every
route, that every source URL sits on an allowlisted official publisher, that every internal link and
anchor resolves, that no blank is undisclosed, and that no page claims a conversion tax exists.

## Layout

```
edition-d/
├── README.md              this summary
├── build/
│   ├── model.py           sources, routes, cost model, tax layer, flags
│   ├── build.py           static generator (standard library only)
│   ├── verify.py          36 mechanical checks
│   └── style.css          no external assets, no web fonts, no tracking
└── docs/                  generated site (committed; Pages serves it)
```
