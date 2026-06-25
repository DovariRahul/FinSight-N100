"""
Day 3 – Data Quality Validator (DQ-01 to DQ-16)

Validates cleaned CSV data in data/processed/ and writes all
failures to output/validation_failures.csv.

Each failure row contains:
    rule_id, company_id, year, table, column, issue, severity
"""

import os
import re
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Helper: load all cleaned tables
# ---------------------------------------------------------------------------

def load_tables(processed_dir):
    """
    Load all *_clean.csv files from processed_dir into a dict keyed by
    table name (e.g. 'companies', 'profitandloss', …).
    """
    tables = {}
    for fname in os.listdir(processed_dir):
        if fname.endswith("_clean.csv"):
            table_name = fname.replace("_clean.csv", "")
            path = os.path.join(processed_dir, fname)
            tables[table_name] = pd.read_csv(path)
    return tables


# ---------------------------------------------------------------------------
# Individual DQ rules – each returns a list of failure dicts
# ---------------------------------------------------------------------------

def dq_01_primary_key_uniqueness(tables):
    """DQ-01: Every table's primary key must be unique."""
    failures = []

    # Tables with composite PK (company_id, year)
    composite_pk_tables = [
        "profitandloss", "balancesheet", "cashflow",
        "financial_ratios", "market_cap",
    ]

    # Tables with single PK on id or company_id
    single_pk_tables = {
        "companies": "id",
        "analysis": "company_id",
        "sectors": "company_id",
        "prosandcons": "company_id",
    }

    # Tables with (company_id, date) PK
    date_pk_tables = {
        "stock_prices": ["company_id", "date"],
    }

    # Tables with other unique keys
    other_pk_tables = {
        "peer_groups": ["peer_group_name", "company_id"],
        "documents": ["company_id", "year"],
    }

    for tname in composite_pk_tables:
        if tname not in tables:
            continue
        df = tables[tname]
        if "company_id" in df.columns and "year" in df.columns:
            dupes = df[df.duplicated(subset=["company_id", "year"], keep=False)]
            for _, row in dupes.drop_duplicates(subset=["company_id", "year"]).iterrows():
                failures.append({
                    "rule_id": "DQ-01",
                    "company_id": row["company_id"],
                    "year": row.get("year", ""),
                    "table": tname,
                    "column": "company_id,year",
                    "issue": "Duplicate primary key (company_id, year)",
                    "severity": "CRITICAL",
                })

    for tname, pk_col in single_pk_tables.items():
        if tname not in tables:
            continue
        df = tables[tname]
        if pk_col in df.columns:
            dupes = df[df.duplicated(subset=[pk_col], keep=False)]
            for _, row in dupes.drop_duplicates(subset=[pk_col]).iterrows():
                failures.append({
                    "rule_id": "DQ-01",
                    "company_id": row.get(pk_col, ""),
                    "year": row.get("year", ""),
                    "table": tname,
                    "column": pk_col,
                    "issue": f"Duplicate primary key ({pk_col})",
                    "severity": "CRITICAL",
                })

    for tname, pk_cols in {**date_pk_tables, **other_pk_tables}.items():
        if tname not in tables:
            continue
        df = tables[tname]
        if all(c in df.columns for c in pk_cols):
            dupes = df[df.duplicated(subset=pk_cols, keep=False)]
            for _, row in dupes.drop_duplicates(subset=pk_cols).iterrows():
                failures.append({
                    "rule_id": "DQ-01",
                    "company_id": row.get("company_id", ""),
                    "year": row.get("year", row.get("date", "")),
                    "table": tname,
                    "column": ",".join(pk_cols),
                    "issue": f"Duplicate primary key ({', '.join(pk_cols)})",
                    "severity": "CRITICAL",
                })

    return failures


def dq_02_composite_key_check(tables):
    """DQ-02: Verify (company_id, year) is unique in time-series tables."""
    failures = []
    ts_tables = [
        "profitandloss", "balancesheet", "cashflow",
        "financial_ratios", "market_cap",
    ]

    for tname in ts_tables:
        if tname not in tables:
            continue
        df = tables[tname]
        if "company_id" not in df.columns or "year" not in df.columns:
            continue
        dupes = df[df.duplicated(subset=["company_id", "year"], keep=False)]
        for _, row in dupes.drop_duplicates(subset=["company_id", "year"]).iterrows():
            failures.append({
                "rule_id": "DQ-02",
                "company_id": row["company_id"],
                "year": row["year"],
                "table": tname,
                "column": "company_id,year",
                "issue": "Duplicate composite key (company_id, year)",
                "severity": "CRITICAL",
            })

    return failures


