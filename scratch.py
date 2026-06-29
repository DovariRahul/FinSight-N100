import sqlite3
import pandas as pd
conn = sqlite3.connect('nifty100.db')
c = conn.cursor()
c.execute("SELECT year FROM profitandloss WHERE company_id='JIOFIN'")
print('JIOFIN P&L years:', c.fetchall())

print('\n--- TASK 5: Cross check TCS for 2024-03 ---')
for table in ['profitandloss', 'balancesheet', 'cashflow']:
    c.execute(f"SELECT * FROM {table} WHERE company_id='TCS' AND year LIKE '2024%'")
    print(table, ':', c.fetchall())
    
c.execute("SELECT year, COUNT(*) FROM profitandloss GROUP BY year")
print('\nP&L year distribution:', c.fetchall())
