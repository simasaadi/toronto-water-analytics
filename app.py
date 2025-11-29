import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from pathlib import Path

# -----------------------------------------------------------------------------
# Paths & data loading
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "raw"   # adjust if your CSVs are elsewhere


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


# -----------------------------------------------------------------------------
# Load curated tables
# -----------------------------------------------------------------------------
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

# optional count column if it exists under different names
has_count = False
for cand in ["count", "n", "N", "NumSamples", "num_samples"]:
    if cand in location_stats.columns:
        location_stats.rename(columns={cand: "SampleCount"}, inplace=True)
        has_count = True
        break

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
st.markdown(
    """
This interactive dashboard explores monthly, spatial, and seasonal patterns  
in Toronto water-quality monitoring data derived from curated CSV tables.  
Use the filters on the left to adjust the analysis window and focus.
"""
)

# -----------------------------------------------------------------------------
# Sidebar – global filters
# -----------------------------------------------------------------------------

st.sidebar.header("Global Filters")

min_year = int(monthly_stats["Year"].min())
max_year = int(monthly_stats["Year"].max())

# default to last ~20 years if possible
default_start = max(min_year, max_year - 20)

year_min, year_max = st.sidebar.select_slider(
    "Year range",
    options=list(range(min_year, max_year + 1)),
    value=(default_start, max_year),
)

# Month ordering helper
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

all_months = sorted(
    monthly_stats["Month_Name"].dropna().unique(),
    key=lambda m: month_order.index(m) if m in month_order else 99,
)

selected_months = st.sidebar.multiselect(
    "Months (for monthly & seasonal views)",
    options=all_months,
    default=all_months,
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data sources: `monthly_overall_stats.csv`, "
    "`monthly_top_characteristics_stats.csv`, "
    "`location_summary_stats.csv`, "
    "`seasonal_median_by_month.csv`."
)

# -----------------------------------------------------------------------------
# Prepare filtered datasets used in multiple tabs
# -----------------------------------------------------------------------------

monthly_filtered = monthly_stats[
    (monthly_stats["Year"] >= year_min)
    & (monthly_stats["Year"] <= year_max)
    & (monthly_stats["Month_Name"].isin(selected_months))
].copy()

top_char_filtered = top_char_stats[
    (top_char_stats["Year"] >= year_min)
    & (top_char_stats["Year"] <= year_max)
].copy()

# -----------------------------------------------------------------------------
# KPI cards – high-level summary
# -----------------------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Year range in view", f"{year_min} – {year_max}")

with col2:
    st.metric("Number of months selected", len(selected_months))

with col3:
    n_locations = location_stats["Location"].nunique()
    st.metric("Monitoring locations", n_locations)

with col4:
    n_parameters = top_char_stats["Characteristic"].nunique()
    st.metric("Distinct parameters", n_parameters)

st.markdown("---")

# -----------------------------------------------------------------------------
# Tabs for different analytical views
# -----------------------------------------------------------------------------

tab_overview, tab_parameters, tab_locations, tab_seasonal = st.tabs(
    ["Overview", "Parameter trends", "Location insights", "Seasonality"]
)

# -----------------------------------------------------------------------------
# TAB 1 – Overview (monthly trends + heatmap + annual trend)
# -----------------------------------------------------------------------------

with tab_overview:
    st.subheader("Monthly mean trends across all monitoring sites")

    if monthly_filtered.empty:
        st.warning("No data for the selected year range and months.")
    else:
        # Line chart – monthly mean over time by month
        fig_monthly = px.line(
            monthly_filtered,
            x="Year",
            y="Mean",
            color="Month_Name",
            category_orders={"Month_Name": month_order},
            labels={
                "Year": "Year",
                "Mean": "Mean measurement value",
                "Month_Name": "Month",
            },
        )
        fig_monthly.update_layout(
            legend_title_text="Month",
            margin=dict(l=40, r=20, t=40, b=40),
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

        st.markdown("#### Month–year heatmap of mean values")

        # Create pivot table for heatmap
        heat_df = (
            monthly_filtered.pivot_table(
                index="Month_Name", columns="Year", values="Mean", aggfunc="mean"
            )
            .reindex(index=month_order)
            .dropna(how="all")
        )

        if not heat_df.empty:
            fig_heat = px.imshow(
                heat_df,
                aspect="auto",
                labels=dict(
                    x="Year",
                    y="Month",
                    color="Mean value",
                ),
            )
            fig_heat.update_layout(margin=dict(l=40, r=20, t=40, b=40))
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info(
                "Not enough data to construct a month–year heatmap for the selected filters."
            )

        st.markdown("#### Annual average across all months")

        annual_df = (
            monthly_filtered.groupby("Year", as_index=False)["Mean"].mean()
        )

        show_roll = False
        if len(annual_df) >= 3:
            show_roll = st.checkbox(
                "Show 3-year rolling average", value=True, help="Smoothed trend across years."
            )
            if show_roll:
                annual_df["Rolling_3yr"] = (
                    annual_df["Mean"]
                    .rolling(window=3, min_periods=1)
                    .mean()
                )

        y_cols = ["Mean"]
        if show_roll and "Rolling_3yr" in annual_df.columns:
            y_cols.append("Rolling_3yr")

        fig_annual = px.line(
            annual_df,
            x="Year",
            y=y_cols,
            markers=True,
            labels={
                "Year": "Year",
                "value": "Average of monthly means",
                "variable": "Series",
            },
        )
        fig_annual.update_layout(
            margin=dict(l=40, r=20, t=40, b=40),
        )
        st.plotly_chart(fig_annual, use_container_width=True)

        # allow download of the filtered monthly data
        st.markdown("##### Download data used in this view")
        csv_bytes = monthly_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered monthly data (CSV)",
            data=csv_bytes,
            file_name=f"monthly_filtered_{year_min}_{year_max}.csv",
            mime="text/csv",
        )