def dq_03_foreign_key_integrity(tables):
    """DQ-03: Every company_id must exist in the companies table."""
    failures = []

    if "companies" not in tables:
        return failures

    valid_ids = set(tables["companies"]["id"].dropna().astype(str).str.strip().str.upper())

    for tname, df in tables.items():
        if tname == "companies":
            continue
        if "company_id" not in df.columns:
            continue

        company_ids = df["company_id"].dropna().astype(str).str.strip().str.upper()
        missing = set(company_ids.unique()) - valid_ids

        for cid in sorted(missing):
            # Get a sample year for the failure record
            sample_year = ""
            if "year" in df.columns:
                match_rows = df[df["company_id"].astype(str).str.strip().str.upper() == cid]
                if not match_rows.empty:
                    sample_year = str(match_rows["year"].iloc[0])
            failures.append({
                "rule_id": "DQ-03",
                "company_id": cid,
                "year": sample_year,
                "table": tname,
                "column": "company_id",
                "issue": "Foreign key missing – company_id not in companies table",
                "severity": "CRITICAL",
            })

    return failures


def dq_04_balance_sheet_validation(tables):
    """DQ-04: total_assets ≈ total_liabilities (within 1%)."""
    failures = []

    if "balancesheet" not in tables:
        return failures

    df = tables["balancesheet"]
    required = ["company_id", "year", "total_assets", "total_liabilities"]
    if not all(c in df.columns for c in required):
        return failures

    for _, row in df.iterrows():
        assets = pd.to_numeric(row["total_assets"], errors="coerce")
        liabilities = pd.to_numeric(row["total_liabilities"], errors="coerce")

        if pd.isna(assets) or pd.isna(liabilities):
            continue

        denominator = max(abs(assets), 1)
        diff_pct = abs(assets - liabilities) / denominator * 100

        if diff_pct >= 1:
            failures.append({
                "rule_id": "DQ-04",
                "company_id": row["company_id"],
                "year": row["year"],
                "table": "balancesheet",
                "column": "total_assets",
                "issue": f"Balance sheet mismatch: assets={assets}, liabilities={liabilities}, diff={diff_pct:.2f}%",
                "severity": "WARNING",
            })

    return failures


def dq_05_opm_cross_validation(tables):
    """DQ-05: Computed OPM should match stored opm_percentage within 1%."""
    failures = []

    if "profitandloss" not in tables:
        return failures

    df = tables["profitandloss"]
    required = ["company_id", "year", "operating_profit", "sales", "opm_percentage"]
    if not all(c in df.columns for c in required):
        return failures

    for _, row in df.iterrows():
        sales = pd.to_numeric(row["sales"], errors="coerce")
        op_profit = pd.to_numeric(row["operating_profit"], errors="coerce")
        stored_opm = pd.to_numeric(row["opm_percentage"], errors="coerce")

        if pd.isna(sales) or pd.isna(op_profit) or pd.isna(stored_opm):
            continue
        if sales == 0:
            continue

        computed_opm = (op_profit / sales) * 100
        diff = abs(computed_opm - stored_opm)

        if diff > 1:
            failures.append({
                "rule_id": "DQ-05",
                "company_id": row["company_id"],
                "year": row["year"],
                "table": "profitandloss",
                "column": "opm_percentage",
                "issue": f"OPM mismatch: stored={stored_opm:.2f}%, computed={computed_opm:.2f}%, diff={diff:.2f}%",
                "severity": "WARNING",
            })

    return failures


def dq_06_positive_sales(tables):
    """DQ-06: Sales must be > 0."""
    failures = []

    if "profitandloss" not in tables:
        return failures

    df = tables["profitandloss"]
    if "sales" not in df.columns:
        return failures

    for _, row in df.iterrows():
        sales = pd.to_numeric(row["sales"], errors="coerce")
        if pd.notna(sales) and sales <= 0:
            failures.append({
                "rule_id": "DQ-06",
                "company_id": row.get("company_id", ""),
                "year": row.get("year", ""),
                "table": "profitandloss",
                "column": "sales",
                "issue": f"Sales is negative or zero: {sales}",
                "severity": "CRITICAL",
            })

    return failures


