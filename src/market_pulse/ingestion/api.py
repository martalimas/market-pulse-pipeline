# src/market_pulse/01_ingestion/api.py
# Single Responsibility: HTTP call only

from market_pulse.logger import get_logger
import requests
from market_pulse.config import ALPHA_VANTAGE_URL, ALPHA_VANTAGE_OUTPUT_SIZE
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = get_logger(__name__)

class RateLimitError(Exception):
    """Raised when Alpha Vantage rate limit is reached."""
    pass

class InvalidSymbolError(Exception):
    """Raised when the stock symbol is invalid — not retryable."""
    pass


@retry(
    retry=retry_if_exception_type(RateLimitError),   # só retry em rate limit
    stop=stop_after_attempt(3),                       # máximo 3 tentativas
    wait=wait_exponential(multiplier=1, min=1, max=8), # backoff: 1s, 2s, 4s
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING)
)


def fetch_stock(symbol: str, api_key: str) -> dict:
    """
    Calls Alpha Vantage API. No storage, no orchestration.
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": ALPHA_VANTAGE_OUTPUT_SIZE,
        "apikey": api_key
    }
    response = requests.get(ALPHA_VANTAGE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if "Error Message" in data:
        logger.error("api_error", symbol=symbol, message=data["Error Message"])
        raise ValueError(f"API error for {symbol}: {data['Error Message']}")

    if "Note" in data:
        logger.warning("rate_limit_reached", symbol=symbol)
        raise ValueError(f"Rate limit reached: {data['Note']}")

    days = len(data.get("Time Series (Daily)", {}))
    logger.info("stock_fetched", symbol=symbol, days=days)
    return data