from database.db import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT
    SUM(amount) AS return_transactions_amount
FROM sales
WHERE amount < 0
""")

print(cursor.fetchone())
conn.close()
