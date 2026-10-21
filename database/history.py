"""
Upload history database queries.

Reusable functions for the Streamlit upload dashboard.
"""

from __future__ import annotations

from typing import Any

from database.db import get_connection


def get_upload_history(limit: int = 20) -> list[dict[str, Any]]:
    """Return the most recent upload-history records."""

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                upload_timestamp,
                file_name,
                rows_read,
                rows_after_preprocessing,
                rows_inserted,
                rows_skipped,
                duplicate_file,
                status,
                message
            FROM upload_history
            ORDER BY upload_timestamp DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

    finally:
        conn.close()


def get_upload_count() -> int:
    """Return the total number of upload-history entries."""

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM upload_history")
        return int(cursor.fetchone()[0])

    finally:
        conn.close()


def get_successful_upload_count() -> int:
    """Return the number of successful uploads."""

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM upload_history
            WHERE status = 'SUCCESS'
            """
        )
        return int(cursor.fetchone()[0])

    finally:
        conn.close()


def get_last_upload() -> dict[str, Any] | None:
    """Return the most recent upload-history record."""

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                upload_timestamp,
                file_name,
                rows_read,
                rows_after_preprocessing,
                rows_inserted,
                rows_skipped,
                duplicate_file,
                status,
                message
            FROM upload_history
            ORDER BY upload_timestamp DESC, id DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        conn.close()
