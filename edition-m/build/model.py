#!/usr/bin/env python3
"""Cost model for Edition M. Pure arithmetic on the inputs in data/inputs.json.

Every row is defined on the same basis: an amount of yuan worth USD A at the midpoint
of Bank of China's own two-way USD quote. "cost" is everything that stops that value
from arriving in the US account. A value of None means the component could not be
confirmed from an official source and is shown blank.
"""
from __future__ import annotations

import json
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
CENT = D("0.01")


def r2(x: D) -> D:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def ceil_int(x: D) -> int:
    return int(x.to_integral_value(rounding=ROUND_CEILING))


def floor_int(x: D) -> int:
    return int(x.to_integral_value(rounding=ROUND_FLOOR))


def clamp(x: D, lo: D, hi: D) -> D:
    return max(lo, min(hi, x))


def load_inputs() -> dict:
    return json.loads((DATA / "inputs.json").read_text(encoding="utf-8"))


class Model:
    def __init__(self, inp: dict | None = None):
        self.inp = inp or load_inputs()
        fx = self.inp["fx"]
        self.bid100 = D(str(fx["boc_spot_bid_per100"]))
        self.ask100 = D(str(fx["boc_spot_ask_per100"]))
        self.cash_ask100 = D(str(fx["boc_cash_ask_per100"]))
        self.mid100 = (self.bid100 + self.ask100) / 2
        self.mid = self.mid100 / 100            # yuan per USD at the midpoint
        self.ask = self.ask100 / 100            # yuan per USD the customer pays
        self.cash_ask = self.cash_ask100 / 100
        self.margin = (self.ask100 - self.mid100) / self.mid100
        self.cash_margin = (self.cash_ask100 - self.mid100) / self.mid100
        a = self.inp["amounts_usd"]
        self.amounts = list(range(a["start"], a["stop"] + 1, a["step"]))
        b = self.inp["boc"]
        self.boc_rate = D(str(b["commission_rate"]))
        self.boc_min = D(str(b["commission_min_cny"]))
        self.boc_max = D(str(b["commission_max_cny"]))
        self.boc_cable = D(str(b["cable_international_cny"]))
        self.boc_full = D(str(b["full_amount_usd"]))
        self.boc_full_ny = D(str(b["full_amount_usd_if_payee_bank_at_boc_new_york"]))
        self.permit_cny = D(str(b["carry_permit_cny"]))
        self.atm_fixed = D(str(b["atm_abroad_fixed_cny"]))
        self.atm_rate = D(str(b["atm_abroad_rate"]))
        self.atm_max = D(str(b["atm_abroad_max_cny"]))
        h = self.inp["hsbc_cn"]
        self.h_rate = D(str(h["commission_rate"]))
        self.h_min = D(str(h["commission_min_cny"]))
        self.h_max = D(str(h["commission_max_cny"]))
        self.h_cable = D(str(h["cable_cny"]))
        self.recv = D(str(self.inp["us_receiving"]["chase_incoming_wire_usd"]))
        w = self.inp["wise"]
        self.wise_cap = D(str(w["per_transfer_cap_cny"]))
        self.wise_quotes = {D(str(q["send_cny"])): D(str(q["fee_cny"])) for q in w["quotes_cny"]}
        c = self.inp["safe_caps"]
        self.card_year = D(str(c["card_cash_abroad_per_year_cny"]))
        self.card_day = D(str(c["card_cash_abroad_per_card_per_day_cny"]))
        self.cash_trip_usd = D(str(c["cash_carry_bank_permit_max_usd"]))
        self.rmb_trip_cny = D(str(c["rmb_cash_per_trip_cny"]))
        self.quota_usd = D("50000")
        self.fxy = {y: D(str(v)) for y, v in self.inp["irs_yearly_average_cny_per_usd"].items() if y != "src"}

    # ---- single-wire building blocks -------------------------------------------------
    def boc_fees_cny(self, usd: D) -> D:
        """Bank of China commission + cable for one wire of `usd`, in yuan."""
        comm = r2(clamp(self.boc_rate * usd * self.ask, self.boc_min, self.boc_max))
        return comm + self.boc_cable

    def boc_wire_cost(self, usd: D) -> dict:
        fx = usd * self.margin
        fees_cny = self.boc_fees_cny(usd)
        fees = fees_cny / self.mid
        return {"fx": fx, "fees_cny": fees_cny, "fees": fees, "full": self.boc_full, "recv": self.recv,
                "total": fx + fees + self.boc_full + self.recv}

    # ---- ladders ---------------------------------------------------------------------
    def ladder_boc(self) -> list[dict]:
        rows = []
        for a in self.amounts:
            A = D(a)
            c = self.boc_wire_cost(A)
            rows.append({"usd": a, "cny_to_pay": r2(A * self.ask), "fx": r2(c["fx"]), "fees_cny": c["fees_cny"],
                         "fees": r2(c["fees"]), "full": c["full"], "recv": c["recv"], "total": r2(c["total"]),
                         "pct": r2(c["total"] / A * 100), "arrives": r2(A - c["total"]), "transfers": 1,
                         "complete": True})
        return rows

    def ladder_quota(self) -> list[dict]:
        rows = []
        for a in self.amounts:
            A = D(a)
            n = ceil_int(A / self.quota_usd)
            total = D(0)
            fees_cny = D(0)
            left = A
            for _ in range(n):
                part = min(left, self.quota_usd)
                c = self.boc_wire_cost(part)
                total += c["total"]
                fees_cny += c["fees_cny"]
                left -= part
            rows.append({"usd": a, "total": r2(total), "pct": r2(total / A * 100), "arrives": r2(A - total),
                         "fees_cny": fees_cny, "transfers": n, "years": n, "complete": True})
        return rows

    def ladder_hsbc(self) -> list[dict]:
        rows = []
        for a in self.amounts:
            A = D(a)
            comm = r2(clamp(self.h_rate * A * self.ask, self.h_min, self.h_max))
            fees_cny = comm + self.h_cable
            fees = fees_cny / self.mid
            known = fees + self.recv
            rows.append({"usd": a, "fees_cny": fees_cny, "fees": r2(fees), "recv": self.recv, "known": r2(known),
                         "known_pct": r2(known / A * 100), "fx": None, "total": None, "pct": None,
                         "arrives": None, "transfers": 1, "complete": False})
        return rows

    def ladder_wise(self) -> list[dict]:
        unit = D(self.amounts[0]) * self.mid                      # yuan worth USD 10,000 at the midpoint
        sizes = sorted(self.wise_quotes)                          # 1x, 2x, 3x, 4x that unit
        assert [s for s in sizes] == [r2(unit * i).quantize(D(1)) for i in (1, 2, 3, 4)], "quotes must match the row unit"
        assert sizes[-1] <= self.wise_cap
        big = self.wise_quotes[sizes[-1]]
        rows = []
        for a in self.amounts:
            A = D(a)
            k = a // self.amounts[0]
            q, r = divmod(k, 4)
            fee_cny = q * big + (self.wise_quotes[sizes[r - 1]] if r else D(0))
            n = q + (1 if r else 0)
            fee = fee_cny / self.mid
            rows.append({"usd": a, "fee_cny": r2(fee_cny), "total": r2(fee), "pct": r2(fee / A * 100),
                         "arrives": r2(A - fee), "transfers": n, "fx": D(0), "complete": True})
        return rows

    def ladder_rmb(self) -> list[dict]:
        rows = []
        for a in self.amounts:
            A = D(a)
            cny = A * self.mid
            comm = r2(clamp(self.boc_rate * cny, self.boc_min, self.boc_max))
            fees_cny = comm + self.boc_cable
            known = fees_cny / self.mid
            rows.append({"usd": a, "cny": r2(cny), "fees_cny": fees_cny, "known": r2(known),
                         "known_pct": r2(known / A * 100), "total": None, "pct": None, "arrives": None,
                         "transfers": 1, "complete": False})
        return rows

    def ladder_cash_usd(self) -> list[dict]:
        rows = []
        for a in self.amounts:
            A = D(a)
            fx = A * self.cash_margin
            trips = ceil_int(A / self.cash_trip_usd)
            permit_later = trips * self.permit_cny / self.mid
            rows.append({"usd": a, "known": r2(fx), "known_pct": r2(fx / A * 100), "trips": trips,
                         "permit_now": D(0), "permit_from_2027": r2(permit_later), "total": None, "pct": None,
                         "arrives": None, "complete": False})
        return rows

    def ladder_cash_rmb(self) -> list[dict]:
        rows = []
        for a in self.amounts:
            cny = D(a) * self.mid
            rows.append({"usd": a, "cny": r2(cny), "trips": ceil_int(cny / self.rmb_trip_cny), "known": None,
                         "total": None, "pct": None, "arrives": None, "complete": False})
        return rows

    def ladder_atm(self) -> list[dict]:
        rows = []
        for a in self.amounts:
            A = D(a)
            cny = A * self.mid
            n_full = floor_int(cny / self.card_day)
            rem = cny - n_full * self.card_day
            fee_cny = n_full * min(self.atm_fixed + self.atm_rate * self.card_day, self.atm_max)
            if rem > 0:
                fee_cny += min(self.atm_fixed + self.atm_rate * rem, self.atm_max)
            known = fee_cny / self.mid
            rows.append({"usd": a, "cny": r2(cny), "withdrawals": n_full + (1 if rem > 0 else 0),
                         "fee_cny": r2(fee_cny), "known": r2(known), "known_pct": r2(known / A * 100),
                         "years": ceil_int(cny / self.card_year), "total": None, "pct": None, "arrives": None,
                         "complete": False})
        return rows

    def ladder_card(self) -> list[dict]:
        return [{"usd": a, "known": None, "total": None, "pct": None, "arrives": None, "complete": False}
                for a in self.amounts]

    def ladders(self) -> dict:
        return {"boc": self.ladder_boc(), "quota": self.ladder_quota(), "hsbc": self.ladder_hsbc(),
                "wise": self.ladder_wise(), "rmb": self.ladder_rmb(), "cash_usd": self.ladder_cash_usd(),
                "cash_rmb": self.ladder_cash_rmb(), "atm": self.ladder_atm(), "card": self.ladder_card()}

    # ---- US currency gain illustration -------------------------------------------------
    def gain_table(self) -> list[dict]:
        rows = []
        for a in self.amounts:
            A = D(a)
            cny = A * self.mid
            proceeds = cny / self.ask
            row = {"usd": a, "proceeds": r2(proceeds)}
            for y, rate in self.fxy.items():
                row[y] = r2(proceeds - cny / rate)
            rows.append(row)
        return rows


def to_jsonable(o):
    if isinstance(o, D):
        return float(o)
    if isinstance(o, dict):
        return {k: to_jsonable(v) for k, v in o.items()}
    if isinstance(o, list):
        return [to_jsonable(v) for v in o]
    return o
