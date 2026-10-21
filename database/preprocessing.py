
from pathlib import Path
from typing import Any

import pandas as pd


def preprocess_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]], dict[str, int], str]:
    """
    Clean invalid rows, classify returns and duplicates, and write a row-level
    data-quality report.

    Returns:
        cleaned_df, cleaning_report, data_quality_summary, report_path
    """
    df = df.copy()
    original_df = df.copy()
    original_rows = len(df)

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    row_index_offset = 6

    def excel_row(index: Any) -> int:
        return int(index) + row_index_offset

    def build_report_row(
        index: Any,
        row: pd.Series,
        issue: str,
        action: str,
    ) -> dict[str, Any]:
        return {
            "Excel Row": excel_row(index),
            "Invoice": row.get("Invoice", ""),
            "Item Code": row.get("Item Code", ""),
            "Qty": row.get("Stock Qty", ""),
            "Issue": issue,
            "Action": action,
        }

    cleaning_report: list[dict[str, Any]] = []
    row_issues: dict[Any, tuple[str, str]] = {}

    # Normalize fields used by validation.
    if "Invoice" in df.columns:
        df["Invoice"] = df["Invoice"].astype("string").fillna("").str.strip()

    if "Posting Date" in df.columns:
        df["Posting Date"] = (
            df["Posting Date"].astype("string").fillna("").str.strip()
        )

    # Blank rows.
    blank_mask = df.isna().all(axis=1)
    blank_count = int(blank_mask.sum())

    for index in df.index[blank_mask]:
        row_issues[index] = ("Blank Row", "Ignored")

    df = df.loc[~blank_mask].copy()
    cleaning_report.append(
        {"Action": "Blank Rows Removed", "Count": blank_count}
    )

    # Ignore TOTAL rows before invoice/date validation.
    total_mask = pd.Series(False, index=df.index)

    if "Item Code" in df.columns:
        total_mask = (
            df["Item Code"].astype("string").fillna("")
            .str.strip().str.upper()
            == "TOTAL"
        )

    total_count = int(total_mask.sum())

    for index in df.index[total_mask]:
        row_issues[index] = ("TOTAL Row", "Ignored")

    df = df.loc[~total_mask].copy()
    cleaning_report.append(
        {"Action": "TOTAL Row Ignored", "Count": total_count}
    )

    # Missing invoice.
    missing_invoice_mask = pd.Series(False, index=df.index)

    if "Invoice" in df.columns:
        invoice = df["Invoice"].astype("string").fillna("").str.strip()
        missing_invoice_mask = (
            invoice.eq("") | invoice.str.lower().eq("nan")
        )

    missing_invoice_count = int(missing_invoice_mask.sum())

    for index in df.index[missing_invoice_mask]:
        row_issues[index] = ("Missing Invoice", "Ignored")

    df = df.loc[~missing_invoice_mask].copy()
    cleaning_report.append(
        {
            "Action": "Rows Without Invoice Removed",
            "Count": missing_invoice_count,
        }
    )

    # Invalid dates.
    invalid_date_mask = pd.Series(False, index=df.index)

    if "Posting Date" in df.columns:
        invalid_date_mask = pd.to_datetime(
            df["Posting Date"], errors="coerce"
        ).isna()

    invalid_date_count = int(invalid_date_mask.sum())

    for index in df.index[invalid_date_mask]:
        row_issues[index] = ("Invalid Date", "Ignored")

    df = df.loc[~invalid_date_mask].copy()
    cleaning_report.append(
        {"Action": "Invalid Dates Removed", "Count": invalid_date_count}
    )

    # Negative rates.
    negative_rate_mask = pd.Series(False, index=df.index)

    if "Rate" in df.columns:
        negative_rate_mask = pd.to_numeric(
            df["Rate"], errors="coerce"
        ) < 0

    negative_rate_count = int(negative_rate_mask.sum())

    for index in df.index[negative_rate_mask]:
        row_issues[index] = ("Negative Rate", "Ignored")

    df = df.loc[~negative_rate_mask].copy()
    cleaning_report.append(
        {"Action": "Negative Rate Removed", "Count": negative_rate_count}
    )

    # Normalize retained text and dates.
    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:
        df[column] = df[column].astype("string").fillna("").str.strip()

    if "Invoice" in df.columns:
        df["Invoice"] = df["Invoice"].str.upper()

    if "Posting Date" in df.columns:
        df["Posting Date"] = pd.to_datetime(
            df["Posting Date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # Identify returns without removing them.
    returns_mask = pd.Series(False, index=df.index)

    if "Amount" in df.columns:
        returns_mask |= pd.to_numeric(
            df["Amount"], errors="coerce"
        ) < 0

    if "Stock Qty" in df.columns:
        returns_mask |= pd.to_numeric(
            df["Stock Qty"], errors="coerce"
        ) < 0

    df["transaction_type"] = "Sale"
    df.loc[returns_mask, "transaction_type"] = "Return"

    returns_count = int(returns_mask.sum())

    for index in df.index[returns_mask]:
        row_issues[index] = ("Return Transaction", "Retained")

    cleaning_report.append(
        {
            "Action": "Return Transactions Identified",
            "Count": returns_count,
        }
    )

    # Exact duplicates are flagged for review, not removed.
    duplicate_mask = df.duplicated(keep="first")
    duplicate_count = int(duplicate_mask.sum())

    for index in df.index[duplicate_mask]:
        if (
            index not in row_issues
            or row_issues[index][0] != "Return Transaction"
        ):
            row_issues[index] = ("Exact Duplicate Row", "Review")

    cleaning_report.append(
        {"Action": "Exact Duplicate Rows", "Count": duplicate_count}
    )

    # Include every original row in the report.
    quality_report_rows = []

    for index, row in original_df.iterrows():
        issue, action = row_issues.get(
            index, ("Valid Transaction", "Upload")
        )
        quality_report_rows.append(
            build_report_row(index, row, issue, action)
        )

    report_df = pd.DataFrame(
        quality_report_rows,
        columns=[
            "Excel Row",
            "Invoice",
            "Item Code",
            "Qty",
            "Issue",
            "Action",
        ],
    )

    if not report_df.empty:
        action_order = {
            "Ignored": 0,
            "Review": 1,
            "Retained": 2,
            "Upload": 3,
        }
        report_df["_Action Order"] = report_df["Action"].map(action_order)
        report_df = report_df.sort_values(
            ["_Action Order", "Excel Row"], kind="stable"
        ).drop(columns="_Action Order")

    rows_removed = original_rows - len(df)

    cleaning_report.extend(
        [
            {"Action": "Original Rows", "Count": int(original_rows)},
            {"Action": "Rows Removed", "Count": int(rows_removed)},
            {"Action": "Rows Ready For Upload", "Count": int(len(df))},
        ]
    )

    data_quality_summary = {
        "Exact Duplicate Rows": duplicate_count,
        "Return Transactions": returns_count,
    }

    report_path = reports_dir / "data_quality_report.csv"
    fallback_path = reports_dir / "data_quality_report_generated.csv"

    try:
        report_df.to_csv(report_path, index=False)
    except PermissionError:
        report_df.to_csv(fallback_path, index=False)
        report_path = fallback_path

    return df, cleaning_report, data_quality_summary, str(report_path.resolve())