import pandas as pd

pd.set_option("display.float_format", "{:,.2f}".format)

from engines.customer_engine import CustomerEngine

engine = CustomerEngine()

print("=" * 70)
print("CUSTOMER SUMMARY")
print("=" * 70)
print(engine.customer_summary().head(10))

print("\n" + "=" * 70)
print("TOP CUSTOMERS BY REVENUE")
print("=" * 70)
print(engine.top_customers_by_revenue())

print("\n" + "=" * 70)
print("TOP CUSTOMERS BY QUANTITY")
print("=" * 70)
print(engine.top_customers_by_quantity())

print("\n" + "=" * 70)
print("CUSTOMER REVENUE")
print("=" * 70)
print(engine.customer_revenue())

print("\n" + "=" * 70)
print("CUSTOMER SALES")
print("=" * 70)
print(engine.customer_sales())

print("\n" + "=" * 70)
print("REPEAT CUSTOMERS")
print("=" * 70)
print(engine.repeat_customers())

print("\n" + "=" * 70)
print("ONE TIME CUSTOMERS")
print("=" * 70)
print(engine.one_time_customers())

print("\n" + "=" * 70)
print("PURCHASE FREQUENCY")
print("=" * 70)
print(engine.purchase_frequency())

print("\n" + "=" * 70)
print("AVERAGE ORDER VALUE")
print("=" * 70)
print(engine.average_order_value())

print("\n" + "=" * 70)
print("CUSTOMER CONTRIBUTION")
print("=" * 70)
print(engine.customer_contribution())

print("\n" + "=" * 70)
print("HIGHEST CUSTOMER CONTRIBUTORS")
print("=" * 70)
print(engine.highest_customer_contributors())

print("\n" + "=" * 70)
print("PARETO CUSTOMERS")
print("=" * 70)
print(engine.pareto_customers())

print("\n" + "=" * 70)
print("PARETO SUMMARY")
print("=" * 70)
print(engine.pareto_summary())

print("\n" + "=" * 70)
print("ABC CUSTOMER ANALYSIS")
print("=" * 70)
print(engine.abc_customer_analysis())

print("\n" + "=" * 70)
print("ABC SUMMARY")
print("=" * 70)
print(engine.abc_summary())

print("\n" + "=" * 70)
print("ACTIVE CUSTOMERS")
print("=" * 70)
print(engine.active_customers())

print("\n" + "=" * 70)
print("DORMANT CUSTOMERS")
print("=" * 70)
print(engine.dormant_customers())

print("\n" + "=" * 70)
print("NEW CUSTOMERS")
print("=" * 70)
print(engine.new_customers())

print("\n" + "=" * 70)
print("MONTHLY CUSTOMER GROWTH")
print("=" * 70)
print(engine.monthly_customer_growth())

print("\n" + "=" * 70)
print("CUSTOMER DETAILS")
print("=" * 70)

customer = input("Enter Customer Name: ").strip()

try:
    details = engine.customer_details(customer)

    print()

    for key, value in details.items():
        print(f"{key:<30}: {value}")

except ValueError as e:
    print(e)

print("\n" + "=" * 70)
print("DEBUG - CUSTOMER CONTRIBUTION")
print("=" * 70)

contribution = engine.customer_contribution()

print(
    contribution[
        contribution["customer"]
        .str.strip()
        .str.lower()
        == "fountain bazaar"
    ]
)

print("\n" + "=" * 70)
print("DEBUG - ABC ANALYSIS")
print("=" * 70)

abc = engine.abc_customer_analysis()

print(
    abc[
        abc["customer"]
        .str.strip()
        .str.lower()
        == "fountain bazaar"
    ]
)