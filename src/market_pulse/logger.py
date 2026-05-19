# src/market_pulse/logger.py
# Single Responsibility: structured logging configuration.
# All modules import from here — single source of truth for logging.

import logging
import json
from datetime import datetime, timezone
from typing import Optional


class StructuredLogger:
    """
    Structured JSON logger for market-pulse-pipeline.
    Outputs machine-readable logs compatible with Azure Monitor.
    Optionally persists logs to a Delta audit table.
    """

    def __init__(self, name: str, spark=None, log_table_path: str = None):
        self.logger          = logging.getLogger(name)
        self.name            = name
        self.spark           = spark
        self.log_table_path  = log_table_path

    def _log(self, level: str, event: str, **kwargs):
        """Builds and logs a structured JSON message."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level":     level,
            "module":    self.name,
            "event":     event,
            **kwargs
        }
        message = json.dumps(payload)

        if level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "DEBUG":
            self.logger.debug(message)

        # Persiste na tabela Delta se configurado
        if self.spark and self.log_table_path:
            self._write_to_delta(payload)

    def _write_to_delta(self, payload: dict):
        """Writes a log entry to the Delta audit table."""
        try:
            from pyspark.sql import Row
            row = Row(**{k: str(v) for k, v in payload.items()})
            df  = self.spark.createDataFrame([row])
            df.write.format("delta").mode("append").option("mergeSchema", "true").save(self.log_table_path)
        except Exception as e:
            # Logging failures should never break the pipeline
            self.logger.error(f"Failed to write log to Delta: {e}")

    def info(self, event: str, **kwargs):
        self._log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs):
        self._log("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs):
        self._log("ERROR", event, **kwargs)

    def debug(self, event: str, **kwargs):
        self._log("DEBUG", event, **kwargs)


def get_logger(name: str, spark=None, log_table_path: str = None) -> StructuredLogger:
    """
    Factory function — returns a StructuredLogger for the given module.

    Args:
        name:           Module name (use __name__)
        spark:          SparkSession (optional — needed for Delta persistence)
        log_table_path: ADLS path for audit Delta table (optional)

    Usage:
        # Logs only to console:
        logger = get_logger(__name__)

        # Logs to console + Delta table:
        logger = get_logger(__name__, spark=spark, log_table_path=LOG_TABLE_PATH)
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )
    return StructuredLogger(name, spark=spark, log_table_path=log_table_path)