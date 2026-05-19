import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Adiciona o path do projecto para importar as funções
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



def test_ingest_stock_success(sample_api_response):
    """
    ingest_stock() should return the raw API response
    when the API returns valid data.
    """
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = sample_api_response
        mock_get.return_value.raise_for_status = MagicMock()

        from notebooks.bronze_ingestion import ingest_stock
        result = ingest_stock("AAPL", "fake_key")

        assert result == sample_api_response
        assert "Meta Data" in result
        assert "Time Series (Daily)" in result