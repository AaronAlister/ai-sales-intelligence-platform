from database.db import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT *
FROM upload_history
ORDER BY upload_timestamp DESC
""")

rows = cursor.fetchall()

print("\nUPLOAD HISTORY")
print("-" * 100)

for row in rows:
    print(
        row["upload_timestamp"],
        "|",
        row["file_name"],
        "|",
        row["rows_inserted"],
        "rows",
        "|",
        row["status"]
    )

conn.close()