def dq_07_net_cash_flow(tables):
    """DQ-07: operating + investing + financing ≈ net_cash_flow (±10 crore)."""
    failures = []

    if "cashflow" not in tables:
        return failures

    df = tables["cashflow"]
    required = [
        "company_id", "year",
        "operating_activity", "investing_activity",
        "financing_activity", "net_cash_flow",
    ]
    if not all(c in df.columns for c in required):
        return failures

    for _, row in df.iterrows():
        operating = pd.to_numeric(row["operating_activity"], errors="coerce")
        investing = pd.to_numeric(row["investing_activity"], errors="coerce")
        financing = pd.to_numeric(row["financing_activity"], errors="coerce")
        net_cf = pd.to_numeric(row["net_cash_flow"], errors="coerce")

        if any(pd.isna(v) for v in [operating, investing, financing, net_cf]):
            continue

        expected = operating + investing + financing
        diff = abs(expected - net_cf)

        if diff > 10:
            failures.append({
                "rule_id": "DQ-07",
                "company_id": row["company_id"],
                "year": row["year"],
                "table": "cashflow",
                "column": "net_cash_flow",
                "issue": f"Cash flow mismatch: expected={expected:.1f}, actual={net_cf:.1f}, diff={diff:.1f} Cr",
                "severity": "WARNING",
            })

    return failures


def dq_08_tax_percentage(tables):
    """DQ-08: Computed tax rate should match stored tax_percentage within ±5%."""
    failures = []

    if "profitandloss" not in tables:
        return failures

    df = tables["profitandloss"]
    required = ["company_id", "year", "profit_before_tax", "net_profit", "tax_percentage"]
    if not all(c in df.columns for c in required):
        return failures

    for _, row in df.iterrows():
        pbt = pd.to_numeric(row["profit_before_tax"], errors="coerce")
        pat = pd.to_numeric(row["net_profit"], errors="coerce")
        stored_tax = pd.to_numeric(row["tax_percentage"], errors="coerce")

        if pd.isna(pbt) or pd.isna(pat) or pd.isna(stored_tax):
            continue
        if pbt == 0:
            continue

        computed_tax = ((pbt - pat) / pbt) * 100
        diff = abs(computed_tax - stored_tax)

        if diff > 5:
            failures.append({
                "rule_id": "DQ-08",
                "company_id": row["company_id"],
                "year": row["year"],
                "table": "profitandloss",
                "column": "tax_percentage",
                "issue": f"Tax rate mismatch: stored={stored_tax:.2f}%, computed={computed_tax:.2f}%, diff={diff:.2f}%",
                "severity": "WARNING",
            })

    return failures


def dq_09_dividend_payout(tables):
    """DQ-09: Dividend payout should not be unrealistic (> 200%)."""
    failures = []

    if "profitandloss" not in tables:
        return failures

    df = tables["profitandloss"]
    if "dividend_payout" not in df.columns:
        return failures

    for _, row in df.iterrows():
        payout = pd.to_numeric(row["dividend_payout"], errors="coerce")
        if pd.notna(payout) and payout > 200:
            failures.append({
                "rule_id": "DQ-09",
                "company_id": row.get("company_id", ""),
                "year": row.get("year", ""),
                "table": "profitandloss",
                "column": "dividend_payout",
                "issue": f"Unrealistic dividend payout: {payout}%",
                "severity": "WARNING",
            })

    return failures


def dq_10_eps_sign(tables):
    """DQ-10: If net_profit > 0 then EPS should be > 0."""
    failures = []

    if "profitandloss" not in tables:
        return failures

    df = tables["profitandloss"]
    if "net_profit" not in df.columns or "eps" not in df.columns:
        return failures

    for _, row in df.iterrows():
        net_profit = pd.to_numeric(row["net_profit"], errors="coerce")
        eps = pd.to_numeric(row["eps"], errors="coerce")

        if pd.isna(net_profit) or pd.isna(eps):
            continue

        if net_profit > 0 and eps <= 0:
            failures.append({
                "rule_id": "DQ-10",
                "company_id": row.get("company_id", ""),
                "year": row.get("year", ""),
                "table": "profitandloss",
                "column": "eps",
                "issue": f"EPS sign mismatch: net_profit={net_profit}, eps={eps}",
                "severity": "WARNING",
            })

    return failures


