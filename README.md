# 📊 Employee Analytics & Workforce Intelligence Platform

A comprehensive Data Analyst platform built with **Python**, **Pandas**, **SQL**, **PostgreSQL**, **Streamlit**, and **Plotly** to ingest, clean, store, query, and visualize employee information.

---

## 🎯 Project Goals & Business Objectives

1. **Workforce Ingestion**: Seamlessly ingest raw employee rosters from CSV or Excel formats.
2. **Automated Data Cleaning**: Detect and eliminate duplicate records, intelligently impute missing salaries, normalize department taxonomy, and flag statistical compensation outliers.
3. **Relational Database Storage**: Persist cleaned employee data into **PostgreSQL** (with zero-configuration fallback to local **SQLite**).
4. **SQL Analytics Suite**: Answer key business questions regarding department headcounts, compensation structures, flight risks, turnover drivers, and attendance patterns using modular SQL queries.
5. **Executive Interactive Dashboard**: Provide an engaging, modern dashboard with dynamic multi-filters, KPIs, and responsive Plotly visualizations.

---

## 🏗️ Architecture Overview

```
Raw CSV / Excel Roster
        │
        ▼
┌──────────────────────────────────────┐
│       Data Cleaning Pipeline         │
│  - Exact & ID Deduplication          │
│  - Missing Salary Imputation (Median)│
│  - Department Taxonomy Normalization │
│  - Statistical Outlier Flagging (IQR)│
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│       Relational Database Layer      │
│     PostgreSQL / SQLite via          │
│          SQLAlchemy ORM              │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│          SQL Analytics Engine        │
│  - Department Breakdown              │
│  - Salary Tiers & Equity             │
│  - Experience vs Compensation Matrix │
│  - Turnover & Flight Risk Analysis   │
│  - Attendance & Remote Correlation   │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Streamlit & Plotly Executive Hub    │
│  - 5 Glassmorphic KPI Cards          │
│  - Real-Time Dynamic Sidebar Filters │
│  - Interactive SQL Studio Terminal   │
│  - Export Cleaned Data & CSV Reports │
└──────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.10+ / 3.14** | Core programming language and runtime |
| **Pandas & NumPy** | Data manipulation, transformation, statistical analysis, and cleaning |
| **SQL & SQLAlchemy** | Relational data persistence, DDL schema, and analytical queries |
| **PostgreSQL** | Primary relational database engine (via `psycopg2-binary`) |
| **SQLite** | Instant zero-configuration local embedded database engine |
| **Streamlit** | Executive web dashboard framework with reactive state |
| **Plotly** | High-fidelity, interactive visualizations and responsive charts |
| **Antigravity IDE** | Integrated development and deployment environment |

---

## 📁 Repository Structure

```
├── .env.example                     # Environment template for PostgreSQL credentials
├── requirements.txt                 # Project dependencies
├── README.md                        # Documentation & setup guide
├── app.py                           # Main Streamlit dashboard application
├── analysis/
│   └── cleaner.py                   # Automated data cleaning & audit log pipeline
├── components/
│   └── charts.py                    # Curated Plotly interactive visualizations
├── database/
│   ├── connection.py                # Database engine manager (PostgreSQL & SQLite fallback)
│   ├── schema.sql                   # Database DDL schema for employees & departments
│   ├── queries.sql                  # Production SQL analytics queries with documentation
│   └── db_ops.py                    # Database operations, ingestion, and query execution
├── data/
│   ├── generate_sample_data.py      # Script to generate realistic raw CSV and Excel datasets
│   └── raw/
│       ├── employees_sample.csv     # Sample CSV dataset with raw dirty anomalies
│       └── employees_sample.xlsx    # Sample Excel dataset
└── tests/
    ├── test_cleaner.py              # Automated tests for data cleaning logic
    └── test_database.py             # Automated tests for database operations and SQL queries
```

---

## 🚀 Quick Start Guide

### 1. Installation

Ensure Python is installed, then install the required dependencies:

```powershell
python -m pip install -r requirements.txt
```

### 2. Generate Sample Data

Generate 500+ realistic employee records in CSV and Excel formats:

```powershell
python data/generate_sample_data.py
```

### 3. Configure Database (Optional)

- By default, the application runs instantly with **SQLite** (`data/employee_analytics.db`) without requiring any setup.
- To connect to a **PostgreSQL** instance, copy `.env.example` to `.env` and fill in your credentials:

```ini
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=employee_db
DB_USER=postgres
DB_PASSWORD=your_password
```

Alternatively, configure connection credentials directly inside the **Database Settings** tab within the application UI!

### 4. Run the Dashboard

Launch the Streamlit web application:

```powershell
python -m streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 📊 Dashboard Capabilities & Highlights

1. **Executive Overview**:
   - Total headcount, Average base salary, Turnover rate, Average experience, and Attendance rate.
   - Headcount donut chart and overall salary distribution with mean & median markers.
2. **Department & Salary Insights**:
   - Salary distribution box plots across departments.
   - Summary table with headcount, average, median, minimum, and maximum salaries.
   - Experience vs. Compensation scatter plot with OLS trendlines.
3. **Experience & Turnover**:
   - Department-level attrition rates (%).
   - Pareto breakdown of employee resignation causes (compensation, work-life balance, etc.).
   - **Flight Risk Detection**: Identifies top performers (rating ≥ 4.0) earning below their department average salary.
4. **Attendance & Workplace Patterns**:
   - Attendance rate distribution by workplace mode (On-site, Hybrid, Remote).
   - Department attendance and leave consumption rates.
5. **Data Ingestion & Automated Cleaning**:
   - Upload any custom CSV or Excel file.
   - Live audit report showing removed duplicates, imputed salaries, and normalized departments.
   - One-click "Commit to Database" and "Export Cleaned CSV" buttons.
6. **SQL Studio**:
   - Choose from pre-configured business analytical SQL queries.
   - Interactive SQL editor to compose and run custom queries.
   - Instant chart generation and CSV results export.

---

## 🧪 Automated Testing

Run the test suite to verify data cleaning and database operations:

```powershell
python -m unittest discover -s tests -v
```
