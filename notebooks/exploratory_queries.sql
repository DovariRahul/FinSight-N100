-- Day 7: Exploratory SQL Queries
-- 10 Useful Queries for FinSight N100 Data Analysis

-- 1. Total Companies
SELECT COUNT(*) AS total_companies
FROM companies;

-- 2. Total Profit & Loss Records
SELECT COUNT(*) AS total_pl_records
FROM profitandloss;

-- 3. Companies by Sector
SELECT broad_sector, COUNT(*) AS count
FROM sectors
GROUP BY broad_sector
ORDER BY count DESC;

-- 4. Top 10 Companies by Sales (Latest Year)
SELECT p.company_id, c.company_name, p.year, p.sales
FROM profitandloss p
JOIN companies c ON p.company_id = c.id
WHERE p.year = (SELECT MAX(year) FROM profitandloss)
ORDER BY p.sales DESC
LIMIT 10;

-- 5. Companies with Highest Net Profit (All Time)
SELECT p.company_id, c.company_name, p.year, p.net_profit
FROM profitandloss p
JOIN companies c ON p.company_id = c.id
ORDER BY p.net_profit DESC
LIMIT 10;

-- 6. Average Return on Capital Employed (ROCE) by Sector
SELECT s.broad_sector, ROUND(AVG(c.roce_percentage), 2) AS avg_roce
FROM companies c
JOIN sectors s ON c.id = s.company_id
WHERE c.roce_percentage IS NOT NULL
GROUP BY s.broad_sector
ORDER BY avg_roce DESC;

-- 7. Highest Market Capitalization Companies in 2024
SELECT m.company_id, c.company_name, m.year, m.market_cap_crore
FROM market_cap m
JOIN companies c ON m.company_id = c.id
WHERE m.year = 2024
ORDER BY m.market_cap_crore DESC
LIMIT 10;

-- 8. Top 5 Companies with Best Compounded Sales Growth
SELECT a.company_id, c.company_name, a.compounded_sales_growth
FROM analysis a
JOIN companies c ON a.company_id = c.id
WHERE a.compounded_sales_growth IS NOT NULL
ORDER BY CAST(REPLACE(a.compounded_sales_growth, '%', '') AS REAL) DESC
LIMIT 5;

-- 9. Companies with the Most Consistent Operating Margin
SELECT company_id, 
       ROUND(AVG(opm_percentage), 2) AS avg_opm,
       ROUND(MAX(opm_percentage) - MIN(opm_percentage), 2) AS opm_volatility
FROM profitandloss
GROUP BY company_id
HAVING COUNT(*) > 5
ORDER BY opm_volatility ASC
LIMIT 10;

-- 10. Debt-to-Equity Analysis for Highest Debt Companies
SELECT f.company_id, c.company_name, f.year, f.total_debt_cr, f.debt_to_equity
FROM financial_ratios f
JOIN companies c ON f.company_id = c.id
WHERE f.year = (SELECT MAX(year) FROM financial_ratios) 
  AND f.total_debt_cr IS NOT NULL
ORDER BY f.total_debt_cr DESC
LIMIT 10;
