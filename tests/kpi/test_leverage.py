"""
FinSight N100 – Day 9: Unit Tests for Leverage and Efficiency Ratios
====================================================================

At least 8 test cases covering leverage calculations, warnings, labels, and efficiency metrics.
"""

import sys
import os
import logging

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)

import pytest
from src.analytics.ratios import (
    calculate_debt_to_equity,
    check_high_leverage,
    calculate_interest_coverage,
    get_icr_label,
    check_interest_warning,
    calculate_net_debt,
    calculate_asset_turnover,
)


# ── Test 1: Debt-to-Equity and High Leverage ───────────────────────────────
class TestDebtToEquity:
    def test_debt_free_company(self):
        """Borrowings = 0 -> D/E = 0 (and not None)."""
        result = calculate_debt_to_equity(
            borrowings=0, equity_capital=100, reserves=400
        )
        assert result == 0.0

    def test_normal_calculation(self):
        """Borrowings = 1000, Equity = 500, Reserves = 1500 -> D/E = 0.5."""
        result = calculate_debt_to_equity(
            borrowings=1000, equity_capital=500, reserves=1500
        )
        assert result == 0.5

    def test_negative_or_zero_equity_returns_none(self, caplog):
        """Equity + Reserves <= 0 -> None and logs warning."""
        with caplog.at_level(logging.WARNING):
            result = calculate_debt_to_equity(
                borrowings=100, equity_capital=0, reserves=0
            )
        assert result is None
        assert "cannot compute Debt-to-Equity" in caplog.text

    def test_none_inputs(self):
        assert calculate_debt_to_equity(None, 100, 200) is None
        assert calculate_debt_to_equity(100, None, 200) is None
        assert calculate_debt_to_equity(100, 100, None) is None


# ── Test 2: High Leverage Flag ─────────────────────────────────────────────
class TestHighLeverageFlag:
    def test_high_leverage_warning(self):
        """D/E > 5 -> Flag = True."""
        assert check_high_leverage(de_ratio=5.1, broad_sector="Energy") is True
        assert check_high_leverage(de_ratio=4.9, broad_sector="Energy") is False

    def test_financial_company_exception(self):
        """No High Leverage warning for Financial sector even if D/E > 5."""
        assert check_high_leverage(de_ratio=10.0, broad_sector="Financials") is False

    def test_none_leverage(self):
        assert check_high_leverage(de_ratio=None, broad_sector="Energy") is False


# ── Test 3: Interest Coverage Ratio ────────────────────────────────────────
class TestInterestCoverage:
    def test_normal_calculation(self):
        """(Operating Profit = 500 + Other Income = 100) / Interest = 200 -> 3.0."""
        result = calculate_interest_coverage(
            operating_profit=500, other_income=100, interest=200
        )
        assert result == 3.0

    def test_interest_zero_returns_none(self):
        """Interest = 0 -> ICR = None."""
        result = calculate_interest_coverage(
            operating_profit=500, other_income=100, interest=0
        )
        assert result is None

    def test_none_inputs(self):
        assert calculate_interest_coverage(None, 100, 200) is None
        assert calculate_interest_coverage(500, None, 200) is None
        assert calculate_interest_coverage(500, 100, None) is None


# ── Test 4: Debt-Free Label ────────────────────────────────────────────────
class TestDebtFreeLabel:
    def test_debt_free_label_when_icr_is_none(self):
        """ICR = None -> Label = 'Debt Free'."""
        assert get_icr_label(icr=None) == "Debt Free"

    def test_no_label_when_icr_exists(self):
        """ICR is not None -> Label = None."""
        assert get_icr_label(icr=3.0) is None


# ── Test 5: Interest Coverage Warning ─────────────────────────────────────
class TestInterestWarning:
    def test_warning_triggered(self):
        """ICR < 1.5 -> Warning = True."""
        assert check_interest_warning(icr=1.2) is True

    def test_warning_not_triggered(self):
        """ICR >= 1.5 -> Warning = False."""
        assert check_interest_warning(icr=1.5) is False
        assert check_interest_warning(icr=3.0) is False

    def test_no_warning_if_icr_is_none(self):
        """ICR = None (debt-free) -> Warning = False."""
        assert check_interest_warning(icr=None) is False


# ── Test 6: Net Debt ───────────────────────────────────────────────────────
class TestNetDebt:
    def test_normal_calculation(self):
        """Borrowings = 1000, Investments = 300 -> Net Debt = 700."""
        result = calculate_net_debt(borrowings=1000, investments=300)
        assert result == 700.0

    def test_none_inputs(self):
        assert calculate_net_debt(None, 300) is None
        assert calculate_net_debt(1000, None) is None


# ── Test 7: Asset Turnover Ratio ───────────────────────────────────────────
class TestAssetTurnover:
    def test_normal_calculation(self):
        """Sales = 6000, Total Assets = 3000 -> Asset Turnover = 2.0."""
        result = calculate_asset_turnover(sales=6000, total_assets=3000)
        assert result == 2.0

    def test_assets_zero_returns_none(self, caplog):
        """Total Assets = 0 -> None."""
        with caplog.at_level(logging.WARNING):
            result = calculate_asset_turnover(sales=6000, total_assets=0)
        assert result is None
        assert "cannot compute Asset Turnover" in caplog.text

    def test_assets_negative_returns_none(self, caplog):
        """Total Assets <= 0 -> None."""
        with caplog.at_level(logging.WARNING):
            result = calculate_asset_turnover(sales=6000, total_assets=-100)
        assert result is None
        assert "cannot compute Asset Turnover" in caplog.text

    def test_none_inputs(self):
        assert calculate_asset_turnover(None, 3000) is None
        assert calculate_asset_turnover(6000, None) is None
