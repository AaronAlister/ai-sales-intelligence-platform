import pandas as pd

from engines.product_engine import ProductEngine

# =====================================================
# Pandas Display Settings
# =====================================================

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 60)


def print_header(title):
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)


def print_dataframe(title, df):
    print(f"\n{title}")
    print("-" * len(title))

    if df.empty:
        print("No data found.")
    else:
        print(df.to_string(index=False))


def main():

    engine = ProductEngine()

    try:

        # =====================================================
        # Cache Verification
        # =====================================================

        print_header("CACHE VERIFICATION")

        print(f"Product Sales Records : {len(engine.product_sales)}")
        print(f"Product Return Records: {len(engine.product_returns)}")
        print(f"Monthly Records       : {len(engine.monthly_product_sales)}")

        # =====================================================
        # Sales Analysis
        # =====================================================

        print_header("SALES ANALYSIS")

        top_products = engine.top_selling_products().copy()
        bottom_products = engine.bottom_selling_products().copy()

        # Format quantity
        top_products["quantity"] = top_products["quantity"].map(
            lambda x: f"{x:,.0f}"
        )

        bottom_products["quantity"] = bottom_products["quantity"].map(
            lambda x: f"{x:,.0f}"
        )

        print_dataframe(
            "Top Selling Products",
            top_products
        )

        print_dataframe(
            "Bottom Selling Products",
            bottom_products
        )

        # =====================================================
        # Revenue Analysis
        # =====================================================

        print_header("REVENUE ANALYSIS")

        highest_revenue = engine.highest_revenue_products().copy()
        lowest_revenue = engine.lowest_revenue_products().copy()

        # Format revenue
        highest_revenue["revenue"] = highest_revenue["revenue"].map(
            lambda x: f"₹{x:,.2f}"
        )

        lowest_revenue["revenue"] = lowest_revenue["revenue"].map(
            lambda x: f"₹{x:,.2f}"
        )

        print_dataframe(
            "Highest Revenue Products",
            highest_revenue
        )

        print_dataframe(
            "Lowest Revenue Products",
            lowest_revenue
        )

        # =====================================================
        # Return Analytics
        # =====================================================

        print_header("RETURN ANALYSIS")

        highest_returns = engine.highest_returned_products().copy()
        lowest_returns = engine.lowest_returned_products().copy()
        highest_return_value = engine.highest_return_value_products().copy()
        lowest_return_value = engine.lowest_return_value_products().copy()
        return_rate = engine.return_rate_by_product().copy()
        return_value_rate = engine.return_value_rate_by_product().copy()

        highest_returns["returned_quantity"] = (
            highest_returns["returned_quantity"]
            .map(lambda x: f"{x:,.0f}")
        )

        lowest_returns["returned_quantity"] = (
            lowest_returns["returned_quantity"]
            .map(lambda x: f"{x:,.0f}")
        )

        highest_return_value["returned_value"] = (
            highest_return_value["returned_value"]
            .map(lambda x: f"₹{x:,.2f}")
        )

        lowest_return_value["returned_value"] = (
            lowest_return_value["returned_value"]
            .map(lambda x: f"₹{x:,.2f}")
        )

        return_rate["return_rate"] = (
            return_rate["return_rate"]
            .map(lambda x: f"{x:.2f}%")
        )

        return_value_rate["revenue"] = (
            return_value_rate["revenue"]
            .map(lambda x: f"₹{x:,.2f}")
        )

        return_value_rate["returned_value"] = (
            return_value_rate["returned_value"]
            .map(lambda x: f"₹{x:,.2f}")
        )

        return_value_rate["return_value_rate"] = (
            return_value_rate["return_value_rate"]
            .map(lambda x: f"{x:.2f}%")
        )

        print_dataframe(
            "Highest Returned Products",
            highest_returns
        )

        print_dataframe(
            "Lowest Returned Products",
            lowest_returns
        )

        print_dataframe(
            "Highest Return Value Products",
            highest_return_value
        )

        print_dataframe(
            "Lowest Return Value Products",
            lowest_return_value
        )

        print_dataframe(
            "Highest Return Rate (By Quantity)",
            return_rate
        )

        print_dataframe(
            "Highest Return Value Rate",
            return_value_rate
        )

        # =====================================================
        # Growth Analytics
        # =====================================================

        print_header("GROWTH ANALYSIS")

        CURRENT_PERIOD = "2026-07"
        PREVIOUS_PERIOD = "2026-06"

        growth = engine._growth_between_periods(
            current_period=CURRENT_PERIOD,
            previous_period=PREVIOUS_PERIOD
        )

        growing = engine.fastest_growing_products(growth).copy()
        declining = engine.fastest_declining_products(growth).copy()

        growing["quantity_growth"] = (
            growing["quantity_growth"]
            .map(lambda x: f"{x:.2f}%")
        )

        declining["quantity_growth"] = (
            declining["quantity_growth"]
            .map(lambda x: f"{x:.2f}%")
        )

        print_dataframe(
            "Fastest Growing Products",
            growing
        )

        print_dataframe(
            "Fastest Declining Products",
            declining
        )

        volume_growth = engine.biggest_volume_growth(growth).copy()
        revenue_growth = engine.biggest_revenue_growth(growth).copy()

        volume_growth["quantity_change"] = (
            volume_growth["quantity_change"]
            .map(lambda x: f"{x:,.0f}")
        )

        revenue_growth["revenue_change"] = (
            revenue_growth["revenue_change"]
            .map(lambda x: f"₹{x:,.2f}")
        )

        print_dataframe(
            "Biggest Volume Growth",
            volume_growth
        )

        print_dataframe(
            "Biggest Revenue Growth",
            revenue_growth
        )

        # =====================================================
        # Monthly Product Performance
        # =====================================================

        sample_product = (
            engine.product_sales
            .iloc[0]["item_code"]
        )

        print_header("MONTHLY PRODUCT PERFORMANCE")

        monthly = engine.monthly_product_performance(
            sample_product
        ).copy()

        monthly["revenue"] = monthly["revenue"].map(
            lambda x: f"₹{x:,.2f}"
        )

        monthly["quantity_growth"] = (
            monthly["quantity_growth"]
            .map(lambda x: f"{x:.2f}%")
        )

        monthly["revenue_growth"] = (
            monthly["revenue_growth"]
            .map(lambda x: f"{x:.2f}%")
        )

        print(f"\nProduct Code : {sample_product}")

        print_dataframe(
            "Monthly Performance",
            monthly
        )

        # =====================================================
        # Product Contribution
        # =====================================================

        print_header("PRODUCT CONTRIBUTION")

        revenue = engine.highest_revenue_contributors().copy()

        revenue["net_revenue"] = revenue["net_revenue"].map(
            lambda x: f"₹{x:,.2f}"
        )

        revenue["net_revenue_contribution"] = (
            revenue["net_revenue_contribution"]
            .map(lambda x: f"{x:.2f}%")
        )

        print_dataframe(
            "Highest Revenue Contributors",
            revenue
        )

        sales = engine.highest_sales_contributors().copy()

        sales["quantity"] = (
            sales["quantity"]
            .map(lambda x: f"{x:,.0f}")
        )

        sales["quantity_contribution"] = (
            sales["quantity_contribution"]
            .map(lambda x: f"{x:.2f}%")
        )

        print_dataframe(
            "Highest Sales Contributors",
            sales
        )

        pareto_summary = engine.pareto_summary().copy()

        pareto_summary["value"] = pareto_summary.apply(
            lambda row: (
                f"{row['value']:.2f}%"
                if "Percentage" in row["metric"]
                else f"{row['value']:,}"
            ),
            axis=1
        )

        print_dataframe(
            "Pareto Summary (80% Revenue)",
            pareto_summary
        )

        contribution_summary = engine.product_contribution_summary().copy()

        def _format_contribution_summary_value(row):
            metric = row["metric"]
            value = row["value"]

            if metric == "Total Net Revenue":
                return f"₹{value:,.2f}"
            if "Contribution" in metric:
                return f"{value:.2f}%"
            return f"{value:,.0f}"

        contribution_summary["value"] = contribution_summary.apply(
            _format_contribution_summary_value,
            axis=1
        )

        print_dataframe(
            "Product Contribution Summary",
            contribution_summary
        )

        # =====================================================
        # ABC Analysis
        # =====================================================

        print_header("ABC ANALYSIS")

        abc_summary = engine.abc_summary().copy()

        abc_summary["total_net_revenue"] = (
            abc_summary["total_net_revenue"]
            .map(lambda x: f"₹{x:,.2f}")
        )

        abc_summary["total_quantity"] = (
            abc_summary["total_quantity"]
            .map(lambda x: f"{x:,.0f}")
        )

        abc_summary["net_revenue_share"] = (
            abc_summary["net_revenue_share"]
            .map(lambda x: f"{x:.2f}%")
        )

        abc_summary["quantity_share"] = (
            abc_summary["quantity_share"]
            .map(lambda x: f"{x:.2f}%")
        )

        print_dataframe(
            "ABC Class Summary",
            abc_summary
        )

        top_a_products = engine.top_products_by_class("A").copy()

        top_a_products["net_revenue"] = (
            top_a_products["net_revenue"]
            .map(lambda x: f"₹{x:,.2f}")
        )

        top_a_products["net_revenue_contribution"] = (
            top_a_products["net_revenue_contribution"]
            .map(lambda x: f"{x:.2f}%")
        )

        print_dataframe(
            "Top 'A' Class Products",
            top_a_products
        )

        # =====================================================
        # Success
        # =====================================================

        print("\n" + "=" * 80)
        print("PRODUCT ENGINE TEST PASSED".center(80))
        print("=" * 80)

    finally:
        engine.close()


if __name__ == "__main__":
    main()