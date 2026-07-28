from engines.kpi_engine import KPIEngine


def format_value(key, value, currency_fields, percentage_fields):

    if key in currency_fields:
        return f"\u20b9{value:,.2f}"

    if key in percentage_fields:
        return f"{value:.2f}%"

    if isinstance(value, float):
        return f"{value:,.2f}"

    if isinstance(value, int):
        return f"{value:,}"

    return f"{value}"


def print_section(title, keys, summary, currency_fields, percentage_fields):

    print(f"\n{title}")
    print("-" * 70)

    for key in keys:

        if key not in summary:
            continue

        value = summary[key]

        formatted = format_value(
            key,
            value,
            currency_fields,
            percentage_fields
        )

        print(f"{key:<30}: {formatted}")


def main():
    kpi = KPIEngine()

    summary = kpi.dashboard_summary()

    currency_fields = {
        "Gross Sales",
        "Returns Value",
        "Net Sales",
        "Average Order Value",
        "Average Revenue / Customer"
    }

    percentage_fields = {
        "Return Rate (%)",
        "Average Discount (%)"
    }

    sections = [
        (
            "SALES",
            [
                "Gross Sales",
                "Returns Value",
                "Net Sales",
                "Return Rate (%)"
            ]
        ),
        (
            "ORDERS",
            [
                "Total Orders",
                "Average Order Value",
                "Average Items / Order"
            ]
        ),
        (
            "PRODUCTS",
            [
                "Gross Quantity",
                "Net Quantity",
                "Return Transactions",
                "Total Products"
            ]
        ),
        (
            "CUSTOMERS",
            [
                "Total Customers",
                "Average Revenue / Customer",
                "Average Discount (%)"
            ]
        ),
        (
            "SYSTEM",
            [
                "Successful Uploads",
                "Latest Upload"
            ]
        )
    ]

    print("=" * 70)
    print("AI SALES INTELLIGENCE PLATFORM")
    print("EXECUTIVE KPI DASHBOARD")
    print("=" * 70)

    for title, keys in sections:
        print_section(
            title,
            keys,
            summary,
            currency_fields,
            percentage_fields
        )

    print("\n" + "=" * 70)

    kpi.close()


if __name__ == "__main__":
    main()