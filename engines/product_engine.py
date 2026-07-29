from typing import Optional

import pandas as pd

from engines.base_engine import BaseEngine
from utils.constants import (
    SALE,
    RETURN,
    DEFAULT_LIMIT,
    MONTH_FORMAT,
)


class ProductEngine(BaseEngine):
    """
    Product Analytics Engine.

    Responsible for all product-level business analytics.
    """

    # =====================================================
    # Initialization
    # =====================================================

    def __init__(self):
        super().__init__()
        self.refresh()

    # =====================================================
    # Cache
    # =====================================================

    def refresh(self):
        """
        Refresh all cached datasets.

        Call this after new data is uploaded through the ETL pipeline.
        """

        self.product_sales = self._product_sales()
        self.product_returns = self._product_returns()
        self.monthly_product_sales = self._monthly_product_sales()

        # Combined product dataset
        self.product_summary = self._product_summary()

        # Contribution / Pareto analysis
        self.product_contribution = self._product_contribution()

    # =====================================================
    # Private Helpers
    # =====================================================

    def _product_summary(self) -> pd.DataFrame:
        """
        Combines sales and returns into a single dataframe.

        This cached dataframe is used by all advanced
        product intelligence reports.
        """

        summary = self.product_sales.merge(
            self.product_returns,
            how="left",
            on=["item_code", "item_name"]
        )

        summary = summary.fillna({
            "returned_quantity": 0,
            "returned_value": 0,
            "return_transactions": 0
        })

        summary["return_rate"] = (
            summary["returned_quantity"] /
            summary["quantity"]
        ) * 100

        summary["return_rate"] = (
            summary["return_rate"]
            .replace([float("inf"), -float("inf")], 0)
            .fillna(0)
            .round(2)
        )

        # Share of a product's GROSS revenue that was wiped out by
        # returns. This is what exposes products that sell a lot but
        # net almost nothing, e.g. a product returned at ~99% of its
        # gross value would look like a top seller on quantity alone
        # while contributing almost no net revenue.
        summary["return_value_rate"] = (
            summary["returned_value"] /
            summary["revenue"]
        ) * 100

        summary["return_value_rate"] = (
            summary["return_value_rate"]
            .replace([float("inf"), -float("inf")], 0)
            .fillna(0)
            .round(2)
        )

        return summary

    def _product_contribution(self) -> pd.DataFrame:
        """
        Computes each product's contribution to total quantity sold and
        total NET revenue (gross sales minus returns), along with
        cumulative contribution (used for Pareto / ABC analysis).

        Revenue contribution deliberately uses net revenue rather than
        gross revenue, so Pareto and ABC reporting reflect actual
        business value after returns rather than raw sales volume.
        """

        df = self.product_summary.copy()

        df["net_revenue"] = df["revenue"] - df["returned_value"]

        total_quantity = df["quantity"].sum()
        total_net_revenue = df["net_revenue"].sum()

        df["quantity_contribution"] = (
            df["quantity"] / total_quantity
        ) * 100

        df["net_revenue_contribution"] = (
            df["net_revenue"] / total_net_revenue
        ) * 100

        df = df.sort_values(
            "net_revenue",
            ascending=False
        ).reset_index(drop=True)

        df["cumulative_net_revenue"] = (
            df["net_revenue_contribution"]
            .cumsum()
        )

        df["cumulative_quantity"] = (
            df["quantity_contribution"]
            .cumsum()
        )

        df = df.round(2)

        # ABC classification, based on cumulative NET revenue share.
        # A wide final bin (rather than a hard 100 cap) absorbs any
        # rounding drift from cumsum-ing already-rounded percentages.
        df["abc_class"] = pd.cut(
            df["cumulative_net_revenue"],
            bins=[-float("inf"), 80, 95, float("inf")],
            labels=["A", "B", "C"]
        )

        return df

    def _validate_abc_class(self, abc_class: str) -> None:
        """
        Ensures the given ABC class is one of 'A', 'B', or 'C'.
        """

        if abc_class not in ("A", "B", "C"):
            raise ValueError(
                f"Invalid ABC class '{abc_class}'. "
                "Must be one of 'A', 'B', 'C'."
            )

    def _growth_between_periods(
        self,
        current_period: str,
        previous_period: str
    ) -> pd.DataFrame:
        """
        Builds growth metrics for every product between two
        specific periods (e.g. months, quarters, years — anything
        that matches a value in the `month` column).

        Returns a dataframe containing:
            month
            item_code
            item_name
            quantity
            revenue
            previous_quantity
            previous_revenue
            quantity_change
            revenue_change
            quantity_growth
            revenue_growth
        """

        current = (
            self.monthly_product_sales[
                self.monthly_product_sales["month"] == current_period
            ]
            .copy()
        )

        previous = (
            self.monthly_product_sales[
                self.monthly_product_sales["month"] == previous_period
            ]
            .copy()
        )

        previous = previous.rename(
            columns={
                "quantity": "previous_quantity",
                "revenue": "previous_revenue"
            }
        )

        current = current.merge(
            previous[
                [
                    "item_code",
                    "previous_quantity",
                    "previous_revenue"
                ]
            ],
            on="item_code",
            how="left"
        )

        current["previous_quantity"] = (
            current["previous_quantity"]
            .fillna(0)
        )

        current["previous_revenue"] = (
            current["previous_revenue"]
            .fillna(0)
        )

        current["quantity_change"] = (
            current["quantity"] -
            current["previous_quantity"]
        )

        current["revenue_change"] = (
            current["revenue"] -
            current["previous_revenue"]
        )

        current["quantity_growth"] = (
            current["quantity_change"] /
            current["previous_quantity"]
        ) * 100

        current["revenue_growth"] = (
            current["revenue_change"] /
            current["previous_revenue"]
        ) * 100

        current = current.replace(
            [float("inf"), -float("inf")],
            0
        ).fillna(0)

        return current.round(2)

    def _product_sales(self) -> pd.DataFrame:
        """
        Returns product-wise sales summary.
        """

        sql = """
        SELECT
            item_code,
            item_name,
            SUM(stock_qty) AS quantity,
            SUM(amount) AS revenue,
            COUNT(DISTINCT invoice) AS orders,
            AVG(rate) AS average_price
        FROM sales
        WHERE transaction_type = ?
        GROUP BY item_code, item_name
        """

        df = self.query(sql, (SALE,))

        return (
            df.sort_values(
                ["quantity", "revenue"],
                ascending=[False, False]
            )
            .reset_index(drop=True)
        )

    def _product_returns(self) -> pd.DataFrame:
        """
        Returns product-wise return summary.
        """

        sql = """
        SELECT
            item_code,
            item_name,
            ABS(SUM(stock_qty)) AS returned_quantity,
            ABS(SUM(amount)) AS returned_value,
            COUNT(*) AS return_transactions
        FROM sales
        WHERE transaction_type = ?
        GROUP BY item_code, item_name
        """

        return self.query(sql, (RETURN,))

    def _monthly_product_sales(self) -> pd.DataFrame:
        """
        Returns monthly product sales summary.
        """

        sql = f"""
        SELECT
            strftime('{MONTH_FORMAT}', posting_date) AS month,
            item_code,
            item_name,
            SUM(stock_qty) AS quantity,
            SUM(amount) AS revenue
        FROM sales
        WHERE transaction_type = ?
        GROUP BY month, item_code, item_name
        ORDER BY month
        """

        return self.query(sql, (SALE,))

    # =====================================================
    # Sales Analysis
    # =====================================================

    def top_selling_products(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the top-selling products by quantity.
        """

        self._validate_limit(limit)

        return (
            self.product_sales
            .nlargest(limit, "quantity")
            [["item_name", "quantity"]]
            .reset_index(drop=True)
        )

    def bottom_selling_products(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the lowest-selling products by quantity.
        """

        self._validate_limit(limit)

        return (
            self.product_sales
            .nsmallest(limit, "quantity")
            [["item_name", "quantity"]]
            .reset_index(drop=True)
        )

    # =====================================================
    # Revenue Analysis
    # =====================================================

    def highest_revenue_products(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the highest revenue-generating products.
        """

        self._validate_limit(limit)

        return (
            self.product_sales
            .nlargest(limit, "revenue")
            [["item_name", "revenue"]]
            .reset_index(drop=True)
        )

    def lowest_revenue_products(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the lowest revenue-generating products.
        """

        self._validate_limit(limit)

        return (
            self.product_sales
            .nsmallest(limit, "revenue")
            [["item_name", "revenue"]]
            .reset_index(drop=True)
        )

    # =====================================================
    # Return Analytics
    # =====================================================
    def highest_returned_products(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the products with the highest returned quantity.
        """

        self._validate_limit(limit)

        return (
            self.product_summary
            .nlargest(limit, "returned_quantity")
            [["item_name", "returned_quantity"]]
            .reset_index(drop=True)
        )

    def lowest_returned_products(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the products with the lowest returned quantity.
        """

        self._validate_limit(limit)

        return (
            self.product_summary
            .query("returned_quantity > 0")
            .nsmallest(limit, "returned_quantity")
            [["item_name", "returned_quantity"]]
            .reset_index(drop=True)
        )

    def highest_return_value_products(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the products with the highest return value products.
        """

        self._validate_limit(limit)

        return (
            self.product_summary
            .nlargest(limit, "returned_value")
            [["item_name", "returned_value"]]
            .reset_index(drop=True)
        )

    def lowest_return_value_products(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the products with the lowest return value products.
        """

        self._validate_limit(limit)

        return (
            self.product_summary
            .query("returned_value > 0")
            .nsmallest(limit, "returned_value")
            [["item_name", "returned_value"]]
            .reset_index(drop=True)
        )

    def return_rate_by_product(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Products with the highest percentage of returned QUANTITY
        (units returned / units sold).
        """

        self._validate_limit(limit)

        return (
            self.product_summary
            .query("quantity > 0")
            .query("returned_quantity > 0")
            .nlargest(limit, "return_rate")
            [["item_name", "return_rate"]]
            .reset_index(drop=True)
        )

    def return_value_rate_by_product(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Products with the highest percentage of GROSS REVENUE wiped
        out by returns (returned_value / revenue).

        This is a different signal than return_rate_by_product: a
        product can have a modest returned-quantity rate but a very
        high returned-value rate if the returned units were the
        expensive ones, or vice versa. It's also the fastest way to
        explain why a big-selling product isn't landing in ABC
        class 'A'.
        """

        self._validate_limit(limit)

        return (
            self.product_summary
            .query("revenue > 0")
            .query("returned_value > 0")
            .nlargest(limit, "return_value_rate")
            [[
                "item_name",
                "revenue",
                "returned_value",
                "return_value_rate"
            ]]
            .reset_index(drop=True)
        )

    # =====================================================
    # Growth Analytics
    # =====================================================
    def monthly_product_performance(
        self,
        product_code: str
    ) -> pd.DataFrame:
        """
        Returns monthly performance of a product, with month-over-month
        growth calculated directly from the historical monthly data.
        """

        df = (
            self.monthly_product_sales[
                self.monthly_product_sales["item_code"] == product_code
            ]
            .sort_values("month")
            .reset_index(drop=True)
        )

        df["previous_quantity"] = df["quantity"].shift(1)
        df["previous_revenue"] = df["revenue"].shift(1)

        df["quantity_growth"] = (
            (
                df["quantity"] -
                df["previous_quantity"]
            )
            /
            df["previous_quantity"]
        ) * 100

        df["revenue_growth"] = (
            (
                df["revenue"] -
                df["previous_revenue"]
            )
            /
            df["previous_revenue"]
        ) * 100

        for column in ["quantity_growth", "revenue_growth"]:

            df[column] = (
                df[column]
                .replace([float("inf"), -float("inf")], 0)
                .fillna(0)
                .round(2)
            )

        return (
            df[
                [
                    "month",
                    "quantity",
                    "revenue",
                    "quantity_growth",
                    "revenue_growth"
                ]
            ]
            .reset_index(drop=True)
        )

    def fastest_growing_products(
        self,
        growth: pd.DataFrame,
        limit: int = DEFAULT_LIMIT,
        minimum_previous_quantity: int = 20
    ) -> pd.DataFrame:
        """
        Returns products with the highest percentage growth.

        Expects a `growth` dataframe produced by
        `_growth_between_periods()`. Products with very small
        previous sales are ignored to avoid misleading percentages.
        """

        self._validate_limit(limit)

        growth = growth[
            growth["previous_quantity"] >=
            minimum_previous_quantity
        ]

        return (
            growth
            .nlargest(limit, "quantity_growth")
            [[
                "item_name",
                "previous_quantity",
                "quantity",
                "quantity_growth"
            ]]
            .reset_index(drop=True)
        )

    def fastest_declining_products(
        self,
        growth: pd.DataFrame,
        limit: int = DEFAULT_LIMIT,
        minimum_previous_quantity: int = 20
    ) -> pd.DataFrame:
        """
        Returns products with the largest percentage decline.

        Expects a `growth` dataframe produced by
        `_growth_between_periods()`.
        """

        self._validate_limit(limit)

        growth = growth[
            growth["previous_quantity"] >=
            minimum_previous_quantity
        ]

        return (
            growth
            .nsmallest(limit, "quantity_growth")
            [[
                "item_name",
                "previous_quantity",
                "quantity",
                "quantity_growth"
            ]]
            .reset_index(drop=True)
        )

    def biggest_volume_growth(
        self,
        growth: pd.DataFrame,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns products with the largest increase in units sold.

        Expects a `growth` dataframe produced by
        `_growth_between_periods()`.
        """

        self._validate_limit(limit)

        return (
            growth
            .nlargest(limit, "quantity_change")
            [[
                "item_name",
                "quantity_change"
            ]]
            .reset_index(drop=True)
        )

    def biggest_revenue_growth(
        self,
        growth: pd.DataFrame,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns products with the largest increase in revenue.

        Expects a `growth` dataframe produced by
        `_growth_between_periods()`.
        """

        self._validate_limit(limit)

        return (
            growth
            .nlargest(limit, "revenue_change")
            [[
                "item_name",
                "revenue_change"
            ]]
            .reset_index(drop=True)
        )

    def product_growth(
        self,
        product_code: str
    ) -> pd.DataFrame:
        """
        Alias for monthly product performance.
        """

        return self.monthly_product_performance(product_code)

    # =====================================================
    # Contribution Analytics
    # =====================================================

    def highest_revenue_contributors(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the products contributing the most to total NET revenue.
        """

        self._validate_limit(limit)

        return (
            self.product_contribution
            .nlargest(limit, "net_revenue_contribution")
            [[
                "item_name",
                "net_revenue",
                "net_revenue_contribution"
            ]]
            .reset_index(drop=True)
        )

    def highest_sales_contributors(
        self,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the products contributing the most to total quantity sold.
        """

        self._validate_limit(limit)

        return (
            self.product_contribution
            .nlargest(limit, "quantity_contribution")
            [[
                "item_name",
                "quantity",
                "quantity_contribution"
            ]]
            .reset_index(drop=True)
        )

    def contribution_by_product(
        self,
        product_code: str
    ) -> pd.DataFrame:
        """
        Returns the contribution breakdown for a single product.
        """

        return (
            self.product_contribution[
                self.product_contribution["item_code"] == product_code
            ][[
                "item_name",
                "quantity_contribution",
                "net_revenue",
                "net_revenue_contribution",
                "cumulative_net_revenue"
            ]]
            .reset_index(drop=True)
        )

    def pareto_products(self) -> pd.DataFrame:
        """
        Products responsible for roughly 80% of NET revenue.
        """

        return (
            self.product_contribution[
                self.product_contribution[
                    "cumulative_net_revenue"
                ] <= 80
            ][[
                "item_name",
                "net_revenue",
                "net_revenue_contribution",
                "cumulative_net_revenue"
            ]]
            .reset_index(drop=True)
        )

    def pareto_summary(self) -> pd.DataFrame:
        """
        Executive-level summary of the Pareto (80% revenue) breakdown:
        how many products it actually takes to reach 80% of revenue,
        out of the total product catalog.
        """

        total_products = len(self.product_contribution)
        products_for_80 = len(self.pareto_products())
        remaining_products = total_products - products_for_80

        percentage_of_products = (
            round((products_for_80 / total_products) * 100, 2)
            if total_products
            else 0
        )

        return pd.DataFrame({
            "metric": [
                "Total Products",
                "Products Contributing To 80% Revenue",
                "Percentage Of Products",
                "Remaining Products"
            ],
            "value": [
                total_products,
                products_for_80,
                percentage_of_products,
                remaining_products
            ]
        })

    def product_contribution_summary(self) -> pd.DataFrame:
        """
        Concise executive summary of overall contribution metrics,
        based on NET revenue (gross sales minus returns).
        """

        total_net_revenue = self.product_contribution["net_revenue"].sum()
        total_quantity = self.product_sales["quantity"].sum()

        top_revenue_contribution = (
            self.product_contribution["net_revenue_contribution"].max()
        )

        top_quantity_contribution = (
            self.product_contribution["quantity_contribution"].max()
        )

        products_for_80 = len(self.pareto_products())

        return pd.DataFrame({
            "metric": [
                "Total Net Revenue",
                "Total Quantity",
                "Top Product Net Revenue Contribution",
                "Top Product Quantity Contribution",
                "Products Needed For 80%"
            ],
            "value": [
                total_net_revenue,
                total_quantity,
                top_revenue_contribution,
                top_quantity_contribution,
                products_for_80
            ]
        })

    # =====================================================
    # ABC Analysis
    # =====================================================

    def abc_summary(self) -> pd.DataFrame:
        """
        Returns product count, net revenue, and quantity totals for
        each ABC class (A: 0-80%, B: 80-95%, C: 95-100% cumulative
        NET revenue).
        """

        summary = (
            self.product_contribution
            .groupby("abc_class", observed=True)
            .agg(
                product_count=("item_code", "count"),
                total_net_revenue=("net_revenue", "sum"),
                total_quantity=("quantity", "sum")
            )
            .reindex(["A", "B", "C"])
            .reset_index()
        )

        summary["net_revenue_share"] = (
            summary["total_net_revenue"] /
            summary["total_net_revenue"].sum() * 100
        ).round(2)

        summary["quantity_share"] = (
            summary["total_quantity"] /
            summary["total_quantity"].sum() * 100
        ).round(2)

        return summary

    def products_by_class(
        self,
        abc_class: str
    ) -> pd.DataFrame:
        """
        Returns all products belonging to a given ABC class.
        """

        abc_class = abc_class.upper()
        self._validate_abc_class(abc_class)

        return (
            self.product_contribution
            .query("abc_class == @abc_class")
            [[
                "item_name",
                "net_revenue",
                "net_revenue_contribution",
                "cumulative_net_revenue"
            ]]
            .reset_index(drop=True)
        )

    def top_products_by_class(
        self,
        abc_class: str,
        limit: int = DEFAULT_LIMIT
    ) -> pd.DataFrame:
        """
        Returns the top revenue-generating products within a
        given ABC class.
        """

        abc_class = abc_class.upper()
        self._validate_abc_class(abc_class)
        self._validate_limit(limit)

        return (
            self.product_contribution
            .query("abc_class == @abc_class")
            .nlargest(limit, "net_revenue")
            [[
                "item_name",
                "net_revenue",
                "net_revenue_contribution"
            ]]
            .reset_index(drop=True)
        )

    def revenue_by_class(self, abc_class: str) -> float:
        """
        Returns total NET revenue generated by a given ABC class.
        """

        abc_class = abc_class.upper()
        self._validate_abc_class(abc_class)

        return round(
            self.product_contribution
            .query("abc_class == @abc_class")["net_revenue"]
            .sum(),
            2
        )

    def quantity_by_class(self, abc_class: str) -> float:
        """
        Returns total quantity sold by a given ABC class.
        """

        abc_class = abc_class.upper()
        self._validate_abc_class(abc_class)

        return (
            self.product_contribution
            .query("abc_class == @abc_class")["quantity"]
            .sum()
        )

    def class_of_product(self, product_code: str) -> Optional[str]:
        """
        Returns the ABC class ('A', 'B', or 'C') of a single product,
        or None if the product code isn't found.
        """

        match = self.product_contribution[
            self.product_contribution["item_code"] == product_code
        ]

        if match.empty:
            return None

        return str(match.iloc[0]["abc_class"])

    # =====================================================
    # Product Lookup
    # =====================================================

    def product_details(self, product_code: str) -> pd.DataFrame:
        """
        Returns all transactions for a given product.
        """

        sql = """
        SELECT
            invoice,
            posting_date,
            customer,
            stock_qty,
            rate,
            amount,
            transaction_type
        FROM sales
        WHERE item_code = ?
        ORDER BY posting_date
        """

        return self.query(sql, (product_code,))