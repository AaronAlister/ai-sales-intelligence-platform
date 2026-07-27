from database.etl_pipeline import upload_excel


# ==========================================
# Excel File Path
# ==========================================

excel_file = r"data\uploads\sales_missing_column.xlsx"      # Change if your file has a different name


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

    elif result["stage"] == "duplicate_check":

        print("\n⚠ Dataset already exists in the database.\n")

        print(f"Rows Read        : {result['rows_read']}")
        print(f"Matching Records : {result['matching_records']}")

        print("\nDuplicate Invoices:")

        for invoice in result["duplicate_invoices"]:
            print(f"  • {invoice}")

    else:

        print(result["message"])


else:

    print("\n✅ Upload Successful\n")

    print(f"Status                     : {result['status']}")
    print(f"Rows Read                  : {result['rows_read']}")
    print(f"Rows After Preprocessing   : {result['rows_after_preprocessing']}")
    print(f"Rows Uploaded              : {result['rows_inserted']}")
    print(f"Rows Skipped               : {result['rows_skipped']}")

    print("\nCleaning Report")

    for item in result["cleaning_report"]:

        print(
            f"  {item['Action']:<35} : {item['Count']}"
        )

    if result["existing_records_found"]:

        print("\nExisting invoices skipped:")

        for invoice in result["duplicate_invoices"]:

            print(f"  • {invoice}")

    print("\n" + "=" * 60)
    print("UPLOAD COMPLETED SUCCESSFULLY")
    print("=" * 60)