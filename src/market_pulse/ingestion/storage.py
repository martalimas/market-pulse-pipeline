# src/market_pulse/01_ingestion/storage.py
# Single Responsibility: write to ADLS only.
# No API calls, no orchestration.

import json
import logging
from datetime import datetime, timezone

from market_pulse.config import STORAGE_ACCOUNT, CONTAINER


def build_bronze_path(symbol: str) -> tuple[str, str]:
    """
    Builds the ADLS path for a Bronze Landing file.
    Returns (directory, filename) tuple.
    Same partition structure: /stocks/ingest_date=YYYY-MM-DD/SYMBOL_TIMESTAMP.json
    """
    now         = datetime.now(timezone.utc)
    ingest_date = now.strftime("%Y-%m-%d")
    ingest_ts   = now.strftime("%Y%m%d_%H%M%S")
    directory   = f"stocks/ingest_date={ingest_date}"
    filename    = f"{symbol}_{ingest_ts}.json"
    return directory, filename


def save_to_bronze_databricks(symbol: str, data: dict, dbutils) -> str:
    """
    Writes JSON to ADLS using dbutils.fs.put (Databricks only).
    """
    directory, filename = build_bronze_path(symbol)
    path = f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/{directory}/{filename}"
    dbutils.fs.put(path, json.dumps(data, indent=2), overwrite=True)
    logging.info(f"✅ {symbol} saved to {path}")
    return path


def save_to_bronze_azure(symbol: str, data: dict, service_client) -> str:
    """
    Writes JSON to ADLS using DataLakeServiceClient (Azure Function).
    """
    from market_pulse.config import CONTAINER
    directory, filename = build_bronze_path(symbol)
    fs_client   = service_client.get_file_system_client(CONTAINER)
    dir_client  = fs_client.get_directory_client(directory)
    file_client = dir_client.create_file(filename)
    content     = json.dumps(data, indent=2)
    file_client.upload_data(content, overwrite=True)
    path = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/{directory}/{filename}"
    logging.info(f"✅ {symbol} saved to {path}")
    return path