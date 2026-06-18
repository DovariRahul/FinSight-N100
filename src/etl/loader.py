import os
import pandas as pd
from src.etl.normaliser import normalize_ticker, normalize_year

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

def process_all_files(raw_dir="data/raw", processed_dir="data/processed"):
    """
    Load all Excel files from raw_dir, clean them, and save to processed_dir as CSVs.
    """
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

if __name__ == "__main__":
    # Allow execution directly as script
    # Determine directory paths relative to root workspace
    process_all_files()
