import pandas as pd

for tbl in ['profitandloss', 'balancesheet', 'cashflow']:
    try:
        raw_df = pd.read_excel(f'data/raw/{tbl}.xlsx', header=1 if 'Fintech' in str(pd.read_excel(f'data/raw/{tbl}.xlsx', nrows=0).columns[0]) else 0)
        clean_df = pd.read_csv(f'data/processed/{tbl}_clean.csv')
        print(f"{tbl}: Raw rows={len(raw_df)}, Clean rows={len(clean_df)}")
        # Check how many are TTM in raw
        ttm_count = len(raw_df[raw_df['Year'].astype(str).str.upper() == 'TTM']) if 'Year' in raw_df.columns else 0
        print(f"  TTM rows in raw: {ttm_count}")
        print(f"  Dropped diff: {len(raw_df) - len(clean_df)}")
    except Exception as e:
        print(f"Error on {tbl}: {e}")
