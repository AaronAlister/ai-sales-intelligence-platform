import pandas as pd
from openpyxl.utils import get_column_letter

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


def add_error(errors, df_columns, error_type, column, row, value, description, header_row):
    """Adds a structured validation error."""

    column_index = list(df_columns).index(column) + 1
    excel_column = get_column_letter(column_index)

    # Convert DataFrame index to original Excel row number
    excel_row = row + header_row + 2

    errors.append({
        "Severity": "Error",
        "Type": error_type,
        "Cell": f"{excel_column}{excel_row}",
        "Column": column,
        "Value": value,
        "Description": description
    })


def validate_data(df, header_row=0):
    """
    Validate ERP data.

    Parameters
    ----------
    df : pandas.DataFrame
    header_row : int
        Zero-based Excel header row detected in the ETL.

    Returns
    -------
    (bool, list)
    """

    errors = []

    # Remove completely blank rows
    df = df.dropna(how="all").copy()

    # Ignore ERP total row
    if "Item Code" in df.columns:
        mask = (
            df["Item Code"]
            .astype(str)
            .str.strip()
            .str.upper()
            .eq("TOTAL")
        )
        df = df.loc[~mask]

    # Keep original Excel row numbers
    df = df.reset_index(drop=False).rename(columns={"index": "_excel_index"})

    if df.empty:
        return False, [{
            "Severity": "Error",
            "Type": "Empty File",
            "Cell": "-",
            "Column": "-",
            "Value": "-",
            "Description": "Uploaded file contains no records."
        }]

    missing_columns = [
        c for c in REQUIRED_COLUMNS
        if c not in df.columns
    ]

    if missing_columns:
        for c in missing_columns:
            errors.append({
                "Severity": "Error",
                "Type": "Missing Column",
                "Cell": "-",
                "Column": c,
                "Value": "-",
                "Description": "Required column is missing."
            })
        return False, errors

    df_columns = [c for c in df.columns if c != "_excel_index"]

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
        missing = df[df[column].isna()]

        for _, r in missing.iterrows():
            add_error(
                errors,
                df_columns,
                "Missing Value",
                column,
                int(r["_excel_index"]),
                None,
                "This field cannot be empty.",
                header_row
            )

    converted_dates = pd.to_datetime(df["Posting Date"], errors="coerce")

    invalid_dates = df[
        converted_dates.isna() &
        df["Posting Date"].notna()
    ]

    for _, r in invalid_dates.iterrows():
        add_error(
            errors,
            df_columns,
            "Invalid Date",
            "Posting Date",
            int(r["_excel_index"]),
            r["Posting Date"],
            "Invalid date format.",
            header_row
        )

    numeric_columns = [
        "Stock Qty",
        "Discount %",
        "Rate",
        "Amount"
    ]

    for column in numeric_columns:

        converted = pd.to_numeric(df[column], errors="coerce")

        invalid = df[
            converted.isna() &
            df[column].notna()
        ]

        for _, r in invalid.iterrows():
            add_error(
                errors,
                df_columns,
                "Invalid Number",
                column,
                int(r["_excel_index"]),
                r[column],
                "Numeric value expected.",
                header_row
            )

    # Only Rate cannot be negative.
    converted_rate = pd.to_numeric(df["Rate"], errors="coerce")
    negative_rate = df[converted_rate < 0]

    for _, r in negative_rate.iterrows():
        add_error(
            errors,
            df_columns,
            "Negative Value",
            "Rate",
            int(r["_excel_index"]),
            r["Rate"],
            "Negative values are not allowed.",
            header_row
        )

    return (len(errors) == 0), errors
