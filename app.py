import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

# --------------------------------------------------------------------
# Paths & data loading
# --------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    df = pd.read_csv(path)

    # Strip whitespace from column names, very common in CSVs
    df.columns = [c.strip() for c in df.columns]
    return df


monthly_stats = load_csv("monthly_overall_stats.csv")
top_char_stats = load_csv("monthly_top_characteristics_stats.csv")
location_stats = load_csv("location_summary_stats.csv")
seasonal_stats = load_csv("seasonal_median_by_month.csv")

# --------------------------------------------------------------------
# Column name helpers (be tolerant of small variations)
# --------------------------------------------------------------------
def first_present(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


# Guess column names for the monthly table
COL_YEAR = first_present(monthly_stats, ["Year", "year"])
COL_MONTH_NAME = first_present(monthly_stats, ["Month Name", "month_name", "Month"])
COL_MEAN = first_present(monthly_stats, ["Mean", "mean", "MeanValue"])
COL_ACTIVITY_DT = first_present(monthly_stats, ["Activity Datetime", "activity_datetime", "Date"])

if not all([COL_YEAR, COL_MONTH_NAME, COL_MEAN]):
    st.stop()  # hard stop with a clear message
    # (Streamlit will show the error text we print below)
    raise RuntimeError(
        f"Monthly stats CSV is missing expected columns. "
        f"Found: {list(monthly_stats.columns)}"
    )

# Ensure Year is numeric
monthly_stats[COL_YEAR] = pd.to_numeric(monthly_stats[COL_YEAR], errors="coerce")
monthly_stats = monthly_stats.dropna(subset=[COL_YEAR])
monthly_stats[COL_YEAR] = monthly_stats[COL_YEAR].astype(int)

# --------------------------------------------------------------------
# Streamlit layout
# --------------------------------------------------------------------
st.set_page_config(
    page_title="Toronto Water-Quality Analytics",
    layout="wide",
)

st.title("Toronto Water-Quality Analytics Dashboard")
st.caption("Interactive visualizations generated from processed CSV files.")

# --------------------------------------------------------------------
# Sidebar filters (shared where possible)
# --------------------------------------------------------------------
st.sidebar.header("Filters")

min_year = int(monthly_stats[COL_YEAR].min())
max_year = int(monthly_stats[COL_YEAR].max())

year_range = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

# Month order to keep plots intuitive
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

available_months = sorted(monthly_stats[COL_MONTH_NAME].dropna().unique(),
                          key=lambda m: month_order.index(m) if m in month_order else 99)

selected_months = st.sidebar.multiselect(
    "Months",
    options=available_months,
    default=available_months,
)

# --------------------------------------------------------------------
# 1. Monthly overall trends
# --------------------------------------------------------------------
st.subheader("Monthly Water-Quality Trends (1964–2024)")

df_monthly = monthly_stats.copy()
df_monthly = df_monthly[
    (df_monthly[COL_YEAR] >= year_range[0]) &
    (df_monthly[COL_YEAR] <= year_range[1])
]

if selected_months:
    df_monthly = df_monthly[df_monthly[COL_MONTH_NAME].isin(selected_months)]

if df_monthly.empty:
    st.warning("No data for the selected year range and months.")
else:
    # Choose x-axis: prefer Activity Datetime if present
    x_col = COL_ACTIVITY_DT if COL_ACTIVITY_DT in df_monthly.columns else COL_YEAR

    fig_monthly = px.line(
        df_monthly.sort_values([COL_YEAR, COL_MONTH_NAME]),
        x=x_col,
        y=COL_MEAN,
        color=COL_MONTH_NAME,
        title="Monthly Mean Water-Quality Trends",
        labels={
            x_col: "Year" if x_col == COL_YEAR else "Activity Datetime",
            COL_MEAN: "Mean measurement value",
            COL_MONTH_NAME: "Month",
        },
    )
    fig_monthly.update_layout(legend_title_text="Month", height=500)
    st.plotly_chart(fig_monthly, use_container_width=True)

# --------------------------------------------------------------------
# 2. Top parameters – trends over time
# --------------------------------------------------------------------
st.subheader("Water-Quality Trends for Top Parameters (1964–2024)")

# Try to infer column names in the top-characteristics table
TOP_COL_YEAR = first_present(top_char_stats, ["Year", "year"])
TOP_COL_MEAN = first_present(top_char_stats, ["Mean", "mean"])
TOP_COL_CHAR = first_present(top_char_stats, ["Characteristicname", "characteristicname", "Characteristic"])

if all([TOP_COL_YEAR, TOP_COL_MEAN, TOP_COL_CHAR]):
    top_df = top_char_stats.copy()
    top_df[TOP_COL_YEAR] = pd.to_numeric(top_df[TOP_COL_YEAR], errors="coerce")
    top_df = top_df.dropna(subset=[TOP_COL_YEAR])
    top_df[TOP_COL_YEAR] = top_df[TOP_COL_YEAR].astype(int)

    top_df = top_df[
        (top_df[TOP_COL_YEAR] >= year_range[0]) &
        (top_df[TOP_COL_YEAR] <= year_range[1])
    ]

    if top_df.empty:
        st.warning("No parameter trend data for the selected year range.")
    else:
        fig_params = px.line(
            top_df.sort_values([TOP_COL_YEAR, TOP_COL_CHAR]),
            x=TOP_COL_YEAR,
            y=TOP_COL_MEAN,
            color=TOP_COL_CHAR,
            title="Trends for Top Water-Quality Parameters",
            labels={
                TOP_COL_YEAR: "Year",
                TOP_COL_MEAN: "Mean measurement value",
                TOP_COL_CHAR: "Parameter",
            },
        )
        fig_params.update_layout(legend_title_text="Parameter", height=500)
        st.plotly_chart(fig_params, use_container_width=True)
else:
    st.info(
        "Top-parameter CSV does not have the expected columns; "
        f"found: {list(top_char_stats.columns)}"
    )

# --------------------------------------------------------------------
# 3. Location summary – mean by monitoring location
# --------------------------------------------------------------------
st.subheader("Mean Values by Monitoring Location")

LOC_COL_NAME = first_present(location_stats, ["Monitoringlocationname", "monitoringlocationname", "Location"])
LOC_COL_MEAN = first_present(location_stats, ["Mean", "mean"])

if all([LOC_COL_NAME, LOC_COL_MEAN]):
    loc_df = location_stats.copy()
    # Use only a subset for readability – e.g., top 20 by mean
    loc_df = loc_df.sort_values(LOC_COL_MEAN, ascending=False).head(20)

    fig_loc = px.bar(
        loc_df,
        x=LOC_COL_MEAN,
        y=LOC_COL_NAME,
        orientation="h",
        title="Top 20 Monitoring Locations by Mean Value",
        labels={
            LOC_COL_NAME: "Monitoring location",
            LOC_COL_MEAN: "Mean measurement value",
        },
    )
    fig_loc.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_loc, use_container_width=True)
