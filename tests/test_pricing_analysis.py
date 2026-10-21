import pandas as pd

from engines.pricing_engine import PricingEngine


pd.set_option(
    "display.float_format",
    "{:,.2f}".format,
)


def main() -> None:
    engine = PricingEngine()


    # =====================================================
    # PRICING SUMMARY
    # =====================================================

    print("=" * 70)
    print("PRICING SUMMARY")
    print("=" * 70)
    print(engine.pricing_summary())


    # =====================================================
    # AVERAGE DISCOUNT BY PRODUCT
    # =====================================================

    print("\n" + "=" * 70)
    print("AVERAGE DISCOUNT BY PRODUCT")
    print("=" * 70)
    print(engine.average_discount_by_product())


    # =====================================================
    # HIGHEST DISCOUNTED PRODUCTS
    # =====================================================

    print("\n" + "=" * 70)
    print("HIGHEST DISCOUNTED PRODUCTS")
    print("=" * 70)
    print(engine.highest_discounted_products())


    # =====================================================
    # AVERAGE DISCOUNT BY CUSTOMER
    # =====================================================

    print("\n" + "=" * 70)
    print("AVERAGE DISCOUNT BY CUSTOMER")
    print("=" * 70)
    print(engine.average_discount_by_customer())


    # =====================================================
    # AVERAGE DISCOUNT BY REGION
    # =====================================================

    print("\n" + "=" * 70)
    print("AVERAGE DISCOUNT BY REGION")
    print("=" * 70)
    print(engine.average_discount_by_region())


    # =====================================================
    # DISCOUNT BAND ANALYSIS
    # =====================================================

    print("\n" + "=" * 70)
    print("DISCOUNT BAND ANALYSIS")
    print("=" * 70)
    print(engine.discount_band_analysis())


    # =====================================================
    # REVENUE AFTER DISCOUNTS
    # =====================================================

    print("\n" + "=" * 70)
    print("REVENUE AFTER DISCOUNTS")
    print("=" * 70)
    print(engine.revenue_after_discounts())


    # =====================================================
    # DISCOUNT VS SALES ANALYSIS
    # =====================================================

    print("\n" + "=" * 70)
    print("DISCOUNT VS SALES ANALYSIS")
    print("=" * 70)

    discount_sales = engine.discount_vs_sales()

    print(
        f"Correlation between Discount % and Quantity Sold: "
        f"{discount_sales['correlation']:.4f}"
    )

    print("\nINTERPRETATION")
    print("-" * 70)
    print(discount_sales["interpretation"])

    print("\nPRODUCT-LEVEL DISCOUNT & SALES DATA")
    print("-" * 70)
    print(discount_sales["product_data"])


    # =====================================================
    # PRODUCT PRICING DETAILS
    # =====================================================

    print("\n" + "=" * 70)
    print("PRODUCT PRICING DETAILS")
    print("=" * 70)

    item_code = input("Enter Item Code: ").strip()

    try:
        details = engine.product_price_details(item_code)

        if details.empty:
            print(f"\nNo pricing data found for Item Code: {item_code}")
        else:
            print()

            row = details.iloc[0]

            print(f"{'Item Code':<30}: {row['Item Code']}")
            print(f"{'Product':<30}: {row['Product']}")
            print(f"{'Quantity':<30}: {row['Quantity']:,.2f}")
            print(f"{'Revenue':<30}: ₹{row['Revenue']:,.2f}")
            print(
                f"{'Average Discount %':<30}: "
                f"{row['Average Discount %']:,.2f}%"
            )

    except ValueError as e:
        print(e)


if __name__ == "__main__":
    main()
