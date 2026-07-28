import hashlib
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

from database.db import get_connection
from database.validation import validate_data
from database.preprocessing import preprocess_data

# =====================================================
# ERP Configuration
# =====================================================

ERP_HEADER_ROW = 4  # Excel Row 5


# =====================================================
# File Hash
# =====================================================

def calculate_file_hash(file_path):
    """
    Calculates a SHA-256 hash of the uploaded Excel file.
    Used to prevent the same file from being uploaded twice.
    """

    sha = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(8192):
            sha.update(chunk)

    return sha.hexdigest()


# =====================================================
# Upload Pipeline
# =====================================================

def upload_excel(file_path):

    # =====================================================
    # Read Excel
    # =====================================================

    try:

        temp = pd.read_excel(file_path, header=None)

        header_row = None

        for row_index, (_, row) in enumerate(temp.iterrows()):

            values = [str(value).strip() for value in row.tolist()]

            if "Item Code" in values:
                header_row = row_index
                break

        if header_row is None:
            raise Exception("Could not find the ERP header row.")

        df = pd.read_excel(file_path, header=header_row)

        df = df.dropna(how="all")

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

    except Exception as e:

        return {
            "success": False,
            "stage": "read_excel",
            "message": str(e)
        }

    rows_read = len(df)
    file_name = Path(file_path).name
    file_hash = calculate_file_hash(file_path)

    # =====================================================
    # Validation
    # =====================================================

    valid, validation_report = validate_data(df, header_row)

    if not valid:

        return {
            "success": False,
            "stage": "validation",
            "report": validation_report
        }

    # =====================================================
    # Preprocessing
    # =====================================================

    (
        clean_df,
        cleaning_report,
        data_quality_summary,
        report_path
    ) = preprocess_data(df) # type: ignore

    rows_ready_for_upload = len(clean_df)

    # =====================================================
    # Database Connection
    # =====================================================

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # Duplicate File Check
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM upload_history
        WHERE file_hash = ?
        AND status = 'SUCCESS'
    """, (file_hash,))

    duplicate_file = cursor.fetchone()[0] > 0

    if duplicate_file:

        cursor.execute("""
            INSERT INTO upload_history(

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
        """, (

            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            file_name,
            file_hash,
            rows_read,
            0,
            0,
            rows_read,
            True,
            "REJECTED",
            "Duplicate file upload attempted."

        ))

        conn.commit()
        conn.close()

        return {
            "success": False,
            "stage": "duplicate_file",
            "message": "This Excel file has already been uploaded."
        }

    rows_uploaded = 0

    try:

        # =====================================================
        # Upload Sales Records
        # =====================================================

        for _, row in clean_df.iterrows():

            record_hash = hashlib.sha256(
                (
                    f"{row['Invoice']}|"
                    f"{row['Item Code']}|"
                    f"{row['Posting Date']}|"
                    f"{row['Stock Qty']}|"
                    f"{row['Amount']}"
                ).encode("utf-8")
            ).hexdigest()

            cursor.execute("""
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
            """, (

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
                row["transaction_type"]

            ))

            rows_uploaded += 1

        # =====================================================
        # Upload History
        # =====================================================

        cursor.execute("""
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
        """, (

            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            file_name,
            file_hash,
            rows_read,
            rows_ready_for_upload,
            rows_uploaded,
            0,
            False,
            "SUCCESS",
            f"{rows_uploaded} records uploaded successfully."

        ))

        conn.commit()

    # =====================================================
    # Database Error Handling
    # =====================================================

    except sqlite3.Error as e:

        conn.rollback()

        cursor.execute("""
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
        """, (

            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            file_name,
            file_hash,
            rows_read,
            rows_ready_for_upload,
            rows_uploaded,
            0,
            False,
            "FAILED",
            str(e)

        ))

        conn.commit()
        conn.close()

        return {

            "success": False,
            "stage": "database",
            "message": str(e)

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

        "message": f"{rows_uploaded} records uploaded successfully.",

        "upload_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "rows_read": rows_read,

        "rows_after_preprocessing": rows_ready_for_upload,

        "rows_removed": rows_removed,

        "return_transactions": data_quality_summary.get(
            "Return Transactions",
            0
        ),

        "duplicate_rows": data_quality_summary.get(
            "Exact Duplicate Rows",
            0
        ),

        "rows_inserted": rows_uploaded,

        "rows_skipped": 0,

        "duplicate_file": False,

        "existing_records_found": False,

        "data_quality_summary": data_quality_summary,

        "report_path": str(report_path),

        "cleaning_report": cleaning_report

    }