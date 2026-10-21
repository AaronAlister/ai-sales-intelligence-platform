"""
AQVASTAR Sales Intelligence Platform.

Excel upload and ETL pipeline with:
- exact-file duplicate detection
- business-record duplicate detection
- count-based duplicate handling
- preservation of repeated transactions within an upload
- upload history tracking
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from database.db import get_connection
from database.preprocessing import preprocess_data
from database.validation import validate_data


# =====================================================
# ERP Configuration
# =====================================================

ERP_HEADER_ROW = 4  # Excel Row 5

# Fields used to identify an already-imported business record.
# Counts are compared rather than using a set, so legitimate
# repeated transactions are preserved.
BUSINESS_KEY_COLUMNS: tuple[str, ...] = (
    "Invoice",
    "Item Code",
    "Posting Date",
    "Stock Qty",
    "Amount",
    "transaction_type",
)


# =====================================================
# File Hash
# =====================================================

def calculate_file_hash(file_path: str | Path) -> str:
    """
    Calculate a SHA-256 hash of the uploaded Excel file.

    This is a fast exact-file check. A renamed copy of the same
    file will still produce the same hash.
    """

    sha = hashlib.sha256()

    with Path(file_path).open("rb") as file:
        while chunk := file.read(8192):
            sha.update(chunk)

    return sha.hexdigest()


# =====================================================
# Business Record Key
# =====================================================

def _normalize_key_value(value: Any) -> str:
    """
    Convert a business-key value into a stable string.

    Numeric values are normalized so that values such as 1 and 1.0
    are treated as the same value.
    """

    if pd.isna(value):
        return ""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return format(float(value), ".12g")

    return str(value).strip().upper()


def _build_business_key(
    invoice: Any,
    item_code: Any,
    posting_date: Any,
    stock_qty: Any,
    amount: Any,
    transaction_type: Any,
) -> tuple[str, ...]:
    """Build the normalized business key used for duplicate detection."""

    return (
        _normalize_key_value(invoice),
        _normalize_key_value(item_code),
        _normalize_key_value(posting_date),
        _normalize_key_value(stock_qty),
        _normalize_key_value(amount),
        _normalize_key_value(transaction_type),
    )


def _incoming_business_key(row: pd.Series[Any]) -> tuple[str, ...]:
    """Build a business key from a preprocessed upload row."""

    return _build_business_key(
        row["Invoice"],
        row["Item Code"],
        row["Posting Date"],
        row["Stock Qty"],
        row["Amount"],
        row["transaction_type"],
    )


def _load_existing_record_counts(
    cursor: sqlite3.Cursor,
) -> Counter[tuple[str, ...]]:
    """
    Load counts of existing business records from the sales table.

    A Counter is intentionally used instead of a set. If a legitimate
    transaction occurs multiple times, its multiplicity is preserved.
    """

    cursor.execute(
        """
        SELECT
            invoice,
            item_code,
            posting_date,
            stock_qty,
            amount,
            transaction_type
        FROM sales
        """
    )

    existing_counts: Counter[tuple[str, ...]] = Counter()

    for row in cursor.fetchall():
        key = _build_business_key(
            row["invoice"],
            row["item_code"],
            row["posting_date"],
            row["stock_qty"],
            row["amount"],
            row["transaction_type"],
        )
        existing_counts[key] += 1

    return existing_counts


# =====================================================
# Upload History
# =====================================================

def _insert_upload_history(
    cursor: sqlite3.Cursor,
    *,
    file_name: str,
    file_hash: str,
    rows_read: int,
    rows_after_preprocessing: int,
    rows_inserted: int,
    rows_skipped: int,
    duplicate_file: bool,
    status: str,
    message: str,
) -> None:
    """Insert one upload-history record."""

    cursor.execute(
        """
        INSERT INTO upload_history (
            upload_timestamp,
            file_name,
            file_hash,
            rows_read,
            rows_after_preprocessing,
            rows_inserted,
            rows_skipped,
            duplicate_file,
            status,
            message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            file_name,
            file_hash,
            rows_read,
            rows_after_preprocessing,
            rows_inserted,
            rows_skipped,
            duplicate_file,
            status,
            message,
        ),
    )


# =====================================================
# Upload Pipeline
# =====================================================

