import sqlite3
import pandas as pd

from database.db import get_connection
from database.validation import validate_data
from database.preprocessing import preprocess_data


def upload_excel(file_path):

    # ============================================
    # Read Excel
    # ============================================

    try:
        df = pd.read_excel(file_path)

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    rows_read = len(df)

    # ============================================
    # Validation
    # ============================================

    valid, validation_report = validate_data(df)

    if not valid:

        return {

            "success": False,

            "stage": "validation",

            "report": validation_report

        }

    # ============================================
    # Preprocessing
    # ============================================

    clean_df, cleaning_report = preprocess_data(df)

    # ============================================
    # Database
    # ============================================

    conn = get_connection()

    cursor = conn.cursor()

    rows_inserted = 0

    rows_skipped = 0

    skipped_invoices = []

    # ============================================
    # Insert Records
    # ============================================

    for _, row in clean_df.iterrows():

        try:

            cursor.execute("""

            INSERT INTO sales (

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

            VALUES (

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

        except sqlite3.IntegrityError:

            rows_skipped += 1

            skipped_invoices.append(row["Invoice"])

    conn.commit()

    conn.close()

    # ============================================
    # Upload Summary
    # ============================================

    return {

        "success": True,

        "rows_read": rows_read,

        "rows_after_preprocessing": len(clean_df),

        "rows_inserted": rows_inserted,

        "rows_skipped": rows_skipped,

        "cleaning_report": cleaning_report,

        "skipped_invoices": skipped_invoices

    }