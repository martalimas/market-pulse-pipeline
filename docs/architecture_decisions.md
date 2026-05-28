# Architecture Decisions — Market Pulse Pipeline

This document records the key technical decisions made during the design and implementation of the Market Pulse Pipeline, including the reasoning behind each choice and the alternatives considered.

---

## 1. Cloud Platform: Azure + Databricks

**Decision:** Azure Databricks (Premium, Serverless compute) with ADLS Gen2 as the storage layer.

**Reasoning:** Databricks is the dominant platform for data engineering in the Portuguese and European enterprise market (Noesis, Capgemini, Novabase). Choosing Azure over AWS or GCP aligns with the most common stack in target companies. Serverless compute eliminates cluster management overhead and minimises cost for a personal project with intermittent workloads.

**Alternatives considered:** AWS Glue + S3, GCP Dataproc. Rejected in favour of Databricks-native features (Delta Lake, Unity Catalog, DLT, Lakeflow Jobs) which provide a more cohesive and production-representative stack.

---

## 2. Storage Architecture: ADLS Gen2 + Delta Lake

**Decision:** All layers (landing, bronze, silver, gold) stored in ADLS Gen2 as Delta tables.

**Reasoning:** Delta Lake provides ACID transactions, schema enforcement, time travel, and efficient upserts (MERGE) — essential properties for a reliable data pipeline. ADLS Gen2 integrates natively with Databricks and Unity Catalog via the Access Connector, avoiding credential management in notebooks.

**Alternatives considered:** Azure Blob Storage (no hierarchical namespace, less efficient), Parquet files only (no ACID, no time travel).

---

## 3. Medallion Architecture: Bronze → Silver → Gold

**Decision:** Three-layer medallion architecture with clear separation of concerns.

**Reasoning:**
- **Bronze (Landing + Ingestion):** Raw data preserved exactly as received from the API. Landing stores the original JSON files; Ingestion applies schema mapping from `alpha_vantage_schema.json` without any business logic. Immutability at this layer enables full reprocessing from source.
- **Silver:** Cleaned, validated, dimensional model (`dim_stock`, `fact_prices`). Business logic lives here, not in bronze.
- **Gold:** Aggregated metrics ready for consumption (daily summary, moving averages, volatility, momentum, correlation). No raw data exposed at this layer.

**Alternatives considered:** Two-layer (raw + curated). Rejected because it conflates ingestion concerns with transformation logic, making debugging harder.

---

## 4. Three Ingestion Patterns (Multi-Pattern Bronze)

**Decision:** Implemented three ingestion patterns in parallel rather than choosing one.

| Pattern | Notebook | Use case |
|---|---|---|
| Batch (COPY INTO) | `02_bronze_to_ingestion` | Full historical load, reference |
| Micro-batch (Auto Loader) | `02_bronze_autoloader` | Incremental file ingestion, daily runs |
| Streaming (Event Hubs) | `07_bronze_streaming_eventhubs` | Near-real-time ingestion |

**Reasoning:** Demonstrates understanding of the trade-offs between patterns. Auto Loader is the primary production pattern — it detects new files automatically via checkpoint state, provides exactly-once semantics, and supports schema inference. COPY INTO is simpler but requires explicit file tracking. Event Hubs enables streaming but adds infrastructure cost and complexity.

**Known limitation:** Databricks Serverless does not support continuous streaming triggers (`processingTime`). The Event Hubs notebook uses `trigger(availableNow=True)` (micro-batch) as a workaround. True continuous streaming requires a Classic cluster.

---

## 5. Metadata-Driven Schema Mapping (`alpha_vantage_schema.json`)

**Decision:** Field renaming and type casting defined in a JSON config file, not hardcoded in Python.

**Reasoning:** The Alpha Vantage API returns fields with verbose names (`1. open`, `2. high`, etc.) that need to be renamed for downstream use. Encoding this mapping in a config file separates the *what* (business meaning) from the *how* (Spark transformation logic), making it easy to adapt to schema changes without touching code. This is the metadata-driven ETL pattern common in production pipelines.

