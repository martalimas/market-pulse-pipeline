# tests/test_gold.py

import pytest
import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from market_pulse.gold.metrics import build_daily_summary


def test_build_daily_summary_columns(spark):
    """
    build_daily_summary() should add daily_return_pct,
    intraday_range and intraday_range_pct columns.
    """
    df_fact = spark.createDataFrame([
        ("AAPL", datetime.date(2026, 5, 16), 290.0, 295.0, 289.0, 294.0, 45000000),
    ], ["symbol", "trade_date", "open", "high", "low", "close", "volume"])

    df_result = build_daily_summary(df_fact)

    assert "daily_return_pct"    in df_result.columns
    assert "intraday_range"      in df_result.columns
    assert "intraday_range_pct"  in df_result.columns
    assert "ingest_timestamp"    in df_result.columns


def test_build_daily_summary_return_calculation(spark):
    """
    daily_return_pct = ((close - open) / open) * 100
    open=290, close=294 → return = (4/290)*100 = 1.38%
    """
    df_fact = spark.createDataFrame([
        ("AAPL", datetime.date(2026, 5, 16), 290.0, 295.0, 289.0, 294.0, 45000000),
    ], ["symbol", "trade_date", "open", "high", "low", "close", "volume"])

    df_result = build_daily_summary(df_fact)
    row = df_result.collect()[0]

    assert row["daily_return_pct"] == round(((294.0 - 290.0) / 290.0) * 100, 2)


def test_build_daily_summary_zero_open(spark):
    """
    When open = 0, daily_return_pct should be NULL (avoid division by zero).
    """
    df_fact = spark.createDataFrame([
        ("AAPL", datetime.date(2026, 5, 16), 0.0, 295.0, 289.0, 294.0, 45000000),
    ], ["symbol", "trade_date", "open", "high", "low", "close", "volume"])

    df_result = build_daily_summary(df_fact)
    row = df_result.collect()[0]

    assert row["daily_return_pct"] is None