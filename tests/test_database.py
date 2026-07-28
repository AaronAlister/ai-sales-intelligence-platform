from database.db import get_connection
from tabulate import tabulate

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) AS total FROM sales")
total = cursor.fetchone()["total"]

print("=" * 95)
print("DATABASE STATUS")
print("=" * 95)
print(f"Total Records : {total}")

cursor.execute("""
SELECT
    invoice,
    item_name,
    customer,
    posting_date,
    stock_qty,
    amount
FROM sales
LIMIT 10
""")

rows = cursor.fetchall()

if rows:

    print("\nUploaded Records:\n")

    print(
        tabulate(
            [list(r) for r in rows],
            headers=rows[0].keys(),
            tablefmt="fancy_grid"
        )
    )

else:

    print("\nDatabase is empty.")

conn.close()