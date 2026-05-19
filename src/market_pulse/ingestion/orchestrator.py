# src/market_pulse/01_ingestion/orchestrator.py
# Single Responsibility: orchestrate API calls and storage writes.
# No HTTP logic, no storage logic.

import logging
import time

from market_pulse.config import STOCKS
from market_pulse.ingestion.api import fetch_stock
from market_pulse.ingestion.storage import save_to_bronze_databricks


def ingest_all_stocks(
    stocks: list = STOCKS,
    api_key: str = None,
    dbutils=None,
    sleep_seconds: float = 1.5
) -> tuple[list, list]:
    """
    Orchestrates ingestion of multiple stocks.
    Fetches data from API and saves to Bronze layer.
    Continues processing remaining stocks if one fails.

    Args:
        stocks:        List of tickers to ingest
        api_key:       Alpha Vantage API key
        dbutils:       Databricks dbutils (passed from notebook)
        sleep_seconds: Delay between API calls (rate limit)

    Returns:
        Tuple of (successful_paths, failed_symbols)
    """
    paths  = []
    errors = []

    for symbol in stocks:
        try:
            logging.info(f"🔄 Ingesting {symbol}...")
            data = fetch_stock(symbol, api_key)
            path = save_to_bronze_databricks(symbol, data, dbutils)
            paths.append(path)
            time.sleep(sleep_seconds)
        except Exception as e:
            logging.error(f"❌ Error processing {symbol}: {e}")
            errors.append(symbol)

    logging.info(f"✅ Complete: {len(paths)} saved, {len(errors)} errors")
    return paths, errors