"""
Reusable sales database queries.

These functions are used by dashboards and the upload page.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from database.db import get_connection
from database.history import (
    get_last_upload,
    get_successful_upload_count,
    get_upload_count,
    get_upload_history,
)


class SalesQueries:
    """Queries used by the sales intelligence dashboards."""

    @staticmethod
    def customer_sales() -> list[dict[str, Any]]:
        """Return all sales records."""

        conn = get_connection()

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sales")
            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    @staticmethod
    def get_dataset_summary() -> dict[str, Any]:
        """Return high-level dataset statistics."""

        conn = get_connection()

        try:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM sales")
            total_records = int(cursor.fetchone()[0])

            cursor.execute(
                """
                SELECT COUNT(DISTINCT invoice)
                FROM sales
                """
            )
            total_invoices = int(cursor.fetchone()[0])

            cursor.execute(
                """
                SELECT MIN(posting_date), MAX(posting_date)
                FROM sales
                """
            )
            date_range = cursor.fetchone()

            return {
                "total_records": total_records,
                "total_invoices": total_invoices,
                "first_date": date_range[0],
                "last_date": date_range[1],
                "total_uploads": get_successful_upload_count(),
                "successful_uploads": get_successful_upload_count(),
                "last_upload": get_last_upload(),
            }

        finally:
            conn.close()

    @staticmethod
    def get_latest_posting_date() -> pd.Timestamp | None:
        """Return the latest transaction date in the sales database."""

        conn = get_connection()

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(posting_date) FROM sales")
            row = cursor.fetchone()

            if row is None or row[0] is None:
                return None

            parsed_date = pd.to_datetime(row[0], errors="coerce")

            if pd.isna(parsed_date):
                return None

            return pd.Timestamp(parsed_date)

        finally:
            conn.close()

    @staticmethod
    def get_upload_history(limit: int = 20) -> list[dict[str, Any]]:
        """Return recent upload history."""

        return get_upload_history(limit=limit)

    @staticmethod
    def get_last_upload() -> dict[str, Any] | None:
        """Return the latest upload."""

        return get_last_upload()