import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from src.etl.normaliser import normalize_ticker


def test_normalize_ticker_basic():
    assert normalize_ticker("tcs") == "TCS"

def test_normalize_ticker_whitespace():
    assert normalize_ticker(" TCS ") == "TCS"

def test_normalize_ticker_mixed_case():
    assert normalize_ticker("Tcs") == "TCS"

def test_normalize_ticker_uppercase():
    assert normalize_ticker("INFY") == "INFY"

def test_normalize_ticker_leading_spaces():
    assert normalize_ticker("  reliance") == "RELIANCE"

def test_normalize_ticker_trailing_spaces():
    assert normalize_ticker("wipro  ") == "WIPRO"

def test_normalize_ticker_none():
    assert normalize_ticker(None) == ""

def test_normalize_ticker_numeric():
    assert normalize_ticker(123) == "123"

def test_normalize_ticker_numeric_spaces():
    assert normalize_ticker(" 456 ") == "456"

def test_normalize_ticker_special_chars():
    assert normalize_ticker("tcs-nse") == "TCS-NSE"

def test_normalize_ticker_empty():
    assert normalize_ticker("") == ""

def test_normalize_ticker_just_spaces():
    assert normalize_ticker("   ") == ""

def test_normalize_ticker_hdfc():
    assert normalize_ticker("HdfcBank") == "HDFCBANK"

def test_normalize_ticker_sbi():
    assert normalize_ticker("  sbi  ") == "SBI"

def test_normalize_ticker_lt():
    assert normalize_ticker("L&T") == "L&T"
