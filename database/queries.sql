-- ==============================================================================
-- Analytical SQL Queries for Employee Information Platform
-- ==============================================================================

-- 1. Executive Summary: Core Metrics
-- Calculates total employee headcount, active employees, resigned employees, turnover rate, and workforce averages.
SELECT 
    COUNT(*) AS total_employees,
    SUM(CASE WHEN turnover_status = 'Active' THEN 1 ELSE 0 END) AS active_employees,
    SUM(CASE WHEN turnover_status = 'Resigned' THEN 1 ELSE 0 END) AS resigned_employees,
    ROUND(SUM(CASE WHEN turnover_status = 'Resigned' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS turnover_rate_pct,
    ROUND(AVG(salary), 2) AS average_salary,
    ROUND(AVG(years_of_experience), 1) AS average_experience_years,
    ROUND(AVG(attendance_rate_pct), 2) AS average_attendance_rate_pct
FROM employees;


-- 2. Department Breakdown: Headcount, Compensation & Turnover
-- Evaluates workforce size, total payroll, average and range of salaries, and department-level turnover.
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


-- 3. Salary Distribution by Tier/Bracket
-- Groups employees into analytical compensation brackets to identify salary spread.
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


-- 4. Experience Tier vs Salary & Performance Correlation
-- Measures how experience bands translate to compensation and performance ratings.
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


-- 5. Turnover & Attrition Breakdown by Reason
-- Identifies top root causes behind employee resignations.
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


-- 6. Attendance & Work Mode Analysis
-- Correlates remote work arrangements (Onsite, Hybrid, Remote) with attendance and leaves taken.
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


-- 7. High Performer Flight Risk Identification
-- Flags top performers (score >= 4.0) earning below their department's average compensation.
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
