# 1. Imports (incluindo dlt)
import dlt
from pyspark.sql.functions import col, to_date, current_timestamp

# Source — Bronze Ingestion Delta table path
BRONZE_INGESTION_PATH = (
    "abfss://bronze@marketpulsedatalake.dfs.core.windows.net/ingestion/stocks/"
)

# DIMENSION TABLE — silver_dim_stock
@dlt.table(
    name="silver_dim_stock", #Nome da tabela que vai aparecer no Catalog. Sem isto, o Databricks usaria o nome da função.
    comment="Stock dimension table — one row per symbol with last refresh date and time zone", ## Documentação que aparece no Catalog quando alguém olha para a tabela. Boas práticas — torna a tabela auto-explicativa.
)

def silver_dim_stock():
    return (
        spark.read.format("delta").load(BRONZE_INGESTION_PATH)
            .select("symbol", "last_refreshed", "time_zone")
            .withColumn("last_refreshed", to_date(col("last_refreshed")))
            .withColumn("ingest_timestamp", current_timestamp())
            .dropDuplicates(["symbol"])
    )

#Outros parâmetros úteis (não usámos aqui)
#@dlt.table(
#   name="silver_dim_stock",
#    comment="...",
#    table_properties={                          # Delta table properties
#        "quality": "silver",
#        "pipelines.autoOptimize.managed": "true"
#    },
#    partition_cols=["region"],                  # particionamento
#    path="abfss://...custom_path/",             # path explícito (senão usa default)
#)    

# FACT TABLE — silver_fact_prices

@dlt.table(
    name="silver_fact_prices",
    comment="Daily stock prices fact table with OHLCV values and natural composite key (symbol + trade_date)",
)
#Cada @dlt.expect_or_drop("nome", "condição") é uma regra de qualidade declarativa:
#@dlt.expect("nome", "regra")Avalia mas não filtra — só conta violações
#@dlt.expect_or_drop("nome", "regra")Descarta linhas inválidas (continua pipeline)
#@dlt.expect_or_fail("nome", "regra")Falha o pipeline se alguma violação ocorrer

@dlt.expect_or_drop("valid_open", "open > 0")
@dlt.expect_or_drop("valid_high", "high > 0")
@dlt.expect_or_drop("valid_low", "low > 0")
@dlt.expect_or_drop("valid_close", "close > 0")
@dlt.expect_or_drop("valid_volume", "volume >= 0")
def silver_fact_prices():
    return (
        spark.read.format("delta").load(BRONZE_INGESTION_PATH)
            .select("symbol", "trade_date", "open", "high", "low", "close", "volume")
            .withColumn("trade_date", to_date(col("trade_date")))
            .withColumn("open", col("open").cast("double"))
            .withColumn("high", col("high").cast("double"))
            .withColumn("low", col("low").cast("double"))
            .withColumn("close", col("close").cast("double"))
            .withColumn("volume", col("volume").cast("long"))
            .withColumn("ingest_timestamp", current_timestamp())
            .dropDuplicates(["symbol", "trade_date"])
    )

