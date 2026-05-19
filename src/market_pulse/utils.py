# src/market_pulse/utils.py
# Single Responsibility: generic utility functions shared across all layers.
# No business logic, no layer-specific code.

import logging
from pyspark.sql import DataFrame


def write_delta_table(
    df: DataFrame,
    path: str,
    table_name: str,
    mode: str = "overwrite",
    partition_by: list = None
) -> None:
    """
    Generic Delta writer — reusable across Bronze, Silver and Gold layers.
    The caller decides the write mode (overwrite, append).

    Args:
        df:           DataFrame to write
        path:         ADLS destination path
        table_name:   Logical name for logging
        mode:         Write mode (overwrite, append) — caller's responsibility
        partition_by: Optional partition columns
    """
    writer = df.write.format("delta").mode(mode)
    if partition_by:
        writer = writer.partitionBy(partition_by)
    writer.save(path)
    logging.info(f"✅ {table_name} written to {path}")