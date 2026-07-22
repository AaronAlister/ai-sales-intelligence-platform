import pandas as pd


def preprocess_data(df):
    """
    Performs safe automatic cleaning.

    This function never attempts to repair invalid data.
    It only performs cleaning operations that cannot
    change the meaning of the dataset.

    Returns:
        cleaned_df
        cleaning_report
    """

    # Work on a copy
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

            "Action": "Removed Blank Rows",

            "Count": blank_rows

        })

    # ======================================================
    # Remove Exact Duplicate Rows
    # ======================================================

    duplicate_rows = df.duplicated().sum()

    if duplicate_rows > 0:

        df = df.drop_duplicates()

        cleaning_report.append({

            "Action": "Removed Duplicate Rows",

            "Count": duplicate_rows

        })

    # ======================================================
    # Trim Leading / Trailing Spaces
    # ======================================================

    text_columns = df.select_dtypes(include="object").columns

    trimmed_columns = 0

    for column in text_columns:

        original = df[column].copy()

        df[column] = df[column].astype(str).str.strip()

        if not original.equals(df[column]):
            trimmed_columns += 1

    if trimmed_columns > 0:

        cleaning_report.append({

            "Action": "Trimmed Text Fields",

            "Count": trimmed_columns

        })

    # ======================================================
    # Standardize Invoice IDs
    # ======================================================

    if "Invoice" in df.columns:

        df["Invoice"] = (
            df["Invoice"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        cleaning_report.append({

            "Action": "Standardized Invoice IDs",

            "Count": len(df)

        })

    # ======================================================
    # Summary
    # ======================================================

    rows_removed = original_rows - len(df)

    cleaning_report.append({

        "Action": "Rows Removed",

        "Count": rows_removed

    })

    cleaning_report.append({

        "Action": "Rows Remaining",

        "Count": len(df)

    })

    return df, cleaning_report