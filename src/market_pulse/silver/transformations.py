# src/market_pulse/03_silver/transformations.py
# Single Responsibility: Silver layer transformations only.
# No validation, no I/O.

import logging
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, to_date, current_timestamp

from market_pulse.config import BRONZE_INGESTION_PATH
from market_pulse.logger import get_logger

_default_logger = get_logger(__name__)


def read_bronze(spark: SparkSession, logger=None) -> DataFrame:
    """Reads the Bronze Ingestion Delta table."""
    log = logger or _default_logger
    df = spark.read.format("delta").load(BRONZE_INGESTION_PATH)
    log.info("bronze_loaded", rows=df.count())
    return df


def build_dim_stock(df_bronze: DataFrame, logger=None) -> DataFrame:
    """
    Builds Silver dimension table for stocks.
    Casts last_refreshed to DATE, deduplicates by symbol.
    """
    log = logger or _default_logger
    df = (
        df_bronze.select("symbol", "last_refreshed", "time_zone")
        .withColumn("last_refreshed", to_date(col("last_refreshed")))
        .withColumn("ingest_timestamp", current_timestamp())
        .dropDuplicates(["symbol"])
    )
    log.info("dim_stock_built", rows=df.count())
    return df


def build_fact_prices(df_bronze: DataFrame, logger=None) -> DataFrame:
    """
    Builds Silver fact table for stock prices.
    Casts all types, deduplicates by (symbol, trade_date).
    """
    log = logger or _default_logger
    df = (
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
    log.info("fact_prices_built", rows=df.count())
    return df