import sqlite3
from pathlib import Path

import pandas as pd


class PricingEngine:
    """
    Pricing Intelligence Engine.

    Analyzes product-level pricing, discounts,
    revenue after discounts, and the relationship
    between discounts and sales.
    """

    def __init__(self, db_path: str = "data/sales.db") -> None:
        self.db_path = Path(db_path)

    # =====================================================
    # DATABASE CONNECTION
    # =====================================================

    def _get_connection(self) -> sqlite3.Connection:
        """
        Creates and returns a connection to the SQLite database.
        """
        return sqlite3.connect(self.db_path)

    # =====================================================
    # LOAD PRICING DATA
    # =====================================================

    def _load_pricing_data(self) -> pd.DataFrame:
        """
        Loads the fields required for pricing analysis.
        """

        query = """
        SELECT
            invoice,
            item_code,
            item_name,
            item_group,
            customer,
            place_of_supply,
            posting_date,
            stock_qty,
            discount_percent,
            rate,
            amount,
            transaction_type
        FROM sales
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        return df

    # =====================================================
    # CLEAN PRICING DATA
    # =====================================================

    def _clean_pricing_data(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Cleans and standardizes pricing data.
        """

        df = df.copy()

        # -------------------------------------------------
        # Clean text columns
        # -------------------------------------------------

        text_columns = [
            "invoice",
            "item_code",
            "item_name",
            "item_group",
            "customer",
            "place_of_supply",
            "transaction_type",
        ]

        for column in text_columns:
            if column in df.columns:
                df[column] = (
                    df[column]
                    .astype("string")
                    .str.strip()
                )

        # -------------------------------------------------
        # Convert numeric columns
        # -------------------------------------------------

        numeric_columns = [
            "stock_qty",
            "discount_percent",
            "rate",
            "amount",
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        # -------------------------------------------------
        # Required numeric fields
        # -------------------------------------------------

        df = df.dropna(
            subset=[
                "stock_qty",
                "rate",
                "amount",
            ]
        ).copy()

        # Preserve missing discounts as missing data.
        # Discount analytics explicitly use only valid 0-100% values.

        # -------------------------------------------------
        # Convert posting date
        # -------------------------------------------------

        df["posting_date"] = pd.to_datetime(
            df["posting_date"],
            errors="coerce",
        )

        # -------------------------------------------------
        # Normalize transaction type
        # -------------------------------------------------

        df["transaction_type"] = (
            df["transaction_type"]
            .str.strip()
            .str.title()
        )

        return df

    # =====================================================
    # SALES DATA
    # =====================================================

    def _sales_data(self) -> pd.DataFrame:
        """
        Returns valid Sale transactions only.

        Returns are excluded because they represent
        reversed commercial activity rather than actual
        product sales.
        """

        df = self._load_pricing_data()
        df = self._clean_pricing_data(df)

        return df[
            df["transaction_type"] == "Sale"
        ].copy()

    # =====================================================
    # 1. PRICING SUMMARY
    # =====================================================

    def pricing_summary(self) -> pd.DataFrame:
        """
        Returns the overall pricing summary.

        Metrics:
            Revenue
            Quantity
            Orders
            Products
            Average Discount
        """

        df = self._sales_data()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "Metric",
                    "Value",
                ]
            )

        quantity = float(df["stock_qty"].sum())
        revenue = float(df["amount"].sum())
        orders = int(df["invoice"].nunique())
        products = int(df["item_code"].nunique())

        # -------------------------------------------------
        # Weighted average discount
        # -------------------------------------------------

        absolute_quantity = (
            df["stock_qty"]
            .abs()
            .sum()
        )

        if absolute_quantity != 0:
            weighted_discount = float(
                (
                    df["discount_percent"]
                    * df["stock_qty"].abs()
                ).sum()
                / absolute_quantity
            )
        else:
            weighted_discount = 0.0

        return pd.DataFrame(
            {
                "Metric": [
                    "Revenue",
                    "Quantity",
                    "Orders",
                    "Products",
                    "Average Discount",
                ],
                "Value": [
                    revenue,
                    quantity,
                    orders,
                    products,
                    weighted_discount,
                ],
            }
        )

    # =====================================================
    # 2. AVERAGE DISCOUNT BY PRODUCT
    # =====================================================

    def average_discount_by_product(
        self,
    ) -> pd.DataFrame:
        """
        Calculates the average discount for every product.

        Only valid discounts between 0% and 100%
        are included.

        Returns:
            Item Code
            Product
            Quantity
            Revenue
            Average Discount %
        """

        df = self._sales_data()

        columns = [
            "Item Code",
            "Product",
            "Quantity",
            "Revenue",
            "Average Discount %",
        ]

        if df.empty:
            return pd.DataFrame(columns=columns)

        # -------------------------------------------------
        # Keep valid discounts
        # -------------------------------------------------

        valid = df[
            (df["discount_percent"] >= 0)
            & (df["discount_percent"] <= 100)
        ].copy()

        if valid.empty:
            return pd.DataFrame(columns=columns)

        # -------------------------------------------------
        # Aggregate by product
        # -------------------------------------------------

        valid["_weight"] = valid["stock_qty"].abs()
        valid["_discount_value"] = (
            valid["discount_percent"] * valid["_weight"]
        )

        result = (
            valid.groupby(
                [
                    "item_code",
                    "item_name",
                ],
                as_index=False,
            )
            .agg(
                Quantity=("stock_qty", "sum"),
                Revenue=("amount", "sum"),
                Discount_Value=("_discount_value", "sum"),
                Discount_Weight=("_weight", "sum"),
            )
        )

        result["Average Discount %"] = 0.0
        mask = result["Discount_Weight"] > 0
        result.loc[mask, "Average Discount %"] = (
            result.loc[mask, "Discount_Value"]
            / result.loc[mask, "Discount_Weight"]
        )

        # -------------------------------------------------
        # Rename columns
        # -------------------------------------------------

        result.rename(
            columns={
                "item_code": "Item Code",
                "item_name": "Product",
            },
            inplace=True,
        )

        # -------------------------------------------------
        # Final ordering
        # -------------------------------------------------

        result = result[
            columns
        ]

        result["Average Discount %"] = (
            result["Average Discount %"].round(2)
        )

        return (
            result
            .sort_values(
                by="Average Discount %",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    # =====================================================
    # 3. HIGHEST DISCOUNTED PRODUCTS
    # =====================================================

    def highest_discounted_products(
        self,
        limit: int = 10,
    ) -> pd.DataFrame:
        """
        Returns products with the highest average discounts.
        """

        columns = [
            "Rank",
            "Item Code",
            "Product",
            "Quantity",
            "Revenue",
            "Average Discount %",
        ]

        if limit <= 0:
            return pd.DataFrame(columns=columns)

        result = self.average_discount_by_product()

        if result.empty:
            return pd.DataFrame(columns=columns)

        result = (
            result
            .sort_values(
                by="Average Discount %",
                ascending=False,
            )
            .head(limit)
            .reset_index(drop=True)
        )

        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1),
        )

        return result[
            columns
        ]

    # =====================================================
    # 4. AVERAGE DISCOUNT BY CUSTOMER (NEW)
    # =====================================================

    def average_discount_by_customer(
        self,
    ) -> pd.DataFrame:
        """
        Returns the average discount given to each customer.

        Only valid Sale transactions are included.

        Returns:
            DataFrame containing:
                - Customer
                - Quantity
                - Revenue
                - Average Discount %
        """

        df = self._sales_data()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "Customer",
                    "Quantity",
                    "Revenue",
                    "Average Discount %",
                ]
            )

        # -------------------------------------------------
        # Keep valid customer and discount records
        # -------------------------------------------------

        valid = df[
            df["customer"].notna()
            & df["customer"].ne("")
            & (df["discount_percent"] >= 0)
            & (df["discount_percent"] <= 100)
        ].copy()

        if valid.empty:
            return pd.DataFrame(
                columns=[
                    "Customer",
                    "Quantity",
                    "Revenue",
                    "Average Discount %",
                ]
            )

        # -------------------------------------------------
        # Calculate quantity-weighted recorded discount
        # -------------------------------------------------

        valid["_weight"] = valid["stock_qty"].abs()
        valid["_discount_value"] = (
            valid["discount_percent"] * valid["_weight"]
        )

        # -------------------------------------------------
        # Aggregate customer-level pricing
        # -------------------------------------------------

        grouped = (
            valid.groupby("customer", as_index=False)
            .agg(
                Quantity=("stock_qty", "sum"),
                Revenue=("amount", "sum"),
                Discount_Value=("_discount_value", "sum"),
                Discount_Weight=("_weight", "sum"),
            )
        )

        # -------------------------------------------------
        # Calculate weighted average discount
        # -------------------------------------------------

        grouped["Average Discount %"] = 0.0

        mask = grouped["Discount_Weight"] > 0

        grouped.loc[
            mask,
            "Average Discount %",
        ] = (
            grouped.loc[
                mask,
                "Discount_Value",
            ]
            / grouped.loc[
                mask,
                "Discount_Weight",
            ]
        )

        # -------------------------------------------------
        # Format result
        # -------------------------------------------------

        result = grouped[
            [
                "customer",
                "Quantity",
                "Revenue",
                "Average Discount %",
            ]
        ].copy()

        result.rename(
            columns={
                "customer": "Customer",
            },
            inplace=True,
        )

        result["Average Discount %"] = (
            result["Average Discount %"]
            .round(2)
        )

        return (
            result
            .sort_values(
                by="Average Discount %",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    # =====================================================
    # 5. AVERAGE DISCOUNT BY REGION (NEW)
    # =====================================================

    def average_discount_by_region(
        self,
    ) -> pd.DataFrame:
        """
        Returns the average discount given in each region.

        Only valid Sale transactions are included.

        Returns:
            DataFrame containing:
                - Region
                - Quantity
                - Revenue
                - Average Discount %
        """

        df = self._sales_data()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "Region",
                    "Quantity",
                    "Revenue",
                    "Average Discount %",
                ]
            )

        # -------------------------------------------------
        # Keep valid region and discount records
        # -------------------------------------------------

        valid = df[
            df["place_of_supply"].notna()
            & df["place_of_supply"].ne("")
            & (df["discount_percent"] >= 0)
            & (df["discount_percent"] <= 100)
        ].copy()

        if valid.empty:
            return pd.DataFrame(
                columns=[
                    "Region",
                    "Quantity",
                    "Revenue",
                    "Average Discount %",
                ]
            )

        # -------------------------------------------------
        # Standardize region names
        # -------------------------------------------------

        valid["place_of_supply"] = (
            valid["place_of_supply"]
            .astype("string")
            .str.strip()
            .replace(
                {
                    "34-Pondicherry": "34-Puducherry",
                }
            )
        )

        # -------------------------------------------------
        # Calculate quantity-weighted recorded discount
        # -------------------------------------------------

        valid["_weight"] = valid["stock_qty"].abs()
        valid["_discount_value"] = (
            valid["discount_percent"] * valid["_weight"]
        )

        # -------------------------------------------------
        # Aggregate region-level pricing
        # -------------------------------------------------

        grouped = (
            valid.groupby(
                "place_of_supply",
                as_index=False,
            )
            .agg(
                Quantity=("stock_qty", "sum"),
                Revenue=("amount", "sum"),
                Discount_Value=("_discount_value", "sum"),
                Discount_Weight=("_weight", "sum"),
            )
        )

        # -------------------------------------------------
        # Calculate weighted average discount
        # -------------------------------------------------

        grouped["Average Discount %"] = 0.0

        mask = grouped["Discount_Weight"] > 0

        grouped.loc[
            mask,
            "Average Discount %",
        ] = (
            grouped.loc[
                mask,
                "Discount_Value",
            ]
            / grouped.loc[
                mask,
                "Discount_Weight",
            ]
        )

        # -------------------------------------------------
        # Format result
        # -------------------------------------------------

        result = grouped[
            [
                "place_of_supply",
                "Quantity",
                "Revenue",
                "Average Discount %",
            ]
        ].copy()

        result.rename(
            columns={
                "place_of_supply": "Region",
            },
            inplace=True,
        )

        result["Average Discount %"] = (
            result["Average Discount %"]
            .round(2)
        )

        return (
            result
            .sort_values(
                by="Average Discount %",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    # =====================================================
    # 6. DISCOUNT BAND ANALYSIS (NEW)
    # =====================================================

    def discount_band_analysis(
        self,
    ) -> pd.DataFrame:
        """
        Groups sales transactions into discount bands.

        Discount bands:
            0-5%
            5-10%
            10-15%
            15-20%
            20%+

        Returns:
            DataFrame containing:
                - Discount Band
                - Orders
                - Quantity
                - Revenue
                - Average Revenue per Order
        """

        df = self._sales_data()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "Discount Band",
                    "Orders",
                    "Quantity",
                    "Revenue",
                    "Average Revenue per Order",
                ]
            )

        # -------------------------------------------------
        # Keep valid discount records
        # -------------------------------------------------

        valid = df[
            (df["discount_percent"] >= 0)
            & (df["discount_percent"] <= 100)
        ].copy()

        if valid.empty:
            return pd.DataFrame(
                columns=[
                    "Discount Band",
                    "Orders",
                    "Quantity",
                    "Revenue",
                    "Average Revenue per Order",
                ]
            )

        # -------------------------------------------------
        # Create discount bands
        # -------------------------------------------------

        valid["Discount Band"] = pd.cut(
            valid["discount_percent"],
            bins=[
                -0.000001,
                5,
                10,
                15,
                20,
                float("inf"),
            ],
            labels=[
                "0-5%",
                "5-10%",
                "10-15%",
                "15-20%",
                "20%+",
            ],
            include_lowest=True,
            right=False,
        )

        # -------------------------------------------------
        # Aggregate
        # -------------------------------------------------

        result = (
            valid.groupby(
                "Discount Band",
                observed=False,
                as_index=False,
            )
            .agg(
                Orders=("invoice", "nunique"),
                Quantity=("stock_qty", "sum"),
                Revenue=("amount", "sum"),
            )
        )

        # -------------------------------------------------
        # Calculate average revenue per order
        # -------------------------------------------------

        result["Average Revenue per Order"] = 0.0

        valid_orders = result["Orders"] > 0

        result.loc[
            valid_orders,
            "Average Revenue per Order",
        ] = (
            result.loc[
                valid_orders,
                "Revenue",
            ]
            / result.loc[
                valid_orders,
                "Orders",
            ]
        )

        # -------------------------------------------------
        # Preserve business order of discount bands
        # -------------------------------------------------

        band_order = [
            "0-5%",
            "5-10%",
            "10-15%",
            "15-20%",
            "20%+",
        ]

        result["Discount Band"] = pd.Categorical(
            result["Discount Band"],
            categories=band_order,
            ordered=True,
        )

        result = (
            result
            .sort_values("Discount Band")
            .reset_index(drop=True)
        )

        return result

    # =====================================================
    # 7. REVENUE AFTER DISCOUNTS
    # =====================================================

    def revenue_after_discounts(
        self,
    ) -> pd.DataFrame:
        """
        Calculates revenue after discounts for each product.

        The `amount` field is treated as the actual
        post-discount transaction revenue.

        Gross Value is reconstructed using:

            List Rate =
                Rate / (1 - Discount % / 100)

            Gross Value =
                List Rate × Quantity

            Discount Amount =
                Gross Value - Revenue

        Returns:
            Item Code
            Product
            Quantity
            Gross Value
            Discount Amount
            Revenue After Discounts
            Average Discount %
        """

        df = self._sales_data()

        columns = [
            "Item Code",
            "Product",
            "Quantity",
            "Gross Value",
            "Discount Amount",
            "Revenue After Discounts",
            "Average Discount %",
        ]

        if df.empty:
            return pd.DataFrame(columns=columns)

        df = df.copy()

        # -------------------------------------------------
        # Validate discount values
        # -------------------------------------------------

        df = df[
            df["discount_percent"].notna()
            & df["discount_percent"].between(0, 100)
        ].copy()

        if df.empty:
            return pd.DataFrame(columns=columns)

        # -------------------------------------------------
        # Reconstruct pre-discount rate
        # -------------------------------------------------

        discount_factor = (
            1.0
            - df["discount_percent"] / 100.0
        )

        df["List_Rate"] = (
            df["rate"]
            / discount_factor
        )

        # -------------------------------------------------
        # Calculate gross value
        # -------------------------------------------------

        df["Gross_Value"] = (
            df["List_Rate"]
            * df["stock_qty"]
        )

        df["_weight"] = df["stock_qty"].abs()
        df["_discount_value"] = (
            df["discount_percent"] * df["_weight"]
        )

        # -------------------------------------------------
        # Aggregate by product
        # -------------------------------------------------

        result = (
            df.groupby(
                [
                    "item_code",
                    "item_name",
                ],
                dropna=False,
                as_index=False,
            )
            .agg(
                Quantity=("stock_qty", "sum"),
                Gross_Value=("Gross_Value", "sum"),
                Revenue_After_Discounts=(
                    "amount",
                    "sum",
                ),
                Discount_Value=(
                    "_discount_value",
                    "sum",
                ),
                Discount_Weight=(
                    "_weight",
                    "sum",
                ),
            )
        )

        result["Average Discount %"] = 0.0

        mask = result["Discount_Weight"] > 0

        result.loc[
            mask,
            "Average Discount %",
        ] = (
            result.loc[
                mask,
                "Discount_Value",
            ]
            / result.loc[
                mask,
                "Discount_Weight",
            ]
        )

        # -------------------------------------------------
        # Discount amount
        # -------------------------------------------------

        result["Discount Amount"] = (
            result["Gross_Value"]
            - result["Revenue_After_Discounts"]
        )

        # -------------------------------------------------
        # Rename columns
        # -------------------------------------------------

        result.rename(
            columns={
                "item_code": "Item Code",
                "item_name": "Product",
                "Gross_Value": "Gross Value",
                "Revenue_After_Discounts": (
                    "Revenue After Discounts"
                ),
            },
            inplace=True,
        )

        # -------------------------------------------------
        # Final column order
        # -------------------------------------------------

        result = result[
            columns
        ]

        return (
            result
            .sort_values(
                by="Revenue After Discounts",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    # =====================================================
    # 8. DISCOUNT VS SALES ANALYSIS
    # =====================================================

    def discount_vs_sales(self) -> dict:
        """
        Analyzes the relationship between product-level
        discount percentage and quantity sold.

        Returns:
            correlation
            interpretation
            product_data
        """

        data = self.average_discount_by_product()

        if data.empty:
            return {
                "correlation": 0.0,
                "interpretation": (
                    "No pricing data available."
                ),
                "product_data": data,
            }

        analysis = data[
            [
                "Item Code",
                "Product",
                "Quantity",
                "Revenue",
                "Average Discount %",
            ]
        ].copy()

        analysis = analysis.dropna(
            subset=[
                "Quantity",
                "Average Discount %",
            ]
        )

        if len(analysis) < 2:
            return {
                "correlation": 0.0,
                "interpretation": (
                    "Insufficient product data to "
                    "calculate discount-sales "
                    "correlation."
                ),
                "product_data": (
                    analysis.reset_index(drop=True)
                ),
            }

        correlation_value = analysis[
            "Average Discount %"
        ].corr(
            analysis["Quantity"]
        )

        if pd.isna(correlation_value):
            correlation = 0.0
        else:
            correlation = float(correlation_value)

        # -------------------------------------------------
        # Interpret correlation
        # -------------------------------------------------

        if correlation >= 0.5:
            interpretation = (
                "Strong positive relationship: "
                "products with higher discounts tend "
                "to have higher sales."
            )
        elif correlation >= 0.2:
            interpretation = (
                "Moderate positive relationship: "
                "higher discounts are generally "
                "associated with higher sales."
            )
        elif correlation > -0.2:
            interpretation = (
                "Weak or negligible relationship: "
                "discount level has little linear "
                "relationship with sales."
            )
        elif correlation > -0.5:
            interpretation = (
                "Moderate negative relationship: "
                "higher discounts are generally "
                "associated with lower sales."
            )
        else:
            interpretation = (
                "Strong negative relationship: "
                "products with higher discounts tend "
                "to have lower sales."
            )

        return {
            "correlation": round(
                correlation,
                4,
            ),
            "interpretation": interpretation,
            "product_data": (
                analysis.reset_index(drop=True)
            ),
        }

    # =====================================================
    # 9. PRODUCT PRICING DETAILS
    # =====================================================

    def product_price_details(
        self,
        item_code: str,
    ) -> pd.DataFrame:
        """
        Returns pricing details for a specific product.

        Item-code lookup is:

        - Case-insensitive
        - Whitespace-insensitive

        Example:

            aspfc
            ASPFC
            AspFc

        all resolve to the same product.

        Returns:
            Item Code
            Product
            Quantity
            Revenue
            Average Selling Price
            Average Discount %
        """

        code = (
            str(item_code)
            .strip()
            .casefold()
        )

        if not code:
            raise ValueError(
                "Item Code cannot be empty."
            )

        # -------------------------------------------------
        # Use the engine's actual sales data.
        #
        # This replaces the old self._data reference,
        # which was never defined in PricingEngine.
        # -------------------------------------------------

        data = self._sales_data()

        if data.empty:
            raise ValueError(
                f"No pricing data found for Item Code: "
                f"{item_code}"
            )

        # -------------------------------------------------
        # Case-insensitive item-code comparison
        # -------------------------------------------------

        data["_item_code_lookup"] = (
            data["item_code"]
            .astype("string")
            .str.strip()
            .str.casefold()
        )

        product_data = data[
            data["_item_code_lookup"] == code
        ].copy()

        if product_data.empty:
            raise ValueError(
                f"No pricing data found for Item Code: "
                f"{item_code}"
            )

        # -------------------------------------------------
        # Aggregate product data
        # -------------------------------------------------

        product_data = product_data[
            product_data["discount_percent"].notna()
            & product_data["discount_percent"].between(0, 100)
        ].copy()

        if product_data.empty:
            raise ValueError(
                f"No valid pricing data found for Item Code: "
                f"{item_code}"
            )

        product_data["_weight"] = product_data["stock_qty"].abs()
        product_data["_discount_value"] = (
            product_data["discount_percent"]
            * product_data["_weight"]
        )

        grouped = (
            product_data.groupby(
                [
                    "item_code",
                    "item_name",
                ],
                as_index=False,
            )
            .agg(
                Quantity=("stock_qty", "sum"),
                Revenue=("amount", "sum"),
                Discount_Value=("_discount_value", "sum"),
                Discount_Weight=("_weight", "sum"),
            )
        )

        grouped["Average Discount %"] = 0.0

        mask = grouped["Discount_Weight"] > 0

        grouped.loc[
            mask,
            "Average Discount %",
        ] = (
            grouped.loc[
                mask,
                "Discount_Value",
            ]
            / grouped.loc[
                mask,
                "Discount_Weight",
            ]
        )

        # -------------------------------------------------
        # Calculate average selling price
        # -------------------------------------------------

        grouped["Average Selling Price"] = 0.0

        valid_quantity = (
            grouped["Quantity"] != 0
        )

        grouped.loc[
            valid_quantity,
            "Average Selling Price",
        ] = (
            grouped.loc[
                valid_quantity,
                "Revenue",
            ]
            /
            grouped.loc[
                valid_quantity,
                "Quantity",
            ]
        )

        # -------------------------------------------------
        # Rename columns
        # -------------------------------------------------

        grouped.rename(
            columns={
                "item_code": "Item Code",
                "item_name": "Product",
            },
            inplace=True,
        )

        # -------------------------------------------------
        # Round numerical values
        # -------------------------------------------------

        grouped["Quantity"] = (
            grouped["Quantity"].round(2)
        )

        grouped["Revenue"] = (
            grouped["Revenue"].round(2)
        )

        grouped["Average Selling Price"] = (
            grouped["Average Selling Price"].round(2)
        )

        grouped["Average Discount %"] = (
            grouped["Average Discount %"].round(2)
        )

        # -------------------------------------------------
        # Final column order
        # -------------------------------------------------

        return grouped[
            [
                "Item Code",
                "Product",
                "Quantity",
                "Revenue",
                "Average Selling Price",
                "Average Discount %",
            ]
        ]

    # =====================================================
    # 10. AVERAGE SELLING PRICE
    # =====================================================

    def average_selling_price(
        self,
    ) -> pd.DataFrame:
        """
        Calculates weighted average selling price
        for every product.

        Formula:

            Revenue / Quantity
        """

        df = self._sales_data()

        columns = [
            "Item Code",
            "Product",
            "Quantity",
            "Revenue",
            "Average Selling Price",
        ]

        if df.empty:
            return pd.DataFrame(columns=columns)

        result = (
            df.groupby(
                [
                    "item_code",
                    "item_name",
                ],
                as_index=False,
            )
            .agg(
                Quantity=("stock_qty", "sum"),
                Revenue=("amount", "sum"),
            )
        )

        result["Average Selling Price"] = 0.0

        valid_quantity = (
            result["Quantity"] != 0
        )

        result.loc[
            valid_quantity,
            "Average Selling Price",
        ] = (
            result.loc[
                valid_quantity,
                "Revenue",
            ]
            /
            result.loc[
                valid_quantity,
                "Quantity",
            ]
        )

        result.rename(
            columns={
                "item_code": "Item Code",
                "item_name": "Product",
            },
            inplace=True,
        )

        result = result[
            columns
        ]

        return (
            result
            .sort_values(
                by="Average Selling Price",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    # =====================================================
    # 11. HIGHEST PRICED PRODUCTS
    # =====================================================

    def highest_priced_products(
        self,
        n: int = 10,
    ) -> pd.DataFrame:
        """
        Returns products with the highest
        average selling price.
        """

        if n <= 0:
            raise ValueError(
                "n must be greater than 0."
            )

        result = self.average_selling_price()

        return (
            result
            .head(n)
            .reset_index(drop=True)
            .assign(
                Rank=lambda frame: range(
                    1,
                    len(frame) + 1,
                )
            )
            [
                [
                    "Rank",
                    "Item Code",
                    "Product",
                    "Quantity",
                    "Revenue",
                    "Average Selling Price",
                ]
            ]
        )

    # =====================================================
    # 12. LOWEST PRICED PRODUCTS
    # =====================================================

    def lowest_priced_products(
        self,
        n: int = 10,
    ) -> pd.DataFrame:
        """
        Returns products with the lowest
        average selling price.
        """

        if n <= 0:
            raise ValueError(
                "n must be greater than 0."
            )

        result = (
            self.average_selling_price()
            .sort_values(
                by="Average Selling Price",
                ascending=True,
            )
            .head(n)
            .reset_index(drop=True)
        )

        result.insert(
            0,
            "Rank",
            range(1, len(result) + 1),
        )

        return result

    # =====================================================
    # 13. PRICE REALIZATION
    # =====================================================

    def price_realization(
        self,
    ) -> pd.DataFrame:
        """
        Calculates price realization by product.

        List Rate:
            Rate / (1 - Discount % / 100)

        Gross Value:
            List Rate × Quantity

        Price Realization:
            Revenue / Gross Value × 100
        """

        df = self._sales_data()

        columns = [
            "Item Code",
            "Product",
            "Gross Value",
            "Revenue",
            "Discount Amount",
            "Price Realization %",
        ]

        if df.empty:
            return pd.DataFrame(columns=columns)

        df = df.copy()

        df = df[
            df["discount_percent"].notna()
            & df["discount_percent"].between(0, 100)
        ].copy()

        if df.empty:
            return pd.DataFrame(columns=columns)

        discount_factor = (
            1.0
            - df["discount_percent"] / 100.0
        )

        df["List_Rate"] = (
            df["rate"]
            / discount_factor
        )

        df["Gross_Value"] = (
            df["List_Rate"]
            * df["stock_qty"]
        )

        result = (
            df.groupby(
                [
                    "item_code",
                    "item_name",
                ],
                as_index=False,
            )
            .agg(
                Gross_Value=("Gross_Value", "sum"),
                Revenue=("amount", "sum"),
            )
        )

        result["Discount Amount"] = (
            result["Gross_Value"]
            - result["Revenue"]
        )

        result["Price Realization %"] = 0.0

        valid_gross = (
            result["Gross_Value"] > 0
        )

        result.loc[
            valid_gross,
            "Price Realization %",
        ] = (
            result.loc[
                valid_gross,
                "Revenue",
            ]
            /
            result.loc[
                valid_gross,
                "Gross_Value",
            ]
        ) * 100.0

        result.rename(
            columns={
                "item_code": "Item Code",
                "item_name": "Product",
                "Gross_Value": "Gross Value",
            },
            inplace=True,
        )

        result = result[
            columns
        ]

        return (
            result
            .sort_values(
                by="Revenue",
                ascending=False,
            )
            .reset_index(drop=True)
        )