# market-pulse-pipeline
End-to-end financial data pipeline using Azure Databricks, Delta Lake and Medallion Architecture
# Projecto End-to-End: Financial Stocks Pipeline
**Stack:** Azure Databricks · Delta Lake · Medallion Architecture  
**Repositório:** github.com/martalimas/databricks-learning-journey  
**Estado:** 🔧 Em construção

---

## Objectivo

Pipeline de dados end-to-end que ingere dados reais de stocks financeiros via 3 padrões de ingestão distintos (batch, micro-batch, streaming), os processa através da arquitectura Medallion no Azure Databricks, e os expõe num dashboard analítico.

---

## Arquitectura Geral

```
┌─────────────────────────────────────────────────────────────┐
│                        FONTES                               │
│                                                             │
│  BATCH        Alpha Vantage API → CSV histórico (5 anos)    │
│  MICRO-BATCH  Azure Function (cada 5min) → JSON preço       │
│  STREAMING    Script Python → Azure Event Hubs              │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   ADLS Gen2 (Data Lake)                     │
│                                                             │
│  /bronze/batch/        ← CSV histórico                      │
│  /bronze/api/          ← JSON micro-batch                   │
│  /bronze/streaming/    ← eventos Event Hubs                 │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │ Auto Loader (cloudFiles)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                AZURE DATABRICKS                             │
│                                                             │
│  BRONZE   Raw Delta tables (Auto Loader)                    │
│     ↓     sem transformação, schema inference               │
│                                                             │
│  SILVER   Limpo · Tipado · Deduplicado                      │
│     ↓     DLT / Lakeflow Declarative Pipelines              │
│           + Data Quality Expectations                       │
│                                                             │
│  GOLD     Métricas analíticas                               │
│           · Média móvel 7d e 30d                            │
│           · Volatilidade diária                             │
│           · Volume médio por período                        │
│           · Comparação entre stocks                         │
│                                                             │
│  Orquestração: Lakeflow Jobs                                │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  VISUALIZAÇÃO                               │
│  Power BI (ligação nativa Databricks SQL)                   │
│  ou Databricks SQL Dashboard                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Serviços Azure

| Serviço | Papel | Tier sugerido |
|---|---|---|
| **ADLS Gen2** | Storage central (Data Lake) | Standard LRS |
| **Azure Databricks** | Processamento + Medallion | Trial / Premium |
| **Azure Function** | Chama API cada 5 minutos | Consumption plan |
| **Azure Event Hubs** | Ingestão streaming | Basic |
| **GitHub** | Controlo de versão + CI/CD | Free |

---

## Fonte de Dados

**Alpha Vantage API**
- URL: https://www.alphavantage.co
- Plano: Free (25 chamadas/dia)
- Endpoints utilizados:
  - `TIME_SERIES_DAILY` → histórico CSV (batch)
  - `GLOBAL_QUOTE` → preço actual JSON (micro-batch)
- Stocks alvo: AAPL, MSFT, GOOGL (a definir)

---

## Camadas Medallion em detalhe

### Bronze
- Dados raw sem transformação
- Schema inference automático via Auto Loader
- Particionado por `ingest_date`
- Formato: Delta

### Silver
- Colunas tipadas correctamente
- Duplicados removidos
- Valores nulos tratados
- Coluna `processed_timestamp` adicionada
- Data Quality via DLT Expectations:
  - `price > 0`
  - `volume IS NOT NULL`
  - `symbol IS NOT NULL`

### Gold
- `gold.daily_metrics` — OHLCV diário por stock
- `gold.moving_averages` — médias móveis 7d / 30d
- `gold.volatility` — desvio padrão por período
- `gold.comparison` — comparação entre stocks

---

## Ligação GitHub → Azure / Databricks

```
GitHub (código + notebooks)
    ↓ Git integration
Azure Databricks Repos
    ↓
Notebooks e pipelines versionados
    ↓ CI/CD (GitHub Actions)
Deploy automático para Databricks
```

**Databricks Git Folders** permite ligar directamente o repositório GitHub ao workspace — qualquer commit actualiza o código no Databricks.

---

## Estrutura do Repositório

```
databricks-learning-journey/
└── projects/
    └── 01-financial-stocks-pipeline/
        ├── README.md                  ← este ficheiro
        ├── architecture/
        │   └── architecture.md
        ├── notebooks/
        │   ├── 01_bronze_autoloader.py
        │   ├── 02_silver_dlt.py
        │   └── 03_gold_metrics.py
        ├── pipelines/
        │   └── lakeflow_job.json
        ├── azure_function/
        │   └── function_app.py
        └── streaming/
            └── event_hubs_producer.py
```

---

## Roadmap

- [x] Setup conta Azure + trial
- [x] Criar ADLS Gen2 + container bronze/silver/gold
- [x] Criar Azure Databricks workspace
- [x] Ligar GitHub ao Databricks (Git Folders)
- [x] Ligar o ADLS ao Databricks
    - [x] Criar o Access Connector
    - [x] Dar permissão ao Access Connector no ADLS
    - [x] Ligar o Access Connector ao Databricks
    - [x] Criar o External Location
- [x] Registar Alpha Vantage + obter API key
- [ ] Notebook Bronze — Auto Loader
- [ ] Notebook Silver — DLT + Expectations
- [ ] Notebook Gold — métricas
- [ ] Azure Function — micro-batch
- [ ] Event Hubs — streaming producer
- [ ] Lakeflow Job — orquestração
- [ ] Dashboard — Power BI ou Databricks SQL
- [ ] README final + documentação

---

*Última actualização: Abril 2026*
