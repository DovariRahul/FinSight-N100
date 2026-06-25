import os
import sqlite3
import pandas as pd

def day5_load():
    db_path = 'nifty100.db'
    schema_path = 'db/schema.sql'
    processed_dir = 'data/processed'
    output_dir = 'output'
    
    # 1. Start fresh DB
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    
    with open(schema_path, 'r') as f:
        schema = f.read()
    conn.executescript(schema)
    
    tables_order = [
        "companies",
        "sectors",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "stock_prices",
        "market_cap",
        "financial_ratios",
        "peer_groups"
    ]
    
    audit_data = []
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading data into DB...")
    
    for table in tables_order:
        csv_path = os.path.join(processed_dir, f"{table}_clean.csv")
        if not os.path.exists(csv_path):
            print(f"File {csv_path} not found. Skipping...")
            continue
            
        df = pd.read_csv(csv_path)
        
        # Drop surrogate 'id' columns from tables other than companies
        if 'id' in df.columns and table != 'companies':
            df.drop(columns=['id'], inplace=True)
            
        # Get actual DB columns to filter out extra columns in CSV
        cursor = conn.execute(f"PRAGMA table_info({table});")
        db_cols = [row[1] for row in cursor.fetchall()]
        common_cols = [c for c in df.columns if c in db_cols]
        df = df[common_cols]
            
        rows_read = len(df)
        rows_loaded = 0
        rejected = 0
        
        try:
            # Try batch insert as requested
            df.to_sql(table, conn, if_exists="append", index=False)
            rows_loaded = rows_read
        except Exception as batch_e:
            print(f"Batch insert failed for {table}. Falling back to row-by-row to isolate errors.")
            for _, row in df.iterrows():
                try:
                    row.to_frame().T.to_sql(table, conn, if_exists="append", index=False)
                    rows_loaded += 1
                except Exception as e:
                    rejected += 1
                    print(f"[{table}] Error loading row: {e} | Row values: {row.to_dict()}")
                    
        audit_data.append({
            "Table": table,
            "Rows Read": rows_read,
            "Rows Loaded": rows_loaded,
            "Rejected": rejected
        })
        print(f"[{table}] Read: {rows_read}, Loaded: {rows_loaded}, Rejected: {rejected}")
        
    audit_df = pd.DataFrame(audit_data)
    audit_df.to_csv(os.path.join(output_dir, 'load_audit.csv'), index=False)
    print("\nLoad Audit Report generated at output/load_audit.csv\n")
    
    print("Verifying Row Counts:")
    for table in tables_order:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")
            
    print("\nChecking Foreign Keys...")
    fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if len(fk_errors) == 0:
        print("0 rows")
        print("Meaning: Every company_id exists, No orphan records, All relationships are valid.")
    else:
        print(f"Found {len(fk_errors)} foreign key errors!")
        for err in fk_errors[:5]:
            print(err)
            
    conn.close()

if __name__ == '__main__':
    day5_load()
