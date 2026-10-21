import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# (datetime is not used in the forecasting methods, but we add it per instruction)
from datetime import datetime


class TimeSeriesEngine:
    """
    Time-Series Intelligence Engine.

    Analyzes sales performance across different
    time periods including daily, weekly, monthly,
    quarterly, and yearly intervals.
    """

    def __init__(
        self,
        db_path: str = "data/sales.db",
    ) -> None:
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
    # LOAD TIME-SERIES DATA
    # =====================================================

    def _load_time_series_data(self) -> pd.DataFrame:
        """
        Loads the fields required for time-series analysis.
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
    # CLEAN TIME-SERIES DATA
    # =====================================================

    def _clean_time_series_data(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Cleans and standardizes data required for
        time-series analysis.
        """
        result = df.copy()

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
            if column in result.columns:
                result[column] = result[column].astype("string").str.strip()

        numeric_columns = ["stock_qty", "discount_percent", "rate", "amount"]
        for column in numeric_columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")

        result["posting_date"] = pd.to_datetime(result["posting_date"], errors="coerce")
        result = result.dropna(subset=["posting_date"]).copy()
        result["transaction_type"] = result["transaction_type"].str.strip().str.title()
        return result

    # =====================================================
    # SALES DATA
    # =====================================================

    def _sales_data(self) -> pd.DataFrame:
        """
        Returns valid Sale transactions only.
        """
        df = self._load_time_series_data()
        df = self._clean_time_series_data(df)
        return df[df["transaction_type"] == "Sale"].copy()

    # =====================================================
    # TIME DIMENSIONS
    # =====================================================

    def _add_time_dimensions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds reusable time dimensions to the dataframe.
        """
        result = df.copy()
        result["Date"] = result["posting_date"].dt.normalize()
        result["Week"] = result["posting_date"].dt.to_period("W").dt.start_time
        result["Month"] = result["posting_date"].dt.to_period("M").dt.start_time
        result["Quarter"] = result["posting_date"].dt.to_period("Q").dt.start_time
        result["Year"] = result["posting_date"].dt.to_period("Y").dt.start_time
        return result

    # =====================================================
    # PERIOD VALIDATION
    # =====================================================

    def _period_boundaries(
        self,
        period_column: str,
    ) -> tuple[pd.Timestamp, pd.Timestamp]:
        """
        Returns the first and last calendar boundaries
        represented by the available sales dataset.
        """
        df = self._sales_data()
        if df.empty:
            raise ValueError("No valid sales data is available for period validation.")
        min_date = df["posting_date"].min()
        max_date = df["posting_date"].max()
        if pd.isna(min_date) or pd.isna(max_date):
            raise ValueError("Sales data does not contain valid dates.")

        if period_column == "Date":
            first_period = min_date.normalize()
            last_period = max_date.normalize()
        elif period_column == "Week":
            first_period = min_date.to_period("W").start_time
            last_period = max_date.to_period("W").end_time.normalize()
        elif period_column == "Month":
            first_period = min_date.to_period("M").start_time
            last_period = max_date.to_period("M").end_time.normalize()
        elif period_column == "Quarter":
            first_period = min_date.to_period("Q").start_time
            last_period = max_date.to_period("Q").end_time.normalize()
        elif period_column == "Year":
            first_period = min_date.to_period("Y").start_time
            last_period = max_date.to_period("Y").end_time.normalize()
        else:
            raise ValueError(f"Unsupported period column: {period_column}")
        return first_period, last_period

    @staticmethod
    def _period_status(
        period_start: pd.Timestamp,
        period_end: pd.Timestamp,
        data_start: pd.Timestamp,
        data_end: pd.Timestamp,
    ) -> str:
        """
        Determines whether a period is complete or partial.
        """
        if period_start >= data_start and period_end <= data_end:
            return "Complete"
        return "Partial"

    def _add_period_status(
        self,
        df: pd.DataFrame,
        period_column: str,
    ) -> pd.DataFrame:
        """
        Adds period completeness information.
        """
        result = df.copy()
        if result.empty:
            result["Period Status"] = pd.Series(dtype="string")
            result["Period Complete"] = pd.Series(dtype="boolean")
            return result

        sales_data = self._sales_data()
        if sales_data.empty:
            result["Period Status"] = "Partial"
            result["Period Complete"] = False
            return result

        data_start = sales_data["posting_date"].min()
        data_end = sales_data["posting_date"].max()
        if pd.isna(data_start) or pd.isna(data_end):
            result["Period Status"] = "Partial"
            result["Period Complete"] = False
            return result

        data_start = data_start.normalize()
        data_end = data_end.normalize()

        status_values: list[str] = []
        complete_values: list[bool] = []

        for period in result[period_column]:
            period_timestamp = pd.Timestamp(period)

            if period_column == "Date":
                period_start = period_timestamp
                period_end = period_timestamp
            elif period_column == "Week":
                period_start = period_timestamp
                period_end = period_timestamp + pd.Timedelta(days=6)
            elif period_column == "Month":
                period_start = period_timestamp.to_period("M").start_time
                period_end = period_timestamp.to_period("M").end_time.normalize()
            elif period_column == "Quarter":
                period_start = period_timestamp.to_period("Q").start_time
                period_end = period_timestamp.to_period("Q").end_time.normalize()
            elif period_column == "Year":
                period_start = period_timestamp.to_period("Y").start_time
                period_end = period_timestamp.to_period("Y").end_time.normalize()
            else:
                raise ValueError(f"Unsupported period column: {period_column}")

            status = self._period_status(period_start, period_end, data_start, data_end)
            status_values.append(status)
            complete_values.append(status == "Complete")

        result["Period Status"] = status_values
        result["Period Complete"] = complete_values
        return result

    # =====================================================
    # COMMON AGGREGATION
    # =====================================================

    def _aggregate_by_period(
        self,
        df: pd.DataFrame,
        period_column: str,
    ) -> pd.DataFrame:
        """
        Aggregates sales data for a specified time period.
        """
        columns = [
            period_column,
            "Revenue",
            "Quantity",
            "Orders",
            "Products",
            "Customers",
            "Average Order Value",
            "Period Status",
            "Period Complete",
        ]

        if df.empty:
            return pd.DataFrame(columns=columns)

        grouped = (
            df.groupby(period_column, as_index=False)
            .agg(
                Revenue=("amount", "sum"),
                Quantity=("stock_qty", "sum"),
                Orders=("invoice", "nunique"),
                Products=("item_code", "nunique"),
                Customers=("customer", "nunique"),
            )
        )

        grouped["Average Order Value"] = 0.0
        valid_orders = grouped["Orders"] > 0
        grouped.loc[valid_orders, "Average Order Value"] = (
            grouped.loc[valid_orders, "Revenue"] / grouped.loc[valid_orders, "Orders"]
        )

        grouped = self._add_period_status(grouped, period_column)
        return grouped[columns].sort_values(by=period_column).reset_index(drop=True)

    # =====================================================
    # GROWTH ANALYSIS HELPERS
    # =====================================================

    @staticmethod
    def _calculate_growth(
        current: pd.Series,
        previous: pd.Series,
        comparable: pd.Series,
    ) -> pd.Series:
        """
        Calculates percentage growth only for comparable
        periods with a non-zero previous value.
        """
        growth = pd.Series(float("nan"), index=current.index, dtype="float64")
        valid_previous = previous.notna() & (previous != 0) & comparable
        growth.loc[valid_previous] = (
            (current.loc[valid_previous] - previous.loc[valid_previous])
            / previous.loc[valid_previous]
        ) * 100.0
        return growth

    def _growth_analysis(
        self,
        data: pd.DataFrame,
        period_column: str,
        offset: pd.DateOffset,
    ) -> pd.DataFrame:
        """
        Calculates period-over-period growth.
        """
        columns = [
            period_column,
            "Revenue",
            "Quantity",
            "Orders",
            "Products",
            "Customers",
            "Average Order Value",
            "Previous Revenue",
            "Revenue Growth %",
            "Previous Quantity",
            "Quantity Growth %",
            "Previous Orders",
            "Order Growth %",
            "Previous Average Order Value",
            "AOV Growth %",
            "Period Status",
            "Period Complete",
            "Previous Period Complete",
            "Comparable",
        ]

        if data.empty:
            return pd.DataFrame(columns=columns)

        current = data.copy()
        previous = data[
            [
                period_column,
                "Revenue",
                "Quantity",
                "Orders",
                "Average Order Value",
                "Period Complete",
            ]
        ].copy()

        previous.rename(
            columns={
                period_column: "Previous Period",
                "Revenue": "Previous Revenue",
                "Quantity": "Previous Quantity",
                "Orders": "Previous Orders",
                "Average Order Value": "Previous Average Order Value",
                "Period Complete": "Previous Period Complete",
            },
            inplace=True,
        )

        current["Previous Period"] = current[period_column] - offset
        result = current.merge(previous, on="Previous Period", how="left")

        result["Comparable"] = (
            result["Period Complete"].fillna(False)
            & result["Previous Period Complete"].fillna(False)
        )

        result["Revenue Growth %"] = self._calculate_growth(
            result["Revenue"], result["Previous Revenue"], result["Comparable"]
        )
        result["Quantity Growth %"] = self._calculate_growth(
            result["Quantity"], result["Previous Quantity"], result["Comparable"]
        )
        result["Order Growth %"] = self._calculate_growth(
            result["Orders"], result["Previous Orders"], result["Comparable"]
        )
        result["AOV Growth %"] = self._calculate_growth(
            result["Average Order Value"],
            result["Previous Average Order Value"],
            result["Comparable"],
        )

        result.drop(columns=["Previous Period"], inplace=True)
        return result[columns].sort_values(by=period_column).reset_index(drop=True)

    # =====================================================
    # 1. DAILY SALES
    # =====================================================

    def daily_sales(self) -> pd.DataFrame:
        df = self._sales_data()
        if df.empty:
            return self._aggregate_by_period(df, "Date")
        df = self._add_time_dimensions(df)
        return self._aggregate_by_period(df, "Date")

    # =====================================================
    # 2. WEEKLY SALES
    # =====================================================

    def weekly_sales(self) -> pd.DataFrame:
        df = self._sales_data()
        if df.empty:
            return self._aggregate_by_period(df, "Week")
        df = self._add_time_dimensions(df)
        return self._aggregate_by_period(df, "Week")

    # =====================================================
    # 3. MONTHLY SALES
    # =====================================================

    def monthly_sales(self) -> pd.DataFrame:
        df = self._sales_data()
        if df.empty:
            return self._aggregate_by_period(df, "Month")
        df = self._add_time_dimensions(df)
        return self._aggregate_by_period(df, "Month")

    # =====================================================
    # 4. QUARTERLY SALES
    # =====================================================

    def quarterly_sales(self) -> pd.DataFrame:
        df = self._sales_data()
        if df.empty:
            return self._aggregate_by_period(df, "Quarter")
        df = self._add_time_dimensions(df)
        return self._aggregate_by_period(df, "Quarter")

    # =====================================================
    # 5. YEARLY SALES
    # =====================================================

    def yearly_sales(self) -> pd.DataFrame:
        df = self._sales_data()
        if df.empty:
            return self._aggregate_by_period(df, "Year")
        df = self._add_time_dimensions(df)
        return self._aggregate_by_period(df, "Year")

    # =====================================================
    # 6. MONTH-OVER-MONTH GROWTH
    # =====================================================

    def month_over_month_growth(self) -> pd.DataFrame:
        data = self.monthly_sales()
        return self._growth_analysis(data, "Month", pd.DateOffset(months=1))

    # =====================================================
    # 7. QUARTER-OVER-QUARTER GROWTH
    # =====================================================

    def quarter_over_quarter_growth(self) -> pd.DataFrame:
        data = self.quarterly_sales()
        return self._growth_analysis(data, "Quarter", pd.DateOffset(months=3))

    # =====================================================
    # 8. YEAR-OVER-YEAR GROWTH
    # =====================================================

    def year_over_year_growth(self) -> pd.DataFrame:
        data = self.yearly_sales()
        result = self._growth_analysis(data, "Year", pd.DateOffset(years=1))
        result["Comparable"] = result["Comparable"] & result["Period Complete"]
        growth_columns = ["Revenue Growth %", "Quantity Growth %", "Order Growth %", "AOV Growth %"]
        for col in growth_columns:
            result.loc[~result["Comparable"], col] = float("nan")
        return result

    # =====================================================
    # 9. REVENUE GROWTH RATE
    # =====================================================

    def revenue_growth_rate(self, frequency: str = "monthly") -> pd.DataFrame:
        freq = frequency.strip().lower()
        if freq == "monthly":
            data = self.month_over_month_growth()
            period_column = "Month"
        elif freq == "quarterly":
            data = self.quarter_over_quarter_growth()
            period_column = "Quarter"
        elif freq == "yearly":
            data = self.year_over_year_growth()
            period_column = "Year"
        else:
            raise ValueError("frequency must be one of: monthly, quarterly, yearly.")
        return data[
            [
                period_column,
                "Previous Revenue",
                "Revenue",
                "Revenue Growth %",
                "Period Status",
                "Previous Period Complete",
                "Comparable",
            ]
        ].copy()

    # =====================================================
    # 10. QUANTITY GROWTH RATE
    # =====================================================

    def quantity_growth_rate(self, frequency: str = "monthly") -> pd.DataFrame:
        freq = frequency.strip().lower()
        if freq == "monthly":
            data = self.month_over_month_growth()
            period_column = "Month"
        elif freq == "quarterly":
            data = self.quarter_over_quarter_growth()
            period_column = "Quarter"
        elif freq == "yearly":
            data = self.year_over_year_growth()
            period_column = "Year"
        else:
            raise ValueError("frequency must be one of: monthly, quarterly, yearly.")
        return data[
            [
                period_column,
                "Previous Quantity",
                "Quantity",
                "Quantity Growth %",
                "Period Status",
                "Previous Period Complete",
                "Comparable",
            ]
        ].copy()

    # =====================================================
    # 11. ORDER GROWTH RATE
    # =====================================================

    def order_growth_rate(self, frequency: str = "monthly") -> pd.DataFrame:
        freq = frequency.strip().lower()
        if freq == "monthly":
            data = self.month_over_month_growth()
            period_column = "Month"
        elif freq == "quarterly":
            data = self.quarter_over_quarter_growth()
            period_column = "Quarter"
        elif freq == "yearly":
            data = self.year_over_year_growth()
            period_column = "Year"
        else:
            raise ValueError("frequency must be one of: monthly, quarterly, yearly.")
        return data[
            [
                period_column,
                "Previous Orders",
                "Orders",
                "Order Growth %",
                "Period Status",
                "Previous Period Complete",
                "Comparable",
            ]
        ].copy()

    # =====================================================
    # 12. AVERAGE ORDER VALUE GROWTH
    # =====================================================

    def aov_growth_rate(self, frequency: str = "monthly") -> pd.DataFrame:
        freq = frequency.strip().lower()
        if freq == "monthly":
            data = self.month_over_month_growth()
            period_column = "Month"
        elif freq == "quarterly":
            data = self.quarter_over_quarter_growth()
            period_column = "Quarter"
        elif freq == "yearly":
            data = self.year_over_year_growth()
            period_column = "Year"
        else:
            raise ValueError("frequency must be one of: monthly, quarterly, yearly.")
        return data[
            [
                period_column,
                "Previous Average Order Value",
                "Average Order Value",
                "AOV Growth %",
                "Period Status",
                "Previous Period Complete",
                "Comparable",
            ]
        ].copy()

    # =====================================================
    # 13. MONTHLY YEAR-OVER-YEAR GROWTH
    # =====================================================

    def monthly_year_over_year_growth(self) -> pd.DataFrame:
        data = self.monthly_sales()
        return self._growth_analysis(data, "Month", pd.DateOffset(years=1))

    # =====================================================
    # ROLLING ANALYSIS
    # =====================================================

    def _complete_monthly_series(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty:
            return data.copy()

        result = data.copy()
        result["Month"] = (
            pd.to_datetime(result["Month"], errors="coerce")
            .dt.to_period("M")
            .dt.start_time
        )
        result = result.dropna(subset=["Month"]).copy()
        if result.empty:
            return result
        result = result.sort_values("Month").drop_duplicates(subset=["Month"], keep="first")

        first_month = result["Month"].min()
        last_month = result["Month"].max()
        if pd.isna(first_month) or pd.isna(last_month):
            return result.reset_index(drop=True)

        month_range = pd.date_range(start=first_month, end=last_month, freq="MS")
        result = result.set_index("Month")
        result = result.reindex(month_range)
        result.index.name = "Month"
        result = result.reset_index()

        numeric_columns = ["Revenue", "Quantity", "Orders", "Products", "Customers"]
        for col in numeric_columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0.0)

        result["Average Order Value"] = 0.0
        valid_orders = result["Orders"] > 0
        result.loc[valid_orders, "Average Order Value"] = (
            result.loc[valid_orders, "Revenue"] / result.loc[valid_orders, "Orders"]
        )

        result["Period Complete"] = result["Period Complete"].fillna(False).astype(bool)
        result["Period Status"] = result["Period Status"].fillna("Missing").astype("string")
        return result.sort_values("Month").reset_index(drop=True)

    def _rolling_analysis(self, window: int) -> pd.DataFrame:
        if window <= 0:
            raise ValueError("Rolling window must be greater than zero.")

        data = self.monthly_sales().copy()
        data = self._complete_monthly_series(data)

        columns = [
            "Month",
            "Revenue",
            "Quantity",
            "Orders",
            "Products",
            "Customers",
            "Average Order Value",
            "Rolling Revenue",
            "Rolling Quantity",
            "Rolling Orders",
            "Rolling AOV",
            "Rolling Periods",
            "Rolling Complete",
        ]

        if data.empty:
            return pd.DataFrame(columns=columns)

        data = data.sort_values("Month").reset_index(drop=True)

        data["Rolling Revenue"] = data["Revenue"].rolling(window=window, min_periods=window).sum()
        data["Rolling Quantity"] = data["Quantity"].rolling(window=window, min_periods=window).sum()
        data["Rolling Orders"] = data["Orders"].rolling(window=window, min_periods=window).sum()
        data["Rolling Periods"] = data["Month"].rolling(window=window, min_periods=window).count()

        complete_period_count = (
            data["Period Complete"].astype(int).rolling(window=window, min_periods=window).sum()
        )
        data["Rolling Complete"] = (data["Rolling Periods"] == window) & (
            complete_period_count == window
        )

        data["Rolling AOV"] = float("nan")
        valid_rolling_orders = data["Rolling Orders"] > 0
        data.loc[valid_rolling_orders, "Rolling AOV"] = (
            data.loc[valid_rolling_orders, "Rolling Revenue"]
            / data.loc[valid_rolling_orders, "Rolling Orders"]
        )

        rolling_columns = ["Rolling Revenue", "Rolling Quantity", "Rolling Orders", "Rolling AOV"]
        data.loc[~data["Rolling Complete"], rolling_columns] = float("nan")

        return data[columns].reset_index(drop=True)

    # =====================================================
    # 14. 3-MONTH ROLLING
    # =====================================================

    def rolling_3_month(self) -> pd.DataFrame:
        return self._rolling_analysis(window=3)

    # =====================================================
    # 15. 6-MONTH ROLLING
    # =====================================================

    def rolling_6_month(self) -> pd.DataFrame:
        return self._rolling_analysis(window=6)

    # =====================================================
    # 16. 12-MONTH ROLLING
    # =====================================================

    def rolling_12_month(self) -> pd.DataFrame:
        return self._rolling_analysis(window=12)

    # =========================================================
    # TREND ANALYSIS
    # =========================================================

    @staticmethod
    def _classify_trend(growth_rate: float | None) -> str:
        if growth_rate is None:
            return "Baseline"
        if growth_rate >= 10.0:
            return "Strong Growth"
        if growth_rate >= 3.0:
            return "Moderate Growth"
        if growth_rate > -3.0:
            return "Stable"
        if growth_rate > -10.0:
            return "Moderate Decline"
        return "Strong Decline"

    @staticmethod
    def _trend_strength(growth_rate: float | None) -> str:
        if growth_rate is None:
            return "Baseline"
        abs_growth = abs(growth_rate)
        if abs_growth >= 10.0:
            return "Strong"
        if abs_growth >= 3.0:
            return "Moderate"
        return "Weak"

    def trend_analysis(self, frequency: str = "monthly") -> pd.DataFrame:
        freq_map = {
            "daily": self.daily_sales,
            "weekly": self.weekly_sales,
            "monthly": self.monthly_sales,
            "quarterly": self.quarterly_sales,
            "yearly": self.yearly_sales,
        }
        if frequency not in freq_map:
            raise ValueError("frequency must be one of: daily, weekly, monthly, quarterly, yearly")

        sales_data = freq_map[frequency]()
        if sales_data.empty:
            return pd.DataFrame(
                columns=[
                    "Period",
                    "Revenue",
                    "Revenue Growth %",
                    "Revenue Trend",
                    "Revenue Strength",
                    "Quantity",
                    "Quantity Growth %",
                    "Quantity Trend",
                    "Quantity Strength",
                    "Orders",
                    "Order Growth %",
                    "Order Trend",
                    "Order Strength",
                    "Average Order Value",
                    "AOV Growth %",
                    "AOV Trend",
                    "AOV Strength",
                ]
            )

        result = sales_data.copy()
        period_col_map = {
            "daily": "Date",
            "weekly": "Week",
            "monthly": "Month",
            "quarterly": "Quarter",
            "yearly": "Year",
        }
        period_column = period_col_map[frequency]
        result = result.rename(columns={period_column: "Period"})

        result["Revenue Growth %"] = result["Revenue"].pct_change(fill_method=None).mul(100.0)
        result["Quantity Growth %"] = result["Quantity"].pct_change(fill_method=None).mul(100.0)
        result["Order Growth %"] = result["Orders"].pct_change(fill_method=None).mul(100.0)
        result["AOV Growth %"] = result["Average Order Value"].pct_change(fill_method=None).mul(100.0)

        for col in ["Revenue", "Quantity", "Order", "AOV"]:
            growth_col = f"{col} Growth %"
            trend_col = f"{col} Trend"
            strength_col = f"{col} Strength"
            growth_vals = result[growth_col].tolist()
            result[trend_col] = [
                self._classify_trend(v) if pd.notna(v) else "Baseline" for v in growth_vals
            ]
            result[strength_col] = [
                self._trend_strength(v) if pd.notna(v) else "Baseline" for v in growth_vals
            ]

        columns = [
            "Period",
            "Revenue",
            "Revenue Growth %",
            "Revenue Trend",
            "Revenue Strength",
            "Quantity",
            "Quantity Growth %",
            "Quantity Trend",
            "Quantity Strength",
            "Orders",
            "Order Growth %",
            "Order Trend",
            "Order Strength",
            "Average Order Value",
            "AOV Growth %",
            "AOV Trend",
            "AOV Strength",
        ]
        return result[columns].copy()

    def overall_trend(self, frequency: str = "monthly") -> pd.DataFrame:
        trend_data = self.trend_analysis(frequency=frequency)
        if trend_data.empty:
            return pd.DataFrame(
                columns=[
                    "Period",
                    "Overall Trend",
                    "Overall Strength",
                    "Positive Metrics",
                    "Negative Metrics",
                ]
            )

        rows: list[dict[str, object]] = []
        for _, row in trend_data.iterrows():
            trends = [
                str(row["Revenue Trend"]),
                str(row["Quantity Trend"]),
                str(row["Order Trend"]),
                str(row["AOV Trend"]),
            ]
            growths = [
                row["Revenue Growth %"],
                row["Quantity Growth %"],
                row["Order Growth %"],
                row["AOV Growth %"],
            ]
            valid_growth = [float(v) for v in growths if pd.notna(v)]

            positive = sum(1 for t in trends if "Growth" in t)
            negative = sum(1 for t in trends if "Decline" in t)

            if not valid_growth:
                overall_trend = "Baseline"
                overall_strength = "Baseline"
            else:
                avg_growth = sum(valid_growth) / len(valid_growth)
                overall_trend = self._classify_trend(avg_growth)
                overall_strength = self._trend_strength(avg_growth)

            rows.append(
                {
                    "Period": row["Period"],
                    "Overall Trend": overall_trend,
                    "Overall Strength": overall_strength,
                    "Positive Metrics": positive,
                    "Negative Metrics": negative,
                }
            )
        return pd.DataFrame(rows)

    # =========================================================
    # SUSTAINED TREND ANALYSIS
    # =========================================================

    @staticmethod
    def _classify_sustained_trend(growth_values: list[float]) -> tuple[str, str]:
        if not growth_values:
            return "Baseline", "Baseline"

        positive_count = sum(1 for v in growth_values if v > 3.0)
        negative_count = sum(1 for v in growth_values if v < -3.0)
        stable_count = sum(1 for v in growth_values if -3.0 <= v <= 3.0)
        total = len(growth_values)

        if stable_count == total:
            return "Stable", "Weak"

        if positive_count == total:
            avg = sum(growth_values) / total
            return ("Strong Uptrend", "Strong") if avg >= 10.0 else ("Moderate Uptrend", "Moderate")

        if negative_count == total:
            avg = sum(growth_values) / total
            return ("Strong Downtrend", "Strong") if avg <= -10.0 else ("Moderate Downtrend", "Moderate")

        return "Volatile", "Mixed"

    def sustained_trend_analysis(
        self,
        frequency: str = "monthly",
        window: int = 3,
    ) -> pd.DataFrame:
        if window < 2:
            raise ValueError("window must be at least 2")

        trend_data = self.trend_analysis(frequency=frequency)
        if trend_data.empty:
            return pd.DataFrame(
                columns=[
                    "Period",
                    "Revenue Sustained Trend",
                    "Revenue Trend Strength",
                    "Quantity Sustained Trend",
                    "Quantity Trend Strength",
                    "Order Sustained Trend",
                    "Order Trend Strength",
                    "AOV Sustained Trend",
                    "AOV Trend Strength",
                ]
            )

        metrics = [
            ("Revenue Growth %", "Revenue Sustained Trend", "Revenue Trend Strength"),
            ("Quantity Growth %", "Quantity Sustained Trend", "Quantity Trend Strength"),
            ("Order Growth %", "Order Sustained Trend", "Order Trend Strength"),
            ("AOV Growth %", "AOV Sustained Trend", "AOV Trend Strength"),
        ]

        result = pd.DataFrame({"Period": trend_data["Period"]})

        for growth_col, trend_col, strength_col in metrics:
            growth_values = trend_data[growth_col].tolist()
            sustained_trends: list[str] = []
            strengths: list[str] = []

            for idx in range(len(growth_values)):
                if idx < window:
                    sustained_trends.append("Baseline")
                    strengths.append("Baseline")
                    continue

                window_vals = growth_values[idx - window : idx]
                valid_vals = [float(v) for v in window_vals if pd.notna(v)]
                trend, strength = self._classify_sustained_trend(valid_vals)
                sustained_trends.append(trend)
                strengths.append(strength)

            result[trend_col] = sustained_trends
            result[strength_col] = strengths

        return result

    # =========================================================
    # SEASONALITY ANALYSIS
    # =========================================================

    @staticmethod
    def _classify_seasonality(seasonal_index_range: float) -> str:
        if seasonal_index_range >= 0.50:
            return "Strong Seasonality"
        if seasonal_index_range >= 0.25:
            return "Moderate Seasonality"
        if seasonal_index_range >= 0.10:
            return "Weak Seasonality"
        return "No Clear Seasonality"

    def monthly_seasonality(self) -> pd.DataFrame:
        monthly_data = self.monthly_sales()
        columns = [
            "Month Number",
            "Month",
            "Average Revenue",
            "Seasonal Index",
            "Revenue Contribution",
            "Rank",
        ]
        if monthly_data.empty:
            return pd.DataFrame(columns=columns)

        data = monthly_data.copy()
        data["Month Number"] = pd.to_datetime(data["Month"], errors="coerce").dt.month
        month_names = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December",
        }
        data["Month Name"] = data["Month Number"].map(month_names)

        # Use agg() to produce a DataFrame explicitly
        monthly_average = (
            data.groupby(["Month Number", "Month Name"], as_index=False)
            .agg(Average_Revenue=("Revenue", "mean"))
        )

        overall_avg = float(data["Revenue"].mean())
        if overall_avg == 0.0:
            monthly_average["Seasonal Index"] = 0.0
        else:
            monthly_average["Seasonal Index"] = monthly_average["Average_Revenue"] / overall_avg

        total_avg_rev = float(monthly_average["Average_Revenue"].sum())
        if total_avg_rev == 0.0:
            monthly_average["Revenue Contribution"] = 0.0
        else:
            monthly_average["Revenue Contribution"] = (
                monthly_average["Average_Revenue"] / total_avg_rev * 100.0
            )

        monthly_average = monthly_average.sort_values(
            by="Average_Revenue", ascending=False
        ).reset_index(drop=True)
        monthly_average["Rank"] = monthly_average.index + 1

        result = monthly_average[
            [
                "Month Number",
                "Month Name",
                "Average_Revenue",
                "Seasonal Index",
                "Revenue Contribution",
                "Rank",
            ]
        ].copy()
        result.columns = columns
        return result

    def seasonality_summary(self) -> pd.DataFrame:
        columns = [
            "Seasonal Range",
            "Average Seasonal Index",
            "Peak Month",
            "Lowest Month",
            "Seasonality Classification",
            "Data Points",
            "Sufficient History",
        ]

        seasonality = self.monthly_seasonality()
        if seasonality.empty:
            return pd.DataFrame(
                [{
                    "Seasonal Range": 0.0,
                    "Average Seasonal Index": 0.0,
                    "Peak Month": "N/A",
                    "Lowest Month": "N/A",
                    "Seasonality Classification": "Insufficient Data",
                    "Data Points": 0,
                    "Sufficient History": False,
                }],
                columns=columns,
            )

        seasonal_indices: list[float] = []
        for val in seasonality["Seasonal Index"].tolist():
            if pd.notna(val):
                seasonal_indices.append(float(val))

        if not seasonal_indices:
            return pd.DataFrame(
                [{
                    "Seasonal Range": 0.0,
                    "Average Seasonal Index": 0.0,
                    "Peak Month": "N/A",
                    "Lowest Month": "N/A",
                    "Seasonality Classification": "Insufficient Data",
                    "Data Points": 0,
                    "Sufficient History": False,
                }],
                columns=columns,
            )

        seasonal_range = max(seasonal_indices) - min(seasonal_indices)
        avg_index = sum(seasonal_indices) / len(seasonal_indices)
        peak_month = str(seasonality.iloc[0]["Month"])
        lowest_month = str(seasonality.iloc[-1]["Month"])

        # -------------------------------------------------
        # History validation
        #
        # Seasonality should be based on repeated calendar
        # periods, not simply the number of distinct months.
        #
        # At least 24 months are required for a reliable
        # month-of-year seasonal pattern.
        # -------------------------------------------------

        monthly_data = self.monthly_sales()

        data_points = len(
            monthly_data
        )

        sufficient_history = (
            data_points >= 24
        )

        if sufficient_history:
            classification = (
                self._classify_seasonality(
                    seasonal_range,
                )
            )
        else:
            classification = (
                "Insufficient History"
            )

        return pd.DataFrame(
            [{
                "Seasonal Range": seasonal_range,
                "Average Seasonal Index": avg_index,
                "Peak Month": peak_month,
                "Lowest Month": lowest_month,
                "Seasonality Classification": classification,
                "Data Points": data_points,
                "Sufficient History": sufficient_history,
            }],
            columns=columns,
        )

    def quarterly_seasonality(self) -> pd.DataFrame:
        quarterly_data = self.quarterly_sales()
        columns = [
            "Quarter Number",
            "Quarter",
            "Average Revenue",
            "Seasonal Index",
            "Rank",
        ]
        if quarterly_data.empty:
            return pd.DataFrame(columns=columns)

        data = quarterly_data.copy()
        data["Quarter Number"] = pd.to_datetime(data["Quarter"], errors="coerce").dt.quarter
        quarter_names = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
        data["Quarter Name"] = data["Quarter Number"].map(quarter_names)

        quarter_average = (
            data.groupby(["Quarter Number", "Quarter Name"], as_index=False)
            .agg(Average_Revenue=("Revenue", "mean"))
        )

        overall_avg = float(data["Revenue"].mean())
        if overall_avg == 0.0:
            quarter_average["Seasonal Index"] = 0.0
        else:
            quarter_average["Seasonal Index"] = quarter_average["Average_Revenue"] / overall_avg

        quarter_average = quarter_average.sort_values(
            by="Average_Revenue", ascending=False
        ).reset_index(drop=True)
        quarter_average["Rank"] = quarter_average.index + 1

        result = quarter_average[
            [
                "Quarter Number",
                "Quarter Name",
                "Average_Revenue",
                "Seasonal Index",
                "Rank",
            ]
        ].copy()
        result.columns = columns
        return result

    # =====================================================
    # FORECASTING
    # =====================================================

    def _prepare_forecast_data(
        self,
        metric: str = "Revenue",
    ) -> pd.DataFrame:
        """
        Prepares complete monthly historical data for forecasting.

        Parameters
        ----------
        metric:
            Metric to forecast.

        Returns
        -------
        pd.DataFrame
            DataFrame containing Month and metric values.
        """

        monthly = self.monthly_sales().copy()

        if metric not in monthly.columns:
            raise ValueError(
                f"Unsupported forecast metric: {metric}"
            )

        if "Month" not in monthly.columns:
            raise ValueError(
                "Monthly sales data must contain a Month column."
            )

        data = monthly[
            [
                "Month",
                metric,
            ]
        ].copy()

        data["Month"] = pd.to_datetime(
            data["Month"],
            errors="coerce",
        )

        data[metric] = pd.to_numeric(
            data[metric],
            errors="coerce",
        )

        data = data.dropna(
            subset=[
                "Month",
                metric,
            ]
        )

        data = data.sort_values(
            "Month"
        ).reset_index(
            drop=True
        )

        return data

    def naive_forecast(
        self,
        metric: str = "Revenue",
        periods: int = 3,
    ) -> pd.DataFrame:
        """
        Generates a naive forecast.

        The most recent historical value is used as the
        forecast for every future period.

        Parameters
        ----------
        metric:
            Metric to forecast.
        periods:
            Number of future months.

        Returns
        -------
        pd.DataFrame
            Historical and forecast information.
        """

        if periods <= 0:
            raise ValueError(
                "periods must be greater than zero."
            )

        data = self._prepare_forecast_data(
            metric
        )

        if data.empty:
            return pd.DataFrame(
                columns=[
                    "Month",
                    "Actual",
                    "Forecast",
                    "Method",
                ]
            )

        last_month = data["Month"].iloc[-1]
        last_value = data[metric].iloc[-1]

        future_months = pd.date_range(
            start=last_month + pd.DateOffset(months=1),
            periods=periods,
            freq="MS",
        )

        forecast_values = [
            float(last_value)
            for _ in range(periods)
        ]

        return pd.DataFrame(
            {
                "Month": future_months,
                "Actual": [None] * periods,
                "Forecast": forecast_values,
                "Method": ["Naive"] * periods,
            }
        )

    def moving_average_forecast(
        self,
        metric: str = "Revenue",
        periods: int = 3,
        window: int = 3,
    ) -> pd.DataFrame:
        """
        Generates a moving-average forecast.

        Each future period uses the average of the latest
        available observations.

        Parameters
        ----------
        metric:
            Metric to forecast.
        periods:
            Number of future months.
        window:
            Number of historical periods used for averaging.

        Returns
        -------
        pd.DataFrame
            Forecast values.
        """

        if periods <= 0:
            raise ValueError(
                "periods must be greater than zero."
            )

        if window <= 0:
            raise ValueError(
                "window must be greater than zero."
            )

        data = self._prepare_forecast_data(
            metric
        )

        if data.empty:
            return pd.DataFrame(
                columns=[
                    "Month",
                    "Actual",
                    "Forecast",
                    "Method",
                ]
            )

        values = [
            float(value)
            for value in data[metric].tolist()
        ]

        if len(values) < window:
            raise ValueError(
                "Not enough historical data for the "
                f"requested {window}-period moving average."
            )

        working_values = values.copy()
        forecasts: list[float] = []

        for _ in range(periods):
            recent_values = working_values[-window:]

            average_value = float(
                np.mean(
                    recent_values
                )
            )

            forecasts.append(
                average_value
            )

            working_values.append(
                average_value
            )

        last_month = data["Month"].iloc[-1]

        future_months = pd.date_range(
            start=last_month + pd.DateOffset(months=1),
            periods=periods,
            freq="MS",
        )

        return pd.DataFrame(
            {
                "Month": future_months,
                "Actual": [None] * periods,
                "Forecast": forecasts,
                "Method": [
                    f"{window}-Month Moving Average"
                    for _ in range(periods)
                ],
            }
        )

    def linear_trend_forecast(
        self,
        metric: str = "Revenue",
        periods: int = 3,
    ) -> pd.DataFrame:
        """
        Generates a linear-trend forecast.

        A linear regression is fitted against the historical
        monthly observations and extrapolated into the future.

        Parameters
        ----------
        metric:
            Metric to forecast.
        periods:
            Number of future months.

        Returns
        -------
        pd.DataFrame
            Forecast values.
        """

        if periods <= 0:
            raise ValueError(
                "periods must be greater than zero."
            )

        data = self._prepare_forecast_data(
            metric
        )

        if len(data) < 2:
            raise ValueError(
                "At least two historical observations are "
                "required for linear trend forecasting."
            )

        values = [
            float(value)
            for value in data[metric].tolist()
        ]

        x_values = np.arange(
            len(values),
            dtype=float,
        )

        y_values = np.array(
            values,
            dtype=float,
        )

        slope, intercept = np.polyfit(
            x_values,
            y_values,
            1,
        )

        future_x = np.arange(
            len(values),
            len(values) + periods,
            dtype=float,
        )

        predictions = (
            intercept
            + slope * future_x
        )

        predictions = [
            max(
                0.0,
                float(value),
            )
            for value in predictions
        ]

        last_month = data["Month"].iloc[-1]

        future_months = pd.date_range(
            start=last_month + pd.DateOffset(months=1),
            periods=periods,
            freq="MS",
        )

        return pd.DataFrame(
            {
                "Month": future_months,
                "Actual": [None] * periods,
                "Forecast": predictions,
                "Method": [
                    "Linear Trend"
                    for _ in range(periods)
                ],
            }
        )

    def forecast_revenue(
        self,
        periods: int = 3,
        method: str = "moving_average",
        window: int = 3,
    ) -> pd.DataFrame:
        """
        Forecasts monthly revenue.

        Supported methods:
            - naive
            - moving_average
            - linear_trend
        """

        normalized_method = method.lower().strip()

        if normalized_method == "naive":
            return self.naive_forecast(
                metric="Revenue",
                periods=periods,
            )

        if normalized_method == "moving_average":
            return self.moving_average_forecast(
                metric="Revenue",
                periods=periods,
                window=window,
            )

        if normalized_method == "linear_trend":
            return self.linear_trend_forecast(
                metric="Revenue",
                periods=periods,
            )

        raise ValueError(
            "Unsupported forecasting method. "
            "Use 'naive', 'moving_average', "
            "or 'linear_trend'."
        )

    def forecast_summary(
        self,
        periods: int = 3,
        method: str = "moving_average",
        window: int = 3,
    ) -> pd.DataFrame:
        """
        Returns a business-friendly revenue forecast summary.
        """

        forecast = self.forecast_revenue(
            periods=periods,
            method=method,
            window=window,
        ).copy()

        if forecast.empty:
            return forecast

        forecast["Revenue"] = forecast[
            "Forecast"
        ]

        forecast["Month"] = pd.to_datetime(
            forecast["Month"],
            errors="coerce",
        )

        forecast["Month"] = (
            forecast["Month"]
            .dt.strftime("%Y-%m")
        )

        return forecast[
            [
                "Month",
                "Revenue",
                "Method",
            ]
        ]

    # =====================================================
    # FORECAST EVALUATION
    # =====================================================

    @staticmethod
    def _calculate_mae(
        actual: list[float],
        predicted: list[float],
    ) -> float:
        """
        Calculates Mean Absolute Error (MAE).
        """

        if not actual or not predicted:
            return float("nan")

        errors = [
            abs(
                actual_value - predicted_value
            )
            for actual_value, predicted_value in zip(
                actual,
                predicted,
            )
        ]

        return float(
            np.mean(errors)
        )

    @staticmethod
    def _calculate_rmse(
        actual: list[float],
        predicted: list[float],
    ) -> float:
        """
        Calculates Root Mean Squared Error (RMSE).
        """

        if not actual or not predicted:
            return float("nan")

        squared_errors = [
            (
                actual_value - predicted_value
            ) ** 2
            for actual_value, predicted_value in zip(
                actual,
                predicted,
            )
        ]

        return float(
            np.sqrt(
                np.mean(squared_errors)
            )
        )

    @staticmethod
    def _calculate_mape(
        actual: list[float],
        predicted: list[float],
    ) -> float:
        """
        Calculates Mean Absolute Percentage Error (MAPE).

        Zero actual values are excluded because percentage
        error is undefined for zero.
        """

        valid_pairs = [
            (
                actual_value,
                predicted_value,
            )
            for actual_value, predicted_value in zip(
                actual,
                predicted,
            )
            if actual_value != 0
        ]

        if not valid_pairs:
            return float("nan")

        percentage_errors = [
            abs(
                (
                    actual_value - predicted_value
                )
                / actual_value
            )
            * 100.0
            for actual_value, predicted_value in valid_pairs
        ]

        return float(
            np.mean(
                percentage_errors
            )
        )

    def _forecast_value(
        self,
        values: list[float],
        method: str,
        window: int = 3,
    ) -> float:
        """
        Generates one forecast value using a selected method.

        This helper is used during backtesting.
        """

        if not values:
            return float("nan")

        normalized_method = (
            method.lower().strip()
        )

        if normalized_method == "naive":
            return float(
                values[-1]
            )

        if normalized_method == "moving_average":
            if len(values) < window:
                return float("nan")

            recent_values = values[
                -window:
            ]

            return float(
                np.mean(
                    recent_values
                )
            )

        if normalized_method == "linear_trend":
            if len(values) < 2:
                return float("nan")

            x_values = np.arange(
                len(values),
                dtype=float,
            )

            y_values = np.array(
                values,
                dtype=float,
            )

            slope, intercept = np.polyfit(
                x_values,
                y_values,
                1,
            )

            next_x = float(
                len(values)
            )

            prediction = (
                intercept
                + slope * next_x
            )

            return max(
                0.0,
                float(prediction),
            )

        raise ValueError(
            "Unsupported forecasting method. "
            "Use 'naive', 'moving_average', "
            "or 'linear_trend'."
        )

    # =====================================================
    # UPDATED METHOD: forecast_backtest
    # =====================================================

    def forecast_backtest(
        self,
        metric: str = "Revenue",
        method: str = "moving_average",
        window: int = 3,
        min_history: int = 6,
    ) -> pd.DataFrame:
        """
        Backtests a forecasting method against historical
        monthly observations.

        Incomplete periods are excluded from the evaluation
        using the existing Period Complete field produced by
        the monthly sales analysis.

        Parameters
        ----------
        metric:
            Metric to evaluate.
        method:
            Forecasting method.
        window:
            Moving-average window.
        min_history:
            Minimum number of historical observations required
            before generating a forecast.

        Returns
        -------
        pd.DataFrame
            Actual, predicted and error values for complete
            historical periods only.
        """

        if min_history < 2:
            raise ValueError(
                "min_history must be at least 2."
            )

        if window <= 0:
            raise ValueError(
                "window must be greater than zero."
            )

        # -------------------------------------------------
        # Get monthly data directly so that we retain
        # Period Complete information.
        # -------------------------------------------------

        monthly = self.monthly_sales().copy()

        if metric not in monthly.columns:
            raise ValueError(
                f"Unsupported forecast metric: {metric}"
            )

        if "Month" not in monthly.columns:
            raise ValueError(
                "Monthly sales data must contain a Month column."
            )

        # -------------------------------------------------
        # Remove incomplete periods.
        # -------------------------------------------------

        if "Period Complete" in monthly.columns:
            period_complete = monthly[
                "Period Complete"
            ].astype(bool)

            monthly = monthly[
                period_complete
            ].copy()

        # -------------------------------------------------
        # Prepare required columns.
        # -------------------------------------------------

        data = monthly[
            [
                "Month",
                metric,
            ]
        ].copy()

        data["Month"] = pd.to_datetime(
            data["Month"],
            errors="coerce",
        )

        data[metric] = pd.to_numeric(
            data[metric],
            errors="coerce",
        )

        data = data.dropna(
            subset=[
                "Month",
                metric,
            ]
        )

        data = data.sort_values(
            "Month"
        ).reset_index(
            drop=True
        )

        # -------------------------------------------------
        # Validate historical data.
        # -------------------------------------------------

        if len(data) <= min_history:
            return pd.DataFrame(
                columns=[
                    "Month",
                    "Actual",
                    "Predicted",
                    "Absolute Error",
                    "Percentage Error",
                    "Method",
                ]
            )

        values = [
            float(value)
            for value in data[
                metric
            ].tolist()
        ]

        months = data[
            "Month"
        ].tolist()

        results: list[dict[str, object]] = []

        # -------------------------------------------------
        # Walk-forward backtesting.
        # -------------------------------------------------

        for index in range(
            min_history,
            len(values),
        ):
            history = values[
                :index
            ]

            actual_value = values[
                index
            ]

            predicted_value = (
                self._forecast_value(
                    values=history,
                    method=method,
                    window=window,
                )
            )

            if np.isnan(
                predicted_value
            ):
                continue

            absolute_error = abs(
                actual_value
                - predicted_value
            )

            if actual_value != 0:
                percentage_error = (
                    absolute_error
                    / abs(actual_value)
                ) * 100.0
            else:
                percentage_error = float(
                    "nan"
                )

            results.append(
                {
                    "Month": months[index],
                    "Actual": actual_value,
                    "Predicted": predicted_value,
                    "Absolute Error": absolute_error,
                    "Percentage Error": percentage_error,
                    "Method": method,
                }
            )

        return pd.DataFrame(
            results
        )

    def forecast_accuracy(
        self,
        metric: str = "Revenue",
        method: str = "moving_average",
        window: int = 3,
        min_history: int = 6,
    ) -> pd.DataFrame:
        """
        Calculates forecast accuracy metrics for one method.

        Returns
        -------
        pd.DataFrame
            MAE, RMSE, MAPE and number of backtest periods.
        """

        backtest = self.forecast_backtest(
            metric=metric,
            method=method,
            window=window,
            min_history=min_history,
        )

        if backtest.empty:
            return pd.DataFrame(
                [
                    {
                        "Metric": metric,
                        "Method": method,
                        "MAE": float("nan"),
                        "RMSE": float("nan"),
                        "MAPE": float("nan"),
                        "Backtest Periods": 0,
                    }
                ]
            )

        actual = [
            float(value)
            for value in backtest[
                "Actual"
            ].tolist()
        ]

        predicted = [
            float(value)
            for value in backtest[
                "Predicted"
            ].tolist()
        ]

        return pd.DataFrame(
            [
                {
                    "Metric": metric,
                    "Method": method,
                    "MAE": self._calculate_mae(
                        actual,
                        predicted,
                    ),
                    "RMSE": self._calculate_rmse(
                        actual,
                        predicted,
                    ),
                    "MAPE": self._calculate_mape(
                        actual,
                        predicted,
                    ),
                    "Backtest Periods": len(
                        actual
                    ),
                }
            ]
        )

    def compare_forecast_methods(
        self,
        metric: str = "Revenue",
        window: int = 3,
        min_history: int = 6,
    ) -> pd.DataFrame:
        """
        Compares all supported forecasting methods.
        """

        methods = [
            "naive",
            "moving_average",
            "linear_trend",
        ]

        results: list[pd.DataFrame] = []

        for method in methods:
            accuracy = self.forecast_accuracy(
                metric=metric,
                method=method,
                window=window,
                min_history=min_history,
            )

            results.append(
                accuracy
            )

        if not results:
            return pd.DataFrame(
                columns=[
                    "Metric",
                    "Method",
                    "MAE",
                    "RMSE",
                    "MAPE",
                    "Backtest Periods",
                ]
            )

        return pd.concat(
            results,
            ignore_index=True,
        ).sort_values(
            by="MAPE",
            na_position="last",
        ).reset_index(
            drop=True
        )

    def best_forecast_method(
        self,
        metric: str = "Revenue",
        window: int = 3,
        min_history: int = 6,
    ) -> str:
        """
        Returns the best forecasting method based on MAPE.
        """

        comparison = (
            self.compare_forecast_methods(
                metric=metric,
                window=window,
                min_history=min_history,
            )
        )

        if comparison.empty:
            return "moving_average"

        valid_results = comparison[
            comparison["MAPE"].notna()
        ]

        if valid_results.empty:
            return "moving_average"

        best_method = valid_results.iloc[0][
            "Method"
        ]

        if not isinstance(
            best_method,
            str,
        ):
            return "moving_average"

        return best_method

    # =========================================================
    # FORECAST RELIABILITY
    # =========================================================

    @staticmethod
    def _classify_forecast_reliability(
        mape: float,
        backtest_periods: int,
        model_gap: float,
    ) -> str:
        """
        Classifies forecast reliability using:

        1. Forecast error (MAPE)
        2. Number of historical backtest periods
        3. Difference between the best and second-best
           forecasting methods.

        Reliability levels:

            High
            Moderate
            Low
            Insufficient Data

        MAPE thresholds:

            <= 10% : strong
            <= 20% : good
            <= 30% : moderate
            > 30%  : weak
        """

        if backtest_periods < 6:
            return "Insufficient Data"

        # -------------------------------------------------
        # MAPE quality
        # -------------------------------------------------

        if mape <= 10.0:
            mape_score = 3
        elif mape <= 20.0:
            mape_score = 2
        elif mape <= 30.0:
            mape_score = 1
        else:
            mape_score = 0

        # -------------------------------------------------
        # Historical sample size
        # -------------------------------------------------

        if backtest_periods >= 12:
            history_score = 2
        elif backtest_periods >= 9:
            history_score = 1
        else:
            history_score = 0

        # -------------------------------------------------
        # Model agreement
        #
        # Smaller gap means multiple methods produce
        # similar results.
        # -------------------------------------------------

        if model_gap <= 5.0:
            agreement_score = 2
        elif model_gap <= 15.0:
            agreement_score = 1
        else:
            agreement_score = 0

        total_score = (
            mape_score
            + history_score
            + agreement_score
        )

        if total_score >= 6:
            return "High"

        if total_score >= 3:
            return "Moderate"

        return "Low"

    # =========================================================
    # FORECAST RELIABILITY ANALYSIS
    # =========================================================

    def forecast_reliability(
        self,
        metric: str = "Revenue",
        window: int = 3,
        min_history: int = 6,
    ) -> dict[str, object]:
        """
        Evaluates the reliability of the best available
        forecasting method.

        Returns:
            metric
            method
            mape
            mae
            rmse
            backtest_periods
            second_best_mape
            model_gap
            reliability_score
            reliability_level
            interpretation
        """

        comparison = (
            self.compare_forecast_methods(
                metric=metric,
                window=window,
                min_history=min_history,
            )
        )

        if comparison.empty:
            return {
                "metric": metric,
                "method": "N/A",
                "mape": float("nan"),
                "mae": float("nan"),
                "rmse": float("nan"),
                "backtest_periods": 0,
                "second_best_mape": float("nan"),
                "model_gap": float("nan"),
                "reliability_score": 0,
                "reliability_level": (
                    "Insufficient Data"
                ),
                "interpretation": (
                    "There is not enough historical "
                    "data to evaluate forecast "
                    "reliability."
                ),
            }

        required_columns = {
            "Method",
            "MAE",
            "RMSE",
            "MAPE",
            "Backtest Periods",
        }

        missing_columns = (
            required_columns
            - set(comparison.columns)
        )

        if missing_columns:
            missing_text = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                "Forecast comparison is missing "
                f"required columns: {missing_text}"
            )

        ordered = (
            comparison
            .sort_values(
                by="MAPE",
                ascending=True,
            )
            .reset_index(
                drop=True,
            )
        )

        best_row = ordered.iloc[0]

        best_mape = float(
            best_row["MAPE"]
        )

        best_mae = float(
            best_row["MAE"]
        )

        best_rmse = float(
            best_row["RMSE"]
        )

        backtest_periods = int(
            best_row["Backtest Periods"]
        )

        if len(ordered) >= 2:
            second_best_mape = float(
                ordered.iloc[1]["MAPE"]
            )

            model_gap = (
                second_best_mape
                - best_mape
            )
        else:
            second_best_mape = float(
                "nan"
            )

            model_gap = float(
                "nan"
            )

        # -------------------------------------------------
        # Reliability scoring
        # -------------------------------------------------

        if len(ordered) >= 2:
            reliability_level = (
                self._classify_forecast_reliability(
                    mape=best_mape,
                    backtest_periods=(
                        backtest_periods
                    ),
                    model_gap=model_gap,
                )
            )
        else:
            reliability_level = (
                self._classify_forecast_reliability(
                    mape=best_mape,
                    backtest_periods=(
                        backtest_periods
                    ),
                    model_gap=100.0,
                )
            )

        # -------------------------------------------------
        # Numerical reliability score
        #
        # Score is normalized to 0-100.
        # -------------------------------------------------

        if best_mape <= 10.0:
            mape_points = 50
        elif best_mape <= 20.0:
            mape_points = 40
        elif best_mape <= 30.0:
            mape_points = 30
        elif best_mape <= 40.0:
            mape_points = 15
        else:
            mape_points = 5

        if backtest_periods >= 12:
            history_points = 25
        elif backtest_periods >= 9:
            history_points = 20
        elif backtest_periods >= 6:
            history_points = 10
        else:
            history_points = 0

        if len(ordered) >= 2:
            if model_gap <= 5.0:
                agreement_points = 25
            elif model_gap <= 15.0:
                agreement_points = 15
            else:
                agreement_points = 5
        else:
            agreement_points = 0

        reliability_score = (
            mape_points
            + history_points
            + agreement_points
        )

        # -------------------------------------------------
        # Business interpretation
        # -------------------------------------------------

        if reliability_level == "High":
            interpretation = (
                "The forecast has strong historical "
                "accuracy and sufficient backtest "
                "evidence. It is suitable for "
                "business planning, while still "
                "requiring normal monitoring."
            )

        elif reliability_level == "Moderate":
            interpretation = (
                "The forecast has useful predictive "
                "value, but historical errors or "
                "limited backtest evidence create "
                "meaningful uncertainty. Use it as "
                "a planning guide rather than an "
                "exact target."
            )

        elif reliability_level == "Low":
            interpretation = (
                "The forecast has substantial "
                "uncertainty based on historical "
                "errors and/or model disagreement. "
                "It should not be used as a standalone "
                "decision input."
            )

        else:
            interpretation = (
                "There is insufficient historical "
                "evidence to establish reliable "
                "forecast performance."
            )

        return {
            "metric": metric,
            "method": str(
                best_row["Method"]
            ),
            "mape": round(
                best_mape,
                4,
            ),
            "mae": round(
                best_mae,
                2,
            ),
            "rmse": round(
                best_rmse,
                2,
            ),
            "backtest_periods": (
                backtest_periods
            ),
            "second_best_mape": (
                round(
                    second_best_mape,
                    4,
                )
                if not math.isnan(
                    second_best_mape
                )
                else float("nan")
            ),
            "model_gap": (
                round(
                    model_gap,
                    4,
                )
                if not math.isnan(
                    model_gap
                )
                else float("nan")
            ),
            "reliability_score": (
                reliability_score
            ),
            "reliability_level": (
                reliability_level
            ),
            "interpretation": (
                interpretation
            ),
        }

    # =========================================================
    # FORECAST PREDICTION INTERVALS (HORIZON-AWARE)
    # =========================================================

    def forecast_prediction_intervals(
        self,
        metric: str = "Revenue",
        periods: int = 3,
        method: str = "linear_trend",
        window: int = 3,
        min_history: int = 6,
        confidence: float = 0.95,
    ) -> pd.DataFrame:
        """
        Generates forecasts with horizon-aware prediction
        intervals.

        Historical backtest errors are used to estimate the
        uncertainty of the forecast.

        The interval becomes wider as the forecast horizon
        increases. Therefore:

            1 month ahead  -> narrower interval
            2 months ahead -> wider interval
            3 months ahead -> widest interval

        Parameters
        ----------
        metric:
            Metric to forecast.

        periods:
            Number of future periods.

        method:
            Forecasting method.

        window:
            Moving-average window.

        min_history:
            Minimum historical periods required for
            backtesting.

        confidence:
            Confidence level.

            Supported standard values:
                0.90
                0.95
                0.99

            Other values are supported using the standard
            normal distribution.

        Returns
        -------
        pd.DataFrame
            Forecast dataframe containing:

                Month
                Forecast
                Lower Bound
                Upper Bound
                Confidence
                Interval Width
                Forecast Horizon

        Notes
        -----
        The uncertainty is estimated from historical
        backtest forecast errors rather than using an
        arbitrary percentage.

        The horizon multiplier follows:

            sqrt(h)

        where h is the forecast horizon.

        This is a standard way to increase uncertainty
        as the forecast moves further into the future.
        """

        # -------------------------------------------------
        # Validate parameters
        # -------------------------------------------------

        if periods <= 0:
            raise ValueError(
                "periods must be greater than 0."
            )

        if min_history <= 0:
            raise ValueError(
                "min_history must be greater than 0."
            )

        if window <= 0:
            raise ValueError(
                "window must be greater than 0."
            )

        if not 0.0 < confidence < 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        valid_methods = {
            "moving_average",
            "naive",
            "linear_trend",
        }

        if method not in valid_methods:
            raise ValueError(
                "Unsupported forecasting method: "
                f"{method}"
            )

        # -------------------------------------------------
        # Generate point forecast
        # -------------------------------------------------

        forecast = self.forecast_revenue(
            periods=periods,
            method=method,
            window=window,
        )

        if forecast.empty:
            raise ValueError(
                "Unable to generate forecast."
            )

        if "Forecast" not in forecast.columns:
            raise ValueError(
                "Forecast output is missing the "
                "'Forecast' column."
            )

        # -------------------------------------------------
        # Generate historical backtest
        # -------------------------------------------------

        backtest = self.forecast_backtest(
            metric=metric,
            method=method,
            window=window,
            min_history=min_history,
        )

        if backtest.empty:
            raise ValueError(
                "Insufficient historical data to "
                "calculate prediction intervals."
            )

        required_columns = {
            "Actual",
            "Predicted",
        }

        missing_columns = (
            required_columns
            - set(backtest.columns)
        )

        if missing_columns:
            missing_text = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                "Forecast backtest is missing "
                f"required columns: {missing_text}"
            )

        # -------------------------------------------------
        # Convert historical actual/predicted values
        # -------------------------------------------------

        actual_values = pd.to_numeric(
            backtest["Actual"],
            errors="coerce",
        )

        predicted_values = pd.to_numeric(
            backtest["Predicted"],
            errors="coerce",
        )

        errors = (
            actual_values
            - predicted_values
        ).dropna()

        if len(errors) < 2:
            raise ValueError(
                "At least two historical forecast "
                "errors are required to calculate "
                "prediction intervals."
            )

        # -------------------------------------------------
        # Calculate historical error standard deviation
        # -------------------------------------------------

        error_std_value = errors.std(
            ddof=1,
        )

        if pd.isna(error_std_value):
            raise ValueError(
                "Unable to calculate forecast error "
                "standard deviation."
            )

        error_std = float(
            error_std_value
        )

        if not math.isfinite(error_std):
            raise ValueError(
                "Forecast error standard deviation "
                "is not finite."
            )

        # -------------------------------------------------
        # Calculate confidence critical value
        # -------------------------------------------------

        if confidence == 0.90:
            z_value = 1.645

        elif confidence == 0.95:
            z_value = 1.960

        elif confidence == 0.99:
            z_value = 2.576

        else:
            from statistics import NormalDist

            z_value = NormalDist().inv_cdf(
                0.5 + confidence / 2.0,
            )

        # -------------------------------------------------
        # Prepare result
        # -------------------------------------------------

        result = forecast.copy()

        forecast_values = pd.to_numeric(
            result["Forecast"],
            errors="coerce",
        )

        if forecast_values.isna().any():
            raise ValueError(
                "Forecast contains invalid numeric values."
            )

        # -------------------------------------------------
        # Horizon-aware prediction intervals
        #
        # sqrt(h) causes uncertainty to increase with
        # forecast distance.
        #
        # Example:
        #
        # h=1 -> 1.000
        # h=2 -> 1.414
        # h=3 -> 1.732
        # -------------------------------------------------

        horizons = pd.Series(
            range(
                1,
                len(result) + 1,
            ),
            index=result.index,
            dtype="int64",
        )

        horizon_multiplier = horizons.astype(
            float
        ).pow(
            0.5,
        )

        interval_width = (
            z_value
            * error_std
            * horizon_multiplier
        )

        result["Lower Bound"] = (
            forecast_values
            - interval_width
        )

        result["Upper Bound"] = (
            forecast_values
            + interval_width
        )

        # -------------------------------------------------
        # Revenue cannot have a negative lower bound
        # -------------------------------------------------

        if metric.strip().lower() == "revenue":
            result["Lower Bound"] = (
                result["Lower Bound"]
                .clip(lower=0.0)
            )

        # -------------------------------------------------
        # Add metadata
        # -------------------------------------------------

        result["Confidence"] = (
            confidence * 100.0
        )

        result["Interval Width"] = (
            interval_width
        )

        result["Forecast Horizon"] = (
            horizons
        )

        return result