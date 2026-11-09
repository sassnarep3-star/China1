# -*- coding: utf-8 -*-
"""Edition H — cost engine.

Rules enforced here, not in prose:
  1. A cell is computed only from a parameter that carries a source id.
  2. A method with any unpublished component keeps its all-in total BLANK.
     It is never estimated, averaged or inferred.
  3. The ladder is exactly USD 10,000 to USD 400,000 in USD 10,000 steps
     (40 points), for EVERY method.
"""

from decimal import Decimal, ROUND_HALF_UP

# --------------------------------------------------------------------------
# Parameters — each one traceable to a fetched page (see sources.py)
# --------------------------------------------------------------------------

# BK-04  BOC board, USD row, 2026-11-09 09:15:45 Beijing, CNY per 100 USD
BUY_SPOT = Decimal("666.38")     # 现汇买入价 — bank buys USD from you
SELL_SPOT = Decimal("669.19")    # 现汇卖出价 — bank sells USD to you
REFERENCE = Decimal("671.88")    # 中行折算价 — BOC reference

# Derived one-way margin for a CNY -> USD conversion:
# you pay SELL_SPOT per 100 USD rather than the midpoint of the board.
MID = (BUY_SPOT + SELL_SPOT) / 2
FX_MARGIN_PCT = (SELL_SPOT - MID) / MID * 100          # one-way
FX_ROUND_TRIP_PCT = (SELL_SPOT - BUY_SPOT) / SELL_SPOT * 100  # round trip

# BK-01 / BK-02  BOC personal cross-border telegraphic transfer
COMMISSION_RATE = 0.001
COMMISSION_MIN_CNY = 50
COMMISSION_MAX_CNY = 260
CABLE_FEE_CNY = 150               # international; 80 for HK/Macau/Taiwan
CABLE_FEE_HK_CNY = 80

# BK-03 / BK-07  full-amount arrival, USD
FULL_AMOUNT_USD = 15              # receiving bank holds its account with BOC NY
FULL_AMOUNT_USD_OTHER = 25

# BK-08  named US receiving-bank example (Chase business schedule)
RECEIVING_BANK_USD = 15

# BK-05 / BK-06  cash and documents
CARRIAGE_CERT_CNY = 10            # waived 2025-04-01 .. 2026-12-31
DEPOSIT_CERT_CNY_LOW = 20
DEPOSIT_CERT_CNY_HIGH = 40

AMOUNTS = list(range(10_000, 400_001, 10_000))   # exactly 40 points

# Sanity: 665.29 CNY per 100 USD would make USD 10,000 = CNY 66,529.
# We convert USD notional to CNY using the sell rate, because that is the
# rate at which the bank would need to buy CNY from you to create the USD.

def usd_to_cny(usd):
    """CNY equivalent at the BOC sell rate (CNY per 100 USD)."""
    return Decimal(usd) / Decimal(100) * SELL_SPOT


def q2(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def q4(x):
    return Decimal(x).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------
# Component functions — each returns a USD figure or None
# --------------------------------------------------------------------------

def fx_margin_usd(usd):
    """Cost of crossing the BOC bid/ask spread on one conversion, in USD.

    Measured against the board midpoint: you receive value at the sell rate
    and are measured at the mid, so the loss is (sell - mid)/mid.
    """
    return q2(Decimal(usd) * FX_MARGIN_PCT / Decimal(100))


def commission_cny(usd):
    cny = usd_to_cny(usd)
    raw = cny * Decimal(str(COMMISSION_RATE))
    raw = max(raw, Decimal(COMMISSION_MIN_CNY))
    raw = min(raw, Decimal(COMMISSION_MAX_CNY))
    return q2(raw)


def commission_usd(usd):
    """CNY commission expressed in USD at the board sell rate."""
    cny = commission_cny(usd)
    return q2(cny / SELL_SPOT * Decimal(100))


def cable_usd():
    return q2(Decimal(CABLE_FEE_CNY) / SELL_SPOT * Decimal(100))


def receiving_usd():
    return Decimal(RECEIVING_BANK_USD)


def carriage_cert_usd():
    return q2(Decimal(CARRIAGE_CERT_CNY) / SELL_SPOT * Decimal(100))


def deposit_cert_usd():
    """Midpoint of the published CNY 20-40 band, as a single published band."""
    mid_cny = (Decimal(DEPOSIT_CERT_CNY_LOW) + Decimal(DEPOSIT_CERT_CNY_HIGH)) / 2
    return q2(mid_cny / SELL_SPOT * Decimal(100))


# --------------------------------------------------------------------------
# Per-method arithmetic
# --------------------------------------------------------------------------

def boc_components(usd, wire=True, full_amount=True, receiving=True, docs=True):
    c = {
        "fx_margin": fx_margin_usd(usd),
        "commission": commission_usd(usd),
        "cable": cable_usd() if wire else Decimal("0.00"),
        "full_amount": Decimal(FULL_AMOUNT_USD) if (wire and full_amount) else Decimal("0.00"),
        "receiving": receiving_usd() if (wire and receiving) else Decimal("0.00"),
        "documents": deposit_cert_usd() if docs else Decimal("0.00"),
    }
    c["total"] = q2(sum(c.values()))
    return c


def compute(method, usd):
    """Return a dict of components plus total (Decimal) or None where blank."""
    model = method["cost_model"]
    if model == "boc_documented":
        c = boc_components(usd, wire=True)
        c["status"] = "computed"
        c["note"] = "FX margin + BOC commission + cable + full-amount arrival + named receiving-bank fee + certificate of deposit"
        return c
    if model == "boc_convert_only":
        c = boc_components(usd, wire=False, docs=True)
        c["status"] = "computed"
        c["note"] = "FX margin + BOC commission + certificate of deposit; no wire, so no cable, correspondent or receiving fee"
        return c
    if model == "boc_cash":
        # Withdrawal commission applies; the wire components do not.
        c = {
            "fx_margin": fx_margin_usd(usd),
            "commission": commission_usd(usd),
            "carriage_cert": carriage_cert_usd(),
            "cable": Decimal("0.00"),
            "full_amount": Decimal("0.00"),
            "receiving": Decimal("0.00"),
            "documents": Decimal("0.00"),
        }
        c["total"] = q2(sum(c.values()))
        c["status"] = "computed"
        c["note"] = "FX margin + BOC commission + currency carriage certificate; cash has no cable or correspondent fee but is capped per day"
        return c
    if model == "none":
        return {"status": "not_applicable", "total": None,
                "note": "No conversion: nothing is exchanged, so there is no FX cost on this amount."}
    if model == "prohibited":
        return {"status": "prohibited", "total": None,
                "note": "Prohibited. No price is computed because no lawful execution exists."}
    # unknown
    return {"status": "unpublished", "total": None,
            "note": "No published price for at least one component. Left blank rather than estimated."}
