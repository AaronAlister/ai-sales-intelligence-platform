from engines.regional_engine import RegionalEngine


engine = RegionalEngine()

print("\n" + "=" * 70)
print("AVAILABLE REGIONS")
print("=" * 70)

print(
    engine.get_regions()
)

# =====================================================
# DISPLAY HELPER
# =====================================================

def display_table(df, currency_columns=None, decimal_columns=None):
    """
    Formats numerical values for clean terminal display.
    """

    df = df.copy()

    currency_columns = currency_columns or []
    decimal_columns = decimal_columns or []

    # Format currency
    for column in currency_columns:
        if column in df.columns:
            df[column] = df[column].apply(
                lambda x: f"₹{x:,.2f}"
            )

    # Format decimal values
    for column in decimal_columns:
        if column in df.columns:
            df[column] = df[column].apply(
                lambda x: f"{x:,.3f}"
            )

    # Format integer values
    for column in ["Orders", "Customers", "Rank"]:
        if column in df.columns:
            df[column] = df[column].apply(
                lambda x: f"{int(x):,}"
            )

    print(
        df.to_string(index=False)
    )


# =====================================================
# REGION SUMMARY
# =====================================================

print("\n" + "=" * 70)
print("REGION SUMMARY")
print("=" * 70)

display_table(
    engine.region_summary(),
    currency_columns=["Revenue"],
    decimal_columns=["Quantity"]
)


# =====================================================
# TOP REGIONS BY REVENUE
# =====================================================

print("\n" + "=" * 70)
print("TOP REGIONS BY REVENUE")
print("=" * 70)

display_table(
    engine.top_regions_by_revenue(10),
    currency_columns=["Revenue"]
)


# =====================================================
# TOP REGIONS BY QUANTITY
# =====================================================

print("\n" + "=" * 70)
print("TOP REGIONS BY QUANTITY")
print("=" * 70)

display_table(
    engine.top_regions_by_quantity(10),
    decimal_columns=["Quantity"]
)


# =====================================================
# TOP REGIONS BY ORDERS
# =====================================================

print("\n" + "=" * 70)
print("TOP REGIONS BY ORDERS")
print("=" * 70)

display_table(
    engine.top_regions_by_orders(10)
)


# =====================================================
# WEAKEST REGIONS BY REVENUE
# =====================================================

print("\n" + "=" * 70)
print("WEAKEST REGIONS BY REVENUE")
print("=" * 70)

display_table(
    engine.weak_regions(
        metric="Revenue",
        n=10
    ),
    currency_columns=["Revenue"]
)

# =====================================================
# PHASE 2
# REGIONAL DEMAND
# =====================================================


# =====================================================
# PRODUCT DEMAND BY REGION
# =====================================================

print("\n" + "=" * 70)
print("PRODUCT DEMAND BY REGION")
print("=" * 70)

product_demand = engine.product_demand_by_region()

print(
    product_demand
    .head(30)
    .to_string(index=False)
)


# =====================================================
# TOP PRODUCTS BY REGION
# =====================================================

selected_region = "09-Uttar Pradesh"

print("\n" + "=" * 70)
print(
    f"TOP PRODUCTS IN {selected_region.upper()}"
)
print("=" * 70)

top_products = engine.top_products_by_region(
    selected_region,
    n=10
)

top_products_display = top_products.copy()

