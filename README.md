# Market Pulse Pipeline

End-to-end financial data pipeline using **Azure Databricks**, **Delta Lake** and **Enhanced Medallion Architecture**.

**Repository:** [github.com/martalimas/market-pulse-pipeline](https://github.com/martalimas/market-pulse-pipeline)  
**Status:** 🔧 Stage 2 — Multi-source Ingestion in progress

---

## Objective

Build a production-ready data pipeline that ingests real-world stock market data through three distinct ingestion patterns (batch, micro-batch, streaming), processes it through the Medallion architecture, and exposes analytical metrics through a final dashboard.

The project demonstrates both **imperative** and **declarative (DLT)** approaches, and deliberately shows the **evolution from batch to incremental to streaming** — mirroring real-world data engineering practices.

---

## High-level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SOURCES                              │
│                                                             │
│  BATCH        Alpha Vantage API → manual ingestion     ✅   │
│  MICRO-BATCH  Auto Loader → incremental JSON files     ✅   │
│  STREAMING    Python producer → Azure Event Hubs       ⚠️   │
│               Azure Function (timer trigger)           ⏳   │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   ADLS Gen2 (Data Lake)                     │
│                                                             │
│  /bronze/stocks/         ← Bronze Landing (JSON raw)   ✅   │
│  /bronze/ingestion/      ← Bronze Ingestion (Delta)    ✅   │
│  /bronze/streaming/      ← Event Hubs stream target    ⚠️   │
│  /silver/                ← Silver layer                ✅   │
│  /gold/                  ← Gold layer                  ✅   │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                AZURE DATABRICKS                             │
│                                                             │
│  BRONZE LANDING    Raw JSON files (immutable, partitioned)  │
│        ↓           01_bronze_ingestion                 ✅   │
│                                                             │
│  BRONZE INGESTION  Flattened Delta table                    │
│        ↓           02_bronze_autoloader (Auto Loader)  ✅   │
│                    Incremental append + checkpoint          │
│                                                             │
│  SILVER            Typed · Deduplicated · Validated         │
│        ↓           Imperative (PySpark)                ✅   │
│                    Declarative (DLT + Expectations)    ✅   │
│                                                             │
│  GOLD              Analytical metrics                       │
│                    Imperative (PySpark + Spark SQL)    ✅   │
│                    Declarative (DLT)                   ✅   │
│                                                             │
│  Orchestration: Lakeflow Jobs (end-to-end DAG)         ✅   │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  VISUALIZATION                              │
│  Databricks SQL Dashboard                              ⏳   │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Service | Role | Tier | Status |
|---|---|---|---|
| **Azure ADLS Gen2** | Central Data Lake storage | Standard LRS | ✅ |
| **Azure Databricks** | Processing engine + Medallion | Premium + Serverless | ✅ |
| **Azure Key Vault** | Secure secret storage | Standard | ✅ |
| **Azure Event Hubs** | Streaming ingestion | Basic | ⚠️ |
| **Azure Function** | Automated API caller | Consumption | ⏳ |
| **GitHub** | Version control | Free | ✅ |

---

## Data Source

**Alpha Vantage API**

- **URL:** [alphavantage.co](https://www.alphavantage.co)
- **Plan:** Free (25 requests/day, 5/minute)
- **Endpoints used:**
  - `TIME_SERIES_DAILY` — daily OHLCV history (compact: last 100 days)
  - `GLOBAL_QUOTE` — real-time quote (Event Hubs streaming)
- **Tracked stocks:** `AAPL`, `MSFT`, `IBM`, `EDP.LS`, `GALP.LS`, `BCP.LS`
  - Mix of US tech and Portuguese stocks (Euronext Lisbon)
  - Configurable via `config/alpha_vantage_schema.json`

---

## Medallion Layers

### Bronze Landing
- Raw JSON files exactly as returned by the Alpha Vantage API
- Append-only — files are never modified or deleted
- Partitioned by `ingest_date=YYYY-MM-DD`
- Format: JSON

### Bronze Ingestion
- Flattened Delta table built incrementally from Bronze Landing
- **Stage 1:** Full overwrite batch (`02_bronze_to_ingestion`)
- **Stage 2:** Auto Loader micro-batch (`02_bronze_autoloader`) — checkpoint-based, processes only new files
- All fields kept as `STRING` — type casting delegated to Silver
- Non-flat JSON (Alpha Vantage `Time Series (Daily)` uses dynamic date keys) — handled via `foreachBatch` + `explode(MapType)`

### Silver
- Type casting: `trade_date` → DateType, prices → DoubleType, volume → LongType
- Deduplication on `(symbol, trade_date)`
- Data Quality Expectations (DLT):
  - `open > 0`, `high > 0`, `low > 0`, `close > 0`
  - `volume >= 0`, `symbol IS NOT NULL`
- Two tables: `dim_stock` (one row per symbol), `fact_prices` (one row per `symbol × trade_date`)
- Two implementations: Imperative (PySpark) + Declarative (DLT)

### Gold
- `daily_summary` — OHLCV per stock and day
- `moving_averages` — 7-day and 30-day rolling averages
- `volatility` — daily price standard deviation
- `volume_analysis` — volume aggregations and anomalies
- `stock_comparison` — relative performance across stocks
- Two implementations: Imperative (PySpark + Spark SQL) + Declarative (DLT)

---

## Ingestion Patterns — Evolution

One of the core goals of this project is to demonstrate the evolution from simple batch to production-grade incremental and streaming ingestion:

| Pattern | Notebook | Trigger | Behaviour |
|---|---|---|---|
| Batch | `02_bronze_to_ingestion` | Manual | Reads ALL files, full overwrite |
| Micro-batch | `02_bronze_autoloader` | Manual / Job | Reads only NEW files, append |
| Streaming | `07_bronze_streaming_eventhubs` | Job / continuous | Real-time via Event Hubs |

The migration from batch to Auto Loader required rewriting the transformation from Python `parse_file()` to Spark-native `explode(MapType)` — documented in `docs/02_bronze_autoloader_doc.md`.

---

## Orchestration — Lakeflow Jobs

Full pipeline orchestrated as a DAG:

```
bronze_ingestion
        ↓
bronze_autoloader
        ↓           ↓
silver_imperative   silver_declarative
        ↓                   ↓
gold_imperative     gold_declarative
```

Silver and Gold layers run in parallel (imperative + declarative).  
Full pipeline completes in ~3 minutes on Serverless compute.

---

## Technical Decisions & Limitations

### Auto Loader — `foreachBatch` pattern
The Alpha Vantage JSON uses dynamic date keys in `Time Series (Daily)`, making it a `MapType` in Spark. Direct streaming transformations on nested structs with special characters are unsupported in Serverless. Solution: `foreachBatch` processes each micro-batch as a standard batch DataFrame with full API access.

### Event Hubs — Serverless networking limitation
Serverless compute has restricted outbound network access. The Kafka endpoint (port 9093) is unreachable from Serverless clusters. In production this would run on a Classic cluster or with VNet injection. Code is implemented and correct — limitation is infrastructure, not logic.

### Streaming trigger — `availableNow` vs `processingTime`
Serverless does not support continuous streaming triggers (`processingTime`). All streaming uses `availableNow=True` (micro-batch). True continuous streaming requires Classic cluster.

### Kafka shading in Serverless
Serverless uses a shaded Kafka distribution. SASL authentication requires `kafkashaded.org.apache.kafka` prefix instead of `org.apache.kafka`.

---

## Repository Structure

```
market-pulse-pipeline/
├── README.md
├── config/
│   └── alpha_vantage_schema.json       ← metadata-driven field mapping
├── docs/
│   ├── ROADMAP.md
│   ├── infrastructure_setup.md
│   ├── architecture_decisions.md
│   ├── 02_bronze_autoloader_doc.md     ← Auto Loader design + migration
│   └── 07_bronze_streaming_eventhubs_doc.md ← Event Hubs + Serverless limits
├── 01_bronze_ingestion                 ← API → Bronze Landing (JSON)
├── 02_bronze_to_ingestion              ← Batch ingestion (Stage 1, reference)
├── 02_bronze_autoloader                ← Auto Loader micro-batch (Stage 2)
├── 03_silver_imperative                ← Silver PySpark
├── 04_silver_declarative               ← Silver DLT
├── 05_gold_imperative                  ← Gold PySpark + Spark SQL
├── 06_gold_declarative                 ← Gold DLT
├── 07_bronze_streaming_eventhubs       ← Event Hubs streaming (Stage 2)
└── connection-test                     ← ADLS connectivity test
```

---

## Security

- API keys and connection strings stored in **Azure Key Vault** (`mktpulse-kv`)
- Accessed via **Databricks Secret Scope** (`market-pulse-secrets`)
- Storage credentials managed via **Access Connector** (managed identity — no keys in code)
- No secrets committed to the repository

---

## Setup

For infrastructure setup: [`docs/infrastructure_setup.md`](docs/infrastructure_setup.md)  
For staged roadmap and progress: [`docs/ROADMAP.md`](docs/ROADMAP.md)  
For architectural decisions: [`docs/architecture_decisions.md`](docs/architecture_decisions.md)

---

## Project Status

```
✅ Stage 0 — Infrastructure Setup
   Azure ADLS Gen2, Databricks Premium, Key Vault, Access Connector

✅ Stage 1 — Functional MVP
   Bronze Landing + Ingestion (batch, metadata-driven)
   Silver (imperative + DLT, dedup, expectations)
   Gold (imperative + DLT, 5 metrics)
   Unity Catalog schemas

🔧 Stage 2 — Multi-source Ingestion & Automation
   ✅ Auto Loader micro-batch (incremental Bronze ingestion)
   ✅ Lakeflow Jobs (end-to-end DAG, 3min runtime)
   ⚠️  Event Hubs streaming (code complete, Serverless network limitation)
   ⏳  Azure Function (code pending, subscription limitation)
   ⏳  Dashboard

⏳ Stage 3 — Production Hardening
   Tests, schema enforcement, structured logging, OPTIMIZE

⏳ Stage 4 — DataOps & CI/CD
   GitHub Actions, scheduling, monitoring, dev/prod

⏳ Stage 5 — Advanced Patterns
   SCD Type 2, RSI, ML integration, dbt
```

---

*Built as a portfolio project demonstrating end-to-end data engineering on Azure Databricks.  
Stack: Azure ADLS Gen2 · Databricks Premium Serverless · Delta Lake · DLT · Lakeflow Jobs · Event Hubs · Key Vault  
Last updated: May 2026*