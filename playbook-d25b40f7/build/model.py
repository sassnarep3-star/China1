# -*- coding: utf-8 -*-
"""Cost model of the Playbook. Decimal arithmetic on published inputs only.

A value of None means "no published input": the cell is rendered blank and the
row names the flag that explains why. Nothing is estimated or interpolated.
"""
from decimal import Decimal as D, ROUND_CEILING
import content as C

P = {k: v[0] for k, v in C.PARAMS.items()}
BID = P["boc_bid"] / 100          # CNY per USD, bank buys USD
ASK = P["boc_ask"] / 100          # CNY per USD, bank sells USD
MID = (BID + ASK) / 2
ONE_WAY = (ASK - MID) / MID       # cost of buying USD, relative to the midpoint
WIDTH = (ASK - BID) / MID         # full bid-ask width
AMOUNTS = [D(10000) * i for i in range(1, 41)]
BENCH = [D(10000), D(50000), D(100000), D(200000), D(400000)]
WISE = {q[0]: (q[1], q[2]) for q in C.WISE_QUOTES}


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def ceil(x):
    return int(x.to_integral_value(rounding=ROUND_CEILING))


def boc_comm_cny(a):
    return clamp(P["boc_comm_rate"] * a * MID, P["boc_comm_min_cny"], P["boc_comm_max_cny"])


def hsbc_comm_cny(a):
    return clamp(P["hsbc_comm_rate"] * a * MID, P["hsbc_comm_min_cny"], P["hsbc_comm_max_cny"])


def boc_wire(a, fx=True, full=True):
    """One Bank of China wire of a USD. All components in USD."""
    return {"fx": a * ONE_WAY if fx else D(0),
            "fees": (boc_comm_cny(a) + P["boc_cable_cny"]) / MID,
            "addon": P["boc_full_arrival_usd"] if full else None,
            "recv": P["chase_incoming_usd"]}


def split(a, cap):
    """a split into chunks of at most cap, largest first."""
    out = []
    while a > 0:
        c = min(a, cap)
        out.append(c)
        a -= c
    return out


def row(model, a):
    """Cost components for moving a USD by the given model."""
    r = {"amount": a, "cny": a * ASK, "fx": None, "fees": None, "addon": None, "recv": None,
         "tax": None, "units": "", "flags": [], "na": []}
    if model in ("boc_full", "boc_property"):
        r.update(boc_wire(a))
        r["units"] = "1 wire"
    elif model == "boc_sha":
        r.update(boc_wire(a, full=False))
        r["flags"] = ["F01"]
        r["units"] = "1 wire"
    elif model == "boc_wire_only":
        r.update(boc_wire(a, fx=False))
        r["cny"] = None
        r["na"] = ["cny"]
        r["units"] = "1 wire"
    elif model == "boc_quota":
        parts = split(a, P["quota_usd"])
        ws = [boc_wire(x) for x in parts]
        for k in ("fx", "fees", "addon", "recv"):
            r[k] = sum((w[k] for w in ws), D(0))
        n = len(parts)
        r["units"] = "%d year%s, %d wire%s" % (n, "" if n == 1 else "s", n, "" if n == 1 else "s")
    elif model == "hsbc_premier":
        r["fees"] = (hsbc_comm_cny(a) + P["hsbc_cable_cny"]) / MID
        r["addon"] = P["hsbc_payexact_cny"] / MID
        r["recv"] = P["chase_incoming_usd"]
        r["cny"] = None
        r["flags"] = ["F02"]
        r["units"] = "1 wire"
    elif model == "hsbc_pb":
        r["fees"] = D(0)
        r["recv"] = P["chase_incoming_usd"]
        r["cny"] = None
        r["flags"] = ["F02", "F01"]
        r["units"] = "1 wire"
    elif model == "wise":
        sent = a * MID
        r["cny"] = None
        key = next((k for k in WISE if abs(k - sent) <= 1), None)
        n = ceil(sent / P["wise_cap_cny"])
        r["units"] = "1 transfer" if n == 1 else "%d transfers (CNY 300,000 limit each)" % n
        r["flags"] = ["F04"]
        if key is not None:
            r["fx"] = D(0)                       # provider states mid-market rate
            r["fees"] = WISE[key][0] / MID
            r["addon"] = D(0)
            r["wise_src"] = WISE[key][1]
            r["wise_cny"] = key
    elif model == "boc_dividend":
        r["cny"] = None
        r["tax"] = a * P["div_rate"]
        r["tax_treaty"] = a * P["treaty_div_cap"]
        r["flags"] = ["F26"]
        r["units"] = "gross dividend"
    elif model == "cash":
        n = ceil(a / P["cash_permit_usd"])
        r["fx"] = a * ONE_WAY
        r["fees"] = D(0)                         # carrying permit: CNY 10, waived to 2026-12-31
        r["addon"] = D(0)
        r["flags"] = ["F27"]                     # travel and any US cash-deposit charge: no published figure
        r["units"] = "%d trip%s with permit" % (n, "" if n == 1 else "s")
    elif model == "atm":
        total = a * MID
        parts = split(total, P["card_day_cny"])
        fee = sum((min(P["atm_max_cny"], P["atm_fixed_cny"] + P["atm_rate"] * x) for x in parts), D(0))
        yrs = ceil(total / P["card_year_cny"])
        r["cny"] = None
        r["fees"] = fee / MID
        r["flags"] = ["F05"]
        r["units"] = "%d withdrawal%s, %d year%s" % (len(parts), "" if len(parts) == 1 else "s", yrs, "" if yrs == 1 else "s")
    elif model == "small_recon":
        n = ceil(a / P["recon_day_usd"])
        r["fx"] = a * ONE_WAY
        r["fees"] = D(0)                         # no exchange fee at Bank of China branches
        r["addon"] = D(0)
        r["flags"] = ["F27"]
        r["units"] = "%d days" % n
    else:
        raise KeyError(model)
    if model == "boc_property":
        r["tax_low"] = a * P["deemed_low"]
        r["tax_high"] = a * P["deemed_high"]
    parts = [r[k] for k in ("fx", "fees", "addon", "recv")]
    known = [x for x in parts if x is not None]
    r["known"] = sum(known, D(0)) if known else None
    r["total"] = sum(parts, D(0)) if len(known) == 4 else None
    r["pct"] = (r["total"] / a) if r["total"] is not None else None
    if model == "boc_dividend":
        r["known"] = None
    return r


def ladder(model):
    return [row(model, a) for a in AMOUNTS]


def many_wires(a, n):
    """Total cost of sending a USD in n equal Bank of China wires."""
    w = boc_wire(a / n)
    return (w["fx"] + w["fees"] + w["addon"] + w["recv"]) * n


COMM_CAP_AT = P["boc_comm_max_cny"] / (P["boc_comm_rate"] * MID)   # USD amount where commission reaches its maximum
FIXED_AT_CAP = (P["boc_comm_max_cny"] + P["boc_cable_cny"]) / MID + P["boc_full_arrival_usd"] + P["chase_incoming_usd"]
