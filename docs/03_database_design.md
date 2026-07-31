# Database Design

---

# Overview

The AI Sales Intelligence Platform uses a centralized relational database to store historical sales transactions, enabling consistent analytics, reporting, and AI-driven business intelligence.

Rather than analyzing uploaded Excel files directly, every validated dataset is integrated into a persistent database. This approach ensures that historical sales information is preserved across multiple uploads, allowing long-term trend analysis, customer behavior tracking, forecasting, and executive reporting.

The current implementation uses SQLite due to its simplicity, lightweight architecture, and ease of deployment. The database layer has been designed to remain database-agnostic, allowing future migration to PostgreSQL or other enterprise database systems with minimal modifications.

---

# Design Goals

The database has been designed with the following objectives:

- Maintain a centralized historical sales repository
- Eliminate duplicate records
- Preserve data integrity
- Support analytical queries efficiently
- Enable incremental monthly uploads
- Serve as the single source of truth for all analytics engines
- Support future AI and machine learning modules

---

# Database Architecture

```
                    Excel Upload

                           │

                           ▼

                  Validation Layer

                           │

                           ▼

                 Preprocessing Layer

                           │

                           ▼

                  SQLite Database

          ┌─────────┬─────────┬─────────┐
          │         │         │         │
          ▼         ▼         ▼         ▼

    KPI Engine  Product   Customer   AI Engine
                 Engine     Engine
```

The database acts as the central data repository for every analytical component in the system.

---

# Database Responsibilities

The database layer is responsible for:

- Storing validated sales transactions
- Maintaining historical business data
- Supporting analytical queries
- Tracking uploaded datasets
- Preventing duplicate records
- Providing consistent data access for analytics engines
- Supporting future predictive models

---

# Database Schema

The primary table within the system is the **Sales** table.

| Column           | Data Type | Description               |
| ---------------- | --------- | ------------------------- |
| id               | INTEGER   | Primary Key               |
| invoice          | TEXT      | Unique Invoice Number     |
| item_code        | TEXT      | Product Code              |
| item_name        | TEXT      | Product Name              |
| item_group       | TEXT      | Product Category          |
| customer         | TEXT      | Customer Name             |
| place_of_supply  | TEXT      | Sales Region / City       |
| posting_date     | DATE      | Transaction Date          |
| stock_qty        | REAL      | Quantity Sold             |
| discount_percent | REAL      | Discount Percentage       |
| rate             | REAL      | Unit Selling Price        |
| amount           | REAL      | Transaction Value         |
| created_at       | TIMESTAMP | Record Creation Timestamp |

---

# Primary Key

Each record is assigned an auto-incrementing primary key.

```
id INTEGER PRIMARY KEY AUTOINCREMENT
```

Benefits:

- Unique row identification
- Faster indexing
- Simplified joins
- Efficient querying

---

# Data Types

The schema uses appropriate data types to optimize storage and query performance.

| Data Type | Purpose                       |
| --------- | ----------------------------- |
| INTEGER   | IDs                           |
| TEXT      | Names and identifiers         |
| REAL      | Prices, quantities, discounts |
| DATE      | Transaction dates             |
| TIMESTAMP | Record creation               |

---

# Data Flow

Every uploaded dataset follows the same lifecycle.

```
Excel Upload

↓

Validation

↓

Preprocessing

↓

Duplicate Detection

↓

Database Insert

↓

Analytics Engines
```

This guarantees that only validated and standardized data enters the database.

---

# Data Integrity

Several mechanisms ensure database consistency.

## Validation

The Validation Module verifies:

- Required columns
- Invalid dates
- Missing values
- Negative quantities
- Invalid numeric fields

---

## Preprocessing

The Preprocessing Module performs:

- Whitespace removal
- Blank row removal
- Duplicate row removal
- Date standardization
- Invoice standardization

---

## Duplicate Detection

Duplicate detection occurs at two levels.

### Dataset Level

Prevents the same Excel file from being uploaded multiple times.

### Record Level

Prevents duplicate invoice records from entering the database.

---

# Database Relationships

The current implementation uses a single denormalized sales table to simplify analytical queries.

The following logical entities exist within the dataset:

```
Customer

↓

Invoice

↓

Products

↓

Sales Transaction

↓

Region
```

Although these entities are stored in a single table, they behave as independent business dimensions during analysis.

This design minimizes JOIN operations and improves analytical performance for dashboard workloads.

---

# Query Layer

All database interactions are performed through a dedicated query layer.

Responsibilities include:

- Fetching sales records
- Aggregating KPIs
- Product analysis
- Customer analysis
- Regional analysis
- Pricing analysis
- Time-series analysis

Separating SQL logic from business logic improves maintainability and code organization.

---

# Indexing Strategy

The following columns are good candidates for indexing as the dataset grows:

- invoice
- customer
- item_code
- item_group
- posting_date
- place_of_supply

Indexes reduce query execution time for frequently accessed analytical dimensions.

---

# Scalability

Although SQLite is sufficient for the current project, the architecture supports migration to enterprise databases.

Future migration targets include:

- PostgreSQL
- MySQL
- Microsoft SQL Server
- Amazon RDS

Because all database operations are abstracted through the query layer, migration requires minimal modifications to higher-level analytics engines.

---

# Security Considerations

The database layer follows several security practices.

- Parameterized SQL queries
- Input validation before insertion
- Duplicate protection
- Transaction-based inserts
- Centralized database access
- Controlled write operations

Future enhancements may include:

- User authentication
- Role-Based Access Control (RBAC)
- Database encryption
- Automated backups
- Audit logging

---

# Design Decisions

## Why SQLite?

SQLite was selected because it:

- Requires no server setup
- Is lightweight
- Supports rapid development
- Integrates easily with Python
- Is sufficient for medium-sized analytical datasets

---

## Why a Centralized Database?

Instead of analyzing Excel files directly, maintaining a centralized database provides:

- Historical trend analysis
- Consistent business metrics
- Faster analytical queries
- AI-ready structured data
- Reduced processing overhead

---

## Why a Single Sales Table?

The platform currently uses a denormalized schema because:

- Analytical queries dominate transactional operations
- Dashboard performance benefits from fewer JOINs
- Simpler ETL pipeline
- Easier maintenance

Future enterprise deployments may normalize the schema if transactional complexity increases.

---

# Future Enhancements

The database architecture supports future expansion, including:

- Customer Master Table
- Product Master Table
- Region Dimension Table
- Upload History Table
- Forecast Storage
- Recommendation Cache
- AI Conversation History
- User Management
- Role-Based Permissions

---

# Summary

The database layer serves as the central foundation of the AI Sales Intelligence Platform. By maintaining a validated, centralized, and query-optimized sales repository, it enables reliable business analytics, machine learning, and AI-driven decision support while remaining scalable for future enterprise deployment.
