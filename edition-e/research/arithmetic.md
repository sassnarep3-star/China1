# Arithmetic scenarios — not quotes, not tax

Amounts: `A = 10,000, 20,000, …, 400,000 USD` (40 rows per method).

## Reference FX inputs

- BOC extracted spot selling: `669.29 CNY / USD 100 = 6.6929 CNY/USD`.
- BOC extracted spot buying: `666.48 / 100 = 6.6648`.
- BOC extracted middle: `671.68 / 100 = 6.7168`.
- Quote-midpoint comparator used here: `(6.6648 + 6.6929)/2 = 6.67885`.
- Treasury reporting benchmark: `6.7050 CNY/USD`, effective 2026-09-30; not used as a retail execution rate.

The BOC board timestamp is `2026/11/09 05:30:00`, later than the report date and with unestablished timezone. These are conditional snapshot inputs only.

## FX spread proxy

For a purchase of USD A with CNY:

```
purchase_CNY = A × 6.6929
midpoint_CNY = A × 6.67885
spread_proxy_CNY = A × 0.01405
spread_proxy_USD_at_sell = spread_proxy_CNY / 6.6929
spread_proxy_pct_of_purchase = 0.01405 / 6.6929 × 100 ≈ 0.209924%
```

This is a one-way snapshot spread proxy against the bid/ask midpoint. It is **not** a round-trip loss, tax, fee, executable quote or guaranteed saving. The inherited 0.42% figure uses the full bid/ask gap divided by the ask; it answers a different question.

## BOC standard outward TT sender tariff

For one international telegraphic transfer, excluding optional full-arrival surcharge:

```
percentage_fee_CNY = min(max(purchase_CNY × 0.001, 50), 260)
sender_tariff_CNY = percentage_fee_CNY + 150
sender_tariff_USD_at_sell = sender_tariff_CNY / 6.6929
```

The USD full-arrival service, if eligible and selected, adds USD 15 when the beneficiary banks through BOC New York, otherwise USD 25, subject to the tariff’s service conditions. Other overseas charges are actual/unknown. The grid keeps the optional surcharge separate and leaves receiving charges blank.

## SC electronic overseas transfer, OUR selected

Sender-side published components:

| Tier | Handling | Cable | OUR intermediary | Total CNY |
|---|---:|---:|---:|---:|
| Personal | 100 | 120 | 200 | 420 |
| Ease | 0 | 120 | 200 | 320 |
| Priority | 0 | 0 | 200 | 200 |
| Priority Private | 0 | 0 | 0 | 0 |

These are conditional tariff arithmetic, not an all-in cost. FX execution, tier eligibility and beneficiary-side deductions remain blank/unknown. A zero published sender component is not a zero total cost.

## Worked checks

| USD | Purchase CNY at 6.6929 | Spread proxy CNY | BOC percentage fee CNY | BOC sender tariff CNY |
|---:|---:|---:|---:|---:|
| 10,000 | 66,929.00 | 140.50 | 66.93 | 216.93 |
| 50,000 | 334,645.00 | 702.50 | 260.00 | 410.00 |
| 100,000 | 669,290.00 | 1,405.00 | 260.00 | 410.00 |
| 400,000 | 2,677,160.00 | 5,620.00 | 260.00 | 410.00 |

Rounding: Decimal arithmetic; displayed currency values round half-up to 2 decimals. Unknown values are JSON `null` and render as an explicitly labelled blank, never zero.
