"""
Unit tests for data cleaning logic in analysis/cleaner.py
"""

import unittest
import pandas as pd
import numpy as np
from analysis.cleaner import clean_employee_data

class TestDataCleaner(unittest.TestCase):
    def setUp(self):
        # Create a sample dirty DataFrame
        self.dirty_df = pd.DataFrame({
            "employee_id": ["EMP1001", "EMP1001", "EMP1002", "EMP1003", "EMP1004"],
            "first_name": ["John", "John", "Alice", "Bob", "Charlie"],
            "last_name": ["Doe", "Doe", "Smith", "Jones", "Brown"],
            "department": ["  engineering  ", "  engineering  ", "SALES", None, "hr"],
            "salary": [90000, 90000, np.nan, 85000, 60000],
            "years_of_experience": [4.0, 4.0, 2.5, np.nan, 5.0],
            "turnover_status": ["Active", "Active", "Resigned", "Active", "left"],
            "attendance_rate_pct": [95.0, 95.0, np.nan, 88.0, 92.0]
        })

    def test_duplicate_removal(self):
        cleaned_df, audit = clean_employee_data(self.dirty_df)
        self.assertEqual(len(cleaned_df), 4) # 1 duplicate row removed
        self.assertEqual(audit["duplicate_rows_removed"], 1)

    def test_department_normalization(self):
        cleaned_df, audit = clean_employee_data(self.dirty_df)
        depts = cleaned_df["department"].tolist()
        self.assertIn("Engineering", depts)
        self.assertIn("Sales", depts)
        self.assertIn("Human Resources", depts)
        self.assertIn("Unassigned", depts)

    def test_salary_imputation(self):
        cleaned_df, audit = clean_employee_data(self.dirty_df)
        self.assertFalse(cleaned_df["salary"].isnull().any())
        self.assertEqual(audit["missing_salaries_imputed"], 1)

    def test_turnover_status_standardization(self):
        cleaned_df, _ = clean_employee_data(self.dirty_df)
        statuses = cleaned_df["turnover_status"].tolist()
        # "left" should be standardized to "Resigned"
        self.assertTrue(all(s in ["Active", "Resigned"] for s in statuses))

if __name__ == "__main__":
    unittest.main()
