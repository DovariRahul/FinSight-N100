"""
FinSight N100 – ETL Loader (Day 2 + Day 4)

Day 2: Read Excel -> Normalize -> Save as cleaned CSVs
Day 4: Create SQLite DB -> Load cleaned CSVs into database
"""

import os
import sqlite3
import pandas as pd
from normaliser import normalize_ticker, normalize_year


# ---------------------------------------------------------------------------
# Project root helper
# ---------------------------------------------------------------------------

def _project_root():
    """Return absolute path to the project root (two levels up from this file)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ===================================================================
# Day 2 – Excel to cleaned CSV
# ===================================================================

def load_excel(file_path):
    """
    Load excel file dynamically detecting if Row 0 contains metadata or actual headers.
    Use header=1 if metadata is detected, otherwise header=0.
    """
    df_peek = pd.read_excel(file_path, nrows=0)
    if len(df_peek.columns) > 0:
        first_col = str(df_peek.columns[0])
        if any(k in first_col for k in ["Fintech", "records", "|"]):
            return pd.read_excel(file_path, header=1)
    return pd.read_excel(file_path, header=0)

def clean_dataframe(df, filename):
    """
    Normalize company ids, standardize years, filter TTM rows, and handle duplicate company-year pairs.
    """
    # Standardize column casing and whitespace
    df.columns = [c.strip().lower() for c in df.columns]
    
    # 1. Normalize company ticker identifier
    comp_col = None
    if 'company_id' in df.columns:
        comp_col = 'company_id'
    elif 'id' in df.columns and filename == 'companies.xlsx':
        comp_col = 'id'
        
    if comp_col:
        df[comp_col] = df[comp_col].apply(normalize_ticker)
        
    # 2. Normalize year labels
    year_col = None
    if 'year' in df.columns:
        year_col = 'year'
        
    if year_col:
        # Convert to string and filter out "TTM" values
        df = df[df[year_col].notna()]
        df = df[df[year_col].astype(str).str.strip().str.upper() != 'TTM']
        
        # Determine if we should apply normalize_year (string representations of month-years)
        # Check if there are values containing alphabetical characters representing months
        has_month_strings = df[year_col].astype(str).str.contains(r'[a-zA-Z]').any()
        if has_month_strings:
            df[year_col] = df[year_col].apply(normalize_year)
            
    # 3. Handle duplicates
    if comp_col == 'company_id' and year_col == 'year':
        # Drop duplicate company-year pairs
        before_count = len(df)
        df = df.drop_duplicates(subset=['company_id', 'year'], keep='first')
        dropped = before_count - len(df)
        if dropped > 0:
            print(f"Dropped {dropped} duplicate company-year pairs from {filename}.")
    elif comp_col == 'id' and filename == 'companies.xlsx':
        # Drop duplicate company records
        before_count = len(df)
        df = df.drop_duplicates(subset=['id'], keep='first')
        dropped = before_count - len(df)
        if dropped > 0:
            print(f"Dropped {dropped} duplicate companies from {filename}.")
            
    return df

def process_all_files(raw_dir=None, processed_dir=None):
    """
    Load all Excel files from raw_dir, clean them, and save to processed_dir as CSVs.
    """
    project_root = _project_root()
    if raw_dir is None:
        raw_dir = os.path.join(project_root, "data", "raw")
    if processed_dir is None:
        processed_dir = os.path.join(project_root, "data", "processed")

    os.makedirs(processed_dir, exist_ok=True)
    
    files = [f for f in os.listdir(raw_dir) if f.endswith(".xlsx")]
    for f in files:
        raw_path = os.path.join(raw_dir, f)
        print(f"Processing {f}...")
        try:
            df = load_excel(raw_path)
            df_clean = clean_dataframe(df, f)
            
            # Save to output path
            base_name = os.path.splitext(f)[0]
            out_name = f"{base_name}_clean.csv"
            out_path = os.path.join(processed_dir, out_name)
            
            df_clean.to_csv(out_path, index=False)
            print(f"Saved cleaned data to {out_path} (Shape: {df_clean.shape})")
        except Exception as e:
            print(f"Error processing file {f}: {e}")


# ===================================================================
# Day 4 – Load cleaned CSVs into SQLite
# ===================================================================

# Mapping: table_name -> CSV filename (without _clean.csv suffix)
# and the columns to use as primary key (for dedup before insert)
TABLE_CONFIG = {
    # Parent table (must be loaded first)
    "companies": {
        "csv": "companies_clean.csv",
        "pk_cols": ["id"],
        "id_col": None,  # 'id' IS the PK, don't drop it
    },
    # Child tables with composite PK (company_id, year)
    "profitandloss": {
        "csv": "profitandloss_clean.csv",
        "pk_cols": ["company_id", "year"],
        "id_col": "id",  # surrogate id to drop
    },
    "balancesheet": {
        "csv": "balancesheet_clean.csv",
        "pk_cols": ["company_id", "year"],
        "id_col": "id",
    },
    "cashflow": {
        "csv": "cashflow_clean.csv",
        "pk_cols": ["company_id", "year"],
        "id_col": "id",
    },
    "financial_ratios": {
        "csv": "financial_ratios_clean.csv",
        "pk_cols": ["company_id", "year"],
        "id_col": "id",
    },
    "documents": {
        "csv": "documents_clean.csv",
        "pk_cols": ["company_id", "year"],
        "id_col": "id",
    },
    # Child tables with single PK (company_id)
    "analysis": {
        "csv": "analysis_clean.csv",
        "pk_cols": ["company_id"],
        "id_col": "id",
    },
    "prosandcons": {
        "csv": "prosandcons_clean.csv",
        "pk_cols": ["company_id"],
        "id_col": "id",
    },
    "sectors": {
        "csv": "sectors_clean.csv",
        "pk_cols": ["company_id"],
        "id_col": "id",
    },
    # Stock prices: PK is (company_id, date)
    "stock_prices": {
        "csv": "stock_prices_clean.csv",
        "pk_cols": ["company_id", "date"],
        "id_col": "id",
    },
    # Peer groups: PK is (peer_group_name, company_id)
    "peer_groups": {
        "csv": "peer_groups_clean.csv",
        "pk_cols": ["peer_group_name", "company_id"],
        "id_col": "id",
    },
}


def create_database(db_path, schema_path):
    """
    Create the SQLite database by executing schema.sql.
    Drops existing DB file to start fresh.
    """
    # Remove existing DB for a clean rebuild
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    print(f"Database created: {db_path}")
    print(f"Schema applied from: {schema_path}")

    return conn


def load_table_to_db(conn, table_name, csv_path, config):
    """
    Read a cleaned CSV and insert rows into the SQLite table.
    - Drops the surrogate 'id' column if present
    - Deduplicates on PK columns before insert
    - Skips rows that violate FK constraints (INSERT OR IGNORE)
    """
    if not os.path.exists(csv_path):
        print(f"  [SKIP] CSV not found: {csv_path}")
        return 0

    df = pd.read_csv(csv_path)

    # Drop surrogate id column (not part of the DB schema)
    id_col = config.get("id_col")
    if id_col and id_col in df.columns:
        df = df.drop(columns=[id_col])

    # Deduplicate on PK columns
    pk_cols = config["pk_cols"]
    if all(c in df.columns for c in pk_cols):
        before = len(df)
        df = df.drop_duplicates(subset=pk_cols, keep="first")
        dropped = before - len(df)
        if dropped > 0:
            print(f"  Deduped {dropped} rows on {pk_cols}")

    # Get the actual DB column names from the table
    cursor = conn.execute(f"PRAGMA table_info({table_name});")
    db_columns = [row[1] for row in cursor.fetchall()]

    # Only keep columns that exist in the DB schema
    common_cols = [c for c in df.columns if c in db_columns]
    df = df[common_cols]

    # Insert using INSERT OR IGNORE to skip FK violations gracefully
    placeholders = ", ".join(["?"] * len(common_cols))
    col_names = ", ".join(common_cols)
    insert_sql = f"INSERT OR IGNORE INTO {table_name} ({col_names}) VALUES ({placeholders})"

    inserted = 0
    skipped = 0
    for _, row in df.iterrows():
        try:
            conn.execute(insert_sql, tuple(row))
            inserted += 1
        except sqlite3.IntegrityError as e:
            skipped += 1

    conn.commit()

    msg = f"  [OK] {table_name}: {inserted} rows inserted"
    if skipped > 0:
        msg += f", {skipped} skipped (FK/PK violations)"
    print(msg)

    return inserted


def load_all_to_db(processed_dir=None, db_path=None, schema_path=None):
    """
    Orchestrator: create the SQLite DB and load all cleaned CSVs.
    Companies table is loaded first (parent), then all child tables.
    """
    project_root = _project_root()

    if processed_dir is None:
        processed_dir = os.path.join(project_root, "data", "processed")
    if db_path is None:
        db_path = os.path.join(project_root, "nifty100.db")
    if schema_path is None:
        schema_path = os.path.join(project_root, "db", "schema.sql")

    print("\n" + "=" * 60)
    print("  FinSight N100 - Database Loader (Day 4)")
    print("=" * 60)

    # Step 1: Create database from schema
    conn = create_database(db_path, schema_path)

    # Step 2: Load companies first (parent table for all FKs)
    print("\nLoading tables...")
    companies_config = TABLE_CONFIG["companies"]
    csv_path = os.path.join(processed_dir, companies_config["csv"])
    load_table_to_db(conn, "companies", csv_path, companies_config)

    # Step 3: Load all child tables
    for table_name, config in TABLE_CONFIG.items():
        if table_name == "companies":
            continue  # already loaded
        csv_path = os.path.join(processed_dir, config["csv"])
        load_table_to_db(conn, table_name, csv_path, config)

    # Step 4: Verify
    print(f"\n{'=' * 60}")
    print("  Verification")
    print(f"{'=' * 60}")

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n  Tables created: {len(tables)}")

    for tname in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {tname};").fetchone()[0]
        print(f"    {tname:<25s} {count:>6d} rows")

    # Verify FK enforcement is ON
    fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    print(f"\n  Foreign Key enforcement: {'ON' if fk_status else 'OFF'}")

    print(f"\n  Database saved to: {db_path}")
    print(f"{'=' * 60}\n")

    conn.close()


# ===================================================================
# Entry point
# ===================================================================

if __name__ == "__main__":
    # Step 1: Process raw Excel -> cleaned CSVs (Day 2)
    print("=" * 60)
    print("  Step 1: Processing raw Excel files to cleaned CSVs")
    print("=" * 60)
    process_all_files()

    # Step 2: Load cleaned CSVs -> SQLite (Day 4)
    load_all_to_db()
