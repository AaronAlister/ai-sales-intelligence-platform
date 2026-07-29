import sqlite3
from pathlib import Path


class KPIEngine:
    """
    Executive KPI Engine

    Calculates high-level business metrics for the dashboard.
    """

    DB_PATH = Path("data/sales.db")

    def __init__(self):
        self.conn = sqlite3.connect(self.DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    # =====================================================
    # HELPER
    # =====================================================

    def scalar(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    # =====================================================
    # SALES KPIs
    # =====================================================

    def gross_sales(self):
        return round(
            self.scalar("""
                SELECT COALESCE(SUM(amount),0)
                FROM sales
                WHERE amount > 0
            """),
            2
        )

    def returns_value(self):
        return round(
            self.scalar("""
                SELECT COALESCE(ABS(SUM(amount)),0)
                FROM sales
                WHERE amount < 0
            """),
            2
        )

    def net_sales(self):
        return round(
            self.scalar("""
                SELECT COALESCE(SUM(amount),0)
                FROM sales
            """),
            2
        )

    def return_rate(self):

        gross = self.gross_sales()

        if gross == 0:
            return 0

        return round(
            (self.returns_value() / gross) * 100,
            2
        )

    # =====================================================
    # ORDER KPIs
    # =====================================================

    def total_orders(self):
        return self.scalar("""
            SELECT COUNT(DISTINCT invoice)
            FROM sales
        """)

    def average_order_value(self):

        orders = self.total_orders()

        if orders == 0:
            return 0

        return round(
            self.net_sales() / orders,
            2
        )

    def average_items_per_order(self):

        orders = self.total_orders()

        if orders == 0:
            return 0

        return round(
            self.net_quantity() / orders,
            2
        )

    # =====================================================
    # QUANTITY KPIs
    # =====================================================

    def gross_quantity(self):
        return round(
            self.scalar("""
                SELECT COALESCE(SUM(stock_qty),0)
                FROM sales
                WHERE stock_qty > 0
            """),
            2
        )

    def net_quantity(self):
        return round(
            self.scalar("""
                SELECT COALESCE(SUM(stock_qty),0)
                FROM sales
            """),
            2
        )

    def total_returns(self):
        return self.scalar("""
            SELECT COUNT(*)
            FROM sales
            WHERE transaction_type='Return'
        """)

    # =====================================================
    # PRODUCT KPIs
    # =====================================================

    def total_products(self):
        """
        Returns the number of distinct products that have at least one sale.
        """

        return self.scalar("""
            SELECT COUNT(DISTINCT item_code)
            FROM sales
            WHERE transaction_type = 'Sale'
            """)

    # =====================================================
    # CUSTOMER KPIs
    # =====================================================

    def total_customers(self):
        return self.scalar("""
            SELECT COUNT(DISTINCT customer)
            FROM sales
        """)

    def average_customer_value(self):

        customers = self.total_customers()

        if customers == 0:
            return 0

        return round(
            self.net_sales() / customers,
            2
        )

    # =====================================================
    # DISCOUNT KPIs
    # =====================================================

    def average_discount(self):
        return round(
            self.scalar("""
                SELECT COALESCE(
                    AVG(discount_percent),
                    0
                )
                FROM sales
                WHERE discount_percent >= 0
            """),
            2
        )

    # =====================================================
    # UPLOAD KPIs
    # =====================================================

    def total_uploads(self):
        return self.scalar("""
            SELECT COUNT(*)
            FROM upload_history
            WHERE status='SUCCESS'
        """)

    def latest_upload(self):

        self.cursor.execute("""
            SELECT upload_timestamp
            FROM upload_history
            WHERE status='SUCCESS'
            ORDER BY upload_timestamp DESC
            LIMIT 1
        """)

        row = self.cursor.fetchone()

        if row:
            return row["upload_timestamp"]

        return "No uploads"

    # =====================================================
    # DASHBOARD SUMMARY
    # =====================================================

    def dashboard_summary(self):

        return {

            "Gross Sales": self.gross_sales(),

            "Returns Value": self.returns_value(),

            "Net Sales": self.net_sales(),

            "Return Rate (%)": self.return_rate(),

            "Total Orders": self.total_orders(),

            "Average Order Value": self.average_order_value(),

            "Average Items / Order": self.average_items_per_order(),

            "Gross Quantity": self.gross_quantity(),

            "Net Quantity": self.net_quantity(),

            "Return Transactions": self.total_returns(),

            "Total Products": self.total_products(),

            "Total Customers": self.total_customers(),

            "Average Revenue / Customer": self.average_customer_value(),

            "Average Discount (%)": self.average_discount(),

            "Successful Uploads": self.total_uploads(),

            "Latest Upload": self.latest_upload()

        }

    # =====================================================

    def close(self):
        self.conn.close()


if __name__ == "__main__":

    engine = KPIEngine()

    print("\n" + "=" * 70)
    print("AI SALES INTELLIGENCE PLATFORM")
    print("EXECUTIVE KPI DASHBOARD")
    print("=" * 70)

    summary = engine.dashboard_summary()

    currency_fields = {
        "Gross Sales",
        "Returns Value",
        "Net Sales",
        "Average Order Value",
        "Average Revenue / Customer"
    }

    percentage_fields = {
        "Return Rate (%)",
        "Average Discount (%)"
    }

    for key, value in summary.items():

        if key in currency_fields:
            print(f"{key:<30}: \u20b9{value:,.2f}")

        elif key in percentage_fields:
            print(f"{key:<30}: {value:.2f}%")

        elif isinstance(value, float):
            print(f"{key:<30}: {value:,.2f}")

        else:
            print(f"{key:<30}: {value}")

    print("=" * 70)

    engine.close()