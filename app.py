import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

# -------------------------------------------------
# 1. Basic page config
# -------------------------------------------------
st.set_page_config(
    page_title="Toronto Water-Quality Analytics",
    layout="wide",
)

st.title("Toronto Water-Quality Analytics Dashboard")
st.write("Interactive visualizations generated from processed CSV files.")

DATA_DIR = Path("data")

# -------------------------------------------------
# 2. Load data
# -------------------------------------------------
monthly_stats = pd.read_csv(DATA_DIR / "monthly_overall_stats.csv")
top_char_stats = pd.read_csv(DATA_DIR / "monthly_top_characteristics_stats.csv")
location_stats = pd.read_csv(DATA_DIR / "location_summary_stats.csv")
seasonal_stats = pd.read_csv(DATA_DIR / "seasonal_median_by_month.csv")

# Make sure key columns are present (defensive renames for seasonal table)
seasonal_stats = seasonal_stats.rename(
    columns={
        "month": "Month",
        "median_resultvalue": "Median",
        "month_name": "Month Name",
    }
)

# -------------------------------------------------
# 3. Sidebar filters
# -------------------------------------------------
st.sidebar.header("Filters")

min_year = int(monthly_stats["Year"].min())
max_year = int(monthly_stats["Year"].max())
year_range = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

# Use correct column name here: "Month Name"
if "Month Name" in monthly_stats.columns:
    month_options = sorted(monthly_stats["Month Name"].dropna().unique())
    selected_months = st.sidebar.multiselect(
        "Months (optional)",
        options=month_options,
        default=month_options,
    )
else:
    selected_months = None

# For location-level plots
if "Monitoringlocationname" in location_stats.columns:
    location_options = sorted(location_stats["Monitoringlocationname"].unique())
else:
    location_options = []

selected_locations = st.sidebar.multiselect(
    "Monitoring locations (optional)",
    options=location_options,
    default=location_options,
)

# -------------------------------------------------
# 4. Apply filters
# -------------------------------------------------
filtered_monthly = monthly_stats[
    (monthly_stats["Year"] >= year_range[0])
    & (monthly_stats["Year"] <= year_range[1])
]

if selected_months is not None and len(selected_months) > 0:
    filtered_monthly = filtered_monthly[
        filtered_monthly["Month Name"].isin(selected_months)
    ]

filtered_top_char = top_char_stats[
    (top_char_stats["Year"] >= year_range[0])
    & (top_char_stats["Year"] <= year_range[1])
]

filtered_location = location_stats[
    (location_stats["Year"] >= year_range[0])
    & (location_stats["Year"] <= year_range[1])
]

if len(selected_locations) > 0:
    filtered_location = filtered_location[
        filtered_location["Monitoringlocationname"].isin(selected_locations)
    ]

# -------------------------------------------------
# 5. Layout: three main sections
# -------------------------------------------------

# --- Section 1: Monthly overall trends ---
st.subheader("Monthly Water-Quality Trends (1964–2024)")

fig_monthly = px.line(
    filtered_monthly,
    x="Activity Datetime",
    y="Mean",
    color="Month Name",
    labels={
        "Activity Datetime": "Date",
        "Mean": "Mean Measurement Value",
        "Month Name": "Month",
    },
    template="plotly_white",
)
st.plotly_chart(fig_monthly, use_container_width=True)

# --- Section 2: Top parameters over time ---
st.subheader("Water-Quality Trends for Top Parameters")

if "Characteristicname" in filtered_top_char.columns:
    fig_params = px.line(
        filtered_top_char,
        x="Activity Datetime",
        y="Mean",
        color="Characteristicname",
        labels={
            "Activity Datetime": "Date",
            "Mean": "Mean Measurement Value",
            "Characteristicname": "Parameter",
        },
        template="plotly_white",
        facet_row="Characteristicname",
    )
    fig_params.update_yaxes(matches=None)  # allow each facet its own scale
    st.plotly_chart(fig_params, use_container_width=True)
else:
    st.info("`Characteristicname` column not found in monthly_top_characteristics_stats.csv.")

# --- Section 3: Location summaries + seasonal pattern ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Location-Level Summary (Mean by Year)")
    if "Monitoringlocationname" in filtered_location.columns:
        fig_loc = px.line(
            filtered_location,
            x="Year",
            y="Mean",
            color="Monitoringlocationname",
            labels={
                "Year": "Year",
                "Mean": "Mean Measurement Value",
                "Monitoringlocationname": "Monitoring Location",
            },
            template="plotly_white",
        )
        st.plotly_chart(fig_loc, use_container_width=True)
    else:
        st.info("`Monitoringlocationname` column not found in location_summary_stats.csv.")

with col2:
    st.subheader("Seasonal Pattern (Median by Month)")
    if {"Month", "Median"}.issubset(seasonal_stats.columns):
        fig_seasonal = px.bar(
            seasonal_stats,
            x="Month",
            y="Median",
            labels={
                "Month": "Month",
                "Median": "Median Measurement Value",
            },
            template="plotly_white",
        )
        st.plotly_chart(fig_seasonal, use_container_width=True)
    else:
        st.info("Seasonal median table does not have expected `Month` and `Median` columns.")
