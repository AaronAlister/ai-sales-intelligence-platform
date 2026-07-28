import pandas as pd

from database.preprocessing import preprocess_data


def test_preprocessing_report_uses_original_row_numbers_and_simple_columns(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"Invoice": "INV1", "Posting Date": "2024-01-01", "Amount": 10, "Stock Qty": 1},
            {"Invoice": "INV1", "Posting Date": "2024-01-01", "Amount": 10, "Stock Qty": 1},
            {"Invoice": "", "Posting Date": "bad-date", "Amount": -1, "Stock Qty": 1},
        ],
        index=[1000, 1001, 1002],
    )

    cleaned_df, _, _, report_path = preprocess_data(df)

    assert len(cleaned_df) == 2
    assert 1000 in cleaned_df.index
    assert 1001 in cleaned_df.index
    assert 1002 not in cleaned_df.index

    assert report_path == str(tmp_path / "reports" / "data_quality_report.csv")
    assert (tmp_path / "reports" / "data_quality_report.csv").exists()

    report_df = pd.read_csv(report_path)
    assert list(report_df.columns) == ["Excel Row", "Invoice", "Item Code", "Qty", "Issue", "Action"]

    duplicate_rows = report_df[report_df["Issue"].str.contains("Exact Duplicate Row")]
    assert not duplicate_rows.empty
    assert duplicate_rows.iloc[0]["Excel Row"] == 1007


def test_preprocessing_only_reviews_exact_duplicate_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"Invoice": "INV1", "Item Code": "ITEM1", "Posting Date": "2024-01-01", "Amount": 10, "Stock Qty": 1},
            {"Invoice": "INV1", "Item Code": "ITEM2", "Posting Date": "2024-01-01", "Amount": 20, "Stock Qty": 2},
            {"Invoice": "INV1", "Item Code": "ITEM2", "Posting Date": "2024-01-01", "Amount": 20, "Stock Qty": 2},
        ]
    )

    _, data_cleaning_report, data_quality_summary, report_path = preprocess_data(df)

    assert {"Action": "Rows Ready For Upload", "Count": 3} in data_cleaning_report
    assert data_quality_summary == {"Exact Duplicate Rows": 1, "Return Transactions": 0}

    report_df = pd.read_csv(report_path)
    review_rows = report_df[report_df["Action"].eq("Review")]
    upload_rows = report_df[report_df["Action"].eq("Upload")]

    assert len(review_rows) == 1
    assert review_rows.iloc[0]["Issue"] == "Exact Duplicate Row"
    assert len(upload_rows) == 2
    assert not report_df["Issue"].str.contains("Duplicate Invoice Numbers").any()
    assert not report_df["Issue"].str.contains("Repeated Item in Same Invoice").any()


def test_preprocessing_retains_returns_after_classifying_transaction_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"Invoice": "INV1", "Posting Date": "2024-01-01", "Amount": 10, "Stock Qty": 1},
            {"Invoice": "INV2", "Posting Date": "2024-01-02", "Amount": -5, "Stock Qty": 1},
            {"Invoice": "INV3", "Posting Date": "2024-01-03", "Amount": 5, "Stock Qty": -1},
        ]
    )

    cleaned_df, cleaning_report, data_quality_summary, report_path = preprocess_data(df)

    assert cleaned_df["transaction_type"].tolist() == ["Sale", "Return", "Return"]
    assert cleaned_df["Invoice"].tolist() == ["INV1", "INV2", "INV3"]
    assert {"Action": "Return Transactions Identified", "Count": 2} in cleaning_report
    assert data_quality_summary["Return Transactions"] == 2

    report_df = pd.read_csv(report_path)
    retained_returns = report_df[report_df["Issue"].eq("Return Transaction")]
    assert len(retained_returns) == 2
    assert set(retained_returns["Action"]) == {"Retained"}


def test_preprocessing_ignores_total_row(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"Invoice": "INV1", "Item Code": "ITEM1", "Posting Date": "2024-01-01", "Amount": 10, "Stock Qty": 1},
            {"Invoice": "", "Item Code": " total ", "Posting Date": "", "Amount": 10, "Stock Qty": 1},
        ]
    )

    cleaned_df, cleaning_report, _, report_path = preprocess_data(df)

    assert cleaned_df["Item Code"].tolist() == ["ITEM1"]
    assert {"Action": "TOTAL Row Ignored", "Count": 1} in cleaning_report

    report_df = pd.read_csv(report_path)
    ignored_total = report_df[report_df["Issue"].eq("TOTAL Row")]
    assert len(ignored_total) == 1
    assert ignored_total.iloc[0]["Action"] == "Ignored"


def test_preprocessing_report_groups_ignored_review_upload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"Invoice": "", "Item Code": "TOTAL", "Posting Date": "", "Amount": 45, "Stock Qty": 4},
            {"Invoice": "INV1", "Item Code": "ITEM1", "Posting Date": "2024-01-01", "Amount": 10, "Stock Qty": 1},
            {"Invoice": "INV2", "Item Code": "ITEM2", "Posting Date": "2024-01-02", "Amount": 20, "Stock Qty": 2},
            {"Invoice": "INV2", "Item Code": "ITEM2", "Posting Date": "2024-01-02", "Amount": 20, "Stock Qty": 2},
            {"Invoice": "INV3", "Item Code": "ITEM3", "Posting Date": "2024-01-03", "Amount": -5, "Stock Qty": 1},
        ]
    )

    _, _, _, report_path = preprocess_data(df)

    report_df = pd.read_csv(report_path)

    assert report_df["Action"].tolist() == ["Ignored", "Review", "Retained", "Upload", "Upload"]
