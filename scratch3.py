import sqlite3
conn = sqlite3.connect('nifty100.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
for t in tables:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"{t}: {c.fetchone()[0]}")
