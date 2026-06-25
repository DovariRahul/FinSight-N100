-- ============================================================
-- FinSight N100 – Database Schema
-- 11 tables with Primary Keys and Foreign Keys
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. Companies (Master Table)
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    id                  TEXT PRIMARY KEY,
    company_name        TEXT,
    company_logo        TEXT,
    chart_link          TEXT,
    about_company       TEXT,
    website             TEXT,
    nse_profile         TEXT,
    bse_profile         TEXT,
    face_value          REAL,
    book_value          REAL,
    roce_percentage     REAL,
    roe_percentage      REAL
);

-- ============================================================
-- 2. Profit & Loss
-- ============================================================
CREATE TABLE IF NOT EXISTS profitandloss (
    company_id          TEXT NOT NULL,
    year                TEXT NOT NULL,
    sales               REAL,
    expenses            REAL,
    operating_profit    REAL,
    opm_percentage      REAL,
    other_income        REAL,
    interest            REAL,
    depreciation        REAL,
    profit_before_tax   REAL,
    tax_percentage      REAL,
    net_profit          REAL,
    eps                 REAL,
    dividend_payout     REAL,

    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 3. Balance Sheet
-- ============================================================
CREATE TABLE IF NOT EXISTS balancesheet (
    company_id          TEXT NOT NULL,
    year                TEXT NOT NULL,
    equity_capital      REAL,
    reserves            REAL,
    borrowings          REAL,
    other_liabilities   REAL,
    total_liabilities   REAL,
    fixed_assets        REAL,
    cwip                REAL,
    investments         REAL,
    other_asset         REAL,
    total_assets        REAL,

    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 4. Cash Flow
-- ============================================================
CREATE TABLE IF NOT EXISTS cashflow (
    company_id          TEXT NOT NULL,
    year                TEXT NOT NULL,
    operating_activity  REAL,
    investing_activity  REAL,
    financing_activity  REAL,
    net_cash_flow       REAL,

    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 5. Financial Ratios
-- ============================================================
CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id                  TEXT NOT NULL,
    year                        TEXT NOT NULL,
    net_profit_margin_pct       REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct        REAL,
    debt_to_equity              REAL,
    interest_coverage           REAL,
    asset_turnover              REAL,
    free_cash_flow_cr           REAL,
    capex_cr                    REAL,
    earnings_per_share          REAL,
    book_value_per_share        REAL,
    dividend_payout_ratio_pct   REAL,
    total_debt_cr               REAL,
    cash_from_operations_cr     REAL,

    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 6. Analysis
-- ============================================================
CREATE TABLE IF NOT EXISTS analysis (
    company_id                  TEXT PRIMARY KEY,
    compounded_sales_growth     TEXT,
    compounded_profit_growth    TEXT,
    stock_price_cagr            TEXT,
    roe                         TEXT,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 7. Documents
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    company_id      TEXT NOT NULL,
    year            TEXT NOT NULL,
    annual_report   TEXT,

    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 8. Pros and Cons
-- ============================================================
CREATE TABLE IF NOT EXISTS prosandcons (
    company_id      TEXT PRIMARY KEY,
    pros            TEXT,
    cons            TEXT,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 9. Sectors
-- ============================================================
CREATE TABLE IF NOT EXISTS sectors (
    company_id          TEXT PRIMARY KEY,
    broad_sector        TEXT,
    sub_sector          TEXT,
    index_weight_pct    REAL,
    market_cap_category TEXT,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 10. Stock Prices
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_prices (
    company_id      TEXT NOT NULL,
    date            TEXT NOT NULL,
    open_price      REAL,
    high_price      REAL,
    low_price       REAL,
    close_price     REAL,
    volume          INTEGER,
    adjusted_close  REAL,

    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 11. Peer Groups
-- ============================================================
CREATE TABLE IF NOT EXISTS peer_groups (
    peer_group_name TEXT NOT NULL,
    company_id      TEXT NOT NULL,
    is_benchmark    INTEGER,

    PRIMARY KEY (peer_group_name, company_id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- 12. Market Cap
-- ============================================================
CREATE TABLE IF NOT EXISTS market_cap (
    company_id              TEXT NOT NULL,
    year                    INTEGER NOT NULL,
    market_cap_crore        REAL,
    enterprise_value_crore  REAL,
    pe_ratio                REAL,
    pb_ratio                REAL,
    ev_ebitda               REAL,
    dividend_yield_pct      REAL,

    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