**Alternatives considered:** Hardcoded `withColumnRenamed()` chains. Rejected because they couple business logic to transformation code.

---

## 6. SOLID Code Architecture (`src/market_pulse/`)

**Decision:** Refactored from monolithic notebooks into a SOLID Python package in `src/market_pulse/`.

**Reasoning:** Notebooks are useful for exploration but poor for maintainability and testing. The SOLID structure (Single Responsibility, Open/Closed, etc.) separates concerns: `config.py` holds configuration, `utils.py` holds generic utilities (`write_delta_table`), `logger.py` handles observability, and each layer (`ingestion/`, `bronze/`, `silver/`, `gold/`) owns its business logic. The `*_v2` notebooks are thin orchestration layers that import from `src/`, keeping notebooks clean.

**Key design principle — `write_delta_table`:** The shared writer in `utils.py` handles *how* to write (Delta format, partitioning, mode). The *what* and the write mode (`overwrite` vs `append`) are decided by each calling layer. This keeps `utils.py` free of business logic.

**Alternatives considered:** Single-notebook approach. Rejected because it makes unit testing impossible and code reuse difficult.

---

## 7. Imperative + Declarative Dual Implementation

**Decision:** Each layer (Silver, Gold) implemented twice — imperative (PySpark notebooks) and declarative (DLT pipelines).

**Reasoning:** Demonstrates understanding of both paradigms. Imperative notebooks give full control and are easier to debug step-by-step. DLT declarative pipelines provide automatic lineage, built-in data quality expectations (`@dlt.expect_or_drop`), and managed execution via Lakeflow Pipelines. In production, DLT is preferred for reliability; the imperative versions serve as reference implementations.

---

## 8. Data Quality: Schema Enforcement + DLT Expectations

**Decision:** Two-layer data quality approach.

- **Schema enforcement** at Bronze Ingestion: rejects records that don't match the expected schema, logged to the observability table.
- **DLT expectations** at Silver Declarative: five `@dlt.expect_or_drop` rules on `fact_prices` (non-null symbol, positive prices, valid volume, valid date).

**Reasoning:** Catching bad data early (Bronze) prevents it from propagating downstream. DLT expectations provide a declarative, auditable quality layer that is native to the platform.

---

## 9. Observability: Structured Logging + Delta Table

**Decision:** Dual observability — structured JSON logs to files + a Delta table (`observability_log`) that records pipeline runs with metadata.

**Reasoning:** JSON logs are human-readable and easy to grep. The Delta table enables SQL queries over pipeline history (`SELECT * FROM observability_log WHERE status = 'ERROR'`), supports alerting, and demonstrates production-grade monitoring practices. Both are written by `logger.py` in `src/market_pulse/`.

---

## 10. Error Handling: Tenacity Retry with Exponential Backoff

**Decision:** All API calls to Alpha Vantage wrapped with `tenacity` retry logic (exponential backoff, max 3 attempts).

**Reasoning:** The Alpha Vantage free tier enforces rate limits (1 request/second, 25/day). Transient failures (network timeouts, rate limit responses) should be retried automatically rather than failing the pipeline. `tenacity` provides a clean, declarative way to configure retry behaviour without manual `try/except` loops.

---

## 11. Maintenance Job: OPTIMIZE + Z-ORDER

**Decision:** A dedicated weekly maintenance Lakeflow Job (`08_maintenance`) runs `OPTIMIZE` and `Z-ORDER` on all Delta tables.

**Reasoning:** Delta Lake accumulates small files over time (the "small files problem"), which degrades query performance. `OPTIMIZE` compacts them; `Z-ORDER` co-locates related data (ordered by `symbol` and `date`) to enable data skipping. Running this as a separate scheduled job follows the separation of concerns principle — data processing and maintenance are independent concerns.

