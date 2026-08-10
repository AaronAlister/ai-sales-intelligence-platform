import sqlite3
import pandas as pd
from pathlib import Path


class RegionalEngine:

    def __init__(self, db_path="data/sales.db"):
        self.db_path = Path(db_path)

    # =====================================================
    # DATABASE CONNECTION
    # =====================================================

    def _get_connection(self):
        """
        Creates and returns a connection to the SQLite database.
        """
        return sqlite3.connect(self.db_path)

    # =====================================================
    # LOAD SALES DATA
    # =====================================================

    def _load_sales_data(self):
        """
        Loads the required sales data from the database.
        """

        query = """
        SELECT
            invoice,
            customer,
            place_of_supply,
            stock_qty,
            amount,
            posting_date
        FROM sales
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        return df

    # =====================================================
    # CLEAN REGIONAL DATA
    # =====================================================

    def _clean_region_data(self, df):
        """
        Cleans and standardizes regional sales data.
        """

        df = df.dropna(
            subset=["place_of_supply"]
        ).copy()

        # -------------------------------------------------
        # Clean region names
        # -------------------------------------------------

        df["place_of_supply"] = (
            df["place_of_supply"]
            .astype(str)
            .str.strip()
        )

        # Standardize Puducherry naming
        df["place_of_supply"] = (
            df["place_of_supply"]
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry"
                }
            )
        )

        # -------------------------------------------------
        # Convert numeric columns
        # -------------------------------------------------

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

        df["stock_qty"] = pd.to_numeric(
            df["stock_qty"],
            errors="coerce"
        ).fillna(0)

        return df

        # =====================================================
    # GET AVAILABLE REGIONS
    # =====================================================

    def get_regions(self):
        """
        Returns a list of all available regions.

        Used by the dashboard to populate
        the region selection dropdown.
        """

        query = """
        SELECT DISTINCT place_of_supply
        FROM sales
        WHERE place_of_supply IS NOT NULL
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        regions = (
            df["place_of_supply"]
            .astype(str)
            .str.strip()
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry"
                }
            )
            .drop_duplicates()
            .sort_values()
            .tolist()
        )

        return regions

    # =====================================================
    # 1. REGION SUMMARY
    # =====================================================

    def region_summary(self):
        """
        Returns overall sales performance for every region.

        Metrics:
        - Revenue
        - Quantity
        - Orders
        - Customers

        Sorted by revenue from highest to lowest.
        """

        df = self._load_sales_data()
        df = self._clean_region_data(df)

        summary = (
            df.groupby("place_of_supply")
            .agg(
                Revenue=("amount", "sum"),
                Quantity=("stock_qty", "sum"),
                Orders=("invoice", "nunique"),
                Customers=("customer", "nunique")
            )
            .reset_index()
        )

        summary.rename(
            columns={
                "place_of_supply": "Region"
            },
            inplace=True
        )

        # Highest revenue first
        summary = summary.sort_values(
            by="Revenue",
            ascending=False
        ).reset_index(drop=True)

        # Add rank
        summary.insert(
            0,
            "Rank",
            range(1, len(summary) + 1)
        )

        return summary

    # =====================================================
    # 2. TOP REGIONS BY REVENUE
    # =====================================================

    def top_regions_by_revenue(self, n=10):
        """
        Returns the top-performing regions by revenue.

        Sorted from highest to lowest revenue.
        """

        summary = self.region_summary()

        result = (
            summary[
                [
                    "Rank",
                    "Region",
                    "Revenue"
                ]
            ]
            .head(n)
            .reset_index(drop=True)
        )

        # Re-rank within the returned result
        result["Rank"] = range(1, len(result) + 1)

        return result

    # =====================================================
    # 3. TOP REGIONS BY QUANTITY
    # =====================================================

    def top_regions_by_quantity(self, n=10):
        """
        Returns the top regions by quantity sold.

        Sorted from highest to lowest quantity.
        """

        summary = self.region_summary()

        result = (
            summary[
                [
                    "Region",
                    "Quantity"
                ]
            ]
            .sort_values(
                by="Quantity",
                ascending=False
            )
            .head(n)
            .reset_index(drop=True)
        )

        # Add rank based on quantity
        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

    # =====================================================
    # 4. TOP REGIONS BY ORDERS
    # =====================================================

    def top_regions_by_orders(self, n=10):
        """
        Returns the top regions by number of orders.

        Sorted from highest to lowest orders.
        """

        summary = self.region_summary()

        result = (
            summary[
                [
                    "Region",
                    "Orders"
                ]
            ]
            .sort_values(
                by="Orders",
                ascending=False
            )
            .head(n)
            .reset_index(drop=True)
        )

        # Add rank based on orders
        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

    # =====================================================
    # 5. WEAK REGIONS
    # =====================================================

    def weak_regions(self, metric="Revenue", n=10):
        """
        Returns the weakest-performing regions.

        Parameters:
            metric:
                Revenue
                Quantity
                Orders

            n:
                Number of weak regions to return.

        Results are sorted from weakest to strongest.
        """

        valid_metrics = [
            "Revenue",
            "Quantity",
            "Orders"
        ]

        if metric not in valid_metrics:
            raise ValueError(
                f"Invalid metric '{metric}'. "
                f"Choose from: {valid_metrics}"
            )

        summary = self.region_summary()

        result = (
            summary[
                [
                    "Region",
                    metric
                ]
            ]
            .sort_values(
                by=metric,
                ascending=True
            )
            .head(n)
            .reset_index(drop=True)
        )

        # Add rank based on weakness
        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

            # =====================================================
    # PHASE 2: REGIONAL DEMAND
    # =====================================================

    # =====================================================
    # 6. PRODUCT DEMAND BY REGION
    # =====================================================

    def product_demand_by_region(self):
        """
        Returns product demand across every region.

        Shows:
        - Region
        - Product
        - Quantity

        Sorted by region and quantity sold.
        """

        df = self._load_sales_data()

        # We need product information for Phase 2
        # so reload the required product columns.
        query = """
        SELECT
            item_code,
            item_name,
            place_of_supply,
            stock_qty,
            amount,
            invoice
        FROM sales
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        # -------------------------------------------------
        # Clean regional data
        # -------------------------------------------------

        df = df.dropna(
            subset=[
                "place_of_supply",
                "item_name"
            ]
        ).copy()

        # Clean region names
        df["place_of_supply"] = (
            df["place_of_supply"]
            .astype(str)
            .str.strip()
        )

        # Standardize Puducherry
        df["place_of_supply"] = (
            df["place_of_supply"]
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry"
                }
            )
        )

        # Clean product names
        df["item_name"] = (
            df["item_name"]
            .astype(str)
            .str.strip()
        )

        # Convert quantity
        df["stock_qty"] = pd.to_numeric(
            df["stock_qty"],
            errors="coerce"
        ).fillna(0)

        # -------------------------------------------------
        # Aggregate
        # -------------------------------------------------

        result = (
            df.groupby(
                [
                    "place_of_supply",
                    "item_name"
                ]
            )
            .agg(
                Quantity=("stock_qty", "sum")
            )
            .reset_index()
        )

        result.rename(
            columns={
                "place_of_supply": "Region",
                "item_name": "Product"
            },
            inplace=True
        )

        # Highest quantity within each region
        result = result.sort_values(
            by=[
                "Region",
                "Quantity"
            ],
            ascending=[
                True,
                False
            ]
        ).reset_index(drop=True)

        return result

    # =====================================================
    # 7. TOP PRODUCTS BY REGION
    # =====================================================

    def top_products_by_region(self, region_name, n=10):
        """
        Returns the top products in a specific region.

        Parameters:
            region_name:
                Name of the region.

            n:
                Number of products to return.

        Ranking is based on quantity sold.
        """

        df = self._load_sales_data()

        query = """
        SELECT
            item_code,
            item_name,
            place_of_supply,
            stock_qty,
            amount,
            invoice
        FROM sales
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        # -------------------------------------------------
        # Clean data
        # -------------------------------------------------

        df = df.dropna(
            subset=[
                "place_of_supply",
                "item_name"
            ]
        ).copy()

        df["place_of_supply"] = (
            df["place_of_supply"]
            .astype(str)
            .str.strip()
        )

        df["place_of_supply"] = (
            df["place_of_supply"]
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry"
                }
            )
        )

        df["item_name"] = (
            df["item_name"]
            .astype(str)
            .str.strip()
        )

        df["stock_qty"] = pd.to_numeric(
            df["stock_qty"],
            errors="coerce"
        ).fillna(0)

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

        # -------------------------------------------------
        # Standardize requested region
        # -------------------------------------------------

        region_name = str(region_name).strip()

        if region_name == "34-Pondicherry":
            region_name = "34-Puducherry"

        # -------------------------------------------------
        # Filter region
        # -------------------------------------------------

        region_df = df[
            df["place_of_supply"] == region_name
        ].copy()

        if region_df.empty:
            raise ValueError(
                f"Region '{region_name}' was not found."
            )

        # -------------------------------------------------
        # Aggregate products
        # -------------------------------------------------

        result = (
            region_df.groupby("item_name")
            .agg(
                Quantity=("stock_qty", "sum"),
                Revenue=("amount", "sum"),
                Orders=("invoice", "nunique")
            )
            .reset_index()
        )

        result.rename(
            columns={
                "item_name": "Product"
            },
            inplace=True
        )

        # Highest quantity first
        result = (
            result
            .sort_values(
                by="Quantity",
                ascending=False
            )
            .head(n)
            .reset_index(drop=True)
        )

        # Add rank
        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

    # =====================================================
    # 8. REGIONAL PRODUCT PERFORMANCE
    # =====================================================

    def regional_product_performance(self, region_name):
        """
        Returns product performance for a selected region.

        Metrics:
        - Product
        - Revenue
        - Quantity
        - Orders

        Parameters:
            region_name:
                Region to analyze.

        Results are sorted by revenue from highest
        to lowest.
        """

        query = """
        SELECT
            item_code,
            item_name,
            place_of_supply,
            stock_qty,
            amount,
            invoice
        FROM sales
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        # -------------------------------------------------
        # Clean data
        # -------------------------------------------------

        df = df.dropna(
            subset=[
                "place_of_supply",
                "item_name"
            ]
        ).copy()

        # -------------------------------------------------
        # Clean region names
        # -------------------------------------------------

        df["place_of_supply"] = (
            df["place_of_supply"]
            .astype(str)
            .str.strip()
        )

        # Standardize Puducherry
        df["place_of_supply"] = (
            df["place_of_supply"]
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry"
                }
            )
        )

        # -------------------------------------------------
        # Clean product names
        # -------------------------------------------------

        df["item_name"] = (
            df["item_name"]
            .astype(str)
            .str.strip()
        )

        # -------------------------------------------------
        # Convert numeric columns
        # -------------------------------------------------

        df["stock_qty"] = pd.to_numeric(
            df["stock_qty"],
            errors="coerce"
        ).fillna(0)

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

        # -------------------------------------------------
        # Standardize selected region
        # -------------------------------------------------

        region_name = str(region_name).strip()

        if region_name == "34-Pondicherry":
            region_name = "34-Puducherry"

        # -------------------------------------------------
        # Filter selected region
        # -------------------------------------------------

        region_df = df[
            df["place_of_supply"] == region_name
        ].copy()

        if region_df.empty:
            raise ValueError(
                f"Region '{region_name}' was not found."
            )

        # -------------------------------------------------
        # Aggregate product performance
        # -------------------------------------------------

        result = (
            region_df
            .groupby("item_name")
            .agg(
                Revenue=("amount", "sum"),
                Quantity=("stock_qty", "sum"),
                Orders=("invoice", "nunique")
            )
            .reset_index()
        )

        # Rename product column
        result.rename(
            columns={
                "item_name": "Product"
            },
            inplace=True
        )

        # -------------------------------------------------
        # Sort by revenue
        # -------------------------------------------------

        result = (
            result
            .sort_values(
                by="Revenue",
                ascending=False
            )
            .reset_index(drop=True)
        )

        # -------------------------------------------------
        # Add rank
        # -------------------------------------------------

        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

            # =====================================================
    # PHASE 3: REGIONAL GROWTH
    # =====================================================

    # =====================================================
    # 9. MONTHLY REGIONAL SALES
    # =====================================================

    def monthly_regional_sales(self):
        """
        Returns monthly revenue for every region.

        Metrics:
        - Month
        - Region
        - Revenue

        Results are sorted chronologically and then
        by revenue from highest to lowest.
        """

        query = """
        SELECT
            place_of_supply,
            posting_date,
            amount
        FROM sales
        WHERE
            place_of_supply IS NOT NULL
            AND posting_date IS NOT NULL
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        # -------------------------------------------------
        # Clean data
        # -------------------------------------------------

        df = df.copy()

        # Clean region names
        df["place_of_supply"] = (
            df["place_of_supply"]
            .astype(str)
            .str.strip()
        )

        # Standardize Puducherry
        df["place_of_supply"] = (
            df["place_of_supply"]
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry"
                }
            )
        )

        # Convert date
        df["posting_date"] = pd.to_datetime(
            df["posting_date"],
            errors="coerce"
        )

        # Convert revenue
        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

        # Remove invalid dates
        df = df.dropna(
            subset=["posting_date"]
        )

        # -------------------------------------------------
        # Create monthly period
        # -------------------------------------------------

        df["Month"] = (
            df["posting_date"]
            .dt.to_period("M")
            .astype(str)
        )

        # -------------------------------------------------
        # Aggregate monthly regional revenue
        # -------------------------------------------------

        result = (
            df.groupby(
                [
                    "Month",
                    "place_of_supply"
                ]
            )
            .agg(
                Revenue=("amount", "sum")
            )
            .reset_index()
        )

        result.rename(
            columns={
                "place_of_supply": "Region"
            },
            inplace=True
        )

        # Sort chronologically
        result = (
            result
            .sort_values(
                by=[
                    "Month",
                    "Revenue"
                ],
                ascending=[
                    True,
                    False
                ]
            )
            .reset_index(drop=True)
        )

        return result

    # =====================================================
    # 10. REGIONAL GROWTH
    # =====================================================

    def regional_growth(self):
        """
        Calculates month-over-month revenue growth
        for every region.

        Metrics:
        - Region
        - Previous Month Revenue
        - Current Month Revenue
        - Growth Amount
        - Growth Percentage

        The comparison is between each region's
        latest two available months.
        """

        monthly = self.monthly_regional_sales()

        if monthly.empty:
            return pd.DataFrame(
                columns=[
                    "Region",
                    "Previous Month",
                    "Current Month",
                    "Previous Revenue",
                    "Current Revenue",
                    "Growth Amount",
                    "Growth %"
                ]
            )

        # -------------------------------------------------
        # Get latest two months
        # -------------------------------------------------

        months = sorted(
            monthly["Month"].unique()
        )

        if len(months) < 2:
            return pd.DataFrame(
                columns=[
                    "Region",
                    "Previous Month",
                    "Current Month",
                    "Previous Revenue",
                    "Current Revenue",
                    "Growth Amount",
                    "Growth %"
                ]
            )

        previous_month = months[-2]
        current_month = months[-1]

        # -------------------------------------------------
        # Filter latest two months
        # -------------------------------------------------

        comparison = monthly[
            monthly["Month"].isin(
                [
                    previous_month,
                    current_month
                ]
            )
        ].copy()

        # -------------------------------------------------
        # Pivot months into columns
        # -------------------------------------------------

        pivot = (
            comparison
            .pivot(
                index="Region",
                columns="Month",
                values="Revenue"
            )
            .reset_index()
        )

        # Make sure both months exist as columns
        if previous_month not in pivot.columns:
            pivot[previous_month] = 0

        if current_month not in pivot.columns:
            pivot[current_month] = 0

        # -------------------------------------------------
        # Rename columns
        # -------------------------------------------------

        pivot.rename(
            columns={
                previous_month: "Previous Revenue",
                current_month: "Current Revenue"
            },
            inplace=True
        )

        # -------------------------------------------------
        # Missing values mean no sales
        # -------------------------------------------------

        pivot["Previous Revenue"] = (
            pivot["Previous Revenue"]
            .fillna(0)
        )

        pivot["Current Revenue"] = (
            pivot["Current Revenue"]
            .fillna(0)
        )

        # -------------------------------------------------
        # Growth calculation
        # -------------------------------------------------

        pivot["Growth Amount"] = (
            pivot["Current Revenue"]
            - pivot["Previous Revenue"]
        )

        # -------------------------------------------------
        # Growth percentage
        # -------------------------------------------------

        pivot["Growth %"] = 0.0

        previous_revenue = (
            pivot["Previous Revenue"] != 0
        )

        pivot.loc[
            previous_revenue,
            "Growth %"
        ] = (
            (
                pivot.loc[
                    previous_revenue,
                    "Current Revenue"
                ]
                -
                pivot.loc[
                    previous_revenue,
                    "Previous Revenue"
                ]
            )
            /
            pivot.loc[
                previous_revenue,
                "Previous Revenue"
            ]
        ) * 100

        # -------------------------------------------------
        # Handle new regions
        # -------------------------------------------------

        new_regions = (
            pivot["Previous Revenue"] == 0
        ) & (
            pivot["Current Revenue"] > 0
        )

        pivot.loc[
            new_regions,
            "Growth %"
        ] = float("inf")

        # -------------------------------------------------
        # Add comparison months
        # -------------------------------------------------

        pivot.insert(
            1,
            "Previous Month",
            previous_month
        )

        pivot.insert(
            2,
            "Current Month",
            current_month
        )

        # -------------------------------------------------
        # Final column order
        # -------------------------------------------------

        result = pivot[
            [
                "Region",
                "Previous Month",
                "Current Month",
                "Previous Revenue",
                "Current Revenue",
                "Growth Amount",
                "Growth %"
            ]
        ]

        # Sort by growth
        result = (
            result
            .sort_values(
                by="Growth %",
                ascending=False
            )
            .reset_index(drop=True)
        )

        return result

    # =====================================================
    # 11. FASTEST GROWING REGIONS
    # =====================================================

    def fastest_growing_regions(
        self,
        n=10,
        min_previous_revenue=100000
    ):
        """
        Returns the fastest-growing regions by
        month-over-month revenue growth percentage.

        Parameters:
            n:
                Number of fastest-growing regions to return.

            min_previous_revenue:
                Minimum previous-month revenue required for
                a region to be considered.

        This prevents very small or newly active regions
        from dominating the ranking with inflated growth
        percentages driven by a tiny revenue base.
        """

        growth = self.regional_growth()

        if growth.empty:
            return growth

        result = growth[
            (growth["Growth %"] > 0)
            & (
                growth["Previous Revenue"]
                >= min_previous_revenue
            )
        ].copy()

        result = (
            result
            .sort_values(
                by="Growth %",
                ascending=False
            )
            .head(n)
            .reset_index(drop=True)
        )

        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

    # =====================================================
    # 12. DECLINING REGIONS
    # =====================================================

    def declining_regions(
        self,
        n=10,
        min_current_revenue=100000
    ):
        """
        Returns regions with negative month-over-month
        revenue growth.

        Parameters:
            n:
                Number of declining regions to return.

            min_current_revenue:
                Minimum current-month revenue required
                for a region to be considered.

        This prevents very small regions or regions with
        zero current-month sales from dominating the
        declining-region ranking.
        """

        growth = self.regional_growth()

        if growth.empty:
            return growth

        result = growth[
            (growth["Growth %"] < 0)
            & (
                growth["Current Revenue"]
                >= min_current_revenue
            )
        ].copy()

        result = (
            result
            .sort_values(
                by="Growth %",
                ascending=True
            )
            .head(n)
            .reset_index(drop=True)
        )

        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

    # =====================================================
    # PHASE 4: REGIONAL CONTRIBUTION
    # =====================================================

    # =====================================================
    # 13. REGIONAL CONTRIBUTION
    # =====================================================

    def regional_contribution(self):
        """
        Calculates each region's contribution to total revenue.

        Metrics:
        - Region
        - Revenue
        - Revenue Contribution %
        - Cumulative Contribution %

        Results are sorted by revenue from highest
        to lowest.
        """

        summary = self.region_summary().copy()

        if summary.empty:
            return pd.DataFrame(
                columns=[
                    "Rank",
                    "Region",
                    "Revenue",
                    "Revenue Contribution %",
                    "Cumulative Contribution %"
                ]
            )

        # -------------------------------------------------
        # Total revenue
        # -------------------------------------------------

        total_revenue = summary["Revenue"].sum()

        # -------------------------------------------------
        # Revenue contribution percentage
        # -------------------------------------------------

        if total_revenue == 0:
            summary["Revenue Contribution %"] = 0.0
        else:
            summary["Revenue Contribution %"] = (
                summary["Revenue"]
                / total_revenue
            ) * 100

        # -------------------------------------------------
        # Cumulative contribution
        # -------------------------------------------------

        summary["Cumulative Contribution %"] = (
            summary["Revenue Contribution %"]
            .cumsum()
        )

        # -------------------------------------------------
        # Keep required columns
        # -------------------------------------------------

        result = summary[
            [
                "Rank",
                "Region",
                "Revenue",
                "Revenue Contribution %",
                "Cumulative Contribution %"
            ]
        ].copy()

        return result

    # =====================================================
    # 14. PARETO REGIONS
    # =====================================================

    def pareto_regions(self, threshold=80):
        """
        Identifies the regions required to reach a given
        cumulative revenue contribution.

        Default threshold:
            80%

        Returns all regions up to and including the region
        that crosses the threshold.

        Parameters:
            threshold:
                Cumulative revenue percentage to target.
        """

        if threshold <= 0 or threshold > 100:
            raise ValueError(
                "threshold must be greater than 0 "
                "and less than or equal to 100."
            )

        contribution = self.regional_contribution()

        if contribution.empty:
            return contribution

        # -------------------------------------------------
        # Find regions up to the threshold
        # -------------------------------------------------

        cumulative = (
            contribution["Cumulative Contribution %"]
        )

        # Find the first region that reaches threshold
        threshold_reached = (
            cumulative >= threshold
        )

        if threshold_reached.any():

            first_index = threshold_reached.idxmax()

            result = (
                contribution
                .loc[:first_index]
                .copy()
            )

        else:
            result = contribution.copy()

        return result.reset_index(drop=True)

    # =====================================================
    # 15. ABC REGION ANALYSIS
    # =====================================================

    def abc_region_analysis(
        self,
        a_threshold=80,
        b_threshold=95
    ):
        """
        Classifies regions using cumulative revenue
        contribution.

        Classification:
            A -> Up to 80% cumulative revenue
            B -> 80% to 95% cumulative revenue
            C -> Above 95% cumulative revenue

        Parameters:
            a_threshold:
                Upper cumulative contribution for A regions.

            b_threshold:
                Upper cumulative contribution for B regions.
        """

        if not (
            0 < a_threshold < b_threshold <= 100
        ):
            raise ValueError(
                "Thresholds must satisfy: "
                "0 < a_threshold < b_threshold <= 100"
            )

        contribution = (
            self.regional_contribution()
            .copy()
        )

        if contribution.empty:
            return contribution

        # -------------------------------------------------
        # ABC classification
        # -------------------------------------------------

        def classify_region(cumulative):
            if cumulative <= a_threshold:
                return "A"
            elif cumulative <= b_threshold:
                return "B"
            else:
                return "C"

        contribution["ABC Class"] = (
            contribution[
                "Cumulative Contribution %"
            ]
            .apply(classify_region)
        )

        return contribution

    # =====================================================
    # PHASE 5: GEOGRAPHIC ANALYSIS
    # =====================================================

    # =====================================================
    # 16. REGION CUSTOMER DISTRIBUTION
    # =====================================================

    def region_customer_distribution(self):
        """
        Returns customer distribution across regions.

        Metrics:
        - Region
        - Customers
        - Revenue
        - Orders

        Results are sorted by customer count
        from highest to lowest.
        """

        query = """
        SELECT
            place_of_supply,
            customer,
            invoice,
            amount
        FROM sales
        WHERE
            place_of_supply IS NOT NULL
            AND customer IS NOT NULL
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "Rank",
                    "Region",
                    "Customers",
                    "Revenue",
                    "Orders"
                ]
            )

        # -------------------------------------------------
        # Clean data
        # -------------------------------------------------

        df["place_of_supply"] = (
            df["place_of_supply"]
            .astype(str)
            .str.strip()
        )

        df["customer"] = (
            df["customer"]
            .astype(str)
            .str.strip()
        )

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

        # Standardize Puducherry
        df["place_of_supply"] = (
            df["place_of_supply"]
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry"
                }
            )
        )

        # -------------------------------------------------
        # Aggregate
        # -------------------------------------------------

        result = (
            df.groupby("place_of_supply")
            .agg(
                Customers=("customer", "nunique"),
                Revenue=("amount", "sum"),
                Orders=("invoice", "nunique")
            )
            .reset_index()
        )

        result.rename(
            columns={
                "place_of_supply": "Region"
            },
            inplace=True
        )

        # -------------------------------------------------
        # Sort by customers
        # -------------------------------------------------

        result = (
            result
            .sort_values(
                by="Customers",
                ascending=False
            )
            .reset_index(drop=True)
        )

        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

    # =====================================================
    # 17. REGIONAL AVERAGE ORDER VALUE
    # =====================================================

    def regional_average_order_value(
        self,
        min_orders=1
    ):
        """
        Calculates average order value for each region.

        Formula:
            Revenue / Orders

        Parameters:
            min_orders:
                Minimum number of orders required for a region
                to appear in the ranking.

                Default = 1, meaning all regions are included.

        Results are sorted by average order value
        from highest to lowest.
        """

        summary = self.region_summary().copy()

        if summary.empty:
            return pd.DataFrame(
                columns=[
                    "Rank",
                    "Region",
                    "Revenue",
                    "Orders",
                    "Average Order Value"
                ]
            )

        # -------------------------------------------------
        # Filter by minimum number of orders
        # -------------------------------------------------

        summary = summary[
            summary["Orders"] >= min_orders
        ].copy()

        if summary.empty:
            return pd.DataFrame(
                columns=[
                    "Rank",
                    "Region",
                    "Revenue",
                    "Orders",
                    "Average Order Value"
                ]
            )

        # -------------------------------------------------
        # Calculate AOV
        # -------------------------------------------------

        summary["Average Order Value"] = 0.0

        valid_orders = summary["Orders"] > 0

        summary.loc[
            valid_orders,
            "Average Order Value"
        ] = (
            summary.loc[
                valid_orders,
                "Revenue"
            ]
            /
            summary.loc[
                valid_orders,
                "Orders"
            ]
        )

        # -------------------------------------------------
        # Select columns
        # -------------------------------------------------

        result = summary[
            [
                "Region",
                "Revenue",
                "Orders",
                "Average Order Value"
            ]
        ].copy()

        # -------------------------------------------------
        # Sort
        # -------------------------------------------------

        result = (
            result
            .sort_values(
                by="Average Order Value",
                ascending=False
            )
            .reset_index(drop=True)
        )

        # -------------------------------------------------
        # Add rank
        # -------------------------------------------------

        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

    # =====================================================
    # 18. REGIONAL CUSTOMER COUNT
    # =====================================================

    def regional_customer_count(self):
        """
        Returns the number of unique customers
        in each region.

        Results are sorted from highest to lowest.
        """

        query = """
        SELECT
            place_of_supply,
            customer
        FROM sales
        WHERE
            place_of_supply IS NOT NULL
            AND customer IS NOT NULL
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "Rank",
                    "Region",
                    "Customers"
                ]
            )

        # -------------------------------------------------
        # Clean data
        # -------------------------------------------------

        df["place_of_supply"] = (
            df["place_of_supply"]
            .astype(str)
            .str.strip()
        )

        df["customer"] = (
            df["customer"]
            .astype(str)
            .str.strip()
        )

        # Standardize Puducherry
        df["place_of_supply"] = (
            df["place_of_supply"]
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry"
                }
            )
        )

        # -------------------------------------------------
        # Count customers
        # -------------------------------------------------

        result = (
            df.groupby("place_of_supply")
            .agg(
                Customers=("customer", "nunique")
            )
            .reset_index()
        )

        result.rename(
            columns={
                "place_of_supply": "Region"
            },
            inplace=True
        )

        # -------------------------------------------------
        # Sort
        # -------------------------------------------------

        result = (
            result
            .sort_values(
                by="Customers",
                ascending=False
            )
            .reset_index(drop=True)
        )

        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1)
        )

        return result

    # =====================================================
    # 19. GEOGRAPHIC HEATMAP DATA
    # =====================================================

    def geographic_heatmap_data(self):
        """
        Returns regional revenue data for geographic
        heatmap visualization.

        Visualization is handled by the dashboard layer.

        Metrics:
        - Region
        - Revenue
        - Quantity
        - Orders
        - Customers
        """

        summary = self.region_summary().copy()

        if summary.empty:
            return pd.DataFrame(
                columns=[
                    "Region",
                    "Revenue",
                    "Quantity",
                    "Orders",
                    "Customers"
                ]
            )

        result = summary[
            [
                "Region",
                "Revenue",
                "Quantity",
                "Orders",
                "Customers"
            ]
        ].copy()

        return result

    # =====================================================
    # 20. REGION DETAILS
    # =====================================================

    def region_details(self, region_name):
        """
        Returns a complete profile for a selected region.

        Includes:
        - Revenue
        - Quantity
        - Orders
        - Customers
        - Average Order Value
        - Revenue Contribution
        - Top Product
        """

        query = """
        SELECT
            place_of_supply,
            customer,
            invoice,
            item_name,
            stock_qty,
            amount
        FROM sales
        WHERE
            place_of_supply IS NOT NULL
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        if df.empty:
            raise ValueError(
                "No regional sales data found."
            )

        # -------------------------------------------------
        # Clean data
        # -------------------------------------------------

        df["place_of_supply"] = (
            df["place_of_supply"]
            .astype(str)
            .str.strip()
        )

        df["customer"] = (
            df["customer"]
            .astype(str)
            .str.strip()
        )

        df["item_name"] = (
            df["item_name"]
            .astype(str)
            .str.strip()
        )

        df["stock_qty"] = pd.to_numeric(
            df["stock_qty"],
            errors="coerce"
        ).fillna(0)

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

        # Standardize Puducherry
        df["place_of_supply"] = (
            df["place_of_supply"]
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry"
                }
            )
        )

        # -------------------------------------------------
        # Standardize selected region
        # -------------------------------------------------

        region_name = str(region_name).strip()

        if region_name == "34-Pondicherry":
            region_name = "34-Puducherry"

        # -------------------------------------------------
        # Filter region
        # -------------------------------------------------

        region_df = df[
            df["place_of_supply"] == region_name
        ].copy()

        if region_df.empty:
            raise ValueError(
                f"Region '{region_name}' was not found."
            )

        # -------------------------------------------------
        # Core metrics
        # -------------------------------------------------

        revenue = region_df["amount"].sum()

        quantity = region_df["stock_qty"].sum()

        orders = region_df["invoice"].nunique()

        customers = region_df["customer"].nunique()

        # -------------------------------------------------
        # Average order value
        # -------------------------------------------------

        average_order_value = (
            revenue / orders
            if orders > 0
            else 0
        )

        # -------------------------------------------------
        # Revenue contribution
        # -------------------------------------------------

        total_revenue = df["amount"].sum()

        revenue_contribution = (
            (revenue / total_revenue) * 100
            if total_revenue > 0
            else 0
        )

        # -------------------------------------------------
        # Top product by revenue
        # -------------------------------------------------

        product_sales = (
            region_df
            .groupby("item_name")
            .agg(
                Revenue=("amount", "sum")
            )
            .reset_index()
            .sort_values(
                by="Revenue",
                ascending=False
            )
        )

        if product_sales.empty:
            top_product = None
            top_product_revenue = 0
        else:
            top_product = (
                product_sales.iloc[0]["item_name"]
            )

            top_product_revenue = (
                product_sales.iloc[0]["Revenue"]
            )

        # -------------------------------------------------
        # Return profile
        # -------------------------------------------------

        return {
            "Region": region_name,
            "Revenue": revenue,
            "Quantity": quantity,
            "Orders": orders,
            "Customers": customers,
            "Average Order Value": average_order_value,
            "Revenue Contribution %": revenue_contribution,
            "Top Product": top_product,
            "Top Product Revenue": top_product_revenue
        }