def dq_11_url_validation(tables):
    """DQ-11: URLs in website, company_logo, annual_report must start with http."""
    failures = []

    # Check companies table
    if "companies" in tables:
        df = tables["companies"]
        url_cols = ["website", "company_logo"]
        for col in url_cols:
            if col not in df.columns:
                continue
            for _, row in df.iterrows():
                val = row[col]
                if pd.isna(val) or str(val).strip() == "":
                    continue
                if not str(val).strip().startswith("http"):
                    failures.append({
                        "rule_id": "DQ-11",
                        "company_id": row.get("id", ""),
                        "year": "",
                        "table": "companies",
                        "column": col,
                        "issue": f"Invalid URL (does not start with http): {str(val)[:80]}",
                        "severity": "WARNING",
                    })

    # Check documents table
    if "documents" in tables:
        df = tables["documents"]
        if "annual_report" in df.columns:
            for _, row in df.iterrows():
                val = row["annual_report"]
                if pd.isna(val) or str(val).strip() == "":
                    continue
                if not str(val).strip().startswith("http"):
                    failures.append({
                        "rule_id": "DQ-11",
                        "company_id": row.get("company_id", ""),
                        "year": row.get("year", ""),
                        "table": "documents",
                        "column": "annual_report",
                        "issue": f"Invalid URL (does not start with http): {str(val)[:80]}",
                        "severity": "WARNING",
                    })

    return failures


def dq_12_coverage_validation(tables):
    """DQ-12: Companies with fewer than 5 years of financial history."""
    failures = []

    if "profitandloss" not in tables:
        return failures

    df = tables["profitandloss"]
    if "company_id" not in df.columns or "year" not in df.columns:
        return failures

    year_counts = df.groupby("company_id")["year"].nunique()
    low_coverage = year_counts[year_counts < 5]

    for company_id, count in low_coverage.items():
        failures.append({
            "rule_id": "DQ-12",
            "company_id": company_id,
            "year": "",
            "table": "profitandloss",
            "column": "year",
            "issue": f"Low coverage: only {count} year(s) of financial history (minimum 5)",
            "severity": "WARNING",
        })

    return failures


def dq_13_missing_critical_fields(tables):
    """DQ-13: Check NULL values in company_id, year, sales, total_assets."""
    failures = []

    # Check profitandloss for company_id, year, sales
    if "profitandloss" in tables:
        df = tables["profitandloss"]
        critical_cols = ["company_id", "year", "sales"]
        for col in critical_cols:
            if col not in df.columns:
                continue
            nulls = df[df[col].isna()]
            for _, row in nulls.iterrows():
                failures.append({
                    "rule_id": "DQ-13",
                    "company_id": row.get("company_id", "UNKNOWN"),
                    "year": row.get("year", ""),
                    "table": "profitandloss",
                    "column": col,
                    "issue": f"Missing critical field: {col} is NULL",
                    "severity": "CRITICAL",
                })

    # Check balancesheet for company_id, year, total_assets
    if "balancesheet" in tables:
        df = tables["balancesheet"]
        critical_cols = ["company_id", "year", "total_assets"]
        for col in critical_cols:
            if col not in df.columns:
                continue
            nulls = df[df[col].isna()]
            for _, row in nulls.iterrows():
                failures.append({
                    "rule_id": "DQ-13",
                    "company_id": row.get("company_id", "UNKNOWN"),
                    "year": row.get("year", ""),
                    "table": "balancesheet",
                    "column": col,
                    "issue": f"Missing critical field: {col} is NULL",
                    "severity": "CRITICAL",
                })

    return failures


def dq_14_duplicate_companies(tables):
    """DQ-14: Same company appears multiple times in companies table."""
    failures = []

    if "companies" not in tables:
        return failures

    df = tables["companies"]
    if "id" not in df.columns:
        return failures

    dupes = df[df.duplicated(subset=["id"], keep=False)]
    for _, row in dupes.drop_duplicates(subset=["id"]).iterrows():
        failures.append({
            "rule_id": "DQ-14",
            "company_id": row["id"],
            "year": "",
            "table": "companies",
            "column": "id",
            "issue": "Duplicate company in companies table",
            "severity": "CRITICAL",
        })

    return failures


def dq_15_invalid_year_format(tables):
    """DQ-15: Year column must match YYYY-MM format."""
    failures = []
    year_pattern = re.compile(r"^\d{4}-\d{2}$")

    ts_tables = [
        "profitandloss", "balancesheet", "cashflow",
        "financial_ratios", "market_cap",
    ]

    for tname in ts_tables:
        if tname not in tables:
            continue
        df = tables[tname]
        if "year" not in df.columns:
            continue

        for _, row in df.iterrows():
            year_val = str(row["year"]).strip()
            if not year_pattern.match(year_val):
                failures.append({
                    "rule_id": "DQ-15",
                    "company_id": row.get("company_id", ""),
                    "year": year_val,
                    "table": tname,
                    "column": "year",
                    "issue": f"Invalid year format: '{year_val}' (expected YYYY-MM)",
                    "severity": "WARNING",
                })

    return failures


