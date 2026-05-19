# src/market_pulse/01_ingestion/orchestrator.py
# Single Responsibility: orchestrate API calls and storage writes.
# No HTTP logic, no storage logic.

import logging
import time

from market_pulse.config import STOCKS
from market_pulse.ingestion.api import fetch_stock
from market_pulse.ingestion.storage import save_to_bronze_databricks
from market_pulse.logger import get_logger

# Default logger (console only — no Delta persistence)
_default_logger = get_logger(__name__)


def ingest_all_stocks(
    stocks: list = STOCKS,
    api_key: str = None,
    dbutils=None,
    logger=None,
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
    log = logger or _default_logger

    paths  = []
    errors = []

    log.info("ingestion_started", total_stocks=len(stocks))


    for symbol in stocks:
        try:
            logging.info(f"🔄 Ingesting {symbol}...")
            data = fetch_stock(symbol, api_key)
            path = save_to_bronze_databricks(symbol, data, dbutils)
            paths.append(path)
            log.info("stock_saved", symbol=symbol, path=path)
            time.sleep(sleep_seconds)
        except Exception as e:
            log.error("stock_failed", symbol=symbol, error=str(e))
            errors.append(symbol)

    log.info("ingestion_complete",
             saved=len(paths),
             failed=len(errors),
             failed_symbols=errors)
    return paths, errors