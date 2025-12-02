Toronto Water-Quality Analytics

Long-term trends, seasonal patterns, anomaly detection, and geospatial insights (1964–2024)

## 🚀 Live Dashboard

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20App-red?logo=streamlit)](https://toronto-water-analytics-3trpjjfc6gfsfwax4rxf2.streamlit.app/)

Overview

This project is a full applied analytics case study examining long-term water-quality trends across Toronto’s AOC1 (Area of Concern) using open data from the Great Lakes DataStream platform.

It demonstrates an end-to-end analytics workflow:

Raw data ingestion

Cleaning and standardization

SQL-based aggregation

Exploratory data analysis

Advanced time-series methods

Geospatial visualization

Interactive dashboarding

Communication of insights for policy and environmental management

The goal is to produce a portfolio-grade project that reflects real analytical work relevant to:

Environmental monitoring

Water-resource management

Technical analytics roles

Public-sector decision support

The analysis covers over six decades of measurements across multiple parameters and monitoring locations.

Data Source

Platform: Great Lakes DataStream
Region: Toronto AOC1 monitoring network
Years: ∼1964–2024
Observations: Thousands of sample records
Variables:

Sampling date and time

Monitoring location (ID + lat/lon)

Parameter name

Result values (mean, median, min, max)

Units

Metadata (method, detection limits, etc.)

Project Objectives

Analyze long-term water-quality trends across multiple parameters.

Characterize seasonal dynamics and environmental cycles.

Compare parameter-specific behaviour (chloride, DO, nitrogen, conductance, temperature).

Apply SQL queries to environmental datasets.

Build geospatial and temporal visualizations.

Communicate insights via a Streamlit dashboard.

Produce a deep-dive analytical notebook suitable for technical review.

Analytics Pipeline
1. Data Ingestion & Cleaning

Notebooks:

01_data_cleaning.ipynb

02_exploration.ipynb

Key steps:

Parsing and standardizing dates

Merging date + time into activity_datetime

Enforcing numeric types for result values

Normalizing parameter names

Removing invalid/duplicate entries

Deriving year, month, month_name

Structuring data for time-series analysis

Curated tables produced include:

monthly_overall_stats.csv

monthly_top_characteristics_stats.csv

location_summary_stats.csv

seasonal_median_by_month.csv

2. SQL Analytics

Folder: sql/

quality_trends.sql

Foundational time-series queries:

Mean by year

Mean by month

Parameter-level summaries

Sorting for upward/downward long-term trends

water_usage_queries.sql (Advanced)

5-year rolling averages

Seasonal comparisons (window functions)

Outlier detection (z-score thresholding)

Ranking years with highest/lowest concentrations

Exceedance identification for selected parameters

3. Interactive Dashboard (Streamlit)

Live App:
https://toronto-water-analytics-3rtrpjffc6gfsfwax4rxf2.streamlit.app/

File: app.py

Dashboard features:

Overview

KPI metrics

Summary statistics

High-level narrative

Parameter Trends

Multi-parameter time-series visualization

Location Insights

Ranking monitoring sites by mean value

Seasonality

Median monthly cycles by parameter

4. In-Depth Analysis Notebook (NEW)

Notebook: 05_in_depth_water_quality_analysis.ipynb

This notebook extends the project beyond the dashboard, adding advanced statistical, temporal, and spatial analytics.

Included Analyses
A. Correlation Analysis

Daily mean pivot

Parameter correlation heatmap

B. Seasonal Boxplots

Month-by-month distribution

Variability, medians, outliers

C. Anomaly Detection

Monthly aggregation

Rolling 12-month z-scores

Automatic anomaly flagging (|z| ≥ 3)

D. Seasonal Decomposition

statsmodels additive decomposition

Trend / seasonality / residual separation

E. Linear Trend Modeling

OLS regression on yearly means

Slope (per year & per decade)

R² and model interpretation

F. Spatial Analytics (Folium Maps)

Station map (marker size = sample count)

Color-scaled station map (mean concentration)

Heatmap of intensity / high-value clusters

These provide spatial patterns that complement the time-series analysis.

Key Insights
1. Seasonal Patterns

Specific conductance & chloride peak in winter

Water temperature peaks in summer

DO inversely tracks temperature

Nitrogen parameters show broader seasonal variability

2. Long-Term Trends

Some parameters show gradual increases

Others stabilize or decline, possibly reflecting urban or regulatory changes

3. Parameter Behavior

Chloride: high variability + winter spikes

DO: stable but strongly seasonal

Conductance: clear seasonality and long-term dynamics

4. Spatial Insights

Certain monitoring sites consistently show higher means

Spatial gradients visible in color-scale maps

Heatmaps highlight clusters of elevated measurements

Repository Structure
toronto-water-analytics/
│
├── data/
│   ├── raw/
│   ├── cleaned/
│
├── notebooks/
│   ├── 00_load_to_sql.ipynb
│   ├── 01_data_cleaning.ipynb
│   ├── 02_exploration.ipynb
│   ├── 03_analysis.ipynb
│   ├── 04_export_for_tableau.ipynb
│   ├── 05_in_depth_water_quality_analysis.ipynb   ← NEW
│
├── sql/
│   ├── quality_trends.sql
│   ├── water_usage_queries.sql
│
├── app.py
├── requirements.txt
└── README.md

How to Run Locally
git clone https://github.com/simasaadi/toronto-water-analytics.git
cd toronto-water-analytics

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py


SQL:

sqlite3 water_quality.db < sql/quality_trends.sql

Future Enhancements

Add multi-parameter spatial clustering

Automated monthly data-refresh pipeline

Comparison against regulatory threshold values

Forecasting (Prophet / ARIMA)

Integration with geospatial boundaries (subwatersheds, land use areas)

Author

Sima Saadi
Toronto-based environmental researcher & data analyst
