"""
Database Operations Module for Employee Analytics Platform.
Handles schema initialization, data ingestion, and analytical query execution.
"""

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

# Predefined queries mapped to descriptive titles
PREDEFINED_QUERIES = {
    "1. Executive Workforce Overview": """
SELECT 
    COUNT(*) AS total_employees,
    SUM(CASE WHEN turnover_status = 'Active' THEN 1 ELSE 0 END) AS active_employees,
    SUM(CASE WHEN turnover_status = 'Resigned' THEN 1 ELSE 0 END) AS resigned_employees,
    ROUND(SUM(CASE WHEN turnover_status = 'Resigned' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS turnover_rate_pct,
    ROUND(AVG(salary), 2) AS average_salary,
    ROUND(AVG(years_of_experience), 1) AS average_experience_years,
    ROUND(AVG(attendance_rate_pct), 2) AS average_attendance_rate_pct
FROM employees;
""",

    "2. Department Headcount & Payroll Breakdown": """
SELECT 
    department,
    COUNT(*) AS total_headcount,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM employees), 2) AS pct_of_workforce,
    ROUND(AVG(salary), 2) AS avg_salary,
    ROUND(MIN(salary), 2) AS min_salary,
    ROUND(MAX(salary), 2) AS max_salary,
    ROUND(SUM(salary), 2) AS total_payroll,
    SUM(CASE WHEN turnover_status = 'Resigned' THEN 1 ELSE 0 END) AS resigned_count,
    ROUND(SUM(CASE WHEN turnover_status = 'Resigned' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS dept_turnover_rate_pct
FROM employees
GROUP BY department
ORDER BY total_headcount DESC;
""",

    "3. Salary Distribution by Brackets": """
SELECT 
    CASE 
        WHEN salary < 60000 THEN '1. Entry (< $60k)'
        WHEN salary >= 60000 AND salary < 90000 THEN '2. Mid-Tier ($60k - $90k)'
        WHEN salary >= 90000 AND salary < 120000 THEN '3. Upper-Mid ($90k - $120k)'
        WHEN salary >= 120000 AND salary < 150000 THEN '4. Senior ($120k - $150k)'
        ELSE '5. Executive / Principal (> $150k)'
    END AS salary_bracket,
    COUNT(*) AS employee_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM employees), 2) AS pct_of_total,
    ROUND(AVG(years_of_experience), 1) AS avg_experience_years,
    ROUND(AVG(salary), 2) AS avg_salary_in_bracket
FROM employees
GROUP BY 
    CASE 
        WHEN salary < 60000 THEN '1. Entry (< $60k)'
        WHEN salary >= 60000 AND salary < 90000 THEN '2. Mid-Tier ($60k - $90k)'
        WHEN salary >= 90000 AND salary < 120000 THEN '3. Upper-Mid ($90k - $120k)'
        WHEN salary >= 120000 AND salary < 150000 THEN '4. Senior ($120k - $150k)'
        ELSE '5. Executive / Principal (> $150k)'
    END
ORDER BY salary_bracket ASC;
""",

    "4. Experience Bands vs Salary & Performance": """
SELECT 
    CASE 
        WHEN years_of_experience < 2 THEN '0 - 2 Years (Entry)'
        WHEN years_of_experience >= 2 AND years_of_experience < 5 THEN '3 - 5 Years (Mid-Level)'
        WHEN years_of_experience >= 5 AND years_of_experience < 10 THEN '6 - 10 Years (Senior)'
        ELSE '10+ Years (Lead / Staff)'
    END AS experience_band,
    COUNT(*) AS headcount,
    ROUND(AVG(salary), 2) AS avg_salary,
    ROUND(AVG(performance_score), 2) AS avg_performance_rating,
    ROUND(AVG(attendance_rate_pct), 2) AS avg_attendance_pct,
    ROUND(SUM(CASE WHEN turnover_status = 'Resigned' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS turnover_rate_pct
FROM employees
GROUP BY 
    CASE 
        WHEN years_of_experience < 2 THEN '0 - 2 Years (Entry)'
        WHEN years_of_experience >= 2 AND years_of_experience < 5 THEN '3 - 5 Years (Mid-Level)'
        WHEN years_of_experience >= 5 AND years_of_experience < 10 THEN '6 - 10 Years (Senior)'
        ELSE '10+ Years (Lead / Staff)'
    END
ORDER BY avg_salary ASC;
""",

    "5. Turnover Reasons Breakdown": """
SELECT 
    COALESCE(turnover_reason, 'Unspecified / Other') AS exit_reason,
    COUNT(*) AS exit_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM employees WHERE turnover_status = 'Resigned'), 2) AS pct_of_resigned,
    ROUND(AVG(years_of_experience), 1) AS avg_years_experience,
    ROUND(AVG(salary), 2) AS avg_past_salary
FROM employees
WHERE turnover_status = 'Resigned'
GROUP BY turnover_reason
ORDER BY exit_count DESC;
""",

    "6. Attendance & Remote Work Mode Correlation": """
SELECT 
    CASE 
        WHEN remote_work_ratio = 0.0 THEN 'On-site (0% Remote)'
        WHEN remote_work_ratio = 0.5 THEN 'Hybrid (50% Remote)'
        WHEN remote_work_ratio = 1.0 THEN 'Fully Remote (100%)'
        ELSE 'Flexible'
    END AS work_arrangement,
    COUNT(*) AS headcount,
    ROUND(AVG(attendance_rate_pct), 2) AS avg_attendance_pct,
    ROUND(AVG(leaves_taken), 1) AS avg_leaves_taken,
    ROUND(AVG(performance_score), 2) AS avg_performance_score
FROM employees
GROUP BY 
    CASE 
        WHEN remote_work_ratio = 0.0 THEN 'On-site (0% Remote)'
        WHEN remote_work_ratio = 0.5 THEN 'Hybrid (50% Remote)'
        WHEN remote_work_ratio = 1.0 THEN 'Fully Remote (100%)'
        ELSE 'Flexible'
    END
ORDER BY avg_attendance_pct DESC;
""",

    "7. High Performer Flight Risk (Compensation Gap)": """
WITH DeptSalaryAvg AS (
    SELECT 
        department,
        AVG(salary) AS dept_avg_salary
    FROM employees
    GROUP BY department
)
SELECT 
    e.employee_id,
    e.full_name,
    e.department,
    e.job_title,
    e.performance_score,
    ROUND(e.salary, 2) AS current_salary,
    ROUND(d.dept_avg_salary, 2) AS department_avg_salary,
    ROUND(d.dept_avg_salary - e.salary, 2) AS salary_deficit,
    ROUND(e.years_of_experience, 1) AS experience_years
FROM employees e
JOIN DeptSalaryAvg d ON e.department = d.department
WHERE e.turnover_status = 'Active'
  AND e.performance_score >= 4.0
  AND e.salary < d.dept_avg_salary
ORDER BY salary_deficit DESC
LIMIT 15;
"""
}