# -----------------------------------------------------------------------------
# TAB 2 – Parameter trends (line + summary + trends + boxplot)
# -----------------------------------------------------------------------------

with tab_parameters:
    st.subheader("Trends for key water-quality parameters")

    if top_char_filtered.empty:
        st.warning("No parameter data for the selected year range.")
    else:
        # Allow user to focus on selected parameters
        all_chars = sorted(top_char_filtered["Characteristic"].dropna().unique())
        default_chars = all_chars[:5] if len(all_chars) > 5 else all_chars

        selected_chars = st.multiselect(
            "Select parameters to display",
            options=all_chars,
            default=default_chars,
        )

        if not selected_chars:
            st.info("Please select at least one parameter.")
        else:
            df_params = top_char_filtered[
                top_char_filtered["Characteristic"].isin(selected_chars)
            ].copy()

            view_mode = st.radio(
                "Value scaling",
                ["Raw means", "Indexed (first year = 100)"],
                horizontal=True,
            )

            small_multiples = st.checkbox(
                "Show one panel per parameter (small multiples)", value=False
            )

            # Prepare data for plotting
            df_plot = df_params.copy().sort_values(["Characteristic", "Year"])

            if view_mode == "Indexed (first year = 100)":
                df_plot["Value"] = df_plot.groupby("Characteristic")["Mean"].transform(
                    lambda s: (s / s.iloc[0]) * 100 if s.iloc[0] != 0 else np.nan
                )
                y_col = "Value"
                y_label = "Indexed mean (first year = 100)"
            else:
                df_plot["Value"] = df_plot["Mean"]
                y_col = "Value"
                y_label = "Mean measurement value"

            # Line chart over time
            if small_multiples:
                fig_top = px.line(
                    df_plot,
                    x="Year",
                    y=y_col,
                    color="Characteristic",
                    facet_col="Characteristic",
                    facet_col_wrap=2,
                    markers=True,
                    labels={
                        "Year": "Year",
                        y_col: y_label,
                        "Characteristic": "Parameter",
                    },
                )
                fig_top.update_layout(showlegend=False)
            else:
                fig_top = px.line(
                    df_plot,
                    x="Year",
                    y=y_col,
                    color="Characteristic",
                    markers=True,
                    labels={
                        "Year": "Year",
                        y_col: y_label,
                        "Characteristic": "Parameter",
                    },
                )

            fig_top.update_layout(
                legend_title_text="Parameter",
                margin=dict(l=40, r=20, t=40, b=40),
            )
            st.plotly_chart(fig_top, use_container_width=True)

            # Summary stats table (raw means)
            st.markdown("#### Summary statistics for selected parameters")
            summary = (
                df_params.groupby("Characteristic")["Mean"]
                .agg(["count", "mean", "min", "max"])
                .rename(
                    columns={
                        "count": "Observations",
                        "mean": "Mean of means",
                        "min": "Min mean",
                        "max": "Max mean",
                    }
                )
            )

            # Trend metrics (simple linear regression + % change)
            trends = []
            for char, grp in df_params.groupby("Characteristic"):
                grp_sorted = grp.sort_values("Year")
                if grp_sorted["Year"].nunique() > 1:
                    x = grp_sorted["Year"].values
                    y = grp_sorted["Mean"].values
                    slope, intercept = np.polyfit(x, y, 1)
                    first_val = y[0]
                    last_val = y[-1]
                    pct_change = (
                        (last_val - first_val) / first_val * 100
                        if first_val != 0
                        else np.nan
                    )
                else:
                    slope = np.nan
                    pct_change = np.nan

                trends.append(
                    {
                        "Characteristic": char,
                        "Trend slope per year": slope,
                        "% change (first→last year)": pct_change,
                        "Years of data": grp_sorted["Year"].nunique(),
                    }
                )

            trend_df = pd.DataFrame(trends).set_index("Characteristic")
            trend_df = trend_df.round(2)

            col_summary, col_trend = st.columns(2)
            with col_summary:
                st.dataframe(summary, use_container_width=True)
            with col_trend:
                st.dataframe(trend_df, use_container_width=True)

            st.markdown("#### Distribution of mean values by parameter")

            # Boxplot (each characteristic = distribution across years)
            box_df = df_params.copy()

            fig_box = px.box(
                box_df,
                x="Characteristic",
                y="Mean",
                points="all",
                labels={
                    "Characteristic": "Parameter",
                    "Mean": "Mean measurement value",
                },
            )
            fig_box.update_layout(
                margin=dict(l=40, r=20, t=40, b=40),
            )
            st.plotly_chart(fig_box, use_container_width=True)

            # download button for parameter-level data
            st.markdown("##### Download parameter-level data (filtered)")
            param_csv = df_params.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download parameter data (CSV)",
                data=param_csv,
                file_name=f"parameter_trends_{year_min}_{year_max}.csv",
                mime="text/csv",
            )

