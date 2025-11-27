-- =====================================================================
-- water_usage_queries.sql
-- Advanced analytical SQL for the Toronto Water Analytics project
-- Database: toronto_water.db (SQLite)
--
-- Tables used:
--   monthly_overall_stats            -- global monthly stats
--   monthly_top_characteristics_stats-- monthly stats by parameter
--   location_summary_stats           -- long-term stats by location
--   seasonal_median_by_month         -- multi-year seasonal medians
--
-- NOTE: Each query below is independent. Run them one by one.
-- =====================================================================


/**********************************************************************
  1. Global 5-year rolling average of monthly mean values
     - Uses monthly_overall_stats
     - Provides a smoother long-term signal for trend analysis
**********************************************************************/
WITH yearly AS (
    SELECT
        year,
        AVG(mean) AS annual_mean
    FROM monthly_overall_stats
    GROUP BY year
),
rolling_5yr AS (
    SELECT
        year,
        annual_mean,
        AVG(annual_mean) OVER (
            ORDER BY year
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) AS rolling_5yr_avg
    FROM yearly
)
SELECT
    year,
    annual_mean,
    rolling_5yr_avg
FROM rolling_5yr
ORDER BY year;


/**********************************************************************
  2. Parameter trend ranking: early period vs. recent period
     - Uses monthly_top_characteristics_stats
     - Compares average mean values before 2000 vs. from 2010 onward
     - Ranks parameters by absolute and percentage change
**********************************************************************/
WITH param_periods AS (
    SELECT
        characteristicname AS characteristic,
        CASE
            WHEN year <= 2000 THEN 'early'
            WHEN year >= 2010 THEN 'recent'
            ELSE 'middle'
        END AS period_group,
        mean
    FROM monthly_top_characteristics_stats
),
summaries AS (
    SELECT
        characteristic,
        period_group,
        AVG(mean) AS avg_mean
    FROM param_periods
    WHERE period_group IN ('early', 'recent')
    GROUP BY characteristic, period_group
),
pivoted AS (
    SELECT
        characteristic,
        MAX(CASE WHEN period_group = 'early'  THEN avg_mean END) AS early_avg,
        MAX(CASE WHEN period_group = 'recent' THEN avg_mean END) AS recent_avg
    FROM summaries
    GROUP BY characteristic
),
with_change AS (
    SELECT
        characteristic,
        early_avg,
        recent_avg,
        (recent_avg - early_avg) AS abs_change,
        CASE
            WHEN early_avg IS NULL OR early_avg = 0 THEN NULL
            ELSE 100.0 * (recent_avg - early_avg) / early_avg
        END AS pct_change
    FROM pivoted
)
SELECT
    characteristic,
    early_avg,
    recent_avg,
    abs_change,
    pct_change
FROM with_change
WHERE early_avg IS NOT NULL
  AND recent_avg IS NOT NULL
ORDER BY abs_change DESC
LIMIT 20;  -- top 20 parameters with largest increase


/**********************************************************************
  3. Monthly seasonality by parameter
     - Uses monthly_top_characteristics_stats
     - For each parameter & month, computes long-term mean
     - Highlights months where each parameter tends to peak
**********************************************************************/
WITH month_stats AS (
    SELECT
        characteristicname AS characteristic,
        month_name,
        AVG(mean) AS mean_value
    FROM monthly_top_characteristics_stats
    GROUP BY characteristic, month_name
),
ranked AS (
    SELECT
        characteristic,
        month_name,
        mean_value,
        RANK() OVER (
            PARTITION BY characteristic
            ORDER BY mean_value DESC
        ) AS month_rank
    FROM month_stats
)
SELECT
    characteristic,
    month_name,
    mean_value,
    month_rank
FROM ranked
WHERE month_rank <= 3            -- top 3 months for each parameter
ORDER BY characteristic, month_rank;


/**********************************************************************
  4. Exceedance analysis by parameter and year
     - Uses monthly_top_characteristics_stats
     - Counts how many months per year exceed a chosen threshold
     - Threshold can be adjusted depending on the unit/parameter
**********************************************************************/

-- Set a generic threshold; adjust as needed for your context
-- e.g., 100 could represent a regulatory guideline for a pollutant
WITH base AS (
    SELECT
        year,
        characteristicname AS characteristic,
        month_name,
        mean
    FROM monthly_top_characteristics_stats
),
flags AS (
    SELECT
        year,
        characteristic,
        month_name,
        mean,
        CASE WHEN mean > 100 THEN 1 ELSE 0 END AS exceed_flag
    FROM base
),
by_year AS (
    SELECT
        characteristic,
        year,
        SUM(exceed_flag) AS months_exceeding,
        COUNT(*)         AS months_observed
    FROM flags
    GROUP BY characteristic, year
)
SELECT
    characteristic,
    year,
    months_exceeding,
    months_observed,
    CASE
        WHEN months_observed = 0 THEN NULL
        ELSE 100.0 * months_exceeding / months_observed
    END AS pct_months_exceeding
FROM by_year
WHERE months_observed >= 6           -- require at least half the months
ORDER BY characteristic, year;


/**********************************************************************
  5. Location-level variability and ranking
     - Uses location_summary_stats
     - Estimates variability using ratio max(mean)/min(mean)
       if those columns are available; otherwise uses count & mean
**********************************************************************/

-- Basic ranking of locations by mean and sampling effort
SELECT
    monitoringlocationname AS location,
    mean                   AS mean_value,
    count                  AS num_samples
FROM location_summary_stats
ORDER BY mean_value DESC
LIMIT 50;


-- If your location_summary_stats table has min and max columns
-- (min_resultvalue, max_resultvalue), you can uncomment and adapt:

/*
SELECT
    monitoringlocationname AS location,
    mean                   AS mean_value,
    min                    AS min_value,
    max                    AS max_value,
    CASE
        WHEN min IS NULL OR min = 0 THEN NULL
        ELSE max / min
    END AS variability_ratio
FROM location_summary_stats
ORDER BY variability_ratio DESC
LIMIT 50;
*/


/**********************************************************************
  6. Global anomaly detection: months far from long-term mean
     - Uses monthly_overall_stats
     - Flags months where mean is more than 2 standard deviations
       away from the long-term monthly mean
**********************************************************************/
WITH base AS (
    SELECT
        year,
        month,
        month_name,
        mean
    FROM monthly_overall_stats
),
stats AS (
    SELECT
        AVG(mean) AS global_mean,
        -- standard deviation approximation using VAR_POP
        -- SQLite doesn't have VAR_POP by default, so we compute manually:
        AVG(mean * mean) - AVG(mean) * AVG(mean) AS var_pop
    FROM base
),
joined AS (
    SELECT
        b.year,
        b.month,
        b.month_name,
        b.mean,
        s.global_mean,
        sqrt(s.var_pop) AS std_dev
    FROM base b
    CROSS JOIN stats s
),
flagged AS (
    SELECT
        year,
        month,
        month_name,
        mean,
        global_mean,
        std_dev,
        CASE
            WHEN std_dev IS NULL OR std_dev = 0 THEN 0
            WHEN ABS(mean - global_mean) >= 2 * std_dev THEN 1
            ELSE 0
        END AS is_anomaly
    FROM joined
)
SELECT
    year,
    month_name,
    mean,
    global_mean,
    std_dev,
    is_anomaly
FROM flagged
WHERE is_anomaly = 1
ORDER BY year, month;