---

## 12. CI/CD: GitHub Actions (Simplified)

**Decision:** GitHub Actions workflow (`.github/workflows/tests.yml`) runs the bronze ingestion test suite on every push to `main`.

**Reasoning:** CI/CD closes the DataOps loop — every code change is automatically validated before it reaches the repository. The workflow is intentionally simplified: it installs only lightweight dependencies (`pytest`, `requests`, `tenacity`) without PySpark, runs only the bronze tests (which are environment-independent), and sets `PYTHONPATH=src` explicitly. This approach gives fast feedback (under 30 seconds) without the complexity of a full PySpark environment in CI.

**Known limitation:** Silver and Gold tests require a live Spark session and cannot run in GitHub Actions without a Databricks cluster or a heavy Docker image. Extending CI to cover those layers is a Stage 5 item.

---

## 13. Unity Catalog: Partial Registration

**Decision:** Only the Gold layer and Silver Declarative (DLT) tables are registered in Unity Catalog (`market_pulse_databricks`). Bronze and Silver Imperative tables exist as Delta files in ADLS but are not registered as catalog tables.

**Reasoning:** Registration in Unity Catalog adds governance (access control, lineage, tagging) but requires explicit `CREATE TABLE` statements or DLT target schema configuration. The imperative layers write to ADLS paths directly, which is sufficient for a personal project. Gold and DLT tables are registered because they are the consumption layer — downstream users (dashboards, SQL queries) benefit from catalog discoverability.

**Future improvement:** Register all layers via `CREATE TABLE ... USING DELTA LOCATION '...'` for full lineage visibility in Unity Catalog.

---

## 14. SCD Type 2 on `dim_stock`

**Decision:** Implemented Slowly Changing Dimension Type 2 on `dim_stock`, storing history in a separate table `dim_stock_scd2` at `silver/dim_stock_scd2/` rather than overwriting the existing dimension.

**Reasoning:** `dim_stock` holds metadata about each stock (last refresh timestamp, timezone). When that metadata changes, a simple overwrite loses the history of when the change occurred. SCD Type 2 preserves the full audit trail by closing the old record (`valid_to = current_date`, `is_current = FALSE`) and inserting a new active record (`valid_to = 9999-12-31`, `is_current = TRUE`). This enables point-in-time queries — joining `fact_prices` to the version of `dim_stock` that was active on any given date.

**Implementation:** Delta Lake MERGE statement with three-way logic:
- **MATCHED + changed attributes** → close existing row (`valid_to`, `is_current = FALSE`)
- **NOT MATCHED** → insert new row with `valid_from = current_date`, `valid_to = 9999-12-31`, `is_current = TRUE`
- A second INSERT opens the new version for rows that were closed in the same operation.

**Schema additions:** `valid_from DATE`, `valid_to DATE`, `is_current BOOLEAN`

**Alternatives considered:** SCD Type 1 (overwrite) — simpler but destroys history. SCD Type 2 with ARRAY OF STRUCT — more compact but harder to query with standard SQL and incompatible with Delta MERGE.

---

## 15. Time Travel

**Decision:** Demonstrated Delta Lake Time Travel on pipeline tables using both `VERSION AS OF` and `TIMESTAMP AS OF` syntax.

**Reasoning:** Time Travel is one of Delta Lake's most powerful features for production pipelines — it enables recovery from accidental overwrites, auditing of data at any point in history, and reproducible ML training datasets. Including Time Travel demonstrations in the project shows understanding of Delta Lake beyond basic read/write operations.

**Use cases demonstrated:**
- Querying a table as it existed at a previous version
- Recovering data after an unintended transformation
- Comparing current vs historical state of a metric

**Retention:** Delta transaction log retains history for 30 days by default (`delta.logRetentionDuration`). VACUUM removes files older than the retention threshold — running VACUUM too aggressively breaks Time Travel.

---

*Last updated: May 2026*
