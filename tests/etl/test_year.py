import pytest
from src.etl.normaliser import normalize_year

def test_normalize_year_mar_23():
    assert normalize_year("Mar-23") == "2023-03"

def test_normalize_year_mar_24():
    assert normalize_year("Mar-24") == "2024-03"

def test_normalize_year_dec_22():
    assert normalize_year("Dec-22") == "2022-12"

def test_normalize_year_space_separator():
    assert normalize_year("Dec 2012") == "2012-12"

def test_normalize_year_space_separator_mar():
    assert normalize_year("Mar 2014") == "2014-03"

def test_normalize_year_extra_suffix_9m():
    assert normalize_year("Mar 2016 9m") == "2016-03"

def test_normalize_year_extra_suffix_15():
    assert normalize_year("Mar 2023 15") == "2023-03"

def test_normalize_year_whitespace_handling():
    assert normalize_year("  Mar-23  ") == "2023-03"

def test_normalize_year_lowercase_month():
    assert normalize_year("dec-22") == "2022-12"

def test_normalize_year_uppercase_month():
    assert normalize_year("JAN-21") == "2021-01"

def test_normalize_year_feb_20():
    assert normalize_year("Feb-20") == "2020-02"

def test_normalize_year_apr_19():
    assert normalize_year("Apr-19") == "2019-04"

def test_normalize_year_may_18():
    assert normalize_year("May-18") == "2018-05"

def test_normalize_year_jun_17():
    assert normalize_year("Jun-17") == "2017-06"

def test_normalize_year_jul_16():
    assert normalize_year("Jul-16") == "2016-07"

def test_normalize_year_aug_15():
    assert normalize_year("Aug-15") == "2015-08"

def test_normalize_year_sep_14():
    assert normalize_year("Sep-14") == "2014-09"

def test_normalize_year_oct_13():
    assert normalize_year("Oct-13") == "2013-10"

def test_normalize_year_nov_12():
    assert normalize_year("Nov-12") == "2012-11"

def test_normalize_year_sep_2023():
    assert normalize_year("Sep 2023") == "2023-09"

def test_normalize_year_numeric():
    assert normalize_year("2013") == "2013-03"
    assert normalize_year("2024.5") == "2024-09"
    assert normalize_year(2021) == "2021-03"
    assert normalize_year("23") == "2023-03"

def test_normalize_year_invalid_formats():
    with pytest.raises(ValueError):
        normalize_year("TTM")
    with pytest.raises(ValueError):
        normalize_year("2024.3")
    with pytest.raises(ValueError):
        normalize_year(None)
    with pytest.raises(ValueError):
        normalize_year("invalid")

