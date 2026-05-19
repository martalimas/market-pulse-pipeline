# src/market_pulse/03_silver/transformations.py
# Single Responsibility: Silver layer transformations only.
# No validation, no I/O.

import logging
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, to_date, current_timestamp

from market_pulse.config import BRONZE_INGESTION_PATH


def read_bronze(spark: SparkSession) -> DataFrame:
    """Reads the Bronze Ingestion Delta table."""
    df = spark.read.format("delta").load(BRONZE_INGESTION_PATH)
    logging.info(f"✅ Bronze loaded — {df.count()} rows")
    return df


def build_dim_stock(df_bronze: DataFrame) -> DataFrame:
    """
    Builds Silver dimension table for stocks.
    Casts last_refreshed to DATE, deduplicates by symbol.
    """
    return (
        df_bronze.select("symbol", "last_refreshed", "time_zone")
        .withColumn("last_refreshed", to_date(col("last_refreshed")))
        .withColumn("ingest_timestamp", current_timestamp())
        .dropDuplicates(["symbol"])
    )


def build_fact_prices(df_bronze: DataFrame) -> DataFrame:
    """
    Builds Silver fact table for stock prices.
    Casts all types, deduplicates by (symbol, trade_date).
    """
    return (
        df_bronze.select("symbol", "trade_date", "open", "high", "low", "close", "volume")
        .withColumn("trade_date", to_date(col("trade_date")))
        .withColumn("open",   col("open").cast("double"))
        .withColumn("high",   col("high").cast("double"))
        .withColumn("low",    col("low").cast("double"))
        .withColumn("close",  col("close").cast("double"))
        .withColumn("volume", col("volume").cast("long"))
        .withColumn("ingest_timestamp", current_timestamp())
        .dropDuplicates(["symbol", "trade_date"])
    )