# -----------------------------------------------------------------------------
# TAB 3 – Location insights
# -----------------------------------------------------------------------------

with tab_locations:
    st.subheader("Monitoring locations by mean value")

    if location_stats.empty:
        st.warning("No location summary data available.")
    else:
        # Slider for how many locations to show
        max_n = int(min(50, len(location_stats)))
        top_n = st.slider(
            "Number of locations to display (sorted by mean value)",
            min_value=5,
            max_value=max_n,
            value=min(20, max_n),
            step=1,
        )

        sort_option = st.radio(
            "Sort locations by",
            ["Highest mean", "Lowest mean"],
            horizontal=True,
        )

        ascending = sort_option == "Lowest mean"

        df_loc = (
            location_stats.sort_values("Mean", ascending=ascending)
            .head(top_n)
            .copy()
        )

        # Colour by mean value for more analytical feel
        fig_loc = px.bar(
            df_loc,
            x="Mean",
            y="Location",
            orientation="h",
            color="Mean",
            color_continuous_scale="Blues",
            labels={
                "Mean": "Mean measurement value",
                "Location": "Monitoring location",
            },
            hover_data=["Mean"]
            + (["SampleCount"] if has_count and "SampleCount" in df_loc.columns else []),
        )
        fig_loc.update_layout(
            yaxis=dict(autorange="reversed"),
            margin=dict(l=200, r=20, t=40, b=40),
            coloraxis_colorbar_title="Mean",
        )
        st.plotly_chart(fig_loc, use_container_width=True)

        st.markdown("#### Location detail")
        st.dataframe(df_loc, use_container_width=True)

        # download button
        loc_csv = df_loc.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download displayed locations (CSV)",
            data=loc_csv,
            file_name="location_summary_topN.csv",
            mime="text/csv",
        )

# -----------------------------------------------------------------------------
# TAB 4 – Seasonality
# -----------------------------------------------------------------------------

with tab_seasonal:
    st.subheader("Seasonal median patterns")

    seasonal_df = seasonal_stats.copy()

    if seasonal_df.empty:
        st.warning("No seasonal median data available.")
    else:
        # Align month order
        if seasonal_df["Month_Name"].dtype == object:
            seasonal_df["Month_Name"] = pd.Categorical(
                seasonal_df["Month_Name"],
                categories=month_order,
                ordered=True,
            )
            seasonal_df = seasonal_df.sort_values("Month_Name")

        # Filter by selected months to keep behaviour consistent
        seasonal_df = seasonal_df[seasonal_df["Month_Name"].isin(selected_months)]

        if seasonal_df.empty:
            st.info(
                "No seasonal data for the selected months. Try including more months."
            )
        else:
            chart_type = st.radio(
                "Chart view",
                ["Bar (median per month)", "Line (median per month)"],
                horizontal=True,
            )

            if chart_type.startswith("Bar"):
                fig_season = px.bar(
                    seasonal_df,
                    x="Month_Name",
                    y="Median",
                    labels={
                        "Month_Name": "Month",
                        "Median": "Median measurement value",
                    },
                )
            else:
                fig_season = px.line(
                    seasonal_df,
                    x="Month_Name",
                    y="Median",
                    markers=True,
                    labels={
                        "Month_Name": "Month",
                        "Median": "Median measurement value",
                    },
                )

            fig_season.update_layout(
                margin=dict(l=40, r=20, t=40, b=40),
            )
            st.plotly_chart(fig_season, use_container_width=True)

            st.markdown("#### Seasonal median values (table)")
            st.dataframe(seasonal_df, use_container_width=True)

            seas_csv = seasonal_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download seasonal medians (CSV)",
                data=seas_csv,
                file_name="seasonal_median_by_month_filtered.csv",
                mime="text/csv",
            )