def dq_16_numeric_data_validation(tables):
    """DQ-16: Numeric columns must actually contain numeric values."""
    failures = []

    numeric_checks = {
        "profitandloss": [
            "sales", "expenses", "operating_profit", "opm_percentage",
            "other_income", "interest", "depreciation", "profit_before_tax",
            "tax_percentage", "net_profit", "eps", "dividend_payout",
        ],
        "balancesheet": [
            "equity_capital", "reserves", "borrowings", "other_liabilities",
            "total_liabilities", "fixed_assets", "cwip", "investments",
            "other_asset", "total_assets",
        ],
        "cashflow": [
            "operating_activity", "investing_activity",
            "financing_activity", "net_cash_flow",
        ],
    }

    for tname, columns in numeric_checks.items():
        if tname not in tables:
            continue
        df = tables[tname]

        for col in columns:
            if col not in df.columns:
                continue

            # Try converting to numeric; non-convertible values become NaN
            numeric_vals = pd.to_numeric(df[col], errors="coerce")
            # Find rows that were NOT NaN originally but became NaN after conversion
            non_numeric_mask = numeric_vals.isna() & df[col].notna()

            for _, row in df[non_numeric_mask].iterrows():
                failures.append({
                    "rule_id": "DQ-16",
                    "company_id": row.get("company_id", ""),
                    "year": row.get("year", ""),
                    "table": tname,
                    "column": col,
                    "issue": f"Non-numeric value in numeric column: '{row[col]}'",
                    "severity": "CRITICAL",
                })

    return failures


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_all_validations(processed_dir=None, output_path=None):
    """
    Run all 16 DQ rules against the cleaned CSVs and write failures to CSV.
    """
    # Resolve paths relative to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    if processed_dir is None:
        processed_dir = os.path.join(project_root, "data", "processed")
    if output_path is None:
        output_dir = os.path.join(project_root, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "validation_failures.csv")

    print("=" * 60)
    print("  FinSight N100 – Data Quality Validation (DQ-01 to DQ-16)")
    print("=" * 60)
    print(f"\nLoading tables from: {processed_dir}")

    tables = load_tables(processed_dir)
    print(f"Loaded {len(tables)} tables: {', '.join(sorted(tables.keys()))}\n")

    # Collect all DQ rule functions
    all_rules = [
        ("DQ-01", "Primary Key Uniqueness", dq_01_primary_key_uniqueness),
        ("DQ-02", "Composite Key Check", dq_02_composite_key_check),
        ("DQ-03", "Foreign Key Integrity", dq_03_foreign_key_integrity),
        ("DQ-04", "Balance Sheet Validation", dq_04_balance_sheet_validation),
        ("DQ-05", "OPM Cross-Validation", dq_05_opm_cross_validation),
        ("DQ-06", "Positive Sales", dq_06_positive_sales),
        ("DQ-07", "Net Cash Flow", dq_07_net_cash_flow),
        ("DQ-08", "Tax Percentage", dq_08_tax_percentage),
        ("DQ-09", "Dividend Payout", dq_09_dividend_payout),
        ("DQ-10", "EPS Sign", dq_10_eps_sign),
        ("DQ-11", "URL Validation", dq_11_url_validation),
        ("DQ-12", "Coverage Validation", dq_12_coverage_validation),
        ("DQ-13", "Missing Critical Fields", dq_13_missing_critical_fields),
        ("DQ-14", "Duplicate Companies", dq_14_duplicate_companies),
        ("DQ-15", "Invalid Year Format", dq_15_invalid_year_format),
        ("DQ-16", "Numeric Data Validation", dq_16_numeric_data_validation),
    ]

    all_failures = []

    for rule_id, rule_name, rule_fn in all_rules:
        failures = rule_fn(tables)
        count = len(failures)
        status = "PASS" if count == 0 else "FAIL"
        icon = "[OK]" if count == 0 else "[!!]"
        print(f"  {icon} {rule_id}: {rule_name:<30s} -> {status} ({count} issue{'s' if count != 1 else ''})")
        all_failures.extend(failures)

    # Write results
    columns = ["rule_id", "company_id", "year", "table", "column", "issue", "severity"]
    df_failures = pd.DataFrame(all_failures, columns=columns)
    df_failures.to_csv(output_path, index=False)

    # Summary
    print(f"\n{'=' * 60}")
    total = len(df_failures)
    critical = len(df_failures[df_failures["severity"] == "CRITICAL"]) if total > 0 else 0
    warning = len(df_failures[df_failures["severity"] == "WARNING"]) if total > 0 else 0
    print(f"  Total issues: {total}  (CRITICAL: {critical}, WARNING: {warning})")
    print(f"  Results saved to: {output_path}")
    print(f"{'=' * 60}\n")

    return df_failures


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_all_validations()
