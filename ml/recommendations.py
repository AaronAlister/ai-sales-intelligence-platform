"""Evidence-based product and customer recommendations."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


class RecommendationEngine:
    """Generate simple, explainable recommendations from transaction data."""

    def __init__(self, db_path: str = "data/sales.db") -> None:
        self.db_path = Path(db_path)

    def product_opportunities(self, limit: int = 10) -> pd.DataFrame:
        if not self.db_path.exists():
            return pd.DataFrame()
        query = """
            SELECT item_code, item_name, transaction_type, amount, stock_qty,
                   discount_percent, invoice
            FROM sales
        """
        with sqlite3.connect(self.db_path) as connection:
            df = pd.read_sql_query(query, connection)
        if df.empty:
            return pd.DataFrame()

        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["stock_qty"] = pd.to_numeric(df["stock_qty"], errors="coerce").fillna(0)
        df["discount_percent"] = pd.to_numeric(df["discount_percent"], errors="coerce")
        df["type"] = df["transaction_type"].astype(str).str.strip().str.lower()
        sales = df[df["type"] == "sale"].copy()
        if sales.empty:
            return pd.DataFrame()

        summary = sales.groupby(["item_code", "item_name"], dropna=False).agg(
            Revenue=("amount", "sum"),
            Quantity=("stock_qty", "sum"),
            Orders=("invoice", "nunique"),
            AverageDiscount=("discount_percent", "mean"),
        ).reset_index()
        summary = summary[summary["Revenue"] > 0].copy()
        if summary.empty:
            return summary

        revenue_cutoff = summary["Revenue"].quantile(0.75)
        quantity_cutoff = summary["Quantity"].quantile(0.75)
        discount_cutoff = summary["AverageDiscount"].quantile(0.75)
        summary["Opportunity"] = "Monitor performance"
        summary.loc[
            (summary["Revenue"] >= revenue_cutoff) & (summary["Quantity"] >= quantity_cutoff),
            "Opportunity",
        ] = "Protect availability of high-performing product"
        summary.loc[
            (summary["AverageDiscount"] >= discount_cutoff) & (summary["Revenue"] < revenue_cutoff),
            "Opportunity",
        ] = "Review discount effectiveness"
        summary.loc[
            (summary["Revenue"] < summary["Revenue"].median())
            & (summary["Quantity"] >= quantity_cutoff),
            "Opportunity",
        ] = "Review revenue per unit and product mix"

        return summary.sort_values("Revenue", ascending=False).head(max(1, limit)).reset_index(drop=True)

    def customer_retention_opportunities(self, inactive_days: int = 90, limit: int = 20) -> pd.DataFrame:
        if not self.db_path.exists():
            return pd.DataFrame()
        query = """
            SELECT customer, invoice, posting_date, amount, transaction_type
            FROM sales
        """
        with sqlite3.connect(self.db_path) as connection:
            df = pd.read_sql_query(query, connection)
        if df.empty:
            return pd.DataFrame()

        df["posting_date"] = pd.to_datetime(df["posting_date"], errors="coerce")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["type"] = df["transaction_type"].astype(str).str.strip().str.lower()
        df = df[(df["type"] == "sale") & df["customer"].notna() & df["posting_date"].notna()]
        if df.empty:
            return pd.DataFrame()

        snapshot = df["posting_date"].max()
        result = df.groupby("customer", as_index=False).agg(
            LastPurchase=("posting_date", "max"),
            Orders=("invoice", "nunique"),
            LifetimeRevenue=("amount", "sum"),
        )
        result["DaysInactive"] = (snapshot - result["LastPurchase"]).dt.days
        result = result[result["DaysInactive"] >= max(1, inactive_days)].copy()
        result["Recommendation"] = "Review for a relevant re-engagement offer"
        return result.sort_values("LifetimeRevenue", ascending=False).head(max(1, limit)).reset_index(drop=True)
