# KPI Engine

---

# Overview

The KPI Engine is the foundational analytics module of the AI Sales Intelligence Platform. It computes high-level Key Performance Indicators (KPIs) from transactional sales data and provides a centralized source of business metrics for dashboards, reports, and downstream analytics engines.

Unlike specialized engines that focus on products, customers, or regions, the KPI Engine provides organization-wide metrics that summarize overall business performance.

All KPI calculations are deterministic, read-only operations performed on the centralized sales database.

---

# Purpose

The KPI Engine is responsible for transforming raw sales transactions into meaningful business metrics that enable management to monitor business performance.

Its objectives are to:

- Calculate standardized business KPIs
- Provide executive-level performance summaries
- Supply metrics to dashboards
- Support analytical engines with reusable KPI calculations
- Provide structured inputs for the AI Engine

---

# Business Value

Business leaders require a concise overview of organizational performance before investigating individual business areas.

The KPI Engine provides immediate visibility into critical performance indicators, allowing decision-makers to answer questions such as:

- What is the total revenue generated?
- What is the actual revenue after returns?
- How many orders have been processed?
- What is the average order value?
- How many customers purchased products?
- What percentage of sales were returned?
- What is the average discount offered?
- When was the latest data upload completed?

These KPIs serve as the executive health check for the organization.

---

# Responsibilities

The KPI Engine is responsible for:

- Computing sales KPIs
- Computing order KPIs
- Computing quantity KPIs
- Computing customer KPIs
- Computing product KPIs
- Computing discount KPIs
- Monitoring upload activity
- Providing dashboard-ready KPI summaries

---

# Engine Architecture

```text
KPIEngine

├── Sales KPIs
│     gross_sales()
│     returns_value()
│     net_sales()
│     return_rate()
│
├── Order KPIs
│     total_orders()
│     average_order_value()
│     average_items_per_order()
│
├── Quantity KPIs
│     gross_quantity()
│     net_quantity()
│     total_returns()
│
├── Product KPIs
│     total_products()
│
├── Customer KPIs
│     total_customers()
│     average_revenue_per_customer()
│
├── Discount KPIs
│     average_discount()
│
├── Upload KPIs
│     successful_uploads()
│     latest_upload()
│
└── Dashboard
      dashboard_summary()
```

---

# Engine Workflow

```text
Sales Database

        │

        ▼

Read Transaction Data

        │

        ▼

Compute KPI Metrics

        │

        ▼

Aggregate Dashboard Summary

        │

        ├────────────► Streamlit Dashboard

        ├────────────► Executive Reports

        └────────────► AI Engine
```

The KPI Engine performs only read operations and never modifies transactional data.

---

# KPI Categories

## 1. Sales KPIs

Sales KPIs evaluate the financial performance of the business.

### gross_sales()

#### Purpose

Calculates the total sales revenue before deducting returned transactions.

#### Formula

```
Gross Sales = Σ Sales Amount
```

#### Output

Returns the total gross sales value.

#### Business Value

Provides the highest-level revenue metric and serves as the starting point for financial analysis.

---

### returns_value()

#### Purpose

Calculates the total monetary value of returned transactions.

#### Formula

```
Returns Value = Σ Return Amount
```

#### Output

Returns the total value of all returns.

#### Business Value

Measures revenue lost due to product returns and helps evaluate return trends.

---

### net_sales()

#### Purpose

Calculates actual revenue retained after returns.

#### Formula

```
Net Sales = Gross Sales − Returns Value
```

#### Output

Returns the total net sales value.

#### Business Value

Represents the organization's realized revenue and is commonly used in executive reporting.

---

### return_rate()

#### Purpose

Calculates the percentage of gross sales lost through returns.

#### Formula

```
Return Rate (%) =
(Returns Value / Gross Sales) × 100
```

#### Output

Returns the overall return percentage.

#### Business Value

Provides insight into customer satisfaction, product quality, and return behavior.

---

# 2. Order KPIs

Order KPIs evaluate customer purchasing activity.

### total_orders()

#### Purpose

Calculates the total number of unique customer orders.

#### Formula

```
COUNT(DISTINCT Invoice)
```

#### Output

Returns the total order count.

#### Business Value

Measures business transaction volume.

---

### average_order_value()

#### Purpose

Calculates the average revenue generated per order.

#### Formula

```
Average Order Value =
Net Sales / Total Orders
```

#### Output

Returns the average value of an order.

#### Business Value

Measures customer spending behavior and average basket value.

---

### average_items_per_order()

#### Purpose

Calculates the average quantity of products purchased per order.

#### Formula

```
Average Items per Order =
Net Quantity / Total Orders
```

#### Output

Returns the average number of items purchased in each order.

#### Business Value

Provides insight into purchasing patterns and basket size.

---

# 3. Quantity KPIs

Quantity KPIs measure product movement.

### gross_quantity()

#### Purpose

Calculates the total quantity sold before returns.

#### Output

Returns the gross quantity sold.

---

### net_quantity()

#### Purpose

Calculates the quantity sold after deducting returned items.

#### Output

Returns the net quantity sold.

---

### total_returns()

#### Purpose

Calculates the total number of return transactions.

#### Output

Returns the total return transaction count.

