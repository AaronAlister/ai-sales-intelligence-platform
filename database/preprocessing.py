import pandas as pd


def preprocess_data(df):
    """
    Performs safe automatic cleaning.

    This function never modifies business data.
    It only performs cleaning operations that are
    safe and reversible.

    Returns:
        cleaned_df
        cleaning_report
    """

    # ======================================================
    # Work on a Copy
    # ======================================================

    df = df.copy()

    cleaning_report = []

    original_rows = len(df)

    # ======================================================
    # Remove Completely Blank Rows
    # ======================================================

    blank_rows = df.isna().all(axis=1).sum()

    if blank_rows > 0:
        df = df.dropna(how="all")

    cleaning_report.append({
        "Action": "Blank Rows Removed",
        "Count": int(blank_rows)
    })

    # ======================================================
    # Remove Exact Duplicate Rows
    # ======================================================

    duplicate_rows = df.duplicated().sum()

    if duplicate_rows > 0:
        df = df.drop_duplicates()

    cleaning_report.append({
        "Action": "Duplicate Rows Removed",
        "Count": int(duplicate_rows)
    })

    # ======================================================
    # Trim Leading / Trailing Spaces
    # ======================================================

    text_columns = df.select_dtypes(include="object").columns

    trimmed_values = 0

    for column in text_columns:

        original = df[column].astype(str)

        cleaned = original.str.strip()

        trimmed_values += (original != cleaned).sum()

        df[column] = cleaned

    cleaning_report.append({
        "Action": "Text Values Trimmed",
        "Count": int(trimmed_values)
    })

    # ======================================================
    # Standardize Invoice IDs
    # ======================================================

    if "Invoice" in df.columns:

        original_invoice = df["Invoice"].astype(str)

        standardized_invoice = (
            original_invoice
            .str.strip()
            .str.upper()
        )

        invoice_changes = (
            original_invoice != standardized_invoice
        ).sum()

        df["Invoice"] = standardized_invoice

        cleaning_report.append({
            "Action": "Invoice IDs Standardized",
            "Count": int(invoice_changes)
        })

    # ======================================================
    # Standardize Posting Dates
    # ======================================================

    if "Posting Date" in df.columns:

        original_dates = df["Posting Date"].copy()

        standardized_dates = (
            pd.to_datetime(df["Posting Date"])
            .dt.strftime("%Y-%m-%d")
        )

        date_changes = (
            original_dates.astype(str) != standardized_dates
        ).sum()

        df["Posting Date"] = standardized_dates

        cleaning_report.append({
            "Action": "Posting Dates Standardized",
            "Count": int(date_changes)
        })

    # ======================================================
    # Summary
    # ======================================================

    rows_removed = original_rows - len(df)

    cleaning_report.append({
        "Action": "Original Rows",
        "Count": int(original_rows)
    })

    cleaning_report.append({
        "Action": "Rows Removed During Cleaning",
        "Count": int(rows_removed)
    })

    cleaning_report.append({
        "Action": "Rows Remaining",
        "Count": int(len(df))
    })

    return df, cleaning_report