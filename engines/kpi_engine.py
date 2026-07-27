from database.db import get_connection


def get_dashboard_metrics():
    """
    Returns the main KPI metrics for the dashboard.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ROUND(COALESCE(SUM(amount), 0), 2) AS total_revenue,

            COUNT(DISTINCT invoice) AS total_orders,

            COUNT(DISTINCT customer) AS total_customers,

            COUNT(DISTINCT item_code) AS total_products,

            ROUND(COALESCE(SUM(stock_qty), 0), 2) AS total_quantity,

            ROUND(
                COALESCE(
                    SUM(amount) /
                    NULLIF(COUNT(DISTINCT invoice), 0),
                0),
            2) AS average_order_value

        FROM sales
    """)

    row = cursor.fetchone()

    conn.close()

    return {

        "total_revenue": row["total_revenue"],

        "total_orders": row["total_orders"],

        "total_customers": row["total_customers"],

        "total_products": row["total_products"],

        "total_quantity": row["total_quantity"],

        "average_order_value": row["average_order_value"]

    }