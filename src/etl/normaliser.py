import re

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
    'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
}

def normalize_ticker(ticker):
    """Normalize company_id/ticker to uppercase stripped string."""
    if ticker is None:
        return ""
    return str(ticker).strip().upper()

def normalize_year(year):
    """
    Standardise year labels (e.g. Mar-23 -> 2023-03).
    Supports:
    - MMM-yy (e.g., Mar-23)
    - MMM yyyy (e.g., Dec 2012)
    - MMM yyyy <extra> (e.g., Mar 2016 9m, Mar 2023 15)
    - Numeric years (e.g. 2013 -> 2013-03, 2024.5 -> 2024-09)
    Raises ValueError for invalid/unparseable values.
    """
    if year is None:
        raise ValueError("Year value cannot be None")
    
    val = str(year).strip()
    
    if val.upper() == "TTM":
        raise ValueError("TTM is not a standard fiscal year label")
        
    # Check if the string is numeric (e.g. "2013" or "2024.5" or "2013.0")
    if re.match(r'^\d+(?:\.\d+)?$', val):
        f_val = float(val)
        year_num = int(f_val)
        if year_num < 100:
            year_num += 2000
        decimal_part = f_val - int(f_val)
        if abs(decimal_part) < 1e-9:
            # e.g., 2013 -> March
            return f"{year_num}-03"
        elif abs(decimal_part - 0.5) < 1e-9:
            # e.g., 2024.5 -> September
            return f"{year_num}-09"
        else:
            raise ValueError(f"Cannot parse year decimal value: {val}")
        
    # Match pattern: 3 letter month followed by separator then 2 or 4 digit year, optional trailing characters
    match = re.match(r'^([a-zA-Z]{3})[- ]?(\d{2,4})(?:\s+.*)?$', val)
    if not match:
        raise ValueError(f"Cannot parse year format: {val}")
        
    month_str, year_str = match.groups()
    month_key = month_str.lower()
    
    if month_key not in MONTH_MAP:
        raise ValueError(f"Invalid month: {month_str}")
        
    month_num = MONTH_MAP[month_key]
    
    if len(year_str) == 2:
        # Standardize 2-digit years by assuming 2000s (consistent with the dataset time span)
        full_year = f"20{year_str}"
    elif len(year_str) == 4:
        full_year = year_str
    else:
        raise ValueError(f"Invalid year length: {year_str}")
        
    return f"{full_year}-{month_num}"
