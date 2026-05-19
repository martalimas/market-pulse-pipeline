# src/market_pulse/03_silver/validation.py
# Single Responsibility: data quality validation only.
# No transformations, no I/O.

import logging
from pyspark.sql import DataFrame
from pyspark.sql.functions import col

from market_pulse.logger import get_logger

_default_logger = get_logger(__name__)


def validate_dim_stock(df_dim: DataFrame, logger=None) -> DataFrame:
    """
    Applies data quality rules to dim_stock.
    Drops rows where symbol, last_refreshed or time_zone are NULL.
    Logs count of dropped rows.
    """
    log = logger or _default_logger
    total_before = df_dim.count()
    df_valid = df_dim.filter(
        col("symbol").isNotNull() &
        col("last_refreshed").isNotNull() &
        col("time_zone").isNotNull()
    )
    dropped = total_before - df_valid.count()
    log.info("dim_stock_validated", total=total_before, dropped=dropped)
    return df_valid


def validate_fact_prices(df_fact: DataFrame, logger=None) -> DataFrame:
    """
    Applies data quality rules to fact_prices.
    Drops rows where prices are <= 0 or volume < 0.
    Logs count of dropped rows.
    """
    log = logger or _default_logger
    total_before = df_fact.count()
    df_valid = df_fact.filter(
        (col("open")   > 0) &
        (col("high")   > 0) &
        (col("low")    > 0) &
        (col("close")  > 0) &
        (col("volume") >= 0)
    )
    dropped = total_before - df_valid.count()
    log.info("fact_prices_validated", total=total_before, dropped=dropped)
    return df_valid