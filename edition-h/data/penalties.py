# -*- coding: utf-8 -*-
"""Edition H — decomposition of "the conversion penalty".

The user's premise is that converting CNY to USD triggers "a considerable amount
of taxes". Checked line by line against primary law, that premise splits into
FOUR different things, only one of which is a tax and only one of which is a
conversion charge:

  LAYER 1  Friction        FX margin, commission, cable, correspondent,
                           receiving bank, documents. Small, published,
                           unavoidable, and measured here.
  LAYER 2  Underlying tax  PRC IIT on the INCOME behind the money (salary,
                           property gain, dividends). Legally due whether or
                           not you ever move it.
  LAYER 3  Conduct penalty PRC sanction for using a prohibited channel:
                           20% to 100% of the amount.
  LAYER 4  US reporting    FBAR / 8938 / 3520 failures: 20% to 50% of the
                           balance, plus failure-to-file additions.

Only Layer 1 is a cost of converting. Layers 2-4 are costs of the money's
history and of non-compliance.
"""

# --------------------------------------------------------------------------
# LAYER 1 — friction, per amount, computed by the engine in costs.py
# --------------------------------------------------------------------------
LAYER1_NOTE = (
    "Published components only. The FX margin is the one-way bid/ask measured "
    "from the BOC board on 2026-11-09; the commission, cable, full-amount, "
    "receiving and document figures are the banks' own published prices."
)

# --------------------------------------------------------------------------
# LAYER 2 — the underlying PRC income tax. Rates are statutory; the BASE is
# personal and unknown, so no dollar figure is computed.
# --------------------------------------------------------------------------
LAYER2 = [
    dict(id="TAX-CN-1", item="Is converting CNY to USD itself subject to PRC IIT?",
         rate="0%", base="not applicable",
         finding="No. PRC IIT is imposed on nine enumerated categories of income (CN-18). A currency exchange of your own after-tax principal is not one of them, so there is nothing to tax on the exchange itself.",
         status="verified", sources=["CN-18"]),
    dict(id="TAX-CN-2", item="PRC IIT on a transfer of assets (e.g. a property gain)",
         rate="20% flat", base="the gain, not the price",
         finding="Where the money in the account came from disposing of an asset, the 20% flat rate applies to the gain. It is charged whether or not you remit, so remitting does not create it — it only requires you to prove it was paid.",
         status="verified", sources=["CN-19"]),
    dict(id="TAX-CN-3", item="PRC IIT on salary and wages",
         rate="3% to 45% progressive", base="taxable salary after the standard deduction",
         finding="Salary is the one category where a PRC tax record is routinely generated, which is exactly why the salary route (A06) is the easiest to document.",
         status="verified", sources=["CN-18"]),
    dict(id="TAX-CN-4", item="PRC tax on the amount actually being transferred",
         rate="", base="",
         finding="No provision retrieved imposes tax on the transfer of after-tax principal. This row is deliberately blank rather than filled with a rate.",
         status="blank_unverified", sources=["CN-18"]),
]

# --------------------------------------------------------------------------
# LAYER 3 — PRC conduct penalties
# --------------------------------------------------------------------------
LAYER3 = [
    dict(id="PEN-1", conduct="Evading FX control (逃汇): moving domestic FX or capital abroad in breach of the rules",
         cn="逃汇", min_pct=0, max_pct=30, escalator="30% to 100% where the circumstances are serious",
         other="Repatriation order; confiscation of illegal gains; criminal referral where the threshold is met",
         sources=["CN-04"]),
    dict(id="PEN-2", conduct="Private, disguised or brokered FX dealing (地下钱庄, mirror trade)",
         cn="私自买卖外汇", min_pct=0, max_pct=30, escalator="30% to 100% where serious",
         other="Warning; confiscation of illegal gains; criminal referral",
         sources=["CN-05"]),
    dict(id="PEN-3", conduct="Breaching the currency-carriage rules at the border",
         cn="违反规定携带外汇出入境", min_pct=0, max_pct=20, escalator="none published",
         other="Warning; Customs penalties where the law so provides",
         sources=["CN-06"]),
    dict(id="PEN-4", conduct="Splitting to evade quota or authenticity supervision (watchlist)",
         cn="分拆 / 关注名单", min_pct=0, max_pct=0, escalator="not a fine: enhanced review",
         other="Watchlist for the year of listing plus two more; every subsequent FX transaction pushed to the counter with strict documentary review; applies to the person who LENDS a quota as well as the borrower",
         sources=["CN-03", "CN-11"]),
    dict(id="PEN-5", conduct="Fiat-to-virtual-currency conversion and related business activity",
         cn="虚拟货币", min_pct=0, max_pct=0, escalator="classified as illegal financial activity",
         other="Strictly prohibited and to be suppressed; criminal liability where the activity constitutes a crime. The FX-law fine ranges in PEN-1/PEN-2 apply to the FX-control breach that funds it.",
         sources=["CN-20"]),
]

