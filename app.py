import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Toronto Water-Quality Trends",
    layout="wide"
)

st.title("Toronto Water-Quality Analytics Dashboard")
st.markdown("Interactive visualizations generated from processed CSV files.")

# ---- Load Data ----
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

location_stats = load_csv("data/location_summary_stats.csv")
monthly_stats = load_csv("data/monthly_overall_stats.csv")
top_stats = load_csv("data/monthly_top_characteristics_stats.csv")
seasonal_stats = load_csv("data/seasonal_median_by_month.csv")

st.sidebar.title("Filters")

# ---- Section 1: Monthly Mean Trends ----
st.header("Monthly Water-Quality Trends (1964–2024)")

month_choice = st.sidebar.multiselect(
    "Select months to display:",
    sorted(monthly_stats["Month Name"].unique()),
    default=["January", "April", "July", "October"]
)

filtered_monthly = monthly_stats[monthly_stats["Month Name"].isin(month_choice)]

fig1 = px.line(
    filtered_monthly,
    x="Year",
    y="Mean",
    color="Month Name",
    title="Monthly Mean Water-Quality Trends",
    markers=True
)
st.plotly_chart(fig1, use_container_width=True)


# ---- Section 2: Top Characteristics Trends ----
st.header("Top Water-Quality Parameters Over Time")

param_choice = st.sidebar.multiselect(
    "Select Parameters:",
    sorted(top_stats["characteristicname"].unique()),
    default=sorted(top_stats["characteristicname"].unique())
)

filtered_params = top_stats[top_stats["characteristicname"].isin(param_choice)]

fig2 = px.line(
    filtered_params,
    x="Year",
    y="Mean",
    color="characteristicname",
    title="Trends for Key Water-Quality Parameters",
    markers=False
)

st.plotly_chart(fig2, use_container_width=True)


# ---- Section 3: Seasonal Trends ----
st.header("Seasonal Median Trends by Month")

fig3 = px.line(
    seasonal_stats,
    x="season",
    y="median_value",
    color="characteristicname",
    title="Seasonal Median Values",
    markers=True
)

st.plotly_chart(fig3, use_container_width=True)


# ---- Section 4: Station Summary Table ----
st.header("Monitoring Locations – Summary Statistics")

st.dataframe(location_stats)


