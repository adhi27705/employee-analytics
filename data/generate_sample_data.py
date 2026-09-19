"""
Script to generate synthetic realistic employee datasets in CSV and Excel formats.
Includes intentional missing values, duplicates, and format variations
to showcase automated data cleaning.
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)

DEPARTMENTS = [
    "Engineering", "Sales", "Marketing", "Human Resources",
    "Finance", "Operations", "Product", "Customer Success"
]

TITLES_BY_DEPT = {
    "Engineering": ["Software Engineer", "Senior Software Engineer", "DevOps Engineer", "Data Scientist", "QA Lead", "Engineering Manager"],
    "Sales": ["Sales Associate", "Account Executive", "Sales Manager", "Business Development Rep", "Enterprise Sales Lead"],
    "Marketing": ["Marketing Specialist", "Content Strategist", "SEO Analyst", "Growth Marketing Lead", "Brand Designer"],
    "Human Resources": ["HR Generalist", "Recruiter", "HR Business Partner", "Talent Acquisition Lead", "HR Director"],
    "Finance": ["Financial Analyst", "Staff Accountant", "Payroll Specialist", "Finance Manager", "Controller"],
    "Operations": ["Operations Associate", "Supply Chain Analyst", "Operations Manager", "Logistics Coordinator"],
    "Product": ["Associate Product Manager", "Product Manager", "Senior Product Manager", "Technical Product Lead"],
    "Customer Success": ["Support Specialist", "Customer Success Manager", "Implementation Consultant", "CS Team Lead"]
}

SALARY_BASE_BY_DEPT = {
    "Engineering": (75000, 165000),
    "Sales": (55000, 135000),
    "Marketing": (52000, 115000),
    "Human Resources": (50000, 105000),
    "Finance": (62000, 140000),
    "Operations": (50000, 110000),
    "Product": (80000, 160000),
    "Customer Success": (48000, 95000)
}

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra",
    "Alexander", "Rachel", "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet",
    "Dennis", "Ruth", "Jerry", "Maria", "Tyler", "Heather", "Aaron", "Diane"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey"
]

LOCATIONS = ["New York, NY", "San Francisco, CA", "Chicago, IL", "Austin, TX", "London, UK", "Remote"]
EDUCATIONS = ["Bachelor's", "Master's", "PhD", "Associate's"]
TURNOVER_REASONS = [
    "Better Compensation", "Career Transition", "Work-Life Balance",
    "Relocation", "Pursuing Higher Education", "Company Culture", "Health/Personal"
]

def generate_employee_dataset(num_records=500):
    start_date = datetime(2018, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range_days = (end_date - start_date).days

    records = []
    
    for i in range(1, num_records + 1):
        emp_id = f"EMP{1000 + i:04d}"
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        dept = random.choice(DEPARTMENTS)
        title = random.choice(TITLES_BY_DEPT[dept])
        
        # Experience: 0 to 22 years
        experience = round(max(0.5, np.random.gamma(shape=3.0, scale=2.0)), 1)
        if experience > 25:
            experience = 25.0
            
        # Salary calculation based on dept, experience, random variation
        base_min, base_max = SALARY_BASE_BY_DEPT[dept]
        exp_multiplier = 1 + (experience * 0.04)
        raw_salary = (base_min + (base_max - base_min) * (experience / 25.0) * 0.8) * np.random.uniform(0.9, 1.15)
        salary = round(min(max(raw_salary, 42000), 220000), -2)
        
        # Hire date
        days_offset = random.randint(0, date_range_days)
        hire_date = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        # Status & Turnover
        is_turnover = np.random.rand() < 0.17 # ~17% turnover
        if is_turnover:
            turnover_status = "Resigned"
            # Exit date at least 90 days after hire
            h_dt = datetime.strptime(hire_date, "%Y-%m-%d")
            max_exit = min(h_dt + timedelta(days=random.randint(90, 1200)), datetime(2026, 1, 1))
            if max_exit <= h_dt:
                max_exit = h_dt + timedelta(days=90)
            turnover_date = max_exit.strftime("%Y-%m-%d")
            turnover_reason = random.choice(TURNOVER_REASONS)
        else:
            turnover_status = "Active"
            turnover_date = None
            turnover_reason = None
            
        # Performance rating (1 to 5)
        perf_score = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.15, 0.50, 0.22, 0.08])[0]
        
        # Attendance rate (75% - 100%)
        attendance_rate = round(np.random.beta(a=18, b=2) * 100, 1)
        attendance_rate = max(70.0, min(100.0, attendance_rate))
        
        # Leaves taken per year
        leaves_taken = random.randint(3, 24)
        
        # Remote work ratio (0.0 = Onsite, 0.5 = Hybrid, 1.0 = Remote)
        remote_ratio = random.choice([0.0, 0.5, 1.0])
        
        location = random.choice(LOCATIONS)
        education = random.choices(EDUCATIONS, weights=[0.55, 0.32, 0.05, 0.08])[0]
        email = f"{fname.lower()}.{lname.lower()}{i%50}@company.com"

        records.append({
            "employee_id": emp_id,
            "first_name": fname,
            "last_name": lname,
            "email": email,
            "department": dept,
            "job_title": title,
            "salary": salary,
            "hire_date": hire_date,
            "years_of_experience": experience,
            "education_level": education,
            "performance_score": perf_score,
            "turnover_status": turnover_status,
            "turnover_date": turnover_date,
            "turnover_reason": turnover_reason,
            "attendance_rate_pct": attendance_rate,
            "leaves_taken": leaves_taken,
            "remote_work_ratio": remote_ratio,
            "office_location": location
        })

    df = pd.DataFrame(records)

    # Introduce deliberate dirty data to showcase data cleaning:
    # 1. Duplicate rows (10 duplicate rows appended)
    duplicates = df.sample(n=12, random_state=101).copy()
    df = pd.concat([df, duplicates], ignore_index=True)
    
    # 2. Inconsistent department casing / trailing whitespace in a few rows
    dirty_indices = random.sample(range(len(df)), 25)
    for idx in dirty_indices[:8]:
        curr = df.at[idx, "department"]
        df.at[idx, "department"] = f"  {curr.lower()}  "
    for idx in dirty_indices[8:14]:
        curr = df.at[idx, "department"]
        df.at[idx, "department"] = curr.upper()
        
    # 3. Missing values in Salary, Department, Performance Score, Attendance
    missing_salary_idx = random.sample(range(len(df)), 15)
    for idx in missing_salary_idx:
        df.at[idx, "salary"] = np.nan
        
    missing_dept_idx = random.sample(range(len(df)), 8)
    for idx in missing_dept_idx:
        df.at[idx, "department"] = None
        
    missing_perf_idx = random.sample(range(len(df)), 12)
    for idx in missing_perf_idx:
        df.at[idx, "performance_score"] = np.nan
        
    missing_attend_idx = random.sample(range(len(df)), 10)
    for idx in missing_attend_idx:
        df.at[idx, "attendance_rate_pct"] = np.nan

    # Shuffle rows
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    return df

def main():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    
    print("Generating synthetic employee datasets...")
    df = generate_employee_dataset(num_records=520)
    
    csv_path = os.path.join("data", "raw", "employees_sample.csv")
    xlsx_path = os.path.join("data", "raw", "employees_sample.xlsx")
    
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV sample dataset to {csv_path} ({len(df)} rows)")
    
    df.to_excel(xlsx_path, index=False)
    print(f"Saved Excel sample dataset to {xlsx_path} ({len(df)} rows)")

if __name__ == "__main__":
    main()