def init_db(engine: Engine) -> None:
    """
    Initializes required tables in PostgreSQL or SQLite.
    """
    is_sqlite = "sqlite" in str(engine.url)
    
    with engine.begin() as conn:
        # Create departments table
        if is_sqlite:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS departments (
                    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    department_name TEXT UNIQUE NOT NULL
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id TEXT PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    department TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    salary REAL NOT NULL,
                    hire_date TEXT,
                    years_of_experience REAL DEFAULT 0.0,
                    education_level TEXT,
                    performance_score REAL,
                    turnover_status TEXT DEFAULT 'Active',
                    turnover_date TEXT,
                    turnover_reason TEXT,
                    attendance_rate_pct REAL DEFAULT 90.0,
                    leaves_taken INTEGER DEFAULT 0,
                    remote_work_ratio REAL DEFAULT 0.0,
                    office_location TEXT,
                    is_salary_outlier INTEGER DEFAULT 0
                );
            """))
        else:
            # PostgreSQL
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS departments (
                    department_id SERIAL PRIMARY KEY,
                    department_name VARCHAR(100) UNIQUE NOT NULL
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id VARCHAR(50) PRIMARY KEY,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    full_name VARCHAR(200) NOT NULL,
                    email VARCHAR(150),
                    department VARCHAR(100) NOT NULL,
                    job_title VARCHAR(150) NOT NULL,
                    salary NUMERIC(12, 2) NOT NULL,
                    hire_date DATE,
                    years_of_experience NUMERIC(4, 1) DEFAULT 0.0,
                    education_level VARCHAR(50),
                    performance_score NUMERIC(3, 1),
                    turnover_status VARCHAR(20) DEFAULT 'Active',
                    turnover_date DATE,
                    turnover_reason VARCHAR(150),
                    attendance_rate_pct NUMERIC(5, 2) DEFAULT 90.0,
                    leaves_taken INT DEFAULT 0,
                    remote_work_ratio NUMERIC(3, 2) DEFAULT 0.0,
                    office_location VARCHAR(100),
                    is_salary_outlier BOOLEAN DEFAULT FALSE
                );
            """))

def insert_cleaned_employees(df: pd.DataFrame, engine: Engine, if_exists: str = "replace") -> int:
    """
    Inserts or replaces employee data in the database.
    Also syncs the departments table.
    """
    init_db(engine)
    
    # Store into employees table
    df_to_save = df.copy()
    
    # Handle boolean column for SQLite
    if "is_salary_outlier" in df_to_save.columns and "sqlite" in str(engine.url):
        df_to_save["is_salary_outlier"] = df_to_save["is_salary_outlier"].astype(int)
        
    df_to_save.to_sql("employees", engine, if_exists=if_exists, index=False)
    
    # Populate departments table
    if "department" in df.columns:
        depts = sorted([d for d in df["department"].dropna().unique() if d != "Unassigned"])
        dept_df = pd.DataFrame({"department_name": depts})
        dept_df.to_sql("departments", engine, if_exists="replace", index=False)
        
    return len(df_to_save)

def execute_query(sql_query: str, engine: Engine, params: dict = None) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Executes a SQL query and returns results as a DataFrame.
    Returns: (df_result, error_message)
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(sql_query), conn, params=params)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def get_employee_dataframe(engine: Engine) -> pd.DataFrame:
    """Retrieves all records from the employees table."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql_table("employees", conn)
        return df
    except Exception:
        # Table might not exist yet
        return pd.DataFrame()