#### Business Value

Measures return activity across the organization.

---

# 4. Product KPIs

### total_products()

#### Purpose

Calculates the number of unique products sold.

#### Formula

```
COUNT(DISTINCT Product)
```

#### Output

Returns the total unique products.

#### Business Value

Measures product portfolio coverage.

---

# 5. Customer KPIs

### total_customers()

#### Purpose

Calculates the number of unique purchasing customers.

#### Formula

```
COUNT(DISTINCT Customer)
```

#### Output

Returns the total customer count.

#### Business Value

Measures customer base size.

---

### average_revenue_per_customer()

#### Purpose

Calculates the average revenue generated per customer.

#### Formula

```
Average Revenue per Customer =
Net Sales / Total Customers
```

#### Output

Returns the average customer revenue.

#### Business Value

Measures customer value and supports customer segmentation.

---

# 6. Discount KPIs

### average_discount()

#### Purpose

Calculates the average discount percentage across all sales transactions.

#### Formula

```
Average Discount =
AVG(Discount Percentage)
```

#### Output

Returns the average discount applied.

#### Business Value

Evaluates pricing strategies and promotional effectiveness.

---

# 7. Upload KPIs

Operational KPIs that monitor data ingestion.

### successful_uploads()

#### Purpose

Returns the number of successfully processed dataset uploads.

#### Output

Returns the upload count.

#### Business Value

Provides visibility into ETL pipeline activity.

---

### latest_upload()

#### Purpose

Returns the timestamp of the latest successful upload.

#### Output

Returns the most recent upload date and time.

#### Business Value

Allows users to verify data freshness before making business decisions.

---

# 8. Dashboard

### dashboard_summary()

#### Purpose

Aggregates all KPI calculations into a single structured response used by the executive dashboard.

#### Output

The dashboard summary includes:

- Sales KPIs
- Order KPIs
- Quantity KPIs
- Product KPIs
- Customer KPIs
- Discount KPIs
- Upload KPIs

#### Business Value

Reduces redundant database queries by consolidating executive metrics into a single operation.

---

# Engine Dependencies

The KPI Engine depends on:

- SQLite Database
- Query Layer

The following components consume KPI Engine outputs:

- Streamlit Dashboard
- Product Engine
- Customer Engine
- Regional Engine
- Pricing Engine
- Time-Series Engine
- AI Engine
- Executive Reports

---

# Inputs

The KPI Engine operates on transactional sales data stored within the centralized database.

Primary inputs include:

- Sales transactions
- Invoice information
- Product information
- Customer information
- Upload metadata

---

# Outputs

The KPI Engine produces:

- Executive KPI summaries
- Dashboard metrics
- AI Engine input metrics
- Business performance indicators

---

# Business Questions Answered

The KPI Engine enables organizations to answer questions such as:

- What is the organization's total revenue?
- What is the net revenue after returns?
- How many customer orders have been processed?
- What is the average value of an order?
- How many products were sold?
- How many customers purchased during the selected period?
- What percentage of revenue was returned?
- What average discount is being offered?
- When was the latest sales data uploaded?

---

# Example Dashboard Output

```text
======================================================================
EXECUTIVE KPI DASHBOARD
======================================================================

SALES
----------------------------------------------------------------------
Gross Sales                   : ₹X,XXX,XXX.XX
Returns Value                 : ₹XXX,XXX.XX
Net Sales                     : ₹X,XXX,XXX.XX
Return Rate (%)               : X.XX%

ORDERS
----------------------------------------------------------------------
Total Orders                  : X,XXX
Average Order Value           : ₹XX,XXX.XX
Average Items / Order         : XX.XX

PRODUCTS
----------------------------------------------------------------------
Gross Quantity                : XXX,XXX
Net Quantity                  : XXX,XXX
Return Transactions           : XXX
Total Products                : XXXX

CUSTOMERS
----------------------------------------------------------------------
Total Customers               : XXX
Average Revenue / Customer    : ₹XXX,XXX.XX
Average Discount (%)          : XX.XX%

SYSTEM
----------------------------------------------------------------------
Successful Uploads            : X
Latest Upload                 : YYYY-MM-DD HH:MM:SS
======================================================================
```

---

# Performance Considerations

To ensure efficient execution:

- KPI calculations are implemented as read-only operations.
- Aggregations are performed efficiently using SQL and vectorized data operations.
- Dashboard metrics are consolidated into a single summary to reduce repeated queries.
- The engine avoids unnecessary database access by grouping related KPI calculations.

---

# Future Enhancements

Planned enhancements include:

- Gross Profit
- Profit Margin
- Revenue Growth Rate
- Month-over-Month Growth
- Year-over-Year Growth
- Revenue by Product Category
- Revenue by Region
- Revenue by Sales Representative
- Customer Lifetime Value (CLV)
- Forecasted KPI Dashboard

---

# Summary

The KPI Engine serves as the analytical foundation of the AI Sales Intelligence Platform. It transforms transactional sales data into standardized business metrics that support executive reporting, dashboards, downstream analytics engines, and AI-generated business insights. By centralizing KPI calculations within a dedicated engine, the platform ensures consistency, reusability, scalability, and reliable decision-making across the entire analytics ecosystem.
