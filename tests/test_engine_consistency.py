from engines.kpi_engine import KPIEngine
from engines.product_engine import ProductEngine


def compare(title, kpi_value, product_value, tolerance=0.01):
    """
    Compare values between KPIEngine and ProductEngine.
    """

    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)

    if isinstance(kpi_value, float):
        difference = abs(kpi_value - product_value)

        print(f"KPI Engine     : {kpi_value:,.2f}")
        print(f"Product Engine : {product_value:,.2f}")
        print(f"Difference     : {difference:.6f}")
        print(f"Match          : {difference < tolerance}")

    else:
        print(f"KPI Engine     : {kpi_value}")
        print(f"Product Engine : {product_value}")
        print(f"Match          : {kpi_value == product_value}")


def main():

    kpi = KPIEngine()
    product = ProductEngine()

    try:

        print("=" * 80)
        print("KPI ENGINE vs PRODUCT ENGINE".center(80))
        print("=" * 80)

        # =====================================================
        # Gross Sales
        # =====================================================

        compare(
            "Gross Sales",
            kpi.gross_sales(),
            product.product_sales["revenue"].sum()
        )

        # =====================================================
        # Gross Quantity
        # =====================================================

        compare(
            "Gross Quantity",
            kpi.gross_quantity(),
            product.product_sales["quantity"].sum()
        )

        # =====================================================
        # Returns Value
        # =====================================================

        compare(
            "Returns Value",
            kpi.returns_value(),
            product.product_returns["returned_value"].sum()
        )

        # =====================================================
        # Return Transactions
        # =====================================================

        compare(
            "Return Transactions",
            kpi.total_returns(),
            product.product_returns["return_transactions"].sum()
        )

        # =====================================================
        # Product Counts
        # =====================================================

        compare(
            "Distinct Products",
            kpi.total_products(),
            len(product.product_sales)
        )

        # =====================================================
        # Summary
        # =====================================================

        print("\n" + "=" * 80)
        print("ENGINE CONSISTENCY TEST COMPLETED".center(80))
        print("=" * 80)

    finally:
        product.close()
        kpi.close()


if __name__ == "__main__":
    main()