import pandas as pd

from database.db import get_connection

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", None)


def main():

    conn = get_connection()

    sql = """
    SELECT
        item_name,
        ROUND(SUM(stock_qty), 2) AS quantity,
        COUNT(DISTINCT invoice) AS invoices,
        ROUND(SUM(amount), 2) AS revenue
    FROM sales
    WHERE transaction_type = 'Sale'
    GROUP BY item_name
    ORDER BY quantity DESC
    LIMIT 10;
    """

    df = pd.read_sql_query(sql, conn)

    print("\nTop 10 Products by Quantity")
    print("=" * 120)
    print(df.to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()