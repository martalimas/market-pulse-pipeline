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

## Stage 1 — Functional MVP 🔧

Goal: end-to-end Bronze → Silver → Gold pipeline with manual batch ingestion.

- [x] **Bronze Landing** — raw JSON files in ADLS
- [x] **Bronze Ingestion** — flattened Delta table (metadata-driven config)
- [ ] **Silver (imperative)** — typed, deduplicated, validated tables
- [ ] **Silver (declarative — DLT)** — same logic with Lakeflow
- [ ] **Gold** — moving averages, volatility, comparisons
- [ ] **Dashboard** — Power BI or Databricks SQL Dashboard
- [ ] **README & documentation** — final polish

---

## Stage 2 — Multi-source Ingestion ⏳

- [ ] **Auto Loader (cloudFiles)** — replace manual file loop
- [ ] **Azure Function** — micro-batch (5min API calls)
- [ ] **Event Hubs** — streaming Python producer
- [ ] **Lakeflow Jobs** — File Arrival triggers
- [ ] **Historical batch load** — bulk load from Alpha Vantage CSV

---

## Stage 3 — Production Hardening ⏳

- [ ] Schema enforcement with explicit `StructType`
- [ ] Automated tests (`pytest`, `great_expectations`)
- [ ] Structured logging
- [ ] Robust error handling and retries
- [ ] `OPTIMIZE` and `Z-ORDER` for performance
- [ ] Data contracts between layers

---

## Stage 4 — DataOps & Automation ⏳

- [ ] GitHub Actions CI/CD
- [ ] Pipeline scheduling (cron + file triggers)
- [ ] Monitoring & alerting
- [ ] Auto-generated schema docs and lineage
- [ ] Cost monitoring

---

## Stage 5 — Advanced Patterns ⏳

- [ ] SCD Type 2 on `dim_stock`
- [ ] Feature engineering (RSI, volatility bands)
- [ ] ML model integration
- [ ] Time travel demonstrations
- [ ] Multi-source unification (Yahoo Finance, Bloomberg)
- [ ] **dbt alternative** (bonus) — re-implement Silver/Gold using dbt 
      to demonstrate cross-platform skill

---

## Status Summary

| Stage | Status |
|---|---|
| 0 — Infrastructure | ✅ Complete |
| 1 — Functional MVP | 🔧 In progress |
| 2 — Multi-source Ingestion | ⏳ Planned |
| 3 — Production Hardening | ⏳ Planned |
| 4 — DataOps & Automation | ⏳ Planned |
| 5 — Advanced Patterns | ⏳ Planned |

---

*Last updated: May 2026*