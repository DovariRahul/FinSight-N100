"""
FinSight N100 – Day 8: Unit Tests for Profitability Ratios
===========================================================

At least 8 test cases covering normal calculations and edge cases.
"""

import sys
import os
import logging

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)

import pytest
from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    derive_ebit,
)


# ── Test 1: Normal Net Profit Margin ──────────────────────────────────────
class TestNetProfitMargin:
    def test_normal_calculation(self):
        """NPM for Sales=1000, Net Profit=200 → 20.0%"""
        result = calculate_net_profit_margin(net_profit=200, sales=1000)
        assert result == 20.0

    def test_sales_zero_returns_none(self):
        """Sales = 0 → cannot divide → None"""
        result = calculate_net_profit_margin(net_profit=200, sales=0)
        assert result is None

    def test_none_inputs(self):
        """Any None input → None"""
        assert calculate_net_profit_margin(net_profit=None, sales=1000) is None
        assert calculate_net_profit_margin(net_profit=200, sales=None) is None

    def test_negative_profit(self):
        """Negative net profit yields a negative margin."""
        result = calculate_net_profit_margin(net_profit=-50, sales=500)
        assert result == -10.0


# ── Test 2: Operating Profit Margin (with cross-check) ───────────────────
class TestOperatingProfitMargin:
    def test_normal_calculation(self):
        """OPM for Sales=1000, Operating Profit=250 → 25.0%"""
        result = calculate_operating_profit_margin(
            operating_profit=250, sales=1000
        )
        assert result == 25.0

    def test_sales_zero_returns_none(self):
        result = calculate_operating_profit_margin(
            operating_profit=250, sales=0
        )
        assert result is None

    def test_opm_match_no_warning(self, caplog):
        """When dataset OPM matches (within 1 pp), no warning is logged."""
        with caplog.at_level(logging.WARNING):
            result = calculate_operating_profit_margin(
                operating_profit=250,
                sales=1000,
                dataset_opm=25.0,
            )
        assert result == 25.0
        assert "OPM mismatch" not in caplog.text

    def test_opm_mismatch_logs_warning(self, caplog):
        """When dataset OPM differs by >1 pp, a warning is logged."""
        with caplog.at_level(logging.WARNING):
            result = calculate_operating_profit_margin(
                operating_profit=220,
                sales=1000,
                dataset_opm=20.0,
            )
        # Calculated = 22.0%, dataset = 20.0%, diff = 2 pp
        assert result == 22.0
        assert "OPM mismatch" in caplog.text

    def test_opm_within_tolerance(self, caplog):
        """Difference of exactly 1 pp should NOT trigger warning."""
        with caplog.at_level(logging.WARNING):
            calculate_operating_profit_margin(
                operating_profit=210,
                sales=1000,
                dataset_opm=22.0,
            )
        assert "OPM mismatch" not in caplog.text


# ── Test 3: Return on Equity ─────────────────────────────────────────────
class TestROE:
    def test_normal_calculation(self):
        """ROE for Net Profit=500, Equity=500, Reserves=2000 → 20.0%"""
        result = calculate_roe(
            net_profit=500, equity_capital=500, reserves=2000
        )
        assert result == 20.0

    def test_negative_equity_returns_none(self):
        """Equity + Reserves <= 0 → None"""
        result = calculate_roe(
            net_profit=100, equity_capital=10, reserves=-20
        )
        assert result is None

    def test_zero_equity_returns_none(self):
        """Equity + Reserves == 0 → None"""
        result = calculate_roe(
            net_profit=100, equity_capital=0, reserves=0
        )
        assert result is None

    def test_none_input(self):
        assert calculate_roe(None, 100, 200) is None


# ── Test 4: Return on Capital Employed ────────────────────────────────────
class TestROCE:
    def test_normal_calculation(self):
        """ROCE for EBIT=800, Equity=500, Reserves=2500, Borrowings=2000 → 16.0%"""
        result = calculate_roce(
            ebit=800,
            equity_capital=500,
            reserves=2500,
            borrowings=2000,
        )
        assert result == 16.0

    def test_zero_capital_returns_none(self):
        result = calculate_roce(
            ebit=100,
            equity_capital=0,
            reserves=0,
            borrowings=0,
        )
        assert result is None

    def test_financial_sector_logged(self, caplog):
        """Financial-sector companies get an INFO log reminder."""
        with caplog.at_level(logging.INFO):
            result = calculate_roce(
                ebit=500,
                equity_capital=100,
                reserves=400,
                borrowings=5000,
                broad_sector="Financials",
            )
        assert result is not None
        assert "Financials-sector" in caplog.text

    def test_none_input(self):
        assert calculate_roce(None, 100, 200, 300) is None


# ── Test 5: Return on Assets ─────────────────────────────────────────────
class TestROA:
    def test_normal_calculation(self):
        """ROA for Net Profit=300, Total Assets=6000 → 5.0%"""
        result = calculate_roa(net_profit=300, total_assets=6000)
        assert result == 5.0

    def test_total_assets_zero_returns_none(self):
        result = calculate_roa(net_profit=300, total_assets=0)
        assert result is None

    def test_none_input(self):
        assert calculate_roa(None, 6000) is None
        assert calculate_roa(300, None) is None


# ── Test 6: EBIT derivation helper ───────────────────────────────────────
class TestDeriveEBIT:
    def test_normal(self):
        assert derive_ebit(operating_profit=250, other_income=50) == 300.0

    def test_none_input(self):
        assert derive_ebit(None, 50) is None
        assert derive_ebit(250, None) is None
