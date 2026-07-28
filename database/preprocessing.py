import pandas as pd
from pathlib import Path


def preprocess_data(df):
    """
    Stage 1:
        - Remove invalid records.

    Stage 2:
        - Identify Returns
        - Identify Duplicate Transactions

    Returns:
        cleaned_df,
        cleaning_report,
        data_quality_summary,
        report_path
    """

    df = df.copy()

    original_rows = len(df)

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    row_index_offset = 6

    def excel_row(index):
        return int(index) + row_index_offset

    def build_report_row(index, row, status):
        return {
            "Excel Row": excel_row(index),
            "Invoice": row.get("Invoice", ""),
            "Item Code": row.get("Item Code", ""),
            "Qty": row.get("Stock Qty", ""),
            "Status": status
        }

    cleaning_report = []
    quality_report_rows = []

    # =====================================================
    # Normalize basic fields
    # =====================================================

    if "Invoice" in df.columns:
        df["Invoice"] = df["Invoice"].astype(str)

    if "Posting Date" in df.columns:
        df["Posting Date"] = df["Posting Date"].astype(str)

    # =====================================================
    # Stage 1 : Data Cleaning
    # =====================================================

    # -------------------------
    # Blank Rows
    # -------------------------

    blank_mask = df.isna().all(axis=1)

    blank_rows = int(blank_mask.sum())

    if blank_rows:

        for index, row in df[blank_mask].iterrows():
            quality_report_rows.append(
                build_report_row(index, row, "Removed")
            )

        df = df[~blank_mask]

    cleaning_report.append({
        "Action": "Blank Rows Removed",
        "Count": blank_rows
    })

    # -------------------------
    # TOTAL Row
    # -------------------------

    total_removed = 0

    if "Item Code" in df.columns:

        total_mask = (
            df["Item Code"]
            .astype(str)
            .str.strip()
            .str.upper()
            .eq("TOTAL")
        )

        total_removed = int(total_mask.sum())

        if total_removed:

            for index, row in df[total_mask].iterrows():
                quality_report_rows.append(
                    build_report_row(index, row, "Removed")
                )

            df = df[~total_mask]

    cleaning_report.append({
        "Action": "TOTAL Row Ignored",
        "Count": total_removed
    })

    # -------------------------
    # Missing Invoice
    # -------------------------

    missing_invoice_mask = pd.Series(False, index=df.index)

    if "Invoice" in df.columns:

        invoice = df["Invoice"].fillna("").astype(str).str.strip()

        missing_invoice_mask = (
            invoice.eq("") |
            invoice.str.lower().eq("nan")
        )

    missing_invoice_rows = int(missing_invoice_mask.sum())

    if missing_invoice_rows:

        for index, row in df[missing_invoice_mask].iterrows():
            quality_report_rows.append(
                build_report_row(index, row, "Removed")
            )

        df = df[~missing_invoice_mask]

    cleaning_report.append({
        "Action": "Rows Without Invoice Removed",
        "Count": missing_invoice_rows
    })

    # -------------------------
    # Invalid Dates
    # -------------------------

    invalid_date_mask = pd.Series(False, index=df.index)

    if "Posting Date" in df.columns:

        invalid_date_mask = pd.to_datetime(
            df["Posting Date"],
            errors="coerce"
        ).isna()

    invalid_date_rows = int(invalid_date_mask.sum())

    if invalid_date_rows:

        for index, row in df[invalid_date_mask].iterrows():
            quality_report_rows.append(
                build_report_row(index, row, "Removed")
            )

        df = df[~invalid_date_mask]

    cleaning_report.append({
        "Action": "Invalid Dates Removed",
        "Count": invalid_date_rows
    })

    # -------------------------
    # Negative Rate
    # -------------------------

    negative_rate_mask = pd.Series(False, index=df.index)

    if "Rate" in df.columns:

        negative_rate_mask = (
            pd.to_numeric(
                df["Rate"],
                errors="coerce"
            ) < 0
        )

    negative_rate_rows = int(negative_rate_mask.sum())

    if negative_rate_rows:

        for index, row in df[negative_rate_mask].iterrows():
            quality_report_rows.append(
                build_report_row(index, row, "Removed")
            )

        df = df[~negative_rate_mask]

    cleaning_report.append({
        "Action": "Negative Rate Removed",
        "Count": negative_rate_rows
    })

    # =====================================================
    # Normalize Data
    # =====================================================

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:
        df[column] = df[column].astype(str).str.strip()

    if "Invoice" in df.columns:
        df["Invoice"] = df["Invoice"].str.upper()

    if "Posting Date" in df.columns:
        df["Posting Date"] = (
            pd.to_datetime(
                df["Posting Date"],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d")
        )

    # =====================================================
    # Stage 2 : Data Quality Analysis
    # =====================================================

    # -------------------------
    # Return Transactions
    # -------------------------

    returns_mask = pd.Series(False, index=df.index)

    if "Amount" in df.columns:
        returns_mask |= (
            pd.to_numeric(df["Amount"], errors="coerce") < 0
        )

    if "Stock Qty" in df.columns:
        returns_mask |= (
            pd.to_numeric(df["Stock Qty"], errors="coerce") < 0
        )

    df["transaction_type"] = "Sale"
    df.loc[returns_mask, "transaction_type"] = "Return"

    returns_count = int(returns_mask.sum())

    if returns_count:

        for index, row in df[returns_mask].iterrows():

            quality_report_rows.append(
                build_report_row(
                    index,
                    row,
                    "Return"
                )
            )

    cleaning_report.append({
        "Action": "Return Transactions Identified",
        "Count": returns_count
    })

    # -------------------------
    # Exact Duplicate Rows
    # -------------------------

    exact_duplicate_mask = df.duplicated(keep="first")

    duplicate_count = int(exact_duplicate_mask.sum())

    cleaning_report.append({
        "Action": "Exact Duplicate Rows",
        "Count": duplicate_count
    })

    # -------------------------
    # Remaining Transactions (exceptions only)
    # -------------------------

    for index, row in df.iterrows():

        if returns_mask.loc[index]:
            continue

        if exact_duplicate_mask.loc[index]:
            quality_report_rows.append(
                build_report_row(
                    index,
                    row,
                    "Duplicate"
                )
            )

    # =====================================================
    # Summary
    # =====================================================

    rows_removed = original_rows - len(df)

    cleaning_report.extend([
        {
            "Action": "Original Rows",
            "Count": int(original_rows)
        },
        {
            "Action": "Rows Removed",
            "Count": int(rows_removed)
        },
        {
            "Action": "Rows Ready For Upload",
            "Count": int(len(df))
        }
    ])

    data_quality_summary = {
        "Rows Removed": int(rows_removed),
        "Return Transactions": returns_count,
        "Exact Duplicate Rows": duplicate_count
    }

    # =====================================================
    # Build Report
    # =====================================================

    report_df = pd.DataFrame(quality_report_rows)

    report_df = report_df[
        [
            "Excel Row",
            "Invoice",
            "Item Code",
            "Qty",
            "Status"
        ]
    ]

    status_order = {
        "Removed": 0,
        "Duplicate": 1,
        "Return": 2
    }

    report_df["_Sort"] = (
        report_df["Status"]
        .map(status_order)
        .fillna(99)
    )

    report_df = report_df.sort_values(
        by=["_Sort", "Excel Row"],
        kind="stable"
    )

    report_df = report_df.drop(columns="_Sort")

    report_path = reports_dir / "data_quality_report.csv"
    fallback_path = reports_dir / "data_quality_report_generated.csv"

    try:
        report_df.to_csv(report_path, index=False)

    except PermissionError:

        report_df.to_csv(
            fallback_path,
            index=False
        )

        report_path = fallback_path

    return (
        df,
        cleaning_report,
        data_quality_summary,
        str(report_path.resolve())
    )