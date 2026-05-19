# src/market_pulse/04_gold/metrics.py
# Single Responsibility: Gold layer metric computations.
# No configuration, no orchestration.

import logging
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from market_pulse.utils import write_delta_table

from market_pulse.config import (
    SILVER_FACT_PRICES_PATH,
    GOLD_DAILY_SUMMARY_PATH,
    GOLD_VOLUME_ANALYSIS_PATH,
    GOLD_MOVING_AVERAGES_PATH,
    GOLD_VOLATILITY_PATH,
    GOLD_STOCK_COMPARISON_PATH
)


def read_silver_fact_prices(spark: SparkSession) -> DataFrame:
    """Reads Silver fact_prices Delta table."""
    df = spark.read.format("delta").load(SILVER_FACT_PRICES_PATH)
    logging.info(f"✅ Silver fact_prices loaded — {df.count()} rows")
    return df


def build_daily_summary(df_fact: DataFrame) -> DataFrame:
    """Daily metrics: return %, intraday range and range %."""
    return (
        df_fact
        .withColumn("daily_return_pct",
            F.when(F.col("open") != 0,
                F.round(((F.col("close") - F.col("open")) / F.col("open")) * 100, 2)))
        .withColumn("intraday_range",
            F.round(F.col("high") - F.col("low"), 2))
        .withColumn("intraday_range_pct",
            F.when(F.col("open") != 0,
                F.round(((F.col("high") - F.col("low")) / F.col("open")) * 100, 2)))
        .withColumn("ingest_timestamp", F.current_timestamp())
    )


def build_volume_analysis(spark: SparkSession) -> DataFrame:
    """Volume metrics: 30d rolling average, volume vs avg %, high volume flag."""
    query = f"""
    WITH volume_data AS (
        SELECT symbol, trade_date, volume,
            CURRENT_TIMESTAMP() AS ingest_timestamp,
            AVG(volume) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) AS avg_volume_30d
        FROM delta.`{SILVER_FACT_PRICES_PATH}`
    )
    SELECT symbol, trade_date, volume,
        ROUND(avg_volume_30d / 1000000, 2) AS avg_volume_30d_millions,
        ROUND((volume / avg_volume_30d) * 100, 2) AS volume_vs_avg_pct,
        CASE WHEN (volume / avg_volume_30d) * 100 > 150 THEN TRUE ELSE FALSE END AS high_volume_day,
        ingest_timestamp
    FROM volume_data
    """
    return spark.sql(query)


def build_moving_averages(spark: SparkSession) -> DataFrame:
    """SMA 7d and 30d with bullish/bearish signal."""
    query = f"""
    WITH sma_data AS (
        SELECT symbol, trade_date, close,
            ROUND(AVG(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS sma_7d,
            ROUND(AVG(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 2) AS sma_30d,
            CURRENT_TIMESTAMP() AS ingest_timestamp
        FROM delta.`{SILVER_FACT_PRICES_PATH}`
    )
    SELECT symbol, trade_date, close, sma_7d, sma_30d,
        CASE WHEN sma_7d > sma_30d THEN 'bullish' ELSE 'bearish' END AS sma_signal,
        ingest_timestamp
    FROM sma_data
    """
    return spark.sql(query)


def build_volatility(spark: SparkSession) -> DataFrame:
    """Rolling volatility (STDDEV of daily returns) over 7d and 30d."""
    query = f"""
    WITH with_prev AS (
        SELECT symbol, trade_date, close,
            LAG(close) OVER (PARTITION BY symbol ORDER BY trade_date) AS prev_close
        FROM delta.`{SILVER_FACT_PRICES_PATH}`
    ),
    daily_returns AS (
        SELECT symbol, trade_date, close,
            ROUND(((close - prev_close) / prev_close) * 100, 2) AS daily_return_pct
        FROM with_prev WHERE prev_close IS NOT NULL
    )
    SELECT symbol, trade_date, close, daily_return_pct,
        ROUND(STDDEV(daily_return_pct) OVER (
            PARTITION BY symbol ORDER BY trade_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS volatility_7d,
        ROUND(STDDEV(daily_return_pct) OVER (
            PARTITION BY symbol ORDER BY trade_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 2) AS volatility_30d,
        CURRENT_TIMESTAMP() AS ingest_timestamp
    FROM daily_returns
    """
    return spark.sql(query)


def build_stock_comparison(spark: SparkSession) -> DataFrame:
    """Cumulative return since start with daily rank across stocks."""
    query = f"""
    WITH with_start AS (
        SELECT symbol, trade_date, close,
            FIRST_VALUE(close) OVER (
                PARTITION BY symbol ORDER BY trade_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS start_price
        FROM delta.`{SILVER_FACT_PRICES_PATH}`
    )
    SELECT symbol, trade_date, close, start_price,
        ROUND(CASE
            WHEN start_price IS NULL OR start_price = 0 THEN NULL
            ELSE ((close - start_price) / start_price) * 100
        END, 2) AS return_since_start_pct,
        DENSE_RANK() OVER (
            PARTITION BY trade_date
            ORDER BY ((close - start_price) / start_price) DESC) AS rank_by_return,
        CURRENT_TIMESTAMP() AS ingest_timestamp
    FROM with_start
    """
    return spark.sql(query)


