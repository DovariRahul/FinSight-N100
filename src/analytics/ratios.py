"""
FinSight N100 – Day 8: Profitability Ratio Calculations
========================================================

Pure calculation functions for profitability ratios.
These operate on individual data points (not the database directly)
and will later be wired into the pipeline that populates `financial_ratios`.

Every function returns a rounded float (2 decimal places) or None
when the ratio cannot be meaningfully computed.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Financial-sector broad_sector values (used by ROCE special rule)
# ---------------------------------------------------------------------------
FINANCIAL_SECTORS = frozenset({"Financials"})


# ── Task 2: Net Profit Margin ──────────────────────────────────────────────
def calculate_net_profit_margin(
    net_profit: Optional[float],
    sales: Optional[float],
) -> Optional[float]:
    """
    Net Profit Margin = (Net Profit / Sales) × 100

    Returns None when sales is 0 or any input is None.
    """
    if net_profit is None or sales is None:
        return None
    if sales == 0:
        logger.warning("Sales is 0 — cannot compute Net Profit Margin.")
        return None
    return round((net_profit / sales) * 100, 2)


# ── Task 3: Operating Profit Margin ───────────────────────────────────────
def calculate_operating_profit_margin(
    operating_profit: Optional[float],
    sales: Optional[float],
    dataset_opm: Optional[float] = None,
) -> Optional[float]:
    """
    Operating Profit Margin = (Operating Profit / Sales) × 100

    If *dataset_opm* is provided, cross-checks the computed value against
    the dataset value and logs a warning when the difference exceeds 1 pp.

    Returns None when sales is 0 or any required input is None.
    """
    if operating_profit is None or sales is None:
        return None
    if sales == 0:
        logger.warning("Sales is 0 — cannot compute Operating Profit Margin.")
        return None

    calculated_opm = round((operating_profit / sales) * 100, 2)

    # Cross-check against the dataset value
    if dataset_opm is not None:
        diff = abs(calculated_opm - dataset_opm)
        if diff > 1:
            logger.warning(
                "OPM mismatch: dataset=%.2f%%, calculated=%.2f%%, diff=%.2f pp",
                dataset_opm,
                calculated_opm,
                diff,
            )

    return calculated_opm


# ── Task 4: Return on Equity ──────────────────────────────────────────────
def calculate_roe(
    net_profit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
) -> Optional[float]:
    """
    ROE = (Net Profit / (Equity Capital + Reserves)) × 100

    Returns None when (equity + reserves) <= 0 or any input is None.
    """
    if net_profit is None or equity_capital is None or reserves is None:
        return None

    shareholder_equity = equity_capital + reserves
    if shareholder_equity <= 0:
        logger.warning(
            "Equity + Reserves = %.2f (<=0) — cannot compute ROE.",
            shareholder_equity,
        )
        return None
    return round((net_profit / shareholder_equity) * 100, 2)


# ── Task 5: Return on Capital Employed ────────────────────────────────────
def calculate_roce(
    ebit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    borrowings: Optional[float],
    broad_sector: Optional[str] = None,
) -> Optional[float]:
    """
    ROCE = (EBIT / (Equity + Reserves + Borrowings)) × 100

    For companies in the **Financials** sector, high borrowings are
    structural.  The function still computes ROCE but attaches a flag
    in the log so downstream consumers can compare within-sector.

    Returns None when capital employed <= 0 or any required input is None.
    """
    if ebit is None or equity_capital is None or reserves is None or borrowings is None:
        return None

    capital_employed = equity_capital + reserves + borrowings
    if capital_employed <= 0:
        logger.warning(
            "Capital employed = %.2f (<=0) — cannot compute ROCE.",
            capital_employed,
        )
        return None

    roce = round((ebit / capital_employed) * 100, 2)

    if broad_sector and broad_sector in FINANCIAL_SECTORS:
        logger.info(
            "ROCE %.2f%% for a Financials-sector company — "
            "compare within sector only.",
            roce,
        )

    return roce


def derive_ebit(
    operating_profit: Optional[float],
    other_income: Optional[float],
) -> Optional[float]:
    """
    EBIT ≈ Operating Profit + Other Income

    A convenience helper because the P&L table does not store EBIT
    directly.  Returns None if either component is None.
    """
    if operating_profit is None or other_income is None:
        return None
    return round(operating_profit + other_income, 2)


# ── Task 6: Return on Assets ─────────────────────────────────────────────
def calculate_roa(
    net_profit: Optional[float],
    total_assets: Optional[float],
) -> Optional[float]:
    """
    ROA = (Net Profit / Total Assets) × 100

    Returns None when total_assets is 0 or any input is None.
    """
    if net_profit is None or total_assets is None:
        return None
    if total_assets == 0:
        logger.warning("Total Assets is 0 — cannot compute ROA.")
        return None
    return round((net_profit / total_assets) * 100, 2)


# ── Day 9: Leverage and Efficiency Ratio Calculations ─────────────────────────

def calculate_debt_to_equity(
    borrowings: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
) -> Optional[float]:
    """
    Debt-to-Equity = Borrowings / (Equity + Reserves)

    Shows how much debt a company has compared to shareholders' investment.
    Returns 0 when borrowings is 0.
    Returns None when (equity_capital + reserves) <= 0 or any input is None.
    """
    if borrowings is None or equity_capital is None or reserves is None:
        return None
    if borrowings == 0:
        equity_and_reserves = equity_capital + reserves
        if equity_and_reserves <= 0:
            logger.warning(
                "Equity + Reserves = %.2f (<=0) — cannot compute Debt-to-Equity.",
                equity_and_reserves,
            )
            return None
        return 0.0

    equity_and_reserves = equity_capital + reserves
    if equity_and_reserves <= 0:
        logger.warning(
            "Equity + Reserves = %.2f (<=0) — cannot compute Debt-to-Equity.",
            equity_and_reserves,
        )
        return None

    return round(borrowings / equity_and_reserves, 2)


def check_high_leverage(
    de_ratio: Optional[float],
    broad_sector: Optional[str] = None,
) -> bool:
    """
    High Leverage Warning Flag.
    Returns True if D/E > 5, unless the company belongs to the Financials sector.
    Otherwise returns False.
    """
    if de_ratio is None:
        return False
    if broad_sector and broad_sector in FINANCIAL_SECTORS:
        return False
    return de_ratio > 5


def calculate_interest_coverage(
    operating_profit: Optional[float],
    other_income: Optional[float],
    interest: Optional[float],
) -> Optional[float]:
    """
    Interest Coverage = (Operating Profit + Other Income) / Interest

    Measures whether the company earns enough profit to pay its interest expenses.
    Returns None if interest is 0 or any input is None.
    """
    if operating_profit is None or other_income is None or interest is None:
        return None
    if interest == 0:
        return None
    return round((operating_profit + other_income) / interest, 2)


def get_icr_label(
    icr: Optional[float],
) -> Optional[str]:
    """
    Returns 'Debt Free' if ICR is None.
    Otherwise returns None.
    """
    if icr is None:
        return "Debt Free"
    return None


def check_interest_warning(
    icr: Optional[float],
) -> bool:
    """
    Returns True if ICR < 1.5 (and not None).
    Otherwise returns False.
    """
    if icr is None:
        return False
    return icr < 1.5


def calculate_net_debt(
    borrowings: Optional[float],
    investments: Optional[float],
) -> Optional[float]:
    """
    Net Debt = Borrowings - Investments

    Measures the company's actual debt after considering its liquid investments.
    """
    if borrowings is None or investments is None:
        return None
    return round(borrowings - investments, 2)


def calculate_asset_turnover(
    sales: Optional[float],
    total_assets: Optional[float],
) -> Optional[float]:
    """
    Asset Turnover = Sales / Total Assets

    Measures how efficiently a company uses its assets to generate revenue.
    Returns None when total_assets <= 0 or any input is None.
    """
    if sales is None or total_assets is None:
        return None
    if total_assets <= 0:
        logger.warning(
            "Total Assets is %.2f (<=0) — cannot compute Asset Turnover.",
            total_assets,
        )
        return None
    return round(sales / total_assets, 2)

