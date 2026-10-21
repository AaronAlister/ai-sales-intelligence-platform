
"""Statistical anomaly detection for AQVASTAR sales data."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """Detect unusual monthly sales, returns, quantities, and discounts."""

    def __init__(self, db_path: str = "data/sales.db") -> None:
        self.db_path = Path(db_path)

    def _load_data(self) -> pd.DataFrame:
        if not self.db_path.exists():
            return pd.DataFrame()

        query = """
            SELECT posting_date, amount, stock_qty, discount_percent,
                   transaction_type, invoice, item_code, item_name,
                   customer, place_of_supply
            FROM sales
        """

        with sqlite3.connect(self.db_path) as connection:
            return pd.read_sql_query(query, connection)

    def detect_monthly_anomalies(
        self, contamination: float = 0.08
    ) -> pd.DataFrame:
        """Detect unusual monthly revenue, quantity, and returns."""

        df = self._load_data()
        columns = [
            "Month", "Revenue", "Quantity", "Returns",
            "Anomaly", "Anomaly Score",
        ]

        if df.empty:
            return pd.DataFrame(columns=columns)

        df["posting_date"] = pd.to_datetime(
            df["posting_date"], errors="coerce"
        )
        df["amount"] = pd.to_numeric(
            df["amount"], errors="coerce"
        ).fillna(0)
        df["stock_qty"] = pd.to_numeric(
            df["stock_qty"], errors="coerce"
        ).fillna(0)
        df["type"] = (
            df["transaction_type"].astype(str).str.strip().str.lower()
        )

        df = df.dropna(subset=["posting_date"]).copy()

        if df.empty:
            return pd.DataFrame(columns=columns)

        df["Month"] = df["posting_date"].dt.to_period("M").astype(str)

        monthly = df.groupby("Month", as_index=False).agg(
            Revenue=("amount", "sum"),
            Quantity=("stock_qty", "sum"),
            Returns=("type", lambda values: int(values.eq("return").sum())),
        )

        if len(monthly) < 6:
            monthly["Anomaly"] = "Insufficient history"
            monthly["Anomaly Score"] = float("nan")
            return monthly

        features = monthly[["Revenue", "Quantity", "Returns"]].copy()

        model = IsolationForest(
            contamination=min(max(contamination, 0.01), 0.25),
            random_state=42,
        )

        predictions = model.fit_predict(features)

        monthly["Anomaly"] = [
            "Unusual" if value == -1 else "Normal"
            for value in predictions
        ]
        monthly["Anomaly Score"] = model.decision_function(
            features
        ).round(4)

        return monthly.sort_values("Month").reset_index(drop=True)

    def detect_discount_outliers(
        self, contamination: float = 0.03
    ) -> pd.DataFrame:
        """Find transactions with unusual discount percentages."""

        columns = [
            "invoice", "item_code", "item_name",
            "discount_percent", "Anomaly Score",
        ]

        df = self._load_data()

        if df.empty:
            return pd.DataFrame(columns=columns)

        df["discount_percent"] = pd.to_numeric(
            df["discount_percent"], errors="coerce"
        )
        df = df[
            df["discount_percent"].between(0, 100)
        ].dropna(subset=["discount_percent"]).copy()

        if len(df) < 10:
            return pd.DataFrame(columns=columns)

        model = IsolationForest(
            contamination=min(max(contamination, 0.01), 0.25),
            random_state=42,
        )

        features = df[["discount_percent"]]
        mask = model.fit_predict(features) == -1

        df["Anomaly Score"] = model.decision_function(
            features
        ).round(4)

        return (
            df.loc[mask, columns]
            .sort_values("discount_percent", ascending=False)
            .reset_index(drop=True)
        )