import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

# -----------------------------------------------------------------------------
# Paths & data loading
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


def _map_column(df: pd.DataFrame, candidates, new_name):
    """
    Try to map one of the candidate column names in df to a standard new_name.
    If none are found, show a clear Streamlit error and return False.
    """
    for col in df.columns:
        if col in candidates:
            if col != new_name:
                df.rename(columns={col: new_name}, inplace=True)
            return True

    st.error(
        f"Missing expected column for '{new_name}'. "
        f"Tried names {candidates}, but only found: {list(df.columns)}"
    )
    return False


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    df = pd.read_csv(path)

    # Strip whitespace from column names (common issue when exporting from tools)
    df.columns = [c.strip() for c in df.columns]
    return df


# Load all four curated tables
monthly_stats = load_csv("monthly_overall_stats.csv")
top_char_stats = load_csv("monthly_top_characteristics_stats.csv")
location_stats = load_csv("location_summary_stats.csv")
seasonal_stats = load_csv("seasonal_median_by_month.csv")

# -----------------------------------------------------------------------------
# Standardise column names so the rest of the code is safe
# -----------------------------------------------------------------------------

# --- monthly_overall_stats.csv ---
_ok = True
_ok &= _map_column(monthly_stats, ["Year", "year"], "Year")
_ok &= _map_column(
    monthly_stats, ["Month Name", "Month_Name", "month_name"], "Month_Name"
)
_ok &= _map_column(
    monthly_stats,
    ["Mean", "mean", "mean_resultvalue", "Mean_ResultValue"],
    "Mean",
)

# If anything essential is missing, stop here
if not _ok:
    st.stop()

# --- monthly_top_characteristics_stats.csv ---
_ok_top = True
_ok_top &= _map_column(top_char_stats, ["Year", "year"], "Year")
_ok_top &= _map_column(
    top_char_stats,
    ["Characteristicname", "characteristicname", "Parameter", "parameter"],
    "Characteristic",
)
_ok_top &= _map_column(
    top_char_stats,
    ["Mean", "mean", "mean_resultvalue", "Mean_ResultValue"],
    "Mean",
)

if not _ok_top:
    st.stop()

# --- location_summary_stats.csv ---
_ok_loc = True
_ok_loc &= _map_column(
    location_stats,
    [
        "Monitoringlocationname",
        "monitoringlocationname",
        "Monitoring Location",
        "monitoring_location",
    ],
    "Location",
)
_ok_loc &= _map_column(
    location_stats,
    ["Mean", "mean", "mean_resultvalue", "Mean_ResultValue"],
    "Mean",
)

if not _ok_loc:
    st.stop()

# --- seasonal_median_by_month.csv ---
_ok_season = True
_ok_season &= _map_column(
    seasonal_stats, ["Month Name", "Month_Name", "month_name"], "Month_Name"
)
_ok_season &= _map_column(
    seasonal_stats,
    ["Median", "median", "median_resultvalue", "Median_ResultValue"],
    "Median",
)

if not _ok_season:
    st.stop()

# Make sure Year is integer (for slider and axes)
if "Year" in monthly_stats.columns:
    monthly_stats["Year"] = monthly_stats["Year"].astype(int)

if "Year" in top_char_stats.columns:
    top_char_stats["Year"] = top_char_stats["Year"].astype(int)

# -----------------------------------------------------------------------------
# Page configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Toronto Water-Quality Analytics",
    layout="wide",
)

st.title("Toronto Water-Quality Analytics Dashboard")
st.write("Interactive visualizations generated from processed CSV files.")

# -----------------------------------------------------------------------------
# Sidebar filters
# -----------------------------------------------------------------------------

st.sidebar.header("Filters")

min_year = int(monthly_stats["Year"].min())
max_year = int(monthly_stats["Year"].max())

year_min, year_max = st.sidebar.select_slider(
    "Year range",
    options=list(range(min_year, max_year + 1)),
    value=(min_year, max_year),
)

