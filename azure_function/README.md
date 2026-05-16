# Azure Function — market-pulse-ingestion
**market-pulse-pipeline · Stage 2**

Timer-triggered Azure Function that automates the daily stock data ingestion from Alpha Vantage API to ADLS Gen2 Bronze layer.

> **Status:** Code complete. Deploy pending paid Azure subscription.

---

## What this replaces

In Stage 1, the ingestion was manual:
```
You → open Databricks → run 01_bronze_ingestion → API → ADLS
```

With the Azure Function, it becomes fully automated:
```
Azure Function (18:00 UTC, weekdays) → API → ADLS → Auto Loader detects → Bronze Delta
```

---

## The 3 ingestion patterns — how they differ

| Pattern | Component | Trigger | What it does |
|---|---|---|---|
| **Batch** | `01_bronze_ingestion` (notebook) | Manual | Calls API, writes JSON to ADLS |
| **Micro-batch** | `02_bronze_autoloader` | Manual / Job schedule | Reads only NEW JSON files, appends to Delta |
| **Streaming** | `07_bronze_streaming_eventhubs` | Continuous / Job | Reads events from Event Hubs in real-time |

The Azure Function is the **producer** — it generates the data. The Auto Loader and Event Hubs are the **consumers** — they process it.

```
Azure Function → ADLS → Auto Loader → Delta Bronze   (file-based)
Python producer → Event Hubs → Spark Streaming → Delta Bronze   (event-based)
```

---

## Write modes — overwrite vs append

| Component | Write mode | Why |
|---|---|---|
| `01_bronze_ingestion` | New file per run | Each run creates a new timestamped file |
| `02_bronze_to_ingestion` (old) | Overwrite Delta table | Read ALL files, rewrite everything |
| `02_bronze_autoloader` | Append to Delta table | Checkpoint tracks processed files |
| Azure Function | New file per run | Same as notebook — unique timestamp |
| Event Hubs streaming | Append to Delta table | Events flow continuously |

The only component that did overwrite was `02_bronze_to_ingestion` — replaced by Auto Loader in Stage 2.

---

## Schedule — cron expression

```python
schedule="0 0 18 * * 1-5"
```

| Position | Value | Meaning |
|---|---|---|
| Seconds | 0 | at second 0 |
| Minutes | 0 | at minute 0 |
| Hours | 18 | at 18:00 UTC |
| Day of month | * | every day |
| Month | * | every month |
| Day of week | 1-5 | Monday to Friday only |

**Why 18:00 UTC?**
US markets close at 16:00 EST = 21:00 Portugal (summer) = 18:00 UTC.
Running after market close ensures the daily data is complete.

---

## Authentication — no secrets in code

The Function uses **Managed Identity** — the Azure equivalent of the Databricks Access Connector.

```
Databricks:                    Azure Function:
Access Connector (MI)      →   Managed Identity
dbutils.secrets.get()      →   DefaultAzureCredential + SecretClient
dbutils.fs.put()           →   DataLakeServiceClient
```

`DefaultAzureCredential` tries authentication methods in order:
```
In production (Azure Function):
  → Managed Identity  ✅

In local development:
  → Azure CLI (az login)  ✅
```

The same code works in both environments — no changes needed.

---

## Logging — why not print()

Azure Functions run unattended — no one is watching the console at 18:00.

```python
print("✅ AAPL")         → goes nowhere — lost
logging.info("✅ AAPL")  → goes to Azure Monitor — stored, searchable
```

All logs are available in **Azure Portal → Function App → Monitor → Logs**:
```
18:00:01 — 🚀 Market Pulse ingestion started
18:00:03 — ✅ AAPL — 100 days received
18:00:05 — ✅ MSFT — 100 days received
18:00:07 — ❌ Error processing EDP.LS: rate limit
18:00:08 — ✅ Ingestion complete: 5 stocks saved
18:00:08 — ⚠️ Failed stocks: ['EDP.LS']
```

This is the **structured logging** pattern planned for Stage 3 notebooks — the Azure Function implements it from the start because the environment requires it.

---

## Notebook vs Azure Function — side by side

| | `01_bronze_ingestion` (notebook) | `function_app.py` (Azure Function) |
|---|---|---|
| Authentication | `dbutils.secrets.get()` | `DefaultAzureCredential` + `SecretClient` |
| Write to ADLS | `dbutils.fs.put()` | `DataLakeServiceClient.upload_data()` |
| Logging | `print()` | `logging.info/error/warning()` |
| Trigger | Manual | Timer (cron: weekdays 18:00 UTC) |
| Environment | Databricks cluster | Azure Functions runtime |
| Path structure | identical | identical |

---

## File structure

```
azure_function/
├── function_app.py      ← main function code
├── requirements.txt     ← Python dependencies
└── README.md            ← this file
```

### requirements.txt explained

```
azure-functions              ← Azure Function SDK (trigger, bindings)
azure-storage-file-datalake  ← replaces dbutils.fs.put()
azure-identity               ← Managed Identity authentication
azure-keyvault-secrets       ← replaces dbutils.secrets.get()
requests                     ← Alpha Vantage API calls
```

---

## Deploy checklist

To deploy this function to Azure, the following steps are required:

```
1. Create Azure Function App
   → Requires paid subscription (Flex Consumption or Consumption Linux)
   → Free Trial does not support Python on Consumption plan

2. Configure Managed Identity
   → Enable System-assigned Managed Identity on the Function App
   → This gives the Function an identity in Azure AD

3. Grant permissions
   → Key Vault: add Managed Identity as "Key Vault Secrets User"
   → ADLS Gen2: add Managed Identity as "Storage Blob Data Contributor"

4. Deploy the code
   → Via Azure CLI: func azure functionapp publish market-pulse-function
   → Or via GitHub Actions (Stage 4 CI/CD)
   → Or via VS Code Azure Functions extension
```

> **Note:** Steps 1-4 are pending a paid Azure subscription.
> The code is complete, reviewed, and ready for deployment.

---

## Integration with the pipeline

Once deployed, the full automated pipeline becomes:

```
18:00 UTC (weekdays)
    Azure Function wakes up
    → calls Alpha Vantage for 6 stocks
    → writes 6 JSON files to ADLS /bronze/stocks/ingest_date=TODAY/

Lakeflow Job (triggered after Function, or on schedule)
    Task 1: bronze_autoloader  → detects 6 new files, appends to Delta
    Task 2: silver_imperative  → Bronze → Silver
    Task 3: silver_declarative → Bronze → Silver (DLT)
    Task 4: gold_imperative    → Silver → Gold
    Task 5: gold_declarative   → Silver → Gold (DLT)

Dashboard refreshes automatically
```

Full pipeline from API to dashboard — zero manual intervention.