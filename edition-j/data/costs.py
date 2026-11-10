"""Edition J cost engine.

Two things are computed and nothing else is invented:

  FX cost  - the gap between the BOC published bid and ask, expressed two ways:
             the plain bid/ask spread and the spread measured against the
             PBOC-authorised central parity. Both come from numbers that are in
             market.py; neither is a quote for a customer.

  Fees     - Bank of China's own published tariff, evaluated at the CNY amount
             needed to deliver the USD target.

Everything else - receiving-bank fees, intermediary charges, taxes, notarisation
and travel - stays None. None renders as a blank cell on every page and is
counted by verify.py, which fails if a blank is ever rendered as a number.
"""

from data import market

TARGETS = list(range(10_000, 400_001, 10_000))


def boc_rate_buy() -> float:
    """CNY per USD the bank pays you (you sell USD) - 现汇买入价."""
    return market.BOC_BOARD["cash_buy"] / market.BOC_BOARD["unit_per"]


def boc_rate_sell() -> float:
    """CNY per USD the bank charges you (you buy USD) - 现汇卖出价."""
    return market.BOC_BOARD["cash_sell"] / market.BOC_BOARD["unit_per"]


def parity() -> float:
    return market.PARITY["usd_cny"]


def spread_pct_of_bid() -> float:
    """Plain bid/ask spread relative to the bid."""
    b, a = boc_rate_buy(), boc_rate_sell()
    return (a - b) / b


def mid_rate() -> float:
    """The bank's own mid between its published bid and ask."""
    return (boc_rate_buy() + boc_rate_sell()) / 2.0


def spread_pct_of_bid() -> float:
    """Full bid/ask spread relative to the bid - the round-trip cost."""
    b, a = boc_rate_buy(), boc_rate_sell()
    return (a - b) / b


def one_way_cost_pct() -> float:
    """The defensible one-way customer cost: the half-spread.

    Buying USD at the ask instead of the bank's own mid costs (ask-mid)/mid.
    This is the figure used in every ladder row, because it is the only measure
    that does not compare across two different timestamps.
    """
    return (boc_rate_sell() - mid_rate()) / mid_rate()


def round_trip_pct() -> float:
    """What you lose if you convert CNY to USD and back - the '0.42%' figure."""
    return spread_pct_of_bid()


def parity_gap_pct() -> float:
    """Ask vs the PBOC central parity, expressed as a signed percentage.

    Shown ONLY to demonstrate why it must not be used as a cost measure. The
    parity is fixed at 09:15 on the previous day and the board is a day later,
    so the gap mixes a real spread with a day of market movement. On the
    retrieved pair it is NEGATIVE, which would report a negative cost.
    """
    return (boc_rate_sell() - parity()) / parity()


def cny_needed(usd: int) -> float:
    """CNY required to deliver `usd` at the published selling rate."""
    return usd * boc_rate_sell()


def boc_tt_fee_cny(amount_cny: float) -> dict:
    """BOC published cross-border TT tariff (non-HK/Macau/Taiwan corridor)."""
    t = market.BOC_TARIFF
    commission = amount_cny * t["tt_per_mille"]
    commission = max(t["tt_min_cny"], min(commission, t["tt_max_cny"]))
    cable = t["cable_cny"]["other"]
    return {
        "commission_cny": round(commission, 2),
        "cable_cny": cable,
        "total_cny": round(commission + cable, 2),
    }


def boc_domestic_fee_cny(amount_cny: float) -> float:
    """BOC domestic interbank transfer tier, for the onshore-leg comparison."""
    t = market.BOC_TARIFF
    for upper, fee in t["domestic_tiers_cny"]:
        if amount_cny <= upper:
            return fee
    return round(min(amount_cny * t["domestic_above_pct"], t["domestic_above_cap_cny"]), 2)


def boc_intra_fx_fee_cny(amount_cny: float) -> float:
    t = market.BOC_TARIFF
    return round(min(amount_cny * t["intra_fx_per_mille"], t["intra_fx_cap_cny"]), 2)


def fx_cost_usd(usd: int, basis: str = "half") -> float:
    """USD given up to the FX spread at this target size."""
    pct = one_way_cost_pct() if basis == "half" else spread_pct_of_bid()
    return usd * pct


def row_boc_tt(usd: int, tax_rate=None):
    """Published sender tariff plus FX cost at a USD target. Taxes stay None."""
    cny = cny_needed(usd)
    fee = boc_tt_fee_cny(cny)
    fee_usd = fee["total_cny"] / boc_rate_sell()
    fx_usd = fx_cost_usd(usd, "half")
    tax_usd = None
    if tax_rate is not None:
        # Only used for income that is itself taxed at a flat published rate.
        tax_usd = round(usd * tax_rate / (1 - tax_rate), 2)
    return {
        "target_usd": usd,
        "cny_needed": round(cny, 2),
        "fx_cost_usd": round(fx_usd, 2),
        "sender_fee_cny": fee["total_cny"],
        "sender_fee_usd": round(fee_usd, 2),
        "tax_usd": tax_usd,
        "receiver_fee_usd": None,
        "intermediary_usd": None,
        "all_in_usd": None,
    }


def row_limit_only(usd: int):
    """Routes whose price is not published as a schedule: numbers stay blank."""
    return {
        "target_usd": usd,
        "cny_needed": round(cny_needed(usd), 2),
        "fx_cost_usd": None,
        "sender_fee_cny": None,
        "sender_fee_usd": None,
        "tax_usd": None,
        "receiver_fee_usd": None,
        "intermediary_usd": None,
        "all_in_usd": None,
    }


def ladder_for(route) -> list:
    est = route.get("estimate", {})
    mode = est.get("mode")
    if mode == "boc_tt":
        return [row_boc_tt(t, est.get("tax_rate")) for t in TARGETS]
    if mode == "limit_only":
        return [row_limit_only(t) for t in TARGETS]
    return []


# ---------------- compliance penalty arithmetic ----------------

def cn_penalty_exposure(usd: int) -> dict:
    """Statutory maximum exposure under the FX Regulations, converted to USD."""
    from data import market as m
    p = m.CN_PENALTIES
    lo = usd * p["evasion_low_pct"]
    return {
        "evasion_max_ordinary_usd": round(lo, 2),
        "evasion_max_serious_usd": round(usd * p["evasion_high_pct_range"][1], 2),
        "illegal_purchase_max_ordinary_usd": round(usd * p["illegal_purchase_low_pct"], 2),
        "illegal_purchase_max_serious_usd": round(usd * p["illegal_purchase_high_pct_range"][1], 2),
        "border_cash_max_usd": round(usd * p["border_cash_pct"], 2),
        "private_dealing_max_usd": round(usd * p["private_dealing_pct"], 2),
    }


def us_penalty_exposure(balance_usd: int) -> dict:
    p = market.US_PENALTIES
    return {
        "fbar_nonwillful_usd": p["fbar_nonwillful_max_usd"],
        "fbar_willful_50pct_usd": round(balance_usd * p["fbar_willful_pct_of_balance"], 2),
        "fbar_willful_max_usd": max(p["fbar_willful_max_usd"],
                                    round(balance_usd * p["fbar_willful_pct_of_balance"], 2)),
        "form8938_max_usd": p["form8938_irs_summary_max_usd"],
    }
