

# Storage 
STORAGE_ACCOUNT = "marketpulsedatalake"

BRONZE_LANDING_PATH = f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/stocks/"
BRONZE_INGESTION_PATH = f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/ingestion/stocks/"
BRONZE_STREAMING_PATH = f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/streaming/stocks/"
BRONZE_CHECKPOINT_PATH = f"abfss://bronze@{STORAGE_ACCOUNT}.dfs.core.windows.net/_checkpoints/bronze_autoloader/"

SILVER_DIM_STOCK_PATH = f"abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/dim_stock/"
SILVER_FACT_PRICES_PATH = f"abfss://silver@{STORAGE_ACCOUNT}.dfs.core.windows.net/fact_prices/"

GOLD_DAILY_SUMMARY_PATH = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/daily_summary/"
GOLD_MOVING_AVERAGES_PATH = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/moving_averages/"
GOLD_VOLATILITY_PATH = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/volatility/"
GOLD_VOLUME_ANALYSIS_PATH = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/volume_analysis/"
GOLD_STOCK_COMPARISON_PATH = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/stock_comparison/"

#  Stocks 
STOCKS = ["AAPL", "MSFT", "IBM", "EDP.LS", "GALP.LS", "BCP.LS"]

#  API 
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_OUTPUT_SIZE = "compact"  # last 100 trading days

#  Key Vault 
KEY_VAULT_URL = "https://mktpulse-kv.vault.azure.net/"
SECRET_API_KEY = "alphavantage-api-key"
SECRET_EH_CONNECTION = "eventhub-connection-string"

#ADLS
CONTAINER = "bronze"