def upload_excel(file_path: str | Path) -> dict[str, Any]:
    """
    Read, validate, preprocess and append an ERP Excel file.

    Duplicate handling:
    1. An exact file that was previously uploaded successfully is rejected.
    2. A renamed/re-exported file is compared against existing sales records.
    3. Existing business records are skipped.
    4. Repeated records inside the new file are preserved.
    5. If the new file contains more occurrences of a record than the
       database already contains, only the additional occurrences are inserted.
    """

    file_path = Path(file_path)
    file_name = file_path.name

    # =====================================================
    # Read Excel
    # =====================================================

    try:
        temp = pd.read_excel(file_path, header=None)

        header_row: int | None = None

        for row_index, (_, row) in enumerate(temp.iterrows()):
            values = [str(value).strip() for value in row.tolist()]

            if "Item Code" in values:
                header_row = row_index
                break

        if header_row is None:
            raise ValueError("Could not find the ERP header row.")

        df = pd.read_excel(file_path, header=header_row)

        df = df.dropna(how="all")

        df.columns = df.columns.astype(str).str.strip()

    except Exception as e:
        return {
            "success": False,
            "stage": "read_excel",
            "message": str(e),
        }

    rows_read = len(df)
    file_hash = calculate_file_hash(file_path)

    # =====================================================
    # Validation
    # =====================================================

    valid, validation_report = validate_data(df, header_row)

    if not valid:
        return {
            "success": False,
            "stage": "validation",
            "report": validation_report,
        }

    # =====================================================
    # Preprocessing
    # =====================================================

    (
        clean_df,
        cleaning_report,
        data_quality_summary,
        report_path,
    ) = preprocess_data(df)

    rows_ready_for_upload = len(clean_df)

    # =====================================================
    # Database Connection
    # =====================================================

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # =================================================
        # Exact File Duplicate Check
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM upload_history
            WHERE file_hash = ?
              AND status = 'SUCCESS'
            """,
            (file_hash,),
        )

        duplicate_file = cursor.fetchone()[0] > 0

        if duplicate_file:
            _insert_upload_history(
                cursor,
                file_name=file_name,
                file_hash=file_hash,
                rows_read=rows_read,
                rows_after_preprocessing=rows_ready_for_upload,
                rows_inserted=0,
                rows_skipped=rows_ready_for_upload,
                duplicate_file=True,
                status="REJECTED",
                message="Duplicate file upload attempted.",
            )

            conn.commit()

            return {
                "success": False,
                "stage": "duplicate_file",
                "message": "This Excel file has already been uploaded.",
                "rows_read": rows_read,
                "rows_after_preprocessing": rows_ready_for_upload,
                "rows_inserted": 0,
                "rows_skipped": rows_ready_for_upload,
                "duplicate_file": True,
            }

        # =================================================
        # Existing Business Record Counts
        # =================================================

        existing_counts = _load_existing_record_counts(cursor)

        rows_uploaded = 0
        rows_skipped = 0
        existing_records_found = False

        # =================================================
        # Upload Sales Records
        # =================================================

        for _, row in clean_df.iterrows():

            business_key = _incoming_business_key(row)

            # If the database already contains this business record,
            # consume one occurrence from the existing count.
            #
            # This means:
            # DB has A x 3, upload has A x 3 -> insert 0
            # DB has A x 3, upload has A x 5 -> insert 2
            # DB has A x 0, upload has A x 5 -> insert 5
            if existing_counts[business_key] > 0:
                existing_counts[business_key] -= 1
                rows_skipped += 1
                existing_records_found = True
                continue

            # Preserve the existing record_hash format for compatibility
            # with records already present in the database.
            record_hash = hashlib.sha256(
                (
                    f"{row['Invoice']}|"
                    f"{row['Item Code']}|"
                    f"{row['Posting Date']}|"
                    f"{row['Stock Qty']}|"
                    f"{row['Amount']}"
                ).encode("utf-8")
            ).hexdigest()

            cursor.execute(
                """
                INSERT INTO sales (
                    record_hash,
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_hash,
                    row["Invoice"],
                    row["Item Code"],
                    row.get("Item Name"),
                    row.get("Item Group"),
                    row.get("Customer"),
                    row.get("Place of Supply"),
                    row.get("Posting Date"),
                    row.get("Stock Qty"),
                    row.get("Discount %"),
                    row.get("Rate"),
                    row.get("Amount"),
                    row["transaction_type"],
                ),
            )

            rows_uploaded += 1

        # =================================================
        # Upload History
        # =================================================

        if rows_uploaded == 0 and rows_skipped > 0:
            history_message = (
                f"No new records found. {rows_skipped} existing records skipped."
            )
        elif rows_skipped > 0:
            history_message = (
                f"{rows_uploaded} new records uploaded successfully. "
                f"{rows_skipped} existing records skipped."
            )
        else:
            history_message = (
                f"{rows_uploaded} records uploaded successfully."
            )

        _insert_upload_history(
            cursor,
            file_name=file_name,
            file_hash=file_hash,
            rows_read=rows_read,
            rows_after_preprocessing=rows_ready_for_upload,
            rows_inserted=rows_uploaded,
            rows_skipped=rows_skipped,
            duplicate_file=False,
            status="SUCCESS",
            message=history_message,
        )

        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()

        try:
            _insert_upload_history(
                cursor,
                file_name=file_name,
                file_hash=file_hash,
                rows_read=rows_read,
                rows_after_preprocessing=rows_ready_for_upload,
                rows_inserted=rows_uploaded,
                rows_skipped=rows_skipped,
                duplicate_file=False,
                status="FAILED",
                message=str(e),
            )
            conn.commit()
        except sqlite3.Error:
            conn.rollback()

        return {
            "success": False,
            "stage": "database",
            "message": str(e),
        }

    finally:
        conn.close()

    # =====================================================
    # Upload Summary
    # =====================================================

    rows_removed = rows_read - rows_ready_for_upload

    return {
        "success": True,
        "status": "Upload Completed Successfully",
        "message": history_message,
        "upload_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows_read": rows_read,
        "rows_after_preprocessing": rows_ready_for_upload,
        "rows_removed": rows_removed,
        "return_transactions": data_quality_summary.get(
            "Return Transactions",
            0,
        ),
        "duplicate_rows": data_quality_summary.get(
            "Exact Duplicate Rows",
            0,
        ),
        "rows_inserted": rows_uploaded,
        "rows_skipped": rows_skipped,
        "duplicate_file": False,
        "existing_records_found": existing_records_found,
        "data_quality_summary": data_quality_summary,
        "report_path": str(report_path),
        "cleaning_report": cleaning_report,
    }
