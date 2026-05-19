# tests/test_silver.py

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from market_pulse.silver.transformations import build_dim_stock, build_fact_prices
from market_pulse.silver.validation import validate_dim_stock, validate_fact_prices


def test_build_dim_stock(spark, sample_api_response):
    """
    build_dim_stock() should return one row per symbol
    with last_refreshed cast to DateType.
    """
    # ARRANGE — cria DataFrame bronze simples
    df_bronze = spark.createDataFrame([
        ("AAPL", "2026-05-16", "US/Eastern", "2026-05-16", "292.56", "295.27", "292.56", "294.80", "45748129"),
        ("AAPL", "2026-05-15", "US/Eastern", "2026-05-15", "291.97", "293.88", "290.23", "292.68", "42247285"),
        ("MSFT", "2026-05-16", "US/Eastern", "2026-05-16", "415.00", "420.00", "414.00", "418.00", "30000000"),
    ], ["symbol", "last_refreshed", "time_zone", "trade_date", "open", "high", "low", "close", "volume"])

    # ACT
    df_dim = build_dim_stock(df_bronze)

    # ASSERT
    assert df_dim.count() == 2                          # 2 stocks únicos
    assert "last_refreshed" in df_dim.columns           # coluna existe
    assert str(df_dim.schema["last_refreshed"].dataType) == "DateType()"  # é DateType


def test_validate_dim_stock_drops_nulls(spark):
    """
    validate_dim_stock() should drop rows with NULL symbol.
    """
    from pyspark.sql.types import StructType, StructField, StringType, DateType
    import datetime

    df = spark.createDataFrame([
        ("AAPL", datetime.date(2026, 5, 16), "US/Eastern"),
        (None,   datetime.date(2026, 5, 16), "US/Eastern"),   # ← deve ser dropado
    ], ["symbol", "last_refreshed", "time_zone"])

    df_valid = validate_dim_stock(df)

    assert df_valid.count() == 1
    assert df_valid.collect()[0]["symbol"] == "AAPL"


def test_build_fact_prices_types(spark):
    """
    build_fact_prices() should cast numeric columns to correct types.
    """
    df_bronze = spark.createDataFrame([
        ("AAPL", "2026-05-16", "US/Eastern", "2026-05-16", "292.56", "295.27", "292.56", "294.80", "45748129"),
    ], ["symbol", "last_refreshed", "time_zone", "trade_date", "open", "high", "low", "close", "volume"])

    df_fact = build_fact_prices(df_bronze)

    assert str(df_fact.schema["trade_date"].dataType) == "DateType()"
    assert str(df_fact.schema["open"].dataType)       == "DoubleType()"
    assert str(df_fact.schema["volume"].dataType)     == "LongType()"


def test_validate_fact_prices_drops_invalid(spark):
    """
    validate_fact_prices() should drop rows with price <= 0.
    """
    import datetime
    df = spark.createDataFrame([
        ("AAPL", datetime.date(2026, 5, 16), 292.56, 295.27, 292.56, 294.80, 45748129),
        ("AAPL", datetime.date(2026, 5, 15), -1.0,   295.27, 292.56, 294.80, 45748129),  # ← inválido
    ], ["symbol", "trade_date", "open", "high", "low", "close", "volume"])

    df_valid = validate_fact_prices(df)

    assert df_valid.count() == 1