"""
==============================================================================
Employee Analytics Platform - Main Streamlit Dashboard
Tech Stack: Python, Pandas, SQL, PostgreSQL/SQLite, Streamlit, Plotly
==============================================================================
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px

# Add current directory to path for module imports
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection import get_engine, test_db_connection
from database.db_ops import (
    init_db, insert_cleaned_employees, execute_query,
    get_employee_dataframe, PREDEFINED_QUERIES
)
from analysis.cleaner import clean_employee_data
from components.charts import (
    create_department_donut_chart, create_salary_distribution_chart,
    create_salary_by_department_box, create_experience_vs_salary_scatter,
    create_turnover_by_department_chart, create_turnover_reasons_chart,
    create_attendance_trend_chart, create_experience_brackets_chart,
    PRIMARY_COLORS, CHART_LAYOUT_DEFAULTS
)

# ----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS Injection
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Employee Analytics & Intelligence Platform",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
/* Modern typography and dark UI theme */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Glassmorphic KPI Cards */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.kpi-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 1.2rem;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.35);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-3px);
    border-color: rgba(99, 102, 241, 0.4);
}

.kpi-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.35rem;
}

.kpi-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.2;
}

.kpi-delta {
    font-size: 0.78rem;
    margin-top: 0.35rem;
    font-weight: 500;
}

.kpi-delta.positive { color: #10B981; }
.kpi-delta.neutral { color: #38BDF8; }
.kpi-delta.warning { color: #F59E0B; }
.kpi-delta.negative { color: #F43F5E; }

/* Badges */
.badge-postgres {
    background: rgba(49, 130, 206, 0.2);
    color: #60A5FA;
    border: 1px solid rgba(49, 130, 206, 0.4);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-sqlite {
    background: rgba(16, 185, 129, 0.2);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.4);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Header style */
.main-header {
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 2. Session State Initialization
# ----------------------------------------------------------------------------
if "engine" not in st.session_state:
    engine, db_type, status_msg = get_engine()
    st.session_state["engine"] = engine
    st.session_state["db_type"] = db_type
    st.session_state["db_status"] = status_msg

if "employee_df" not in st.session_state:
    # Try loading existing records from DB
    loaded_df = get_employee_dataframe(st.session_state["engine"])
    if not loaded_df.empty:
        st.session_state["employee_df"] = loaded_df
    else:
        # Check if sample CSV exists on disk, if so load and clean it
        sample_path = BASE_DIR / "data" / "raw" / "employees_sample.csv"
        if sample_path.exists():
            raw_sample = pd.read_csv(sample_path)
            cleaned_sample, audit = clean_employee_data(raw_sample)
            insert_cleaned_employees(cleaned_sample, st.session_state["engine"])
            st.session_state["employee_df"] = cleaned_sample
            st.session_state["cleaning_audit"] = audit
        else:
            st.session_state["employee_df"] = pd.DataFrame()

# ----------------------------------------------------------------------------
# 3. Sidebar: Configuration & Interactive Filters
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏢 Employee Analytics Hub")
    
    # Database Connection Badge & Expander
    db_type = st.session_state.get("db_type", "sqlite")
    badge_cls = "badge-postgres" if db_type == "postgresql" else "badge-sqlite"
    st.markdown(f"**Database Engine:** <span class='{badge_cls}'>{db_type.upper()} ACTIVE</span>", unsafe_allow_html=True)
    
    with st.expander("⚙️ Database Connection Settings"):
        st.caption("Connect to PostgreSQL or use embedded SQLite database.")
        db_choice = st.radio("Storage Backend", ["SQLite (Default Local)", "PostgreSQL (Production/Remote)"], index=0 if db_type=="sqlite" else 1)
        
        if "PostgreSQL" in db_choice:
            pg_host = st.text_input("Host", value="localhost")
            pg_port = st.text_input("Port", value="5432")
            pg_name = st.text_input("Database Name", value="employee_db")
            pg_user = st.text_input("Username", value="postgres")
            pg_pwd = st.text_input("Password", value="", type="password")
            
            if st.button("Connect to PostgreSQL", use_container_width=True):
                pg_url = f"postgresql+psycopg2://{pg_user}:{pg_pwd}@{pg_host}:{pg_port}/{pg_name}"
                is_ok, msg = test_db_connection(pg_url)
                if is_ok:
                    eng, dtype, s_msg = get_engine(custom_url=pg_url)
                    st.session_state["engine"] = eng
                    st.session_state["db_type"] = dtype
                    st.session_state["db_status"] = s_msg
                    st.success("Connected to PostgreSQL successfully!")
                    # Reload DB data if present
                    db_df = get_employee_dataframe(eng)
                    if not db_df.empty:
                        st.session_state["employee_df"] = db_df
                    st.rerun()
                else:
                    st.error(f"PostgreSQL connection failed: {msg}")
        else:
            if st.button("Use Embedded SQLite", use_container_width=True):
                sqlite_url = f"sqlite:///{(BASE_DIR / 'data' / 'employee_analytics.db').as_posix()}"
                eng, dtype, s_msg = get_engine(custom_url=sqlite_url)
                st.session_state["engine"] = eng
                st.session_state["db_type"] = dtype
                st.session_state["db_status"] = s_msg
                st.info("Switched to SQLite storage.")
                st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 Global Interactive Filters")
    
    df_current = st.session_state.get("employee_df", pd.DataFrame())
    
    if not df_current.empty:
        # Department Filter
        available_depts = sorted(df_current["department"].dropna().unique().tolist())
        selected_depts = st.multiselect(
            "Departments",
            options=available_depts,
            default=available_depts
        )
        
        # Turnover Status Filter
        status_options = ["All Employees", "Active Only", "Resigned Only"]
        selected_status = st.selectbox("Employment Status", status_options, index=0)
        
        # Experience Slider
        min_exp = float(df_current["years_of_experience"].min())
        max_exp = float(df_current["years_of_experience"].max())
        selected_exp = st.slider(
            "Years of Experience",
            min_value=0.0,
            max_value=float(max(max_exp, 1.0)),
            value=(min_exp, max_exp),
            step=0.5
        )
        
        # Salary Range Slider
        min_sal = float(df_current["salary"].min())
        max_sal = float(df_current["salary"].max())
        selected_salary = st.slider(
            "Salary Range ($)",
            min_value=float(min_sal),
            max_value=float(max_sal),
            value=(min_sal, max_sal),
            step=2500.0,
            format="$%d"
        )
        
        # Work Mode Filter
        work_modes = ["All Modes", "On-site (0%)", "Hybrid (50%)", "Remote (100%)"]
        selected_work_mode = st.selectbox("Work Arrangement", work_modes, index=0)
        
        # Apply filters to create working dataset
        filtered_df = df_current[
            (df_current["department"].isin(selected_depts)) &
            (df_current["years_of_experience"] >= selected_exp[0]) &
            (df_current["years_of_experience"] <= selected_exp[1]) &
            (df_current["salary"] >= selected_salary[0]) &
            (df_current["salary"] <= selected_salary[1])
        ].copy()
        
        if selected_status == "Active Only":
            filtered_df = filtered_df[filtered_df["turnover_status"] == "Active"]
        elif selected_status == "Resigned Only":
            filtered_df = filtered_df[filtered_df["turnover_status"] == "Resigned"]
            
        if selected_work_mode == "On-site (0%)":
            filtered_df = filtered_df[filtered_df["remote_work_ratio"] == 0.0]
        elif selected_work_mode == "Hybrid (50%)":
            filtered_df = filtered_df[filtered_df["remote_work_ratio"] == 0.5]
        elif selected_work_mode == "Remote (100%)":
            filtered_df = filtered_df[filtered_df["remote_work_ratio"] == 1.0]
            
        st.caption(f"Showing **{len(filtered_df):,}** of **{len(df_current):,}** records")
    else:
        filtered_df = pd.DataFrame()
        st.warning("No data loaded yet. Use Data Ingestion tab to upload or generate data.")

    st.markdown("---")
    st.caption("Built for Data Analyst Project | Python • SQL • Streamlit • Plotly")

# ----------------------------------------------------------------------------
# 4. Main View Header
# ----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1 style="margin-bottom: 0.2rem; font-weight: 800; font-size: 2.1rem; color: #F8FAFC;">
        📊 Employee Analytics & Workforce Intelligence
    </h1>
    <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 0;">
        Identify patterns in department headcounts, compensation structures, experience dynamics, attrition, and attendance.
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 5. Top KPI Summary Metrics Bar
# ----------------------------------------------------------------------------
if not filtered_df.empty:
    total_emp = len(filtered_df)
    active_emp = (filtered_df["turnover_status"] == "Active").sum()
    resigned_emp = (filtered_df["turnover_status"] == "Resigned").sum()
    turnover_rate = (resigned_emp / total_emp * 100.0) if total_emp > 0 else 0.0
    avg_sal = filtered_df["salary"].mean() if "salary" in filtered_df.columns else 0.0
    avg_exp = filtered_df["years_of_experience"].mean() if "years_of_experience" in filtered_df.columns else 0.0
    avg_att = filtered_df["attendance_rate_pct"].mean() if "attendance_rate_pct" in filtered_df.columns else 0.0

    turnover_class = "negative" if turnover_rate > 15 else "positive"
    attendance_class = "positive" if avg_att >= 90 else "warning"

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">Total Employees</div>
            <div class="kpi-value">{total_emp:,}</div>
            <div class="kpi-delta neutral">Filtered Workforce</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Average Salary</div>
            <div class="kpi-value">${avg_sal:,.0f}</div>
            <div class="kpi-delta positive">Annual Base</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Turnover Rate</div>
            <div class="kpi-value">{turnover_rate:.1f}%</div>
            <div class="kpi-delta {turnover_class}">{resigned_emp:,} Exited</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Avg Experience</div>
            <div class="kpi-value">{avg_exp:.1f} <span style="font-size: 1.1rem; color: #94A3B8;">yrs</span></div>
            <div class="kpi-delta neutral">Tenure Average</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Attendance Rate</div>
            <div class="kpi-value">{avg_att:.1f}%</div>
            <div class="kpi-delta {attendance_class}">Overall Reliability</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 6. Tab Navigation Layout
# ----------------------------------------------------------------------------
tabs = st.tabs([
    "🏢 Executive Overview",
    "💰 Department & Salary",
    "📈 Experience & Turnover",
    "📅 Attendance Trends",
    "🧹 Ingestion & Cleaning",
    "⚡ SQL Studio"
])

# ----------------------------------------------------------------------------
# TAB 1: Executive Overview
# ----------------------------------------------------------------------------
with tabs[0]:
    if filtered_df.empty:
        st.info("Please load or ingest employee data in the 'Ingestion & Cleaning' tab.")
    else:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.plotly_chart(create_department_donut_chart(filtered_df), use_container_width=True, key="overview_dept_donut")
        with col_right:
            st.plotly_chart(create_salary_distribution_chart(filtered_df), use_container_width=True, key="overview_salary_dist")

        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            st.plotly_chart(create_turnover_by_department_chart(filtered_df), use_container_width=True, key="overview_turnover_by_dept")
        with col_b2:
            st.plotly_chart(create_experience_brackets_chart(filtered_df), use_container_width=True, key="overview_exp_brackets")

# ----------------------------------------------------------------------------
# TAB 2: Department & Salary Analytics
# ----------------------------------------------------------------------------
with tabs[1]:
    if filtered_df.empty:
        st.info("No data available.")
    else:
        st.markdown("### Department Compensation & Distribution Analysis")
        col1, col2 = st.columns([1.1, 0.9])
        with col1:
            st.plotly_chart(create_salary_by_department_box(filtered_df), use_container_width=True, key="dept_salary_box")
        with col2:
            # Department Summary Metrics Table
            dept_summary = filtered_df.groupby("department").agg(
                Headcount=("employee_id", "count"),
                Avg_Salary=("salary", "mean"),
                Median_Salary=("salary", "median"),
                Min_Salary=("salary", "min"),
                Max_Salary=("salary", "max")
            ).reset_index()
            
            dept_summary["Avg_Salary"] = dept_summary["Avg_Salary"].apply(lambda x: f"${x:,.0f}")
            dept_summary["Median_Salary"] = dept_summary["Median_Salary"].apply(lambda x: f"${x:,.0f}")
            dept_summary["Min_Salary"] = dept_summary["Min_Salary"].apply(lambda x: f"${x:,.0f}")
            dept_summary["Max_Salary"] = dept_summary["Max_Salary"].apply(lambda x: f"${x:,.0f}")
            
            st.markdown("#### Department Compensation Summary")
            st.dataframe(dept_summary, use_container_width=True, hide_index=True)
            
        st.markdown("---")
        st.plotly_chart(create_experience_vs_salary_scatter(filtered_df), use_container_width=True, key="dept_exp_vs_salary")

# ----------------------------------------------------------------------------
# TAB 3: Experience & Turnover Analytics
# ----------------------------------------------------------------------------
with tabs[2]:
    if filtered_df.empty:
        st.info("No data available.")
    else:
        st.markdown("### Attrition & Experience Analysis")
        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            st.plotly_chart(create_turnover_by_department_chart(filtered_df), use_container_width=True, key="turnover_tab_by_dept")
        with col_t2:
            st.plotly_chart(create_turnover_reasons_chart(filtered_df), use_container_width=True, key="turnover_tab_reasons")

        st.markdown("#### Top Flight Risks: High Performers with Below-Average Salary")
        # SQL-powered flight risk computation on active records
        dept_avgs = filtered_df.groupby("department")["salary"].mean().to_dict()
        flight_risks = filtered_df[
            (filtered_df["turnover_status"] == "Active") &
            (filtered_df["performance_score"] >= 4.0)
        ].copy()
        
        if not flight_risks.empty:
            flight_risks["dept_avg_sal"] = flight_risks["department"].map(dept_avgs)
            flight_risks["salary_gap"] = flight_risks["dept_avg_sal"] - flight_risks["salary"]
            flight_risks = flight_risks[flight_risks["salary_gap"] > 0].sort_values(by="salary_gap", ascending=False)
            
            if not flight_risks.empty:
                display_risks = flight_risks[[
                    "employee_id", "full_name", "department", "job_title", 
                    "performance_score", "salary", "dept_avg_sal", "salary_gap"
                ]].head(10).copy()
                display_risks["salary"] = display_risks["salary"].apply(lambda x: f"${x:,.0f}")
                display_risks["dept_avg_sal"] = display_risks["dept_avg_sal"].apply(lambda x: f"${x:,.0f}")
                display_risks["salary_gap"] = display_risks["salary_gap"].apply(lambda x: f"${x:,.0f}")
                st.dataframe(display_risks, use_container_width=True, hide_index=True)
            else:
                st.success("No high performers are currently under-compensated compared to department averages!")

# ----------------------------------------------------------------------------
# TAB 4: Attendance & Work Patterns
# ----------------------------------------------------------------------------
with tabs[3]:
    if filtered_df.empty:
        st.info("No data available.")
    else:
        st.markdown("### Attendance Trends & Workplace Flexibility")
        col_a1, col_a2 = st.columns([1, 1])
        with col_a1:
            st.plotly_chart(create_attendance_trend_chart(filtered_df), use_container_width=True, key="attendance_mode_chart")
        with col_a2:
            st.markdown("#### Attendance & Leave Correlation")
            att_by_dept = filtered_df.groupby("department").agg(
                Avg_Attendance=("attendance_rate_pct", "mean"),
                Avg_Leaves_Taken=("leaves_taken", "mean"),
                Avg_Performance=("performance_score", "mean")
            ).reset_index()
            att_by_dept["Avg_Attendance"] = att_by_dept["Avg_Attendance"].apply(lambda x: f"{x:.1f}%")
            att_by_dept["Avg_Leaves_Taken"] = att_by_dept["Avg_Leaves_Taken"].round(1)
            att_by_dept["Avg_Performance"] = att_by_dept["Avg_Performance"].round(2)
            st.dataframe(att_by_dept, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------
# TAB 5: Data Ingestion & Automated Cleaning
# ----------------------------------------------------------------------------
with tabs[4]:
    st.markdown("### 📂 Upload Employee Data (CSV / Excel)")
    st.write("Upload raw employee datasets to run automated missing value imputation, duplicate removal, text normalization, and database storage.")
    
    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            help="Supports standard employee rosters with fields like ID, Department, Salary, Experience, Attendance."
        )
    with col_up2:
        st.markdown("#### Quick Actions")
        if st.button("⚡ Generate & Load Sample Dataset", use_container_width=True):
            with st.spinner("Generating 500+ realistic records with sample anomalies..."):
                from data.generate_sample_data import generate_employee_dataset
                sample_df = generate_employee_dataset(num_records=520)
                cleaned, audit = clean_employee_data(sample_df)
                insert_cleaned_employees(cleaned, st.session_state["engine"])
                st.session_state["employee_df"] = cleaned
                st.session_state["raw_df"] = sample_df
                st.session_state["cleaning_audit"] = audit
                st.success(f"Successfully generated & cleaned {len(cleaned)} records into database!")
                st.rerun()

    raw_data_to_clean = None
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                raw_data_to_clean = pd.read_csv(uploaded_file)
            else:
                raw_data_to_clean = pd.read_excel(uploaded_file)
            st.session_state["raw_df"] = raw_data_to_clean
        except Exception as e:
            st.error(f"Error reading file: {e}")

    # If raw data is loaded or in session state, run cleaning pipeline
    active_raw = st.session_state.get("raw_df")
    if active_raw is not None:
        st.markdown("---")
        st.markdown("### 🧹 Automated Data Cleaning Pipeline Audit")
        
        cleaned_data, audit = clean_employee_data(active_raw)
        st.session_state["cleaning_audit"] = audit
        
        # Display Cleaning Audit Metrics
        audit_c1, audit_c2, audit_c3, audit_c4, audit_c5 = st.columns(5)
        audit_c1.metric("Raw Rows", f"{audit.get('initial_rows', 0):,}")
        audit_c2.metric("Duplicates Dropped", f"{audit.get('duplicate_rows_removed', 0) + audit.get('duplicate_ids_resolved', 0):,}")
        audit_c3.metric("Salaries Imputed", f"{audit.get('missing_salaries_imputed', 0):,}")
        audit_c4.metric("Depts Normalized", f"{audit.get('missing_departments_imputed', 0):,}")
        audit_c5.metric("Final Cleaned Rows", f"{audit.get('final_rows', 0):,}")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### Raw Input Data (First 5 Rows)")
            st.dataframe(active_raw.head(5), use_container_width=True)
        with col_p2:
            st.markdown("#### Cleaned & Standardized Data (First 5 Rows)")
            st.dataframe(cleaned_data.head(5), use_container_width=True)

        if st.button("💾 Commit Cleaned Data to Database", type="primary", use_container_width=True):
            with st.spinner("Writing to database..."):
                rows_written = insert_cleaned_employees(cleaned_data, st.session_state["engine"])
                st.session_state["employee_df"] = cleaned_data
                st.success(f"Successfully committed {rows_written:,} records to {st.session_state['db_type'].upper()} database!")
                st.rerun()

    # Allow downloading currently cleaned dataset
    if not st.session_state.get("employee_df", pd.DataFrame()).empty:
        st.markdown("---")
        st.markdown("#### 📥 Export Cleaned Dataset")
        csv_bytes = st.session_state["employee_df"].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Cleaned Data (CSV)",
            data=csv_bytes,
            file_name=f"cleaned_employee_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ----------------------------------------------------------------------------
# TAB 6: SQL Studio & Analytical Queries
# ----------------------------------------------------------------------------
with tabs[5]:
    st.markdown("### ⚡ SQL Studio: Analytical Query Runner")
    st.write(f"Execute pre-defined analytical queries or compose custom SQL against the active **{st.session_state['db_type'].upper()}** database.")

    query_selection = st.selectbox(
        "Select an Analytical SQL Query Template:",
        options=list(PREDEFINED_QUERIES.keys())
    )

    sql_template = PREDEFINED_QUERIES[query_selection]
    
    custom_sql = st.text_area(
        "SQL Query Editor:",
        value=sql_template.strip(),
        height=220,
        help="You can modify this query or write your own SQL queries against the 'employees' or 'departments' tables."
    )

    if st.button("🚀 Execute Query", type="primary"):
        with st.spinner("Running query against database..."):
            query_result, err = execute_query(custom_sql, st.session_state["engine"])
            if err:
                st.error(f"SQL Execution Error: {err}")
            else:
                st.success(f"Query returned **{len(query_result)}** rows successfully.")
                st.dataframe(query_result, use_container_width=True)
                
                # Auto-visualization for query results
                numeric_cols = query_result.select_dtypes(include=["number"]).columns.tolist()
                text_cols = query_result.select_dtypes(include=["object", "string"]).columns.tolist()
                
                if len(text_cols) >= 1 and len(numeric_cols) >= 1:
                    with st.expander("📊 Quick Chart of Query Results", expanded=True):
                        fig_res = px.bar(
                            query_result,
                            x=text_cols[0],
                            y=numeric_cols[0],
                            color=text_cols[0],
                            color_discrete_sequence=PRIMARY_COLORS,
                            title=f"<b>{numeric_cols[0].replace('_', ' ').title()} by {text_cols[0].replace('_', ' ').title()}</b>"
                        )
                        fig_res.update_layout(**CHART_LAYOUT_DEFAULTS, showlegend=False)
                        st.plotly_chart(fig_res, use_container_width=True, key="sql_custom_query_chart")

                # Export query results
                res_csv = query_result.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Results (CSV)",
                    data=res_csv,
                    file_name="sql_query_results.csv",
                    mime="text/csv"
                )
