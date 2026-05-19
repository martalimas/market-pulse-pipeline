# src/market_pulse/02_bronze/schema.py
# Single Responsibility: JSON schema definition only.
# No transformation, no I/O.

from pyspark.sql.types import (
    StructType, StructField, StringType, MapType
)

meta_schema = StructType([
    StructField("2. Symbol",         StringType(), True),
    StructField("3. Last Refreshed", StringType(), True),
    StructField("5. Time Zone",      StringType(), True)
])

time_series_value_schema = StructType([
    StructField("1. open",   StringType(), True),
    StructField("2. high",   StringType(), True),
    StructField("3. low",    StringType(), True),
    StructField("4. close",  StringType(), True),
    StructField("5. volume", StringType(), True)
])

json_schema = StructType([
    StructField("Meta Data",
                meta_schema, True),
    StructField("Time Series (Daily)",
                MapType(StringType(), time_series_value_schema), True)
])