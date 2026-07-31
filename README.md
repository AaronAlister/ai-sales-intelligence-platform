# AI-Powered Sales Intelligence Platform

An end-to-end Business Intelligence and Analytics platform that transforms raw sales transactions into actionable business insights through automated ETL pipelines, analytical engines, forecasting models, and AI-generated reports.

Built as an internal analytics solution, the platform automates monthly sales data ingestion, validates and cleans datasets, centralizes information in a relational database, and delivers executive dashboards covering products, customers, regions, pricing, and sales trends.

---

## Features

### Data Engineering

- Automated Excel data ingestion
- Data validation and preprocessing
- Duplicate detection
- SQLite data warehouse
- Monthly incremental uploads

### Business Intelligence

- Executive KPI Dashboard
- Product Intelligence Engine
- Customer Intelligence Engine
- Regional Intelligence Engine
- Pricing Intelligence Engine
- Time-Series Analytics

### Artificial Intelligence

- AI-generated business reports
- Automated business insights
- Trend detection
- Sales forecasting
- Executive summaries

### Dashboard

- Interactive Streamlit dashboard
- Executive KPI cards
- Interactive charts
- Drill-down analytics
- Business reports

---

## System Architecture

```text
          Excel Sales Files
                  │
                  ▼
          ETL Pipeline
                  │
                  ▼
          SQLite Database
                  │
                  ▼
         Analytics Engines
   ┌──────────┬──────────┬──────────┐
   ▼          ▼          ▼          ▼
 KPI      Product    Customer   Regional
 Engine    Engine      Engine     Engine
   │          │          │          │
   └──────────┼──────────┼──────────┘
              ▼
      Pricing & Time-Series
              │
              ▼
          AI Engine
              │
              ▼
      Streamlit Dashboard
```

---

## Project Structure

```text
sales-intelligence-platform/

database/
engines/
tests/
docs/
streamlit_app.py
requirements.txt
README.md
```

---

## Analytics Engines

### KPI Engine

Executive business KPIs including:

- Gross Sales
- Net Sales
- Return Analysis
- Orders
- Revenue
- Discounts
- Customer KPIs

### Product Engine

Product intelligence including:

- Sales Analysis
- Return Analysis
- Growth Analysis
- Pareto Analysis
- ABC Classification

### Customer Engine

Customer intelligence including:

- Customer Value
- Loyalty Analysis
- Activity Monitoring
- Customer Contribution
- ABC Segmentation

### Regional Engine

Regional performance analytics including:

- Sales by Region
- Growth Analysis
- Geographic Performance
- Regional Contribution

### Pricing Engine

Pricing analytics including:

- Discount Analysis
- Price Distribution
- Revenue Impact
- Pricing Trends

### Time-Series Engine

Historical analytics including:

- Monthly Sales Trends
- Revenue Trends
- Seasonality
- Forecast Preparation

---

## Technology Stack

| Category         | Technologies          |
| ---------------- | --------------------- |
| Language         | Python                |
| Database         | SQLite, SQLAlchemy    |
| Data Processing  | Pandas, NumPy         |
| Machine Learning | Scikit-learn, Prophet |
| Visualization    | Plotly                |
| Dashboard        | Streamlit             |
| Version Control  | Git, GitHub           |

---

## Documentation

Comprehensive Software Design Documents are available for every major module.

- Project Overview
- System Architecture
- Database Design
- ETL Pipeline
- KPI Engine
- Product Engine
- Customer Engine
- Regional Engine
- Pricing Engine
- Time-Series Engine
- AI Engine

---

## Future Roadmap

- PostgreSQL Support
- REST API
- User Authentication
- Role-Based Access Control
- Automated Scheduled ETL
- Cloud Deployment
- Predictive Analytics
- Recommendation Engine
- Customer Churn Prediction
- Inventory Forecasting

---

## License

This repository contains the implementation of an internal Business Intelligence platform. Proprietary business datasets are not included.
