import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------- Paths ----------
DATA_DIR = Path("data")

MONTHLY_PATH = DATA_DIR / "monthly_overall_stats.csv"
TOP_CHAR_PATH = DATA_DIR / "monthly_top_characteristics_stats.csv"
LOCATION_PATH = DATA_DIR / "location_summary_stats.csv"
SEASONAL_PATH = DATA_DIR / "seasonal_median_by_month.csv"


# ---------- Helpers ----------

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Strip whitespace from column names just in case
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    return df


def find_year_column(df: pd.DataFrame) -> str:
    """
    Try to locate the 'Year' column in a case-insensitive way.
    Returns the actual column name, or None if not found.
    """
    for col in df.columns:
        if isinstance(col, str) and col.strip().lower() == "year":
            return col
    return None


# ---------- Load data ----------

monthly_stats = load_csv(MONTHLY_PATH)
top_char_stats = load_csv(TOP_CHAR_PATH)
location_stats = load_csv(LOCATION_PATH)
seasonal_stats = load_csv(SEASONAL_PATH)

year_col_monthly = find_year_column(monthly_stats)

if year_col_monthly is None:
    st.error(
        "Could not find a 'Year' column in monthly_overall_stats.csv. "
        "Please check the file and make sure it has a Year column."
    )
    st.stop()

# We will also try to find year column in the other tables (if present)
year_col_top = find_year_column(top_char_stats)
year_col_loc = find_year_column(location_stats)
year_col_seasonal = find_year_column(seasonal_stats)

# Make sure the year series is numeric
year_series = pd.to_numeric(monthly_stats[year_col_monthly], errors="coerce").dropna()
min_year = int(year_series.min())
max_year = int(year_series.max())


# ---------- Layout ----------

st.set_page_config(
    page_title="Toronto Water-Quality Analytics",
    layout="wide",
)

st.title("Toronto Water-Quality Analytics Dashboard")
st.write("Interactive visualizations generated from processed CSV files.")

st.sidebar.header("Filters")

# Year range filter (based on monthly_overall_stats)
year_range = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

# Optional month filter if Month Name column exists
month_name_col = None
for col in monthly_stats.columns:
    if isinstance(col, str) and col.strip().lower() in ["month name", "month_name"]:
        month_name_col = col
        break

if month_name_col:
    all_months = list(monthly_stats[month_name_col].dropna().unique())
    all_months_sorted = sorted(all_months, key=lambda m: pd.to_datetime(m, format="%B").month)
    selected_months = st.sidebar.multiselect(
        "Months",
        options=all_months_sorted,
        default=all_months_sorted,
    )
else:
    selected_months = None


# ---------- 1. Monthly overall trends ----------

st.subheader("Monthly Water-Quality Trends (1964–2024)")

df_monthly = monthly_stats.copy()
df_monthly[year_col_monthly] = pd.to_numeric(df_monthly[year_col_monthly], errors="coerce")

mask = (df_monthly[year_col_monthly] >= year_range[0]) & (
    df_monthly[year_col_monthly] <= year_range[1]
)
df_monthly = df_monthly[mask]

if month_name_col and selected_months:
    df_monthly = df_monthly[df_monthly[month_name_col].isin(selected_months)]

if df_monthly.empty:
    st.info("No data for the selected filters.")
else:
    fig_monthly = px.line(
        df_monthly,
        x=year_col_monthly,
        y="Mean",
        color=month_name_col if month_name_col else None,
        labels={
            year_col_monthly: "Year",
            "Mean": "Mean Measurement Value",
        },
        title="Monthly Mean Water-Quality Trends",
    )
    fig_monthly.update_layout(legend_title_text="Month")
    st.plotly_chart(fig_monthly, use_container_width=True)


# ---------- 2. Top parameters trends ----------

st.subheader("Trends for Top Water-Quality Parameters")

if year_col_top is not None:
    df_top = top_char_stats.copy()
    df_top[year_col_top] = pd.to_numeric(df_top[year_col_top], errors="coerce")
    mask_top = (df_top[year_col_top] >= year_range[0]) & (
        df_top[year_col_top] <= year_range[1]
    )
    df_top = df_top[mask_top]
else:
    df_top = top_char_stats.copy()

char_col = None
for col in df_top.columns:
    if isinstance(col, str) and col.strip().lower() in ["characteristicname", "parameter", "characteristic"]:
        char_col = col
        break

if df_top.empty or char_col is None:
    st.info("Top-parameter table is missing a recognizable parameter/characteristic column.")
else:
    fig_top = px.line(
        df_top,
        x=year_col_top if year_col_top else df_top.columns[0],
        y="Mean",
        color=char_col,
        facet_row=char_col,
        facet_row_spacing=0.02,
        labels={
            "Mean": "Mean Measurement Value",
            char_col: "Parameter",
        },
        title="Water-Quality Trends for Top Parameters",
    )
    fig_top.update_yaxes(matches=None, showgrid=True)
    fig_top.update_layout(showlegend=False)
    st.plotly_chart(fig_top, use_container_width=True)


# ---------- 3. Location summary (latest period) ----------

st.subheader("Location Summary (Latest Available Years)")

df_loc = location_stats.copy()
if year_col_loc is not None:
    df_loc[year_col_loc] = pd.to_numeric(df_loc[year_col_loc], errors="coerce")
    latest_year = int(df_loc[year_col_loc].max())
    st.caption(f"Showing statistics for latest year in data: **{latest_year}**")
    df_loc_latest = df_loc[df_loc[year_col_loc] == latest_year]
else:
    df_loc_latest = df_loc

# Try to find a location column
loc_col = None
for col in df_loc_latest.columns:
    if isinstance(col, str) and "location" in col.lower():
        loc_col = col
        break

if loc_col is None:
    st.dataframe(df_loc_latest)
else:
    fig_loc = px.bar(
        df_loc_latest,
        x=loc_col,
        y="Mean",
        labels={loc_col: "Monitoring Location", "Mean": "Mean Measurement Value"},
        title="Mean Measurement by Monitoring Location (Latest Year)",
    )
    fig_loc.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig_loc, use_container_width=True)


# ---------- 4. Seasonal pattern (optional) ----------

st.subheader("Seasonal Patterns (Median by Month)")

if not seasonal_stats.empty:
    # Try to find month name column
    season_month_col = None
    for col in seasonal_stats.columns:
        if isinstance(col, str) and col.strip().lower() in ["month name", "month_name", "month"]:
            season_month_col = col
            break

    if season_month_col is None:
        st.dataframe(seasonal_stats)
    else:
        fig_season = px.line(
            seasonal_stats,
            x=season_month_col,
            y="Median",
            labels={season_month_col: "Month", "Median": "Median Measurement Value"},
            title="Seasonal Median Pattern by Month",
        )
        st.plotly_chart(fig_season, use_container_width=True)
else:
    st.info("No seasonal median table found.")
