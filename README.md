# Market Pulse Pipeline

End-to-end financial data pipeline using **Azure Databricks**, **Delta Lake** and **Enhanced Medallion Architecture**.

**Repository:** [github.com/martalimas/market-pulse-pipeline](https://github.com/martalimas/market-pulse-pipeline)  
**Status:** 🔧 Stage 1 — Functional MVP in progress

---

## Objective

Build a production-ready data pipeline that ingests real-world stock 
market data through three distinct ingestion patterns (batch, micro-batch, 
streaming), processes it through the Medallion architecture, and exposes 
analytical metrics through a final dashboard.

The project demonstrates both **imperative** and **declarative (DLT)** 
approaches, mirroring real-world data engineering practices.

---

## High-level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SOURCES                              │
│                                                             │
│  BATCH        Alpha Vantage API → manual ingestion          │
│  MICRO-BATCH  Azure Function (every 5min) → JSON files      │
│  STREAMING    Python producer → Azure Event Hubs            │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   ADLS Gen2 (Data Lake)                     │
│                                                             │
│  /bronze/stocks/         ← Bronze Landing (JSON raw)        │
│  /bronze/ingestion/      ← Bronze Ingestion (Delta flat)    │
│  /silver/                ← Silver layer (typed, validated)  │
│  /gold/                  ← Gold layer (analytics ready)     │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                AZURE DATABRICKS                             │
│                                                             │
│  BRONZE LANDING    Raw JSON files (immutable)               │
│        ↓           dbutils.fs / Auto Loader (planned)       │
│                                                             │
│  BRONZE INGESTION  Flattened Delta table                    │
│        ↓           Metadata-driven config-based parsing     │
│                                                             │
│  SILVER            Typed · Deduplicated · Validated         │
│        ↓           Imperative (PySpark) + Declarative (DLT) │
│                    + Data Quality Expectations              │
│                                                             │
│  GOLD              Analytical metrics                       │
│                    · Moving averages (7d, 30d)              │
│                    · Daily volatility                       │
│                    · Volume aggregations                    │
│                    · Stock comparisons                      │
│                                                             │
│  Orchestration: Lakeflow Jobs (planned)                     │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  VISUALIZATION                              │
│  Power BI (native Databricks SQL connector)                 │
│  or Databricks SQL Dashboard                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Service | Role | Tier |
|---|---|---|
| **Azure ADLS Gen2** | Central Data Lake storage | Standard LRS |
| **Azure Databricks** | Processing engine + Medallion | Premium + Serverless |
| **Azure Key Vault** | Secure secret storage | Standard |
| **Azure Function** | Micro-batch API caller | Consumption (planned) |
| **Azure Event Hubs** | Streaming ingestion | Basic (planned) |
| **GitHub** | Version control + CI/CD | Free |

---

## Data Source

**Alpha Vantage API**

- **URL:** [alphavantage.co](https://www.alphavantage.co)
- **Plan:** Free (25 requests/day, 5/minute)
- **Endpoints:**
  - `TIME_SERIES_DAILY` — daily OHLCV history (compact: 100 days)
  - `GLOBAL_QUOTE` — real-time quote (planned for micro-batch)
- **Tracked stocks:** `AAPL`, `MSFT`, `IBM`, `EDP.LS`, `GALP.LS`, `BCP.LS`
  - Mix of US tech and Portuguese stocks (Euronext Lisbon)
  - List is configurable in the ingestion notebook

---

## Medallion Layers

### Bronze Landing
- Raw JSON files exactly as returned by the API
- Append-only — files are never modified
- Partitioned by `ingest_date=YYYY-MM-DD`
- Format: JSON

### Bronze Ingestion
- Flattened Delta table built from Bronze Landing
- All fields kept as `STRING` (no type casting)
- Defensive coding skips malformed files (logged separately)
- Metadata-driven via `config/alpha_vantage_schema.json`
- Format: Delta

### Silver
- Type casting (dates, doubles, longs)
- Deduplication on natural keys
- Data Quality Expectations:
  - `open > 0`, `high > 0`, `low > 0`, `close > 0`
  - `volume >= 0`
  - `symbol IS NOT NULL`
- Two tables:
  - `silver_dim_stock` — one row per symbol
  - `silver_fact_prices` — one row per `(symbol, trade_date)`
- Implementations:
  - Imperative (PySpark + write Delta)
  - Declarative (Lakeflow DLT)

### Gold
- `gold_daily_metrics` — OHLCV per stock and day
- `gold_moving_averages` — 7d and 30d rolling averages
- `gold_volatility` — daily standard deviation
- `gold_stock_comparison` — relative performance across stocks

---

## Repository Structure

```
market-pulse-pipeline/
├── README.md                       ← this file
├── config/
│   └── alpha_vantage_schema.json   ← metadata-driven mapping
├── docs/
│   ├── ROADMAP.md                  ← staged delivery plan
│   ├── infrastructure_setup.md     ← step-by-step Azure setup
│   └── architecture_decisions.md   ← ADRs
├── 01_bronze_ingestion             ← API → Bronze Landing
├── 02_bronze_to_ingestion          ← Bronze Landing → Bronze Ingestion
├── 03_silver_imperative            ← Bronze Ingestion → Silver (PySpark)
├── 04_silver_declarative           ← Bronze Ingestion → Silver (DLT) [planned]
├── 05_gold_metrics                 ← Silver → Gold [planned]
└── connection-test                 ← ADLS connectivity test
```

---

## Security

- API keys stored in **Azure Key Vault**
- Accessed via **Databricks Secret Scope** (`market-pulse-secrets`)
- Storage credentials managed via **Access Connector** (managed identity)
- No secrets ever committed to the repository

---

## Setup & Running

For step-by-step infrastructure setup instructions, see  
**[`docs/infrastructure_setup.md`](docs/infrastructure_setup.md)**

For the staged delivery plan and progress, see  
**[`docs/ROADMAP.md`](docs/ROADMAP.md)**

For architectural decisions and rationale, see  
**[`docs/architecture_decisions.md`](docs/architecture_decisions.md)**

---

## Project Status

```
✅ Stage 0 — Infrastructure Setup
🔧 Stage 1 — Functional MVP (Bronze done, Silver in progress)
⏳ Stage 2 — Multi-source Ingestion (Auto Loader, Functions, Event Hubs)
⏳ Stage 3 — Production Hardening (tests, schema, error handling)
⏳ Stage 4 — DataOps & Automation (CI/CD, monitoring)
⏳ Stage 5 — Advanced Patterns (SCD, ML, multi-source)
```

---

*Built as a portfolio project to demonstrate end-to-end data engineering 
capabilities on Azure Databricks. Last updated: May 2026.*