# --------------------------------------------------------------------------
# LAYER 4 — US tax and reporting. Reporting obligations first, then penalties.
# --------------------------------------------------------------------------
REPORTING = [
    dict(id="REP-1", form="FinCEN Form 114 (FBAR)",
         who="A US person with a financial interest in, or signature authority over, foreign accounts whose aggregate value exceeded USD 10,000 at any time in the calendar year",
         threshold="USD 10,000 aggregate, at any point in the year",
         when="15 April, automatic extension to 15 October",
         applies_here="YES. A mainland bank account above USD 10,000 at any point triggers it, whether or not the money moves and whether or not it earns interest.",
         sources=["US-04"]),
    dict(id="REP-2", form="Form 8938 (specified foreign financial assets)",
         who="A specified individual (a US citizen is one) holding specified foreign financial assets above the applicable threshold",
         threshold="Living in the US: more than USD 50,000 on the last day, or more than USD 75,000 at any time. Living outside the US: more than USD 200,000 on the last day, or more than USD 300,000 at any time.",
         when="With the annual return, on its due date including extensions",
         applies_here="YES where the threshold is met. It does NOT replace the FBAR, and the FBAR does not replace it.",
         sources=["US-08"]),
    dict(id="REP-3", form="Form 3520 Part IV (gifts and bequests from a foreign person)",
         who="A US person who received a gift or bequest from a foreign person above the reporting threshold",
         threshold="More than USD 100,000 in the year from a non-resident alien or foreign estate",
         when="15 April, generally, with limited extension",
         applies_here="ONLY for a genuine third-party gift or a bequest. A transfer of your OWN money out of your own account is not a gift, and treating it as one is a different error.",
         sources=["US-05"]),
    dict(id="REP-4", form="1% remittance transfer excise tax (Form 720)",
         who="Senders who provide cash, a money order, a cashier's cheque or a similar physical instrument to a remittance transfer provider for a transfer from the United States to a recipient abroad",
         threshold="1% of the remittance",
         when="Collected by the provider; quarterly return",
         applies_here="NO for this scenario. The tax runs from the United States outward. A China-to-United-States transfer is the opposite direction and is outside the described scope. Recorded here because it is widely misapplied to this question.",
         sources=["US-06"]),
]

LAYER4 = [
    dict(id="PEN-6", item="FBAR non-willful violation",
         amount_label="statutory maximum", amount=16536,
         basis="Per violation, inflation-adjusted to USD 16,536 for penalties assessed on or after 17 January 2025. A reasonable-cause exception exists where the transaction or balance was properly reported.",
         status="verified", sources=["US-02"]),
    dict(id="PEN-7", item="FBAR willful violation",
         amount_label="greater of", amount=165353, balance_based=True,
         basis="The greater of USD 165,353 (inflation-adjusted) OR 50% of the account balance at the time of the violation. At USD 400,000 that second limb is USD 200,000.",
         status="verified", sources=["US-09", "US-03"]),
    dict(id="PEN-8", item="Failure to file a US return",
         amount_label="% of tax due", pct=25,
         basis="5% of the tax per month, capped at 25%. Failure to pay adds 0.5% per month, capped at 25%. Where the failure to file is fraudulent the same paragraph is applied with 15% per month and a 75% cap.",
         status="verified", sources=["US-10"]),
    dict(id="PEN-9", item="Accuracy-related underpayment",
         amount_label="% of underpayment", pct=20,
         basis="20% of the portion of the underpayment attributable to negligence, disregard of rules, a substantial understatement, or an undisclosed foreign financial asset understatement.",
         status="verified", sources=["US-11"]),
    dict(id="PEN-10", item="Fraud",
         amount_label="% of underpayment", pct=75,
         basis="75% of the portion of the underpayment attributable to fraud, added to the tax itself.",
         status="verified", sources=["US-12"]),
    dict(id="PEN-11", item="PRC IIT on the underlying income or gain",
         amount_label="", amount=None,
         basis="Depends on the category of income and on the cost basis, neither of which is known. Left blank.",
         status="blank_unverified", sources=["CN-19"]),
]

# --------------------------------------------------------------------------
# The honest answer to "least tax penalties"
# --------------------------------------------------------------------------
STRATEGY = [
    dict(rank=1,
         title="Use the documented route that matches the money's real source",
         why="It is the only class of route where the cost is a published 0.21%-0.9% of the amount. Every prohibited route converts that into a 20%-100% statutory sanction.",
         penalty_exposure="Layer 1 only, plus the underlying PRC tax that is already due",
         sources=["CN-09", "CN-14", "CN-04"]),
    dict(rank=2,
         title="Settle the PRC tax on the income BEFORE applying",
         why="The tax certificate is a required document on the capital-account routes and is the evidence the bank reviews on the current-account route. Paying what is due is not an extra cost of moving money — it is the condition for being allowed to move it, and it stops the 20% from becoming 20% plus a 30%-100% fine.",
         penalty_exposure="Layer 2 only, which is a rate on the gain or income, never on the principal",
         sources=["CN-15", "CN-19"]),
    dict(rank=3,
         title="Fix US reporting before moving anything",
         why="This is where the largest single number in the analysis sits. A willful FBAR penalty is the greater of USD 165,353 or 50% of the balance — USD 200,000 at a USD 400,000 balance — and it is triggered by not filing, not by transferring.",
         penalty_exposure="Layer 4: 20%-50% of the balance plus 25%-75% of the tax",
         sources=["US-09", "US-10", "US-11", "US-12"]),
    dict(rank=4,
         title="Do not use splitting, underground dealing or crypto",
         why="These are the routes that generate the 'considerable penalty' the premise describes. They are not cheaper: they replace a sub-1% fee with a 20%-100% statutory range, and they leave the US reporting obligation intact.",
         penalty_exposure="Layers 3 and 4 together",
         sources=["CN-04", "CN-05", "CN-20"]),
]
