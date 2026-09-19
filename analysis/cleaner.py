"""
Data Cleaning Module for Employee Analytics Platform.
Handles missing values, duplicate records, data type normalization,
and produces comprehensive audit logs.
"""

from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np

# Canonical department names mapping for normalizing slight spelling or casing variations
DEPT_CANONICAL_MAP = {
    "engineering": "Engineering",
    "eng": "Engineering",
    "it": "Engineering",
    "tech": "Engineering",
    "sales": "Sales",
    "marketing": "Marketing",
    "mktg": "Marketing",
    "human resources": "Human Resources",
    "hr": "Human Resources",
    "finance": "Finance",
    "operations": "Operations",
    "ops": "Operations",
    "product": "Product",
    "customer success": "Customer Success",
    "support": "Customer Success"
}

def clean_employee_data(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw employee DataFrame:
    1. Deduplicates rows and IDs
    2. Trims and standardizes text columns (departments, titles, names)
    3. Formats and casts numeric and date types
    4. Imputes missing values intelligently (median/mode)
    5. Flags statistical salary outliers using the IQR method
    
    Returns:
        (cleaned_df, audit_log_dictionary)
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(), {"error": "Input DataFrame is empty."}
        
    df = df_raw.copy()
    
    audit: Dict[str, Any] = {
        "initial_rows": len(df),
        "initial_cols": len(df.columns),
        "duplicate_rows_removed": 0,
        "duplicate_ids_resolved": 0,
        "missing_departments_imputed": 0,
        "missing_salaries_imputed": 0,
        "missing_performance_imputed": 0,
        "missing_attendance_imputed": 0,
        "outliers_flagged": 0,
        "final_rows": 0,
        "missing_summary_before": df.isnull().sum().to_dict()
    }
    
    # 1. Clean Column Names (lowercase, strip whitespace, replace spaces with underscores)
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    
    # Check required ID column
    id_col = None
    for candidate in ["employee_id", "empid", "id", "emp_id"]:
        if candidate in df.columns:
            id_col = candidate
            break
            
    if id_col is None:
        # Generate synthetic employee IDs if none exist
        df["employee_id"] = [f"EMP{1001 + i:04d}" for i in range(len(df))]
        id_col = "employee_id"
    elif id_col != "employee_id":
        df.rename(columns={id_col: "employee_id"}, inplace=True)
        id_col = "employee_id"

    # 2. Drop Exact Duplicate Rows
    exact_duplicates_count = df.duplicated().sum()
    if exact_duplicates_count > 0:
        df = df.drop_duplicates(keep="first")
        audit["duplicate_rows_removed"] = int(exact_duplicates_count)
        
    # 3. Deduplicate by Employee ID (if ID duplicates exist, keep the first non-null record)
    id_duplicates_count = df.duplicated(subset=["employee_id"]).sum()
    if id_duplicates_count > 0:
        df = df.drop_duplicates(subset=["employee_id"], keep="first")
        audit["duplicate_ids_resolved"] = int(id_duplicates_count)
        
    # 4. Standardize text columns
    string_cols = ["first_name", "last_name", "job_title", "department", "education_level", 
                   "turnover_status", "turnover_reason", "office_location"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(["nan", "None", "null", "NULL", "<NA>", "N/A", ""], np.nan)
            
    # Normalize Department Names
    if "department" in df.columns:
        audit["missing_departments_imputed"] = int(df["department"].isnull().sum())
        
        def normalize_dept(val):
            if pd.isna(val):
                return "Unassigned"
            clean_val = str(val).strip().lower()
            return DEPT_CANONICAL_MAP.get(clean_val, str(val).strip().title())
            
        df["department"] = df["department"].apply(normalize_dept)
        
    # Standardize Turnover Status
    if "turnover_status" in df.columns:
        df["turnover_status"] = df["turnover_status"].fillna("Active")
        df["turnover_status"] = df["turnover_status"].apply(
            lambda x: "Resigned" if str(x).strip().lower() in ["resigned", "terminated", "left", "yes", "true", "1"] else "Active"
        )
    else:
        df["turnover_status"] = "Active"
        
    # 5. Convert and Validate Numeric Fields
    # Salary
    if "salary" in df.columns:
        df["salary"] = pd.to_numeric(df["salary"], errors="coerce")
        missing_salaries = int(df["salary"].isnull().sum())
        audit["missing_salaries_imputed"] = missing_salaries
        
        if missing_salaries > 0:
            # Impute with median salary per department if available, else overall median
            dept_medians = df.groupby("department")["salary"].transform("median")
            overall_median = df["salary"].median() if not pd.isna(df["salary"].median()) else 65000.0
            df["salary"] = df["salary"].fillna(dept_medians).fillna(overall_median)
            df["salary"] = df["salary"].round(2)
    else:
        df["salary"] = 65000.0

    # Years of Experience
    if "years_of_experience" in df.columns:
        df["years_of_experience"] = pd.to_numeric(df["years_of_experience"], errors="coerce")
        median_exp = df["years_of_experience"].median()
        df["years_of_experience"] = df["years_of_experience"].fillna(median_exp if not pd.isna(median_exp) else 3.0)
        df["years_of_experience"] = df["years_of_experience"].clip(lower=0.0, upper=45.0).round(1)
    else:
        df["years_of_experience"] = 2.0

    # Performance Score
    if "performance_score" in df.columns:
        df["performance_score"] = pd.to_numeric(df["performance_score"], errors="coerce")
        missing_perf = int(df["performance_score"].isnull().sum())
        audit["missing_performance_imputed"] = missing_perf
        median_perf = df["performance_score"].median()
        df["performance_score"] = df["performance_score"].fillna(median_perf if not pd.isna(median_perf) else 3.0).round(1)
    else:
        df["performance_score"] = 3.0

    # Attendance Rate Pct
    if "attendance_rate_pct" in df.columns:
        df["attendance_rate_pct"] = pd.to_numeric(df["attendance_rate_pct"], errors="coerce")
        missing_attend = int(df["attendance_rate_pct"].isnull().sum())
        audit["missing_attendance_imputed"] = missing_attend
        median_attend = df["attendance_rate_pct"].median()
        df["attendance_rate_pct"] = df["attendance_rate_pct"].fillna(median_attend if not pd.isna(median_attend) else 92.5)
        df["attendance_rate_pct"] = df["attendance_rate_pct"].clip(lower=0.0, upper=100.0).round(1)
    else:
        df["attendance_rate_pct"] = 92.0

    # Leaves Taken
    if "leaves_taken" in df.columns:
        df["leaves_taken"] = pd.to_numeric(df["leaves_taken"], errors="coerce").fillna(10).astype(int)
    else:
        df["leaves_taken"] = 10

    # Remote Work Ratio
    if "remote_work_ratio" in df.columns:
        df["remote_work_ratio"] = pd.to_numeric(df["remote_work_ratio"], errors="coerce").fillna(0.5)
    else:
        df["remote_work_ratio"] = 0.5

    # 6. Parse Dates
    for date_col in ["hire_date", "turnover_date"]:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")

    # Construct full name if first and last name exist
    if "full_name" not in df.columns:
        if "first_name" in df.columns and "last_name" in df.columns:
            df["full_name"] = df["first_name"].fillna("") + " " + df["last_name"].fillna("")
            df["full_name"] = df["full_name"].str.strip()
        else:
            df["full_name"] = df["employee_id"]

    # 7. Outlier Tagging using IQR Method for Salary
    q25 = df["salary"].quantile(0.25)
    q75 = df["salary"].quantile(0.75)
    iqr = q75 - q25
    lower_bound = q25 - 1.5 * iqr
    upper_bound = q75 + 1.5 * iqr
    df["is_salary_outlier"] = (df["salary"] < lower_bound) | (df["salary"] > upper_bound)
    audit["outliers_flagged"] = int(df["is_salary_outlier"].sum())

    # Final summary
    audit["final_rows"] = len(df)
    audit["missing_summary_after"] = df.isnull().sum().to_dict()
    
    return df, audit
