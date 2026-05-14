# Gold Layer — Declarative Approach (DLT / Lakeflow)

import dlt
from pyspark.sql import functions as F

# Source — Silver Declarative tables (Unity Catalog)
SILVER_CATALOG = "market_pulse_databricks"
SILVER_SCHEMA = "silver"


# ============================================
# 1. gold_daily_summary
# ============================================

@dlt.table(
    name="daily_summary",
    comment="Daily metrics per stock: return %, intraday range and range %",
)
def daily_summary():
    return (
        spark.read.table(f"{SILVER_CATALOG}.{SILVER_SCHEMA}.fact_prices")
            .withColumn(
                "daily_return_pct",
                F.round(((F.col("close") - F.col("open")) / F.col("open")) * 100, 2)
            )
            .withColumn(
                "intraday_range",
                F.round(F.col("high") - F.col("low"), 2)
            )
            .withColumn(
                "intraday_range_pct",
                F.round(((F.col("high") - F.col("low")) / F.col("open")) * 100, 2)
            )
            .withColumn("ingest_timestamp", F.current_timestamp())
    )


# ============================================
# 2. gold_volume_analysis
# ============================================

@dlt.table(
    name="volume_analysis",
    comment="Volume metrics with 30-day rolling average and high-volume detection",
)
def volume_analysis():
    query = f"""
        WITH volume_data AS (
            SELECT
                symbol,
                trade_date,
                volume,
                AVG(volume) OVER (
                    PARTITION BY symbol
                    ORDER BY trade_date
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) AS avg_volume_30d
            FROM {SILVER_CATALOG}.{SILVER_SCHEMA}.fact_prices
        )
        SELECT
            symbol,
            trade_date,
            volume,
            ROUND(avg_volume_30d / 1000000, 2) AS avg_volume_30d_millions,
            ROUND((volume / avg_volume_30d) * 100, 2) AS volume_vs_avg_pct,
            CASE
                WHEN (volume / avg_volume_30d) * 100 > 150 THEN TRUE
                ELSE FALSE
            END AS high_volume_day,
            CURRENT_TIMESTAMP() AS ingest_timestamp
        FROM volume_data
    """
    return spark.sql(query)


# ============================================
# 3. gold_moving_averages
# ============================================

@dlt.table(
    name="moving_averages",
    comment="Simple Moving Averages (7d, 30d) with bullish/bearish signal",
)
def moving_averages():
    query = f"""
        WITH sma_data AS (
            SELECT
                symbol,
                trade_date,
                close,
                ROUND(AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY trade_date
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ), 2) AS sma_7d,
                ROUND(AVG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY trade_date
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ), 2) AS sma_30d
            FROM {SILVER_CATALOG}.{SILVER_SCHEMA}.fact_prices
        )
        SELECT
            symbol,
            trade_date,
            close,
            sma_7d,
            sma_30d,
            CASE
                WHEN sma_7d > sma_30d THEN 'bullish'
                ELSE 'bearish'
            END AS sma_signal,
            CURRENT_TIMESTAMP() AS ingest_timestamp
        FROM sma_data
    """
    return spark.sql(query)


# ============================================
# 4. gold_volatility
# ============================================

@dlt.table(
    name="volatility",
    comment="Rolling volatility (STDDEV of daily returns) over 7d and 30d windows",
)
def volatility():
    query = f"""
        WITH with_prev AS (
            SELECT
                symbol,
                trade_date,
                close,
                LAG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY trade_date
                ) AS prev_close
            FROM {SILVER_CATALOG}.{SILVER_SCHEMA}.fact_prices
        ),
        daily_returns AS (
            SELECT
                symbol,
                trade_date,
                close,
                ROUND(((close - prev_close) / prev_close) * 100, 2) AS daily_return_pct
            FROM with_prev
            WHERE prev_close IS NOT NULL
        )
        SELECT
            symbol,
            trade_date,
            close,
            daily_return_pct,
            ROUND(STDDEV(daily_return_pct) OVER (
                PARTITION BY symbol
                ORDER BY trade_date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ), 2) AS volatility_7d,
            ROUND(STDDEV(daily_return_pct) OVER (
                PARTITION BY symbol
                ORDER BY trade_date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ), 2) AS volatility_30d,
            CURRENT_TIMESTAMP() AS ingest_timestamp
        FROM daily_returns
    """
    return spark.sql(query)


# ============================================
# 5. gold_stock_comparison
# ============================================

@dlt.table(
    name="stock_comparison",
    comment="Cumulative return since start with daily rank across stocks",
)
def stock_comparison():
    query = f"""
        WITH with_start AS (
            SELECT
                symbol,
                trade_date,
                close,
                FIRST_VALUE(close) OVER (
                    PARTITION BY symbol
                    ORDER BY trade_date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS start_price
            FROM {SILVER_CATALOG}.{SILVER_SCHEMA}.fact_prices
        )
        SELECT
            symbol,
            trade_date,
            close,
            start_price,
            ROUND(((close - start_price) / start_price) * 100, 2) AS return_since_start_pct,
            DENSE_RANK() OVER (
                PARTITION BY trade_date
                ORDER BY ((close - start_price) / start_price) DESC
            ) AS rank_by_return,
            CURRENT_TIMESTAMP() AS ingest_timestamp
        FROM with_start
    """
    return spark.sql(query)