all_months = list(monthly_stats["Month_Name"].unique())
all_months_sorted = sorted(
    all_months,
    key=lambda m: ["January", "February", "March", "April", "May",
                   "June", "July", "August", "September", "October",
                   "November", "December"].index(m)
    if m in [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    else 99,
)

selected_months = st.sidebar.multiselect(
    "Months",
    options=all_months_sorted,
    default=all_months_sorted,
)

st.sidebar.markdown("---")
st.sidebar.write(
    "Data sources: `monthly_overall_stats.csv`, "
    "`monthly_top_characteristics_stats.csv`, "
    "`location_summary_stats.csv`, "
    "`seasonal_median_by_month.csv`."
)

# -----------------------------------------------------------------------------
# 1. Monthly mean water-quality trends
# -----------------------------------------------------------------------------

st.subheader(f"Monthly Water-Quality Trends ({year_min}–{year_max})")

df_monthly = monthly_stats[
    (monthly_stats["Year"] >= year_min)
    & (monthly_stats["Year"] <= year_max)
    & (monthly_stats["Month_Name"].isin(selected_months))
].copy()

if df_monthly.empty:
    st.warning("No data for the selected year range and months.")
else:
    fig_monthly = px.line(
        df_monthly,
        x="Year",
        y="Mean",
        color="Month_Name",
        title="Monthly Mean Water-Quality Trends",
        labels={
            "Year": "Year",
            "Mean": "Mean measurement value",
            "Month_Name": "Month",
        },
    )
    fig_monthly.update_layout(
        legend_title_text="Month",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

# -----------------------------------------------------------------------------
# 2. Trends for top parameters
# -----------------------------------------------------------------------------

st.subheader("Trends for Top Water-Quality Parameters")

df_top = top_char_stats[
    (top_char_stats["Year"] >= year_min)
    & (top_char_stats["Year"] <= year_max)
].copy()

if df_top.empty:
    st.warning("No parameter data for the selected year range.")
else:
    fig_top = px.line(
        df_top,
        x="Year",
        y="Mean",
        color="Characteristic",
        title="Trends for Top Water-Quality Parameters",
        labels={
            "Year": "Year",
            "Mean": "Mean measurement value",
            "Characteristic": "Parameter",
        },
    )
    fig_top.update_layout(
        legend_title_text="Parameter",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    st.plotly_chart(fig_top, use_container_width=True)

# -----------------------------------------------------------------------------
# 3. Top monitoring locations by mean value
# -----------------------------------------------------------------------------

st.subheader("Top 20 Monitoring Locations by Mean Value")

# Sort descending and take top 20
df_loc = location_stats.sort_values("Mean", ascending=False).head(20)

if df_loc.empty:
    st.warning("No location summary data available.")
else:
    fig_loc = px.bar(
        df_loc,
        x="Mean",
        y="Location",
        orientation="h",
        title="Top 20 Monitoring Locations by Mean Value",
        labels={
            "Mean": "Mean measurement value",
            "Location": "Monitoring location",
        },
    )
    fig_loc.update_layout(
        yaxis=dict(autorange="reversed"),
        margin=dict(l=200, r=20, t=60, b=40),
    )
    st.plotly_chart(fig_loc, use_container_width=True)

# -----------------------------------------------------------------------------
# 4. Seasonal patterns (median by month)
# -----------------------------------------------------------------------------

st.subheader("Seasonal Patterns (Median by Month)")

# Order months correctly if we have standard month names
seasonal_df = seasonal_stats.copy()

month_order = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

if seasonal_df["Month_Name"].dtype == object:
    seasonal_df["Month_Name"] = pd.Categorical(
        seasonal_df["Month_Name"],
        categories=month_order,
        ordered=True,
    )
    seasonal_df = seasonal_df.sort_values("Month_Name")

if seasonal_df.empty:
    st.warning("No seasonal median data available.")
else:
    fig_season = px.bar(
        seasonal_df,
        x="Month_Name",
        y="Median",
        title="Seasonal Median Water-Quality Values by Month",
        labels={
            "Month_Name": "Month",
            "Median": "Median measurement value",
        },
    )
    fig_season.update_layout(
        margin=dict(l=40, r=20, t=60, b=40),
    )
    st.plotly_chart(fig_season, use_container_width=True)
