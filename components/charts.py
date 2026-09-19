"""
Interactive Plotly Visualizations for Employee Analytics Platform.
Designed with rich aesthetics, curated palettes, and interactive tooltips.
"""

from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Modern, harmonious color palette
PRIMARY_COLORS = [
    "#6366F1", "#06B6D4", "#10B981", "#F59E0B",
    "#EC4899", "#8B5CF6", "#3B82F6", "#F97316"
]

CHART_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#F1F5F9", size=12),
    margin=dict(l=20, r=20, t=40, b=20),
    hoverlabel=dict(bgcolor="#1E293B", font_size=12, font_color="#F8FAFC"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

def create_department_donut_chart(df: pd.DataFrame) -> go.Figure:
    """Renders a modern donut chart for employee department distribution."""
    if df.empty or "department" not in df.columns:
        return go.Figure()

    dept_counts = df["department"].value_counts().reset_index()
    dept_counts.columns = ["department", "count"]

    fig = px.pie(
        dept_counts,
        names="department",
        values="count",
        hole=0.55,
        color_discrete_sequence=PRIMARY_COLORS,
        title="<b>Headcount by Department</b>"
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Headcount: %{value} employees<br>Share: %{percent}<extra></extra>",
        marker=dict(line=dict(color="#0F172A", width=2))
    )
    fig.update_layout(**CHART_LAYOUT_DEFAULTS)
    return fig

def create_salary_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Renders a histogram of salaries with mean & median markers."""
    if df.empty or "salary" not in df.columns:
        return go.Figure()

    mean_sal = df["salary"].mean()
    median_sal = df["salary"].median()

    fig = px.histogram(
        df,
        x="salary",
        nbins=25,
        color_discrete_sequence=["#06B6D4"],
        title="<b>Overall Salary Distribution ($)</b>",
        labels={"salary": "Annual Base Salary ($)", "count": "Employee Count"}
    )
    fig.add_vline(
        x=mean_sal,
        line_width=2,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"Mean: ${mean_sal:,.0f}",
        annotation_position="top left",
        annotation_font_color="#F59E0B"
    )
    fig.add_vline(
        x=median_sal,
        line_width=2,
        line_dash="dot",
        line_color="#10B981",
        annotation_text=f"Median: ${median_sal:,.0f}",
        annotation_position="top right",
        annotation_font_color="#10B981"
    )
    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        xaxis=dict(showgrid=True, gridcolor="#334155", tickprefix="$", tickformat=","),
        yaxis=dict(showgrid=True, gridcolor="#334155")
    )
    return fig

def create_salary_by_department_box(df: pd.DataFrame) -> go.Figure:
    """Renders box plots of salary distributions grouped by department."""
    if df.empty or "salary" not in df.columns or "department" not in df.columns:
        return go.Figure()

    # Sort departments by median salary
    order = df.groupby("department")["salary"].median().sort_values(ascending=False).index.tolist()

    fig = px.box(
        df,
        x="department",
        y="salary",
        category_orders={"department": order},
        color="department",
        color_discrete_sequence=PRIMARY_COLORS,
        title="<b>Salary Distribution by Department (Box Plot)</b>",
        labels={"salary": "Salary ($)", "department": "Department"}
    )
    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor="#334155", tickprefix="$", tickformat=","),
        xaxis=dict(showgrid=False, tickangle=-25)
    )
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Salary: $%{y:,.0f}<extra></extra>")
    return fig

def create_experience_vs_salary_scatter(df: pd.DataFrame) -> go.Figure:
    """Renders a scatter plot of Experience vs. Salary colored by department."""
    if df.empty or "years_of_experience" not in df.columns or "salary" not in df.columns:
        return go.Figure()

    has_statsmodels = False
    try:
        import statsmodels.api  # noqa: F401
        has_statsmodels = True
    except ImportError:
        has_statsmodels = False

    hover_cols = [c for c in ["full_name", "job_title", "performance_score", "employee_id"] if c in df.columns]

    scatter_kwargs = dict(
        data_frame=df,
        x="years_of_experience",
        y="salary",
        color="department",
        color_discrete_sequence=PRIMARY_COLORS,
        title="<b>Experience vs. Compensation Matrix</b>",
        labels={
            "years_of_experience": "Years of Experience",
            "salary": "Annual Salary ($)",
            "department": "Department"
        }
    )
    if hover_cols:
        scatter_kwargs["hover_data"] = hover_cols

    if has_statsmodels:
        scatter_kwargs["trendline"] = "ols"

    try:
        fig = px.scatter(**scatter_kwargs)
    except Exception:
        scatter_kwargs.pop("trendline", None)
        try:
            fig = px.scatter(**scatter_kwargs)
        except Exception:
            scatter_kwargs.pop("hover_data", None)
            fig = px.scatter(**scatter_kwargs)

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        xaxis=dict(showgrid=True, gridcolor="#334155", title="Years of Professional Experience"),
        yaxis=dict(showgrid=True, gridcolor="#334155", tickprefix="$", tickformat=",")
    )
    return fig

def create_turnover_by_department_chart(df: pd.DataFrame) -> go.Figure:
    """Renders a bar chart showing employee turnover / attrition rate by department."""
    if df.empty or "department" not in df.columns or "turnover_status" not in df.columns:
        return go.Figure()

    stats = df.groupby("department").agg(
        total=("employee_id", "count"),
        resigned=("turnover_status", lambda s: (s == "Resigned").sum())
    ).reset_index()
    stats["turnover_rate"] = (stats["resigned"] / stats["total"]) * 100.0
    stats = stats.sort_values(by="turnover_rate", ascending=False)

    fig = px.bar(
        stats,
        x="department",
        y="turnover_rate",
        text=stats["turnover_rate"].apply(lambda v: f"{v:.1f}%"),
        color="turnover_rate",
        color_continuous_scale="Reds",
        title="<b>Turnover / Attrition Rate by Department (%)</b>",
        labels={"turnover_rate": "Turnover Rate (%)", "department": "Department"}
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Turnover Rate: %{y:.1f}%<extra></extra>"
    )
    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        coloraxis_showscale=False,
        yaxis=dict(showgrid=True, gridcolor="#334155", ticksuffix="%"),
        xaxis=dict(showgrid=False, tickangle=-20)
    )
    return fig

def create_turnover_reasons_chart(df: pd.DataFrame) -> go.Figure:
    """Renders a horizontal bar chart of top reasons for employee departures."""
    if df.empty or "turnover_reason" not in df.columns:
        return go.Figure()

    resigned_df = df[df["turnover_status"] == "Resigned"]
    if resigned_df.empty:
        return go.Figure()

    reasons = resigned_df["turnover_reason"].dropna().value_counts().reset_index()
    reasons.columns = ["reason", "count"]
    reasons = reasons.sort_values(by="count", ascending=True)

    fig = px.bar(
        reasons,
        x="count",
        y="reason",
        orientation="h",
        color_discrete_sequence=["#EC4899"],
        text="count",
        title="<b>Primary Reasons for Employee Resignation</b>",
        labels={"count": "Number of Exits", "reason": "Reason"}
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        xaxis=dict(showgrid=True, gridcolor="#334155"),
        yaxis=dict(showgrid=False)
    )
    return fig

def create_attendance_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Renders attendance trends by work arrangement and leaves taken."""
    if df.empty or "attendance_rate_pct" not in df.columns:
        return go.Figure()

    # If remote_work_ratio is present, map to arrangements
    work_modes = {0.0: "On-site", 0.5: "Hybrid", 1.0: "Remote"}
    temp_df = df.copy()
    if "remote_work_ratio" in temp_df.columns:
        temp_df["mode"] = temp_df["remote_work_ratio"].map(work_modes).fillna("Flexible")
    else:
        temp_df["mode"] = "Company Average"

    fig = px.box(
        temp_df,
        x="mode",
        y="attendance_rate_pct",
        color="mode",
        color_discrete_sequence=["#10B981", "#6366F1", "#06B6D4"],
        title="<b>Attendance Rate (%) by Work Arrangement</b>",
        labels={"attendance_rate_pct": "Attendance Rate (%)", "mode": "Work Arrangement"}
    )
    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor="#334155", ticksuffix="%")
    )
    return fig

