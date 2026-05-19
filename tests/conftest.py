# conftest.py — fixtures partilhadas por todos os testes É um dado ou objecto preparado antes do teste correr. Em vez de repetir o mesmo setup em cada teste, defines uma vez e reutilizas:

import pytest

@pytest.fixture
def sample_api_response():
    """Simula uma resposta válida da Alpha Vantage API."""
    return {
        "Meta Data": {
            "2. Symbol": "AAPL",
            "3. Last Refreshed": "2026-05-16",
            "5. Time Zone": "US/Eastern"
        },
        "Time Series (Daily)": {
            "2026-05-16": {
                "1. open": "292.56",
                "2. high": "295.27",
                "3. low": "292.56",
                "4. close": "294.80",
                "5. volume": "45748129"
            },
            "2026-05-15": {
                "1. open": "291.97",
                "2. high": "293.88",
                "3. low": "290.23",
                "4. close": "292.68",
                "5. volume": "42247285"
            }
        }
    }

@pytest.fixture
def rate_limit_response():
    """Simula resposta de rate limit da API."""
    return {"Note": "Thank you for using Alpha Vantage..."}

@pytest.fixture
def error_response():
    """Simula resposta de erro da API."""
    return {"Error Message": "Invalid API call."}