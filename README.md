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

# AQVASTAR ML and Intelligence Layer

This package adds ML and evidence-based business findings without replacing the existing engines or dashboards.

## Included

- `ml/anomaly_detection.py`: Isolation Forest detection for unusual monthly metrics and discount outliers.
- `ml/segmentation.py`: RFM features with K-means customer segments.
- `ml/recommendations.py`: Explainable product opportunities and customer re-engagement candidates.
- `ml/forecasting.py`: Adapter to the existing `ForecastEngine`.
- `intelligence/intelligence_engine.py`: Runs ML modules and assembles findings.
- `dashboards/ai_dashboard.py`: Streamlit dashboard for running and reviewing findings.
- `ai/`: Lightweight question routing and report formatting. LLM provider intentionally left unconfigured.

## Add to your project

Copy the `ml`, `intelligence`, and `ai` folders into your project, and copy `dashboards/ai_dashboard.py` into your existing `dashboards` folder. Review/merge rather than overwrite if any of these files already contain work.

Your project must be run from its root folder so `data/sales.db` resolves correctly:

```powershell
streamlit run app.py
```

## Connect the dashboard

If `app.py` already routes `page == "ai"` to `dashboards.ai_dashboard`, retain that route and ensure it calls:

```python
from dashboards.ai_dashboard import render_ai_dashboard
render_ai_dashboard()
```

If your app uses a different entry function convention, adapt that one import/call to match the existing pattern.

To add a navigation button, add `("ai", "INTELLIGENCE")` to the existing navigation page tuple in `dashboards/components/navigation.py`. Preserve the existing page entries and styling.

## Dependencies

The supplied requirements already include `pandas`, `scikit-learn`, and `streamlit`. No LLM SDK is added yet.

## Important notes

- Anomaly detection needs at least six monthly observations to label months as unusual.
- Customer segmentation needs at least two eligible customers.
- Segments and opportunity labels are statistical aids, not causal explanations or automatic pricing instructions.
- `ml/forecasting.py` is an adapter and may need one small adjustment if the current `ForecastEngine.forecast()` signature differs from `forecast(metric=..., periods=...)`.
- The dashboard does not modify existing dashboards or database records.
