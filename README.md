
Toronto Water-Quality Analytics

Long-term trends, seasonal patterns, and parameter-specific insights (1964–2024)
Live dashboard: https://toronto-water-analytics-3rtrpjffc6gfsfwax4rxf2.streamlit.app/

Executive Summary

This project presents a real-world applied analytics case study examining long-term water-quality trends across Toronto’s AOC1 (Area of Concern) using open data from the Great Lakes DataStream platform.
The purpose is to demonstrate a full analytics workflow—from raw data ingestion and cleaning to SQL analytics and interactive dashboarding—while generating insights relevant to environmental managers, policy teams, and technical audiences.

The analysis reveals key temporal and seasonal behavior across parameters such as chloride, dissolved oxygen, Kjeldahl nitrogen, specific conductance, and water temperature, helping illustrate how water quality has evolved over six decades.

This project is built for portfolio demonstration and highlights capabilities in data engineering, exploratory analysis, time-series analytics, SQL, and interactive visualization.

Data Source

Platform: Great Lakes DataStream

Region: Toronto AOC1 monitoring locations

Years covered: ~1964–2024

Observations: Thousands of sample records across parameters, locations, and dates

Variables include:

Activity date & time

Monitoring location

Parameter name

Result values (mean, min, max, medians)

Units

Metadata fields (method, detection limits, etc.)

Project Objectives

Identify long-term water-quality trends across six decades of monitoring.

Analyze seasonal patterns (monthly/annual variation).

Compare parameter-specific behaviors, such as chloride, DO, nitrogen, and conductance.

Demonstrate SQL-based analytical queries for environmental datasets.

Build an interactive Streamlit dashboard to communicate findings clearly.

Pipeline & Methods

This repository follows a clear analytics workflow:

1. Data Ingestion & Cleaning

Notebooks:

01_data_cleaning.ipynb – standardization, missing values, formatting

02_exploration.ipynb – initial EDA, distributions, summary statistics

Cleaning steps included:

Parsing dates

Normalizing parameter names

Removing invalid or duplicate records

Creating month/year fields

Aggregating per-parameter time series

2. Analysis & Feature Engineering

Notebooks:

03_analysis.ipynb – long-term trend analysis

04_export_for_tableau.ipynb – output of curated CSV tables

Created curated tables:

monthly_overall_stats.csv

monthly_top_characteristics_stats.csv

location_summary_stats.csv

seasonal_median_by_month.csv

These were used by the dashboard and for SQL analysis.

3. SQL Analytics

Folder: sql/

quality_trends.sql

Contains foundational time-series aggregations:

Mean by year

Mean by month

Parameter-level grouping

Sorting by long-term trends

water_usage_queries.sql (Advanced SQL)

Includes more complex queries such as:

5-year rolling averages

Anomaly detection (values beyond statistical thresholds)

Seasonal comparisons using window functions

Identifying years with highest/lowest concentrations

Parameter-specific exceedance checks

4. Interactive Dashboard (Streamlit)

Live: https://toronto-water-analytics-3rtrpjffc6gfsfwax4rxf2.streamlit.app/

App file: app.py

The dashboard includes four analytical tabs:

Overview

KPI indicators: date range, number of months, number of parameters, monitoring sites

Clean high-level narrative for non-technical users

Parameter Trends

Time-series comparison across selected parameters.
Parameters available:

Chloride

Dissolved oxygen (DO)

Kjeldahl nitrogen

Specific conductance

Temperature (water)

Location Insights

Top monitoring locations by mean values

Useful for identifying consistently elevated sites

Seasonality

Median monthly patterns

Illustrates expected environmental cycles

Key Insights
1. Seasonal Patterns

Specific conductance and chloride exhibit winter peaks (likely road salt influence).

Water temperature follows expected seasonal cycles.

Dissolved oxygen (DO) shows inverse behavior with temperature (higher in cold months).

2. Long-Term Trends

(As observed visually and from SQL summaries)

Specific conductance shows periods of elevated values in later decades.

Some parameters display stabilization or decline over time, indicating potential improvements or regulatory changes.

3. Parameter-Specific Behavior

Chloride: noticeable variability and winter spikes.

Dissolved oxygen: relatively stable with seasonal oscillation.

Kjeldahl nitrogen: fluctuates with broader seasonal and annual variation.

Specific conductance: strong seasonal and long-term patterns.

These insights have real relevance for environmental monitoring and water policy teams.

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
│
├── sql/
│   ├── quality_trends.sql
│   ├── water_usage_queries.sql
│
├── app.py
├── requirements.txt
└── README.md

How to Run Locally
1. Clone the repository
git clone https://github.com/simasaadi/toronto-water-analytics.git
cd toronto-water-analytics

2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Run the Streamlit app
streamlit run app.py

5. Run SQL scripts

Any SQLite/MySQL/PostgreSQL client will work.
Example using SQLite:

sqlite3 water_quality.db < sql/quality_trends.sql

Future Enhancements

Incorporate geospatial mapping (hotspots, clusters).

Automated ETL pipeline to refresh data monthly.

Parameter exceedance comparison against regulatory water-quality thresholds.

Expand dashboard with time-series forecasting capabilities.

Author

Sima Saadi
Toronto-based environmental researcher & data analyst.
