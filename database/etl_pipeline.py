import sqlite3
import pandas as pd

from database.db import get_connection
from database.validation import validate_data
from database.preprocessing import preprocess_data


def upload_excel(file_path):

    # =====================================================
    # Read Excel
    # =====================================================

    try:
        df = pd.read_excel(file_path)

    except Exception as e:

        return {
            "success": False,
            "stage": "read_excel",
            "message": str(e)
        }

    rows_read = len(df)

    # =====================================================
    # Validation
    # =====================================================

    valid, validation_report = validate_data(df)

    if not valid:

        return {

            "success": False,

            "stage": "validation",

            "report": validation_report

        }

    # =====================================================
    # Preprocessing
    # =====================================================

    clean_df, cleaning_report = preprocess_data(df)

    # =====================================================
    # Database Connection
    # =====================================================

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # Get Existing Invoices
    # =====================================================

    cursor.execute("SELECT invoice FROM sales")

    existing_invoices = {
        row["invoice"]
        for row in cursor.fetchall()
    }

    uploaded_invoices = set(clean_df["Invoice"])

    duplicate_invoices = uploaded_invoices.intersection(existing_invoices)

    new_invoices = uploaded_invoices.difference(existing_invoices)

    # =====================================================
    # Entire File Already Uploaded
    # =====================================================

    if len(new_invoices) == 0:

        conn.close()

        return {

            "success": False,

            "stage": "duplicate_check",

            "duplicate_file": True,

            "message":
                "This dataset has already been uploaded.",

            "rows_read": rows_read,

            "existing_records": len(existing_invoices),

            "matching_records": len(duplicate_invoices),

            "duplicate_invoices": sorted(list(duplicate_invoices))
        }

    # =====================================================
    # Upload Only New Records
    # =====================================================

    rows_inserted = 0

    skipped_invoices = []

    try:

        for _, row in clean_df.iterrows():

            if row["Invoice"] in existing_invoices:

                skipped_invoices.append(row["Invoice"])
                continue

            cursor.execute("""

                INSERT INTO sales(

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
                    amount

                )

                VALUES(

                    ?,?,?,?,?,?,?,?,?,?,?

                )

            """, (

                row["Invoice"],
                row["Item Code"],
                row["Item Name"],
                row["Item Group"],
                row["Customer"],
                row["Place of Supply"],
                row["Posting Date"],
                row["Stock Qty"],
                row["Discount %"],
                row["Rate"],
                row["Amount"]

            ))

            rows_inserted += 1

        conn.commit()

    except sqlite3.Error as e:

        conn.rollback()

        conn.close()

        return {

            "success": False,

            "stage": "database",

            "message": str(e)

        }

    conn.close()

    # =====================================================
    # Upload Summary
    # =====================================================

    return {

        "success": True,

        "status": "Upload Completed Successfully",

        "rows_read": rows_read,

        "rows_after_preprocessing": len(clean_df),

        "rows_inserted": rows_inserted,

        "rows_skipped": len(skipped_invoices),

        "cleaning_report": cleaning_report,

        "duplicate_file": False,

        "existing_records_found": len(skipped_invoices) > 0,

        "duplicate_invoices": skipped_invoices,

        "message":

            f"{rows_inserted} new records uploaded successfully."

    }