# src/market_pulse/02_bronze/transformations.py
# Single Responsibility: transform raw JSON micro-batch into flat Delta rows.
# No schema definition, no I/O configuration.

import logging
from pyspark.sql import DataFrame
from pyspark.sql.functions import col

from market_pulse.bronze.schema import json_schema
from market_pulse.config import BRONZE_INGESTION_PATH


def process_batch(batch_df: DataFrame, batch_id: int) -> None:
    """
    Transforms a raw JSON micro-batch into flat Delta rows.
    Called by Auto Loader via foreachBatch.

    Handles Alpha Vantage non-flat JSON:
    - Meta Data: struct with symbol, last_refreshed, time_zone
    - Time Series (Daily): MapType with dynamic date keys

    Args:
        batch_df: Raw DataFrame from Auto Loader
        batch_id: Micro-batch identifier (managed by Spark)
    """
    df_exploded = batch_df.selectExpr(
        "`Meta Data`.`2. Symbol` as symbol",
        "`Meta Data`.`3. Last Refreshed` as last_refreshed",
        "`Meta Data`.`5. Time Zone` as time_zone",
        "explode(`Time Series (Daily)`) as (trade_date, prices)"
    )

    df_flat = df_exploded.select(
        "symbol",
        "last_refreshed",
        "time_zone",
        "trade_date",
        col("prices.`1. open`").alias("open"),
        col("prices.`2. high`").alias("high"),
        col("prices.`3. low`").alias("low"),
        col("prices.`4. close`").alias("close"),
        col("prices.`5. volume`").alias("volume")
    )

    df_flat.write.format("delta").mode("append").save(BRONZE_INGESTION_PATH)
    logging.info(f"✅ Batch {batch_id} — {df_flat.count()} rows written")