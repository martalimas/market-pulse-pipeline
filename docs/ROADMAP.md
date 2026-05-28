# Project Roadmap — Market Pulse Pipeline

This document outlines the staged delivery plan for the project.

---

## Stage 0 — Infrastructure Setup ✅

- [x] Azure account + trial activation
- [x] Resource Group `rg-market-pulse-pipeline`
- [x] ADLS Gen2 with `bronze` / `silver` / `gold` containers
- [x] Azure Databricks workspace (Premium + Serverless)
- [x] GitHub linked to Databricks (Git Folders)
- [x] ADLS connected to Databricks
  - [x] Access Connector created
  - [x] Permissions granted on ADLS
  - [x] Storage Credential in Databricks
  - [x] External Location configured
- [x] Azure Key Vault + Secret Scope
- [x] Alpha Vantage API key registered and stored securely

---

## Stage 1 — Functional MVP ✅

Goal: end-to-end Bronze → Silver → Gold pipeline with manual batch ingestion.

- [x] **Bronze Landing** — raw JSON files in ADLS
- [x] **Bronze Ingestion** — flattened Delta table (metadata-driven config via `alpha_vantage_schema.json`)
- [x] **Silver (imperative)** — typed, deduplicated, validated tables (`dim_stock`, `fact_prices`)
- [x] **Silver (declarative — DLT)** — same logic with Lakeflow Pipelines + 5 `@dlt.expect_or_drop` quality rules
- [x] **Gold** — 5 metrics: daily summary, moving averages, volatility, momentum, correlation
- [x] **Gold (declarative — DLT)** — same metrics via Lakeflow Pipelines
- [x] **Dashboard** — Databricks SQL Dashboard
- [x] **README & documentation** — architecture decisions, roadmap, infrastructure setup

---

## Stage 2 — Multi-source Ingestion ✅

- [x] **Auto Loader (cloudFiles)** — incremental file ingestion with checkpoint state and schema inference
- [x] **Azure Function** — code complete; not deployed (Serverless trigger limitation)
- [x] **Event Hubs** — streaming producer implemented; runs as micro-batch (`availableNow=True`) due to Serverless constraint — continuous streaming requires Classic cluster
- [x] **Lakeflow Jobs** — 3 jobs: v1 (original), v2 (SOLID), maintenance (weekly)
- [ ] **Historical batch load** — bulk load from Alpha Vantage CSV export

---

## Stage 3 — Production Hardening ✅

- [x] Schema enforcement with explicit `StructType`
- [x] Automated tests — 9 `pytest` unit tests covering bronze ingestion layer
- [x] Structured logging — JSON logs + Delta observability table (`observability_log`)
- [x] Robust error handling — `tenacity` retry with exponential backoff on all API calls
- [x] `OPTIMIZE` and `Z-ORDER` — weekly maintenance job (`08_maintenance`)
- [x] SOLID code architecture — `src/market_pulse/` package (config, utils, logger, ingestion, bronze, silver, gold)

---

## Stage 4 — DataOps & Automation ✅ (partial)

- [x] **GitHub Actions CI/CD** — `.github/workflows/tests.yml` runs bronze tests on every push to `main`; badge visible in README
- [ ] Pipeline scheduling — cron triggers for daily ingestion
- [ ] Monitoring & alerting — Azure Monitor or Databricks alerts
- [ ] Auto-generated schema docs and lineage
- [ ] Cost monitoring

---

## Stage 5 — Advanced Patterns 🔧

- [x] SCD Type 2 on `dim_stock` — MERGE with `valid_from` / `valid_to` / `is_current`, stored at `silver/dim_stock_scd2/`
- [x] Time travel demonstrations — Delta Lake `VERSION AS OF` / `TIMESTAMP AS OF`
- [ ] Feature engineering (RSI, volatility bands)
- [ ] ML model integration
- [ ] Multi-source unification (Yahoo Finance, Bloomberg)
- [ ] **dbt alternative** (bonus) — re-implement Silver/Gold using dbt
      to demonstrate cross-platform skill

---

## Status Summary

| Stage | Status |
|---|---|
| 0 — Infrastructure | ✅ Complete |
| 1 — Functional MVP | ✅ Complete |
| 2 — Multi-source Ingestion | ✅ Complete (with known limitations) |
| 3 — Production Hardening | ✅ Complete |
| 4 — DataOps & Automation | ✅ Partial (CI/CD done; scheduling/monitoring pending) |
| 5 — Advanced Patterns | 🔧 In progress (SCD2 + Time Travel ✅) |

---

*Last updated: May 2026*
