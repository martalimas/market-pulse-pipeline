import azure.functions as func
import logging
import json
import requests
from datetime import datetime, timezone
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.filedatalake import DataLakeServiceClient

# Configuration
KEY_VAULT_URL     = "https://mktpulse-kv.vault.azure.net/"
STORAGE_ACCOUNT   = "marketpulsedatalake"
ADLS_URL          = f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net"
CONTAINER         = "bronze"
STOCKS            = ["AAPL", "MSFT", "IBM", "EDP.LS", "GALP.LS", "BCP.LS"]


#helper functions
def get_secret(secret_name: str) -> str:
    """Reads a secret from Azure Key Vault using Managed Identity."""
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
    return client.get_secret(secret_name).value


def ingest_stock(symbol: str, api_key: str) -> dict:
    """
    Calls Alpha Vantage API and returns raw daily stock data.
    Same logic as the notebook — no Databricks dependencies.
    """
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": api_key
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if "Error Message" in data:
        raise ValueError(f"API error for {symbol}: {data['Error Message']}")

    if "Note" in data:
        raise ValueError(f"Rate limit reached: {data['Note']}")

    logging.info(f"✅ {symbol} — {len(data.get('Time Series (Daily)', {}))} days received")
    return data    


def save_to_adls(
    data: dict,
    symbol: str,
    service_client: DataLakeServiceClient
) -> str:
    """
    Writes raw JSON data to ADLS Gen2 bronze layer.
    Replicates the same partition structure as the notebook:
    /bronze/stocks/ingest_date=YYYY-MM-DD/SYMBOL_TIMESTAMP.json
    """
    now = datetime.now(timezone.utc)
    ingest_date = now.strftime("%Y-%m-%d")
    ingest_ts   = now.strftime("%Y%m%d_%H%M%S")

    # Build path — same structure as notebook
    directory = f"stocks/ingest_date={ingest_date}"
    filename  = f"{symbol}_{ingest_ts}.json"

    # Get filesystem client
    fs_client  = service_client.get_file_system_client(CONTAINER)
    dir_client = fs_client.get_directory_client(directory)
    file_client = dir_client.create_file(filename)

    # Write JSON
    content = json.dumps(data, indent=2)
    file_client.upload_data(content, overwrite=True)

    path = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/{directory}/{filename}"
    logging.info(f"✅ {symbol} saved to {path}")
    return path




app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 0 18 * * 1-5",    # todos os dias úteis às 18h UTC
    arg_name="timer",
    run_on_startup=False
)



def market_pulse_ingestion(timer: func.TimerRequest) -> None:
    """
    Timer-triggered Azure Function.
    Runs weekdays at 18:00 UTC (after US market close).
    Fetches daily stock data from Alpha Vantage and writes to ADLS Gen2.
    """
    logging.info("🚀 Market Pulse ingestion started")

    # Authenticate
    credential     = DefaultAzureCredential()
    api_key        = get_secret("alphavantage-api-key")
    service_client = DataLakeServiceClient(
        account_url=ADLS_URL,
        credential=credential
    )

    # Ingest all stocks
    paths  = []
    errors = []

    for symbol in STOCKS:
        try:
            logging.info(f"🔄 Ingesting {symbol}...")
            data = ingest_stock(symbol, api_key)
            path = save_to_adls(data, symbol, service_client)
            paths.append(path)
        except Exception as e:
            logging.error(f"❌ Error processing {symbol}: {e}")
            errors.append(symbol)




    # Summary
    logging.info(f"✅ Ingestion complete: {len(paths)} stocks saved")
    if errors:
        logging.warning(f"⚠️ Failed stocks: {errors}")


