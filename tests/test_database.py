"""
Unit tests for database initialization, data insertion, and SQL query execution.
"""

import unittest
import pandas as pd
from sqlalchemy import create_engine
from database.db_ops import init_db, insert_cleaned_employees, execute_query, PREDEFINED_QUERIES

class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite database for isolated fast testing
        self.engine = create_engine("sqlite:///:memory:")
        init_db(self.engine)
        
        # Insert sample employee records
        self.sample_df = pd.DataFrame({
            "employee_id": ["EMP001", "EMP002", "EMP003"],
            "first_name": ["Alice", "Bob", "Charlie"],
            "last_name": ["Walker", "Lee", "Davis"],
            "full_name": ["Alice Walker", "Bob Lee", "Charlie Davis"],
            "email": ["alice@co.com", "bob@co.com", "charlie@co.com"],
            "department": ["Engineering", "Sales", "Engineering"],
            "job_title": ["Software Engineer", "Sales Lead", "QA Lead"],
            "salary": [105000.0, 85000.0, 95000.0],
            "hire_date": ["2021-03-15", "2020-06-01", "2022-01-10"],
            "years_of_experience": [4.0, 6.0, 3.5],
            "education_level": ["Master's", "Bachelor's", "Bachelor's"],
            "performance_score": [4.2, 3.8, 4.5],
            "turnover_status": ["Active", "Resigned", "Active"],
            "turnover_date": [None, "2023-05-12", None],
            "turnover_reason": [None, "Better Compensation", None],
            "attendance_rate_pct": [96.0, 89.5, 94.0],
            "leaves_taken": [8, 14, 10],
            "remote_work_ratio": [0.5, 0.0, 1.0],
            "office_location": ["New York, NY", "Chicago, IL", "Remote"],
            "is_salary_outlier": [0, 0, 0]
        })
        insert_cleaned_employees(self.sample_df, self.engine)

    def test_record_count(self):
        df_res, err = execute_query("SELECT COUNT(*) AS total FROM employees;", self.engine)
        self.assertIsNone(err)
        self.assertEqual(df_res.iloc[0]["total"], 3)

    def test_executive_summary_query(self):
        query = PREDEFINED_QUERIES["1. Executive Workforce Overview"]
        df_res, err = execute_query(query, self.engine)
        self.assertIsNone(err)
        self.assertEqual(df_res.iloc[0]["total_employees"], 3)
        self.assertEqual(df_res.iloc[0]["active_employees"], 2)
        self.assertEqual(df_res.iloc[0]["resigned_employees"], 1)

    def test_department_aggregation(self):
        query = PREDEFINED_QUERIES["2. Department Headcount & Payroll Breakdown"]
        df_res, err = execute_query(query, self.engine)
        self.assertIsNone(err)
        self.assertEqual(len(df_res), 2) # Engineering and Sales

if __name__ == "__main__":
    unittest.main()
