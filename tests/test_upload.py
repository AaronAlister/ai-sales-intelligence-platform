from database.etl_pipeline import upload_excel


# ==========================================
# Excel File Path
# ==========================================

excel_file = r"data\uploads\Item_Wise_Sales_Register (66).xlsx"      # Change if your file has a different name


# ==========================================
# Run ETL Pipeline
# ==========================================

result = upload_excel(excel_file)


# ==========================================
# Display Result
# ==========================================

print("\n" + "=" * 60)
print("AI SALES INTELLIGENCE PLATFORM")
print("ETL PIPELINE REPORT")
print("=" * 60)

if not result["success"]:

    print(f"\n❌ Upload Failed")
    print(f"Stage : {result['stage']}")

    if result["stage"] == "validation":

        print("\nValidation Errors:\n")

        for error in result["report"]:

            print(
                f"[{error['Severity']}] "
                f"{error['Type']}"
            )

            print(f"Cell        : {error['Cell']}")
            print(f"Column      : {error['Column']}")
            print(f"Value       : {error['Value']}")
            print(f"Description : {error['Description']}")
            print("-" * 50)

    else:

        print(result["message"])


else:

    print("\n✅ Upload Successful\n")

    cleaning_counts = {
        item["Action"]: item["Count"]
        for item in result.get("cleaning_report", [])
    }

    total_rows_ignored = cleaning_counts.get("TOTAL Row Ignored", 0)
    return_transactions = result.get("return_transactions", 0)
    duplicate_rows = result.get("duplicate_rows", 0)

    print("=" * 50)
    print("UPLOAD SUMMARY")
    print("=" * 50)
    print(f"{'Rows Read':<30}: {result['rows_read']:,}")
    print(f"{'TOTAL Row Ignored':<30}: {total_rows_ignored:,}")
    print(f"{'Rows Removed':<30}: {result['rows_removed']:,}")
    print(f"{'Rows Uploaded':<30}: {result['rows_inserted']:,}")
    print()
    print(f"{'Return Transactions':<30}: {return_transactions:,}")
    print(f"{'Duplicate Rows':<30}: {duplicate_rows:,}")
    print()
    print("=" * 50)
    print("DATA QUALITY SUMMARY")
    print("=" * 50)
    print(f"{'Exact Duplicate Rows':<30}: {duplicate_rows:,}")

    print("\nDetailed Report Saved:")
    print(result["report_path"])

    print("\n" + "=" * 60)
    print("UPLOAD COMPLETED SUCCESSFULLY")
    print("=" * 60)
