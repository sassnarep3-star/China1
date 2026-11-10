"""Edition J market inputs.

Only two numbers are carried into the cost model, and both are transcribed from
pages fetched in this session:

  * the PBOC-authorised USD/CNY central parity (CFETS-FIX), and
  * Bank of China's published USD board (BOC-BOARD).

Both pages state their own timestamp. Every derived figure in the site is
recomputed from this file at build time and re-derived independently by
build/verify.py, so a typo here fails the build instead of reaching the reader.
"""

# --- CFETS / 中国货币网 central parity, page state at retrieval ---
PARITY = {
    "usd_cny": 6.7188,
    "quote_time": "2026-11-09 09:15",
    "monthly_avg_oct_2026": 6.7223,
    "source": "CFETS-FIX",
}

# --- Bank of China board, USD row, published 2026/11/10 07:32:39 ---
# Board unit is CNY per 100 units of foreign currency.
BOC_BOARD = {
    "unit_per": 100.0,
    "cash_buy": 666.22,
    "cash_sell": 669.03,
    "conversion_mid": 671.88,
    "published": "2026/11/10 07:32:39",
    "source": "BOC-BOARD",
}

# --- Bank of China published tariff (BOC-TARIFF) ---
BOC_TARIFF = {
    "tt_per_mille": 0.001,          # 每笔汇款金额的1‰
    "tt_min_cny": 50.0,
    "tt_max_cny": 260.0,
    "cable_cny": {"hongkong_macau_taiwan": 80.0, "other": 150.0},
    "domestic_tiers_cny": [(2000, 2.0), (5000, 5.0), (10000, 10.0), (50000, 15.0)],
    "domestic_above_pct": 0.0003,
    "domestic_above_cap_cny": 50.0,
    "intra_fx_per_mille": 0.001,
    "intra_fx_cap_cny": 200.0,
    "source": "BOC-TARIFF",
}

# --- Wise eligibility and per-transfer caps (WISE-CNY) ---
WISE_TERMS = {
    "bank_app_cap_cny": 300000,
    "alipay_cap_cny": 50000,
    "fee_basis": "quote-only, no published schedule",
    "source": "WISE-CNY",
}

# --- Regulated thresholds that bound the size of individual steps ---
LIMITS = {
    "facilitation_quota_usd_per_year": 50000,   # CN-GUIDE2020 Art. 54 (结汇 and 境内个人购汇)
    "service_trade_doc_threshold_usd": 50000,   # CN-GUIDE2020 Art. 49 / Art. 64
    "cash_withdraw_per_day_usd": 10000,         # CN-GUIDE2020 Art. 86
    "cash_inbound_declare_usd": 5000,           # CN-GUIDE2020 Art. 89
    "cash_outbound_permit_from_usd": 5000,      # CN-GUIDE2020 Art. 89
    "cash_outbound_permit_to_usd": 10000,
    "card_cash_year_cny": 100000,               # CN-CARDS2017
    "card_cash_day_cny": 10000,                 # CN-CARDS2017
    "payment_institution_cap_usd": 50000,       # CN-GUIDE2020 Art. 132
    "postal_private_parcel_cny": 1000,          # China Post public guidance (flagged, see FLAGS)
    "us_currency_report_usd": 10000,            # US-1010340
    "us_fbar_usd": 10000,                       # US-FBAR
    "us_8938_single_us_usd": 50000,             # US-8938
    "us_3520_gift_usd": 100000,                 # US-3520
}

# --- US civil penalty maxima, as published on 2026-11-10 ---
US_PENALTIES = {
    "fbar_nonwillful_max_usd": 16536,       # US-1010821, assessments on/after 2025-01-17
    "fbar_willful_max_usd": 165353,         # US-1010821
    "fbar_willful_pct_of_balance": 0.50,    # US-5321(a)(5)(C)(i)(II)
    "form8938_base_usd": 10000,             # US-6038D(d)(1)
    "form8938_per_30d_usd": 10000,          # US-6038D(d)(2)
    "form8938_period_cap_usd": 50000,       # US-6038D(d)(2)
    "form8938_irs_summary_max_usd": 60000,  # US-8938 comparison table
    "fbar_ignore_max_usd": 10000,           # US-5321(a)(5)(B)(i) statutory base
}

# --- China statutory penalty percentages (CN-FXREG Arts. 39-45) ---
CN_PENALTIES = {
    "evasion_low_pct": 0.30,        # 逃汇, ordinary case: up to 30%
    "evasion_high_pct_range": (0.30, 1.00),   # 逃汇, serious: 30% up to 100%
    "illegal_purchase_low_pct": 0.30,         # 非法套汇
    "illegal_purchase_high_pct_range": (0.30, 1.00),
    "border_cash_pct": 0.20,        # Art. 42
    "private_dealing_pct": 0.30,    # Art. 45
    "source": "CN-FXREG",
}