def create_experience_brackets_chart(df: pd.DataFrame) -> go.Figure:
    """Renders distribution of workforce experience tiers."""
    if df.empty or "years_of_experience" not in df.columns:
        return go.Figure()

    def categorize_exp(years):
        if years < 2:
            return "0-2 Yrs (Entry)"
        elif years < 5:
            return "3-5 Yrs (Mid-Level)"
        elif years < 10:
            return "6-10 Yrs (Senior)"
        else:
            return "10+ Yrs (Lead/Principal)"

    temp = df.copy()
    temp["exp_bracket"] = temp["years_of_experience"].apply(categorize_exp)
    bracket_counts = temp["exp_bracket"].value_counts().reindex(
        ["0-2 Yrs (Entry)", "3-5 Yrs (Mid-Level)", "6-10 Yrs (Senior)", "10+ Yrs (Lead/Principal)"]
    ).dropna().reset_index()
    bracket_counts.columns = ["bracket", "count"]

    fig = px.bar(
        bracket_counts,
        x="bracket",
        y="count",
        color="bracket",
        color_discrete_sequence=["#06B6D4", "#3B82F6", "#6366F1", "#8B5CF6"],
        title="<b>Workforce Experience Tier Distribution</b>",
        text="count",
        labels={"bracket": "Experience Tier", "count": "Employee Count"}
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor="#334155")
    )
    return fig
