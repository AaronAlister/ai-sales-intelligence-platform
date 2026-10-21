"""RFM customer segmentation using K-means."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class CustomerSegmentation:
    """Segment customers by recency, purchase frequency, and monetary value."""

    def __init__(self, db_path: str = "data/sales.db") -> None:
        self.db_path = Path(db_path)

    def run(self, clusters: int = 4) -> pd.DataFrame:
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
        df["customer"] = df["customer"].astype("string").str.strip()
        df = df[(df["type"] == "sale") & df["customer"].notna() & df["posting_date"].notna()]
        df = df[df["customer"] != ""]
        if df.empty:
            return pd.DataFrame()

        snapshot = df["posting_date"].max() + pd.Timedelta(days=1)
        rfm = df.groupby("customer", as_index=False).agg(
            LastPurchase=("posting_date", "max"),
            Frequency=("invoice", "nunique"),
            Monetary=("amount", "sum"),
        )
        rfm["Recency"] = (snapshot - rfm["LastPurchase"]).dt.days
        rfm = rfm.drop(columns=["LastPurchase"])
        if len(rfm) < 2:
            rfm["Segment"] = "Insufficient customers"
            return rfm

        feature_columns = ["Recency", "Frequency", "Monetary"]
        features = rfm[feature_columns].clip(lower=0)
        scaled = StandardScaler().fit_transform(features)
        cluster_count = min(max(2, clusters), len(rfm))
        labels = KMeans(n_clusters=cluster_count, random_state=42, n_init=10).fit_predict(scaled)
        rfm["Cluster"] = labels

        # Give clusters readable labels based on their relative RFM profile.
        profile = rfm.groupby("Cluster")[feature_columns].mean()
        profile["ValueScore"] = (
            -profile["Recency"].rank(pct=True)
            + profile["Frequency"].rank(pct=True)
            + profile["Monetary"].rank(pct=True)
        )
        ordered = profile["ValueScore"].sort_values(ascending=False).index.tolist()
        names = ["High-value", "Loyal", "Potential", "Needs attention"]
        label_map = {
            cluster: names[min(index, len(names) - 1)]
            for index, cluster in enumerate(ordered)
        }
        rfm["Segment"] = rfm["Cluster"].map(label_map)
        return rfm.sort_values(["Segment", "Monetary"], ascending=[True, False]).reset_index(drop=True)
