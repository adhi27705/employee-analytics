-- ==============================================================================
-- Schema Definition: Employee Analytics Database
-- Supports: PostgreSQL and SQLite
-- ==============================================================================

-- Drop existing tables if re-initializing
DROP TABLE IF EXISTS attendance_records;
DROP TABLE IF EXISTS turnover_records;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

-- 1. Departments Reference Table
CREATE TABLE departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Master Employees Table
CREATE TABLE employees (
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
    is_salary_outlier BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Fast Querying and Analytics Performance
CREATE INDEX idx_emp_dept ON employees(department);
CREATE INDEX idx_emp_salary ON employees(salary);
CREATE INDEX idx_emp_status ON employees(turnover_status);
CREATE INDEX idx_emp_hire_date ON employees(hire_date);
CREATE INDEX idx_emp_perf ON employees(performance_score);
