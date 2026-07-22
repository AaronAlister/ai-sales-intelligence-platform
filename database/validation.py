import pandas as pd
from openpyxl.utils import get_column_letter

# ==========================================================
# Required Columns
# ==========================================================

REQUIRED_COLUMNS = [
    "Item Code",
    "Item Name",
    "Item Group",
    "Customer",
    "Place of Supply",
    "Invoice",
    "Posting Date",
    "Stock Qty",
    "Discount %",
    "Rate",
    "Amount"
]


# ==========================================================
# Helper Function
# ==========================================================

def add_error(errors, error_type, column, row, value, description):
    """
    Adds a structured validation error.
    """

    column_index = list(df_columns).index(column) + 1
    excel_column = get_column_letter(column_index)
    excel_row = row + 2  # +1 for zero-based index, +1 for header row

    errors.append({
        "Severity": "Error",
        "Type": error_type,
        "Cell": f"{excel_column}{excel_row}",
        "Column": column,
        "Value": value,
        "Description": description
    })


# ==========================================================
# Validation
# ==========================================================

def validate_data(df):

    global df_columns
    df_columns = df.columns.tolist()

    errors = []

    # ======================================================
    # Empty File
    # ======================================================

    if df.empty:

        errors.append({
            "Severity": "Error",
            "Type": "Empty File",
            "Cell": "-",
            "Column": "-",
            "Value": "-",
            "Description": "Uploaded file contains no records."
        })

        return False, errors

    # ======================================================
    # Required Columns
    # ======================================================

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        for column in missing_columns:

            errors.append({
                "Severity": "Error",
                "Type": "Missing Column",
                "Cell": "-",
                "Column": column,
                "Value": "-",
                "Description": "Required column is missing."
            })

        return False, errors

    # ======================================================
    # Missing Values
    # ======================================================

    required_fields = [
        "Item Code",
        "Item Name",
        "Customer",
        "Invoice",
        "Posting Date",
        "Stock Qty",
        "Rate",
        "Amount"
    ]

    for column in required_fields:

        missing_rows = df[df[column].isna()].index

        for row in missing_rows:

            add_error(
                errors,
                "Missing Value",
                column,
                row,
                None,
                "This field cannot be empty."
            )

    # ======================================================
    # Invalid Dates
    # ======================================================

    converted_dates = pd.to_datetime(
        df["Posting Date"],
        errors="coerce"
    )

    invalid_rows = converted_dates[converted_dates.isna()].index

    for row in invalid_rows:

        add_error(
            errors,
            "Invalid Date",
            "Posting Date",
            row,
            df.loc[row, "Posting Date"],
            "Invalid date format."
        )

    # ======================================================
    # Invalid Numeric Values
    # ======================================================

    numeric_columns = [
        "Stock Qty",
        "Discount %",
        "Rate",
        "Amount"
    ]

    for column in numeric_columns:

        converted = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        invalid_rows = converted[converted.isna()].index

        for row in invalid_rows:

            add_error(
                errors,
                "Invalid Number",
                column,
                row,
                df.loc[row, column],
                "Numeric value expected."
            )

    # ======================================================
    # Negative Values
    # ======================================================

    for column in [
        "Stock Qty",
        "Rate",
        "Amount"
    ]:

        converted = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        negative_rows = converted[converted < 0].index

        for row in negative_rows:

            add_error(
                errors,
                "Negative Value",
                column,
                row,
                df.loc[row, column],
                "Negative values are not allowed."
            )

    # ======================================================
    # Final Result
    # ======================================================

    if errors:
        return False, errors

    return True, []