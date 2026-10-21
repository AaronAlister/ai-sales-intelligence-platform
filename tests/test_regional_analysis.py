
import pandas as pd

from engines.pricing_engine import PricingEngine


def display_table(
    df: pd.DataFrame,
    currency_columns: list[str] | None = None,
    decimal_columns: list[str] | None = None,
) -> None:
    """Format numerical values for clean terminal display."""
    display_df = df.copy()
    currency_columns = currency_columns or []
    decimal_columns = decimal_columns or []

    for column in currency_columns:
        if column in display_df.columns:
            display_df[column] = display_df[column].apply(
                lambda x: f"₹{x:,.2f}"
            )

    for column in decimal_columns:
        if column in display_df.columns:
            display_df[column] = display_df[column].apply(
                lambda x: f"{x:,.3f}"
            )

    for column in [
        "Average Discount",
        "Price Realization %",
        "Discount %",
    ]:
        if column in display_df.columns:
            display_df[column] = display_df[column].apply(
                lambda x: f"{x:,.2f}%"
            )

    for column in ["Orders", "Products", "Rank", "Quantity"]:
        if column in display_df.columns:
            display_df[column] = display_df[column].apply(
                lambda x: f"{int(float(str(x).replace(',', ''))):,}"
            )

    print(display_df.to_string(index=False))


def main() -> None:
    engine = PricingEngine()

    print("\n" + "=" * 70)
    print("PRICING SUMMARY")
    print("=" * 70)
    display_table(
        engine.pricing_summary(),
        currency_columns=["Value"],
    )

    print("\n" + "=" * 70)
    print("AVERAGE SELLING PRICE")
    print("=" * 70)
    display_table(
        engine.average_selling_price(),
        currency_columns=["Revenue", "Average Selling Price"],
        decimal_columns=["Quantity"],
    )

    print("\n" + "=" * 70)
    print("HIGHEST PRICED PRODUCTS")
    print("=" * 70)
    display_table(
        engine.highest_priced_products(10),
        currency_columns=["Average Selling Price", "Revenue"],
        decimal_columns=["Quantity"],
    )

    print("\n" + "=" * 70)
    print("LOWEST PRICED PRODUCTS")
    print("=" * 70)
    display_table(
        engine.lowest_priced_products(10),
        currency_columns=["Average Selling Price", "Revenue"],
        decimal_columns=["Quantity"],
    )

    print("\n" + "=" * 70)
    print("PRICE REALIZATION")
    print("=" * 70)
    price_realization = engine.price_realization()
    display_table(
        price_realization.head(30),
        currency_columns=["Gross Value", "Revenue", "Discount Amount"],
    )

    print("\nShowing first 30 price-realization records.")

    print("\n" + "=" * 70)
    print("PRICE REALIZATION SUMMARY")
    print("=" * 70)

    realization = engine.price_realization()

    if not realization.empty:
        print(
            f"Total Estimated Gross Value : "
            f"₹{realization['Gross Value'].sum():,.2f}"
        )
        print(
            f"Total Revenue               : "
            f"₹{realization['Revenue'].sum():,.2f}"
        )
        print(
            f"Total Estimated Discount    : "
            f"₹{realization['Discount Amount'].sum():,.2f}"
        )

        total_gross = realization["Gross Value"].sum()
        total_revenue = realization["Revenue"].sum()

        if total_gross > 0:
            overall_realization = total_revenue / total_gross * 100
            print(
                f"Overall Price Realization  : "
                f"{overall_realization:,.2f}%"
            )

    print("\n" + "=" * 70)
    print("PRODUCT PRICE DETAILS")
    print("=" * 70)

    item_code = input("Enter Item Code: ").strip()

    if item_code:
        price_data = engine.average_selling_price()
        product = price_data[
            price_data["Item Code"].astype(str) == item_code
        ]

        if product.empty:
            print(f"\nNo pricing data found for Item Code: {item_code}")
        else:
            row = product.iloc[0]

            print(f"\n{'Item Code':<30}: {row['Item Code']}")
            print(f"{'Product':<30}: {row['Product']}")
            print(f"{'Quantity':<30}: {row['Quantity']:,.3f}")
            print(f"{'Revenue':<30}: ₹{row['Revenue']:,.2f}")
            print(
                f"{'Average Selling Price':<30}: "
                f"₹{row['Average Selling Price']:,.2f}"
            )

            realization_data = realization[
                realization["Item Code"].astype(str) == item_code
            ]

            if not realization_data.empty:
                realization_row = realization_data.iloc[0]

                print(
                    f"{'Estimated Gross Value':<30}: "
                    f"₹{realization_row['Gross Value']:,.2f}"
                )
                print(
                    f"{'Estimated Discount Amount':<30}: "
                    f"₹{realization_row['Discount Amount']:,.2f}"
                )
                print(
                    f"{'Price Realization':<30}: "
                    f"{realization_row['Price Realization %']:,.2f}%"
                )


if __name__ == "__main__":
    main()
  