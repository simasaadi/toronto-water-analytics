# app.py
# Toronto Water-Quality Analytics – Streamlit Portfolio App

import pandas as pd
import streamlit as st
import plotly.express as px

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Toronto Water-Quality Analytics",
    layout="wide",
    page_icon="💧",
)

# ---- GLOBAL STYLE ----
st.markdown(
    """
    <style>
    .main { padding-top: 1rem; }
    .css-18e3th9, .css-1d391kg { padding-top: 1rem; }
    .metric-label { font-size: 0.9rem !important; }
    .metric-value { font-size: 1.3rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- LOAD DATA ----
@st.cache_data
def load_data():
    monthly = pd.read_csv("data/monthly_overall_stats.csv")
    top_chars = pd.read_csv("data/monthly_top_characteristics_stats.csv")
    locations = pd.read_csv("data/location_summary_stats.csv")
    seasonal = pd.read_csv("data/seasonal_median_by_month.csv")

    # Basic cleaning / typing for this specific project
    # monthly_overall_stats
    if "Activity Datetime" in monthly.columns:
        monthly["Activity Datetime"] = pd.to_datetime(monthly["Activity Datetime"])
    if "Year" in monthly.columns:
        monthly["Year"] = monthly["Year"].astype(int)

    # monthly_top_characteristics_stats
    if "Year" in top_chars.columns:
        top_chars["Year"] = top_chars["Year"].astype(int)

    # seasonal_median_by_month
    # Expecting: month (1–12), median_resultvalue, month_name
    if "month" in seasonal.columns:
        seasonal["month"] = seasonal["month"].astype(int)

    return monthly, top_chars, locations, seasonal


monthly_stats, top_chars_stats, location_stats, seasonal_stats = load_data()

# ---- SIDEBAR FILTERS ----
st.sidebar.title("Filters")

# Year range slider (based on monthly stats)
if "Year" in monthly_stats.columns:
    min_year = int(monthly_stats["Year"].min())
    max_year = int(monthly_stats["Year"].max())
else:
    # fallback if Year not present
    min_year = int(monthly_stats["Activity Datetime"].dt.year.min())
    max_year = int(monthly_stats["Activity Datetime"].dt.year.max())

year_range = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

# Month filter (uses calendar order)
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
available_months = [
    m for m in month_order
    if "Month Name" in monthly_stats.columns
    and m in monthly_stats["Month Name"].unique()
]
default_months = available_months  # start with all

selected_months = st.sidebar.multiselect(
    "Months",
    options=available_months,
    default=default_months,
)

# Parameter filter for “Top parameters” view
if "Characteristicname" in top_chars_stats.columns:
    all_params = sorted(top_chars_stats["Characteristicname"].unique())
else:
    all_params = []

selected_params = st.sidebar.multiselect(
    "Parameters (for trends chart)",
    options=all_params,
    default=all_params[:5] if all_params else [],
)

st.sidebar.markdown("---")
st.sidebar.caption("Data: Toronto AOC1 water-quality monitoring (processed CSV exports).")

# ---- TITLE & INTRO ----
st.title("Toronto Water-Quality Analytics Dashboard")
st.caption("Interactive visualizations generated from processed water-quality summary tables.")

# ---- OVERVIEW METRICS ----
col1, col2, col3 = st.columns(3)

with col1:
    n_years = max_year - min_year + 1
    st.metric("Years of data", f"{n_years}", f"{min_year}–{max_year}")

with col2:
    if "Monitoringlocationname" in location_stats.columns:
        n_locations = location_stats["Monitoringlocationname"].nunique()
    else:
        n_locations = monthly_stats.get("Monitoringlocationid", pd.Series()).nunique()
    st.metric("Monitoring locations", n_locations)

with col3:
    if "Characteristicname" in top_chars_stats.columns:
        n_params = top_chars_stats["Characteristicname"].nunique()
    else:
        n_params = 0
    st.metric("Water-quality parameters", n_params)

st.markdown("---")

# --------------------------------------------------------------------
# SECTION 1 – Monthly Mean Trends
# --------------------------------------------------------------------
st.subheader("Monthly Mean Water-Quality Trends (1964–2024)")

if "Year" in monthly_stats.columns and "Month Name" in monthly_stats.columns:
    monthly_filtered = monthly_stats[
        (monthly_stats["Year"].between(year_range[0], year_range[1]))
        & (monthly_stats["Month Name"].isin(selected_months))
    ].copy()

    if not monthly_filtered.empty:
        fig_monthly = px.line(
            monthly_filtered,
            x="Activity Datetime" if "Activity Datetime" in monthly_filtered.columns else "Year",
            y="Mean",
            color="Month Name",
            category_orders={"Month Name": month_order},
            template="plotly_dark",
            labels={
                "Activity Datetime": "Activity Datetime",
                "Year": "Year",
                "Mean": "Mean measurement value",
                "Month Name": "Month",
            },
        )
        fig_monthly.update_layout(
            height=500,
            legend_title="Month",
            margin=dict(l=10, r=10, t=40, b=40),
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    else:
        st.info("No data for the selected year range and months.")
else:
    st.warning("Monthly summary table is missing expected columns (Year / Month Name).")

st.caption(
    "Each line shows the monthly mean measurement value across all monitoring locations "
    "for the selected months and years."
)

st.markdown("---")

# --------------------------------------------------------------------
# SECTION 2 – Trends for Top Parameters
# --------------------------------------------------------------------
st.subheader("Trends for Top Water-Quality Parameters")

if selected_params and "Characteristicname" in top_chars_stats.columns:
    chars_filtered = top_chars_stats[
        (top_chars_stats["Year"].between(year_range[0], year_range[1]))
        & (top_chars_stats["Characteristicname"].isin(selected_params))
    ].copy()

    if not chars_filtered.empty:
        fig_params = px.line(
            chars_filtered,
            x="Year",
            y="Mean",
            color="Characteristicname",
            template="plotly_dark",
            labels={
                "Year": "Year",
                "Mean": "Mean measurement value",
                "Characteristicname": "Parameter",
            },
        )
        fig_params.update_layout(
            height=450,
            legend_title="Parameter",
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_params, use_container_width=True)
    else:
        st.info("No parameter data for the selected filters.")
else:
    st.info("No parameters selected or `Characteristicname` column missing.")

st.caption(
    "Use the sidebar to choose which parameters to display. This view highlights long-term "
    "changes in key water-quality indicators."
)

st.markdown("---")

# --------------------------------------------------------------------
# SECTION 3 – Top Monitoring Locations
# --------------------------------------------------------------------
st.subheader("Top Monitoring Locations by Mean Value")

if "Monitoringlocationname" in location_stats.columns and "Mean" in location_stats.columns:
    # always show same top locations (not filtered by year – this table is already aggregated)
    top_locs = (
        location_stats.sort_values("Mean", ascending=False)
        .head(20)
        .copy()
    )

    fig_locs = px.bar(
        top_locs,
        x="Mean",
        y="Monitoringlocationname",
        orientation="h",
        template="plotly_dark",
        labels={
            "Mean": "Mean measurement value",
            "Monitoringlocationname": "Monitoring location",
        },
    )
    fig_locs.update_layout(
        height=550,
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig_locs, use_container_width=True)
else:
    st.warning("Location summary table is missing expected columns.")

st.caption(
    "Locations are ranked by overall mean measurement value across all parameters. "
    "This can help flag sites with consistently higher concentrations."
)

st.markdown("---")

# --------------------------------------------------------------------
# SECTION 4 – Seasonal Patterns
# --------------------------------------------------------------------
st.subheader("Seasonal Patterns (Median by Month)")

if {"month", "median_resultvalue", "month_name"}.issubset(seasonal_stats.columns):
    # keep calendar order
    seasonal_sorted = seasonal_stats.copy()
    seasonal_sorted["month_name"] = pd.Categorical(
        seasonal_sorted["month_name"],
        categories=month_order,
        ordered=True,
    )
    seasonal_sorted = seasonal_sorted.sort_values("month_name")

    fig_seasonal = px.bar(
        seasonal_sorted,
        x="month_name",
        y="median_resultvalue",
        template="plotly_dark",
        labels={
            "month_name": "Month",
            "median_resultvalue": "Median measurement value",
        },
    )
    fig_seasonal.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Month",
    )
    st.plotly_chart(fig_seasonal, use_container_width=True)
else:
    st.warning("Seasonal table is missing expected columns (month, median_resultvalue, month_name).")

st.caption(
    "Median values are more robust to extreme outliers and highlight typical seasonal patterns "
    "over the full monitoring period."
)