else:
    st.info(
        "Location-summary CSV does not have the expected columns; "
        f"found: {list(location_stats.columns)}"
    )

# --------------------------------------------------------------------
# 4. Seasonal pattern – median by month
# --------------------------------------------------------------------
st.subheader("Seasonal Patterns (Median by Month)")

SEAS_COL_MONTH_NAME = first_present(seasonal_stats, ["Month Name", "month_name", "Month"])
SEAS_COL_MEDIAN = first_present(seasonal_stats, ["MedianResultValue", "Median", "median"])

if all([SEAS_COL_MONTH_NAME, SEAS_COL_MEDIAN]):
    seas_df = seasonal_stats.copy()
    # keep month order consistent
    seas_df[SEAS_COL_MONTH_NAME] = pd.Categorical(
        seas_df[SEAS_COL_MONTH_NAME],
        categories=month_order,
        ordered=True,
    )
    seas_df = seas_df.sort_values(SEAS_COL_MONTH_NAME)

    fig_seasonal = px.bar(
        seas_df,
        x=SEAS_COL_MONTH_NAME,
        y=SEAS_COL_MEDIAN,
        title="Seasonal Pattern – Median Value by Month",
        labels={
            SEAS_COL_MONTH_NAME: "Month",
            SEAS_COL_MEDIAN: "Median measurement value",
        },
    )
    fig_seasonal.update_layout(height=400)
    st.plotly_chart(fig_seasonal, use_container_width=True)
else:
    st.info(
        "Seasonal-median CSV does not have the expected columns; "
        f"found: {list(seasonal_stats.columns)}"
    )