top_products_display["Revenue"] = (
    top_products_display["Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

top_products_display["Quantity"] = (
    top_products_display["Quantity"]
    .apply(lambda x: f"{x:,.3f}")
)

top_products_display["Orders"] = (
    top_products_display["Orders"]
    .apply(lambda x: f"{int(x):,}")
)

print(
    top_products_display.to_string(index=False)
)


# =====================================================
# REGIONAL PRODUCT PERFORMANCE
# =====================================================

print("\n" + "=" * 70)
print(
    f"PRODUCT PERFORMANCE IN {selected_region.upper()}"
)
print("=" * 70)

performance = engine.regional_product_performance(
    selected_region
)

performance_display = performance.head(10).copy()

performance_display["Revenue"] = (
    performance_display["Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

performance_display["Quantity"] = (
    performance_display["Quantity"]
    .apply(lambda x: f"{x:,.3f}")
)

performance_display["Orders"] = (
    performance_display["Orders"]
    .apply(lambda x: f"{int(x):,}")
)

print(
    performance_display.to_string(index=False)
)

# =====================================================
# PHASE 3
# REGIONAL GROWTH
# =====================================================


# =====================================================
# MONTHLY REGIONAL SALES
# =====================================================

print("\n" + "=" * 70)
print("MONTHLY REGIONAL SALES")
print("=" * 70)

monthly_sales = engine.monthly_regional_sales()

monthly_display = monthly_sales.copy()

monthly_display["Revenue"] = (
    monthly_display["Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

print(
    monthly_display
    .tail(30)
    .to_string(index=False)
)


# =====================================================
# REGIONAL GROWTH
# =====================================================

print("\n" + "=" * 70)
print("REGIONAL GROWTH")
print("=" * 70)

growth = engine.regional_growth()

growth_display = growth.copy()

growth_display["Previous Revenue"] = (
    growth_display["Previous Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

growth_display["Current Revenue"] = (
    growth_display["Current Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

growth_display["Growth Amount"] = (
    growth_display["Growth Amount"]
    .apply(lambda x: f"₹{x:,.2f}")
)

growth_display["Growth %"] = (
    growth_display["Growth %"]
    .apply(
        lambda x:
        "New Region"
        if x == float("inf")
        else f"{x:,.2f}%"
    )
)

print(
    growth_display.to_string(index=False)
)


# =====================================================
# FASTEST GROWING REGIONS
# =====================================================

print("\n" + "=" * 70)
print("FASTEST GROWING REGIONS BY % (MEANINGFUL MARKETS)")
print("=" * 70)

fastest = engine.fastest_growing_regions(
    n=10,
    min_previous_revenue=100000
)

fastest_display = fastest.copy()

fastest_display["Previous Revenue"] = (
    fastest_display["Previous Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

fastest_display["Current Revenue"] = (
    fastest_display["Current Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

fastest_display["Growth Amount"] = (
    fastest_display["Growth Amount"]
    .apply(lambda x: f"₹{x:,.2f}")
)

fastest_display["Growth %"] = (
    fastest_display["Growth %"]
    .apply(lambda x: f"{x:,.2f}%")
)

print(
    fastest_display.to_string(index=False)
)


# =====================================================
# DECLINING REGIONS
# =====================================================

print("\n" + "=" * 70)
print("DECLINING REGIONS")
print("=" * 70)

declining = engine.declining_regions(
    n=10
)

declining_display = declining.copy()

declining_display["Previous Revenue"] = (
    declining_display["Previous Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

declining_display["Current Revenue"] = (
    declining_display["Current Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

declining_display["Growth Amount"] = (
    declining_display["Growth Amount"]
    .apply(lambda x: f"₹{x:,.2f}")
)

declining_display["Growth %"] = (
    declining_display["Growth %"]
    .apply(lambda x: f"{x:,.2f}%")
)

print(
    declining_display.to_string(index=False)
)

# =====================================================
# PHASE 4
# REGIONAL CONTRIBUTION
# =====================================================


# =====================================================
# REGIONAL CONTRIBUTION
# =====================================================

print("\n" + "=" * 70)
print("REGIONAL CONTRIBUTION")
print("=" * 70)

contribution = engine.regional_contribution()

contribution_display = contribution.copy()

contribution_display["Revenue"] = (
    contribution_display["Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

contribution_display["Revenue Contribution %"] = (
    contribution_display["Revenue Contribution %"]
    .apply(lambda x: f"{x:,.2f}%")
)

contribution_display["Cumulative Contribution %"] = (
    contribution_display["Cumulative Contribution %"]
    .apply(lambda x: f"{x:,.2f}%")
)

print(
    contribution_display.to_string(index=False)
)


# =====================================================
# PARETO REGIONS
# =====================================================

print("\n" + "=" * 70)
print("PARETO REGIONS - 80% REVENUE")
print("=" * 70)

pareto = engine.pareto_regions(
    threshold=80
)

pareto_display = pareto.copy()

pareto_display["Revenue"] = (
    pareto_display["Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

pareto_display["Revenue Contribution %"] = (
    pareto_display["Revenue Contribution %"]
    .apply(lambda x: f"{x:,.2f}%")
)

pareto_display["Cumulative Contribution %"] = (
    pareto_display["Cumulative Contribution %"]
    .apply(lambda x: f"{x:,.2f}%")
)

print(
    pareto_display.to_string(index=False)
)


# =====================================================
# ABC REGION ANALYSIS
# =====================================================

print("\n" + "=" * 70)
print("ABC REGION ANALYSIS")
print("=" * 70)

abc = engine.abc_region_analysis()

abc_display = abc.copy()

abc_display["Revenue"] = (
    abc_display["Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

abc_display["Revenue Contribution %"] = (
    abc_display["Revenue Contribution %"]
    .apply(lambda x: f"{x:,.2f}%")
)

abc_display["Cumulative Contribution %"] = (
    abc_display["Cumulative Contribution %"]
    .apply(lambda x: f"{x:,.2f}%")
)

print(
    abc_display.to_string(index=False)
)

# =====================================================
# PHASE 5
# GEOGRAPHIC ANALYSIS & LOOKUP
# =====================================================


# =====================================================
# REGION CUSTOMER DISTRIBUTION
# =====================================================

print("\n" + "=" * 70)
print("REGION CUSTOMER DISTRIBUTION")
print("=" * 70)

customer_distribution = (
    engine.region_customer_distribution()
)

customer_display = customer_distribution.copy()

customer_display["Revenue"] = (
    customer_display["Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

customer_display["Customers"] = (
    customer_display["Customers"]
    .apply(lambda x: f"{int(x):,}")
)

customer_display["Orders"] = (
    customer_display["Orders"]
    .apply(lambda x: f"{int(x):,}")
)

print(
    customer_display.to_string(index=False)
)


# =====================================================
# REGIONAL AVERAGE ORDER VALUE
# =====================================================

print("\n" + "=" * 70)
print("REGIONAL AVERAGE ORDER VALUE")
print("=" * 70)

aov = engine.regional_average_order_value()

aov_display = aov.copy()

aov_display["Revenue"] = (
    aov_display["Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

aov_display["Orders"] = (
    aov_display["Orders"]
    .apply(lambda x: f"{int(x):,}")
)

aov_display["Average Order Value"] = (
    aov_display["Average Order Value"]
    .apply(lambda x: f"₹{x:,.2f}")
)

print(
    aov_display.to_string(index=False)
)


# =====================================================
# REGIONAL CUSTOMER COUNT
# =====================================================

print("\n" + "=" * 70)
print("REGIONAL CUSTOMER COUNT")
print("=" * 70)

customer_count = (
    engine.regional_customer_count()
)

customer_count_display = (
    customer_count.copy()
)

customer_count_display["Customers"] = (
    customer_count_display["Customers"]
    .apply(lambda x: f"{int(x):,}")
)

print(
    customer_count_display
    .to_string(index=False)
)


# =====================================================
# GEOGRAPHIC HEATMAP DATA
# =====================================================

print("\n" + "=" * 70)
print("GEOGRAPHIC HEATMAP DATA")
print("=" * 70)

heatmap = engine.geographic_heatmap_data()

heatmap_display = heatmap.copy()

heatmap_display["Revenue"] = (
    heatmap_display["Revenue"]
    .apply(lambda x: f"₹{x:,.2f}")
)

heatmap_display["Quantity"] = (
    heatmap_display["Quantity"]
    .apply(lambda x: f"{x:,.3f}")
)

heatmap_display["Orders"] = (
    heatmap_display["Orders"]
    .apply(lambda x: f"{int(x):,}")
)

heatmap_display["Customers"] = (
    heatmap_display["Customers"]
    .apply(lambda x: f"{int(x):,}")
)

print(
    heatmap_display.to_string(index=False)
)


# =====================================================
# REGION DETAILS
# =====================================================

selected_region = "29-Karnataka"

print("\n" + "=" * 70)
print(
    f"REGION DETAILS - {selected_region.upper()}"
)
print("=" * 70)

details = engine.region_details(
    selected_region
)

print(
    f"Region                  : {details['Region']}"
)

print(
    f"Revenue                 : "
    f"₹{details['Revenue']:,.2f}"
)

print(
    f"Quantity                : "
    f"{details['Quantity']:,.3f}"
)

print(
    f"Orders                  : "
    f"{details['Orders']:,}"
)

print(
    f"Customers               : "
    f"{details['Customers']:,}"
)

print(
    f"Average Order Value     : "
    f"₹{details['Average Order Value']:,.2f}"
)

print(
    f"Revenue Contribution    : "
    f"{details['Revenue Contribution %']:,.2f}%"
)

print(
    f"Top Product             : "
    f"{details['Top Product']}"
)

print(
    f"Top Product Revenue     : "
    f"₹{details['Top Product Revenue']:,.2f}"
)