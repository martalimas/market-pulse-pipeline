# tests/test_bronze_ingestion.py

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from market_pulse.ingestion.api import fetch_stock, RateLimitError, InvalidSymbolError


# Adiciona src/ ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from market_pulse.ingestion.api import fetch_stock


def test_fetch_stock_success(sample_api_response):
    """fetch_stock() returns raw API response when API is healthy."""
    with patch("market_pulse.ingestion.api.requests.get") as mock_get:
        mock_get.return_value.json.return_value = sample_api_response
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_stock("AAPL", "fake_key")

        assert result == sample_api_response
        assert "Meta Data" in result
        assert "Time Series (Daily)" in result


def test_fetch_stock_rate_limit(rate_limit_response):
    """fetch_stock() raises ValueError when rate limit is reached."""
    with patch("market_pulse.ingestion.api.requests.get") as mock_get:
        mock_get.return_value.json.return_value = rate_limit_response
        mock_get.return_value.raise_for_status = MagicMock()

        with pytest.raises(RateLimitError):
            fetch_stock("AAPL", "fake_key")


def test_fetch_stock_api_error(error_response):
    """fetch_stock() raises ValueError when API returns error message."""
    with patch("market_pulse.ingestion.api.requests.get") as mock_get:
        mock_get.return_value.json.return_value = error_response
        mock_get.return_value.raise_for_status = MagicMock()

        with pytest.raises(InvalidSymbolError):
            fetch_stock("AAPL", "fake_key")