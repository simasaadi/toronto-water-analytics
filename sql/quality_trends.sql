-- =====================================================================
-- quality_trends.sql
-- Analytical SQL queries for the Toronto Water Analytics project
-- Database: toronto_water.db (SQLite)
--
-- Tables (created in 00_load_to_sql.ipynb from CSV files in /data):
--   monthly_overall_stats
--   monthly_top_characteristics_stats
--   location_summary_stats
--   seasonal_median_by_month
--
-- Column examples:
--   monthly_overall_stats:
--       activity_datetime, count, mean, median, min, max, year, month, month_name
--   monthly_top_characteristics_stats:
--       year, month, month_name, characteristicname, mean, ...
--   location_summary_stats:
--       monitoringlocationname, count, mean, ...
--   seasonal_median_by_month:
--       month_name, median
-- =====================================================================


-- 1. Annual average across all months
--    (matches the "Annual average" line plot in the Streamlit Overview tab)
SELECT
    year,
    AVG(mean) AS annual_average_mean
FROM monthly_overall_stats
GROUP BY year
ORDER BY year;


-- 2. Month–year matrix of mean values
--    (basis for the heatmap in the Overview tab)
SELECT
    year,
    month_name,
    mean AS mean_resultvalue
FROM monthly_overall_stats
ORDER BY year, month;


-- 3. Parameter-level summary over the full period
--    (matches the summary table in the Parameter trends tab)
SELECT
    characteristicname AS characteristic,
    COUNT(*)          AS observations,
    AVG(mean)         AS mean_of_means,
    MIN(mean)         AS min_mean,
    MAX(mean)         AS max_mean
FROM monthly_top_characteristics_stats
GROUP BY characteristicname
ORDER BY mean_of_means DESC;


-- 4. Top locations by overall mean value and sampling effort
--    (aligned with the Location insights bar chart)
SELECT
    monitoringlocationname AS location,
    AVG(mean)              AS mean_resultvalue,
    SUM(count)             AS num_samples
FROM location_summary_stats
GROUP BY monitoringlocationname
HAVING num_samples >= 10           -- filter out rarely sampled locations
ORDER BY mean_resultvalue DESC
LIMIT 50;


-- 5. Seasonal median by month with ordered month labels
--    (corresponds to seasonal_median_by_month.csv and the Seasonality tab)
SELECT
    month_name,
    median AS median_resultvalue
FROM seasonal_median_by_month
ORDER BY CASE month_name
             WHEN 'January'   THEN 1
             WHEN 'February'  THEN 2
             WHEN 'March'     THEN 3
             WHEN 'April'     THEN 4
             WHEN 'May'       THEN 5
             WHEN 'June'      THEN 6
             WHEN 'July'      THEN 7
             WHEN 'August'    THEN 8
             WHEN 'September' THEN 9
             WHEN 'October'   THEN 10
             WHEN 'November'  THEN 11
             WHEN 'December'  THEN 12
         END;

