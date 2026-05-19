# Setup Infraestrutura Azure — Market Pulse Pipeline
**Data:** Abril 2026  
**Estado:** ✅ Concluído

---

## Resumo do que foi criado

| Recurso | Nome | Estado |
|---|---|---|
| Resource Group | `rg-market-pulse-pipeline` | ✅ |
| Storage Account (ADLS Gen2) | `marketpulsedatalake` | ✅ |
| Containers Medallion | `bronze` / `silver` / `gold` | ✅ |
| Azure Databricks Workspace | `market-pulse-databricks` | ✅ |
| Access Connector | `market-pulse-connector` | ✅ |
| Key Vault | `mktpulse-kv` | ✅ |
| Secret Scope | `market-pulse-secrets` | ✅ |
| Secret | `alphavantage-api-key` | ✅ |

---

## Passo 1 — Criar conta Azure

1. Vai a [portal.azure.com](https://portal.azure.com)
2. Clica em **"Start free"**
3. Activa o trial — €200 de créditos por 30 dias

---

## Passo 2 — Criar o Resource Group

1. Pesquisa **"Resource groups"** no portal
2. Clica em **"+ Criar"**

| Campo | Valor |
|---|---|
| Subscription | Azure subscription 1 |
| Resource group | `rg-market-pulse-pipeline` |
| Region | (Europe) West Europe |

---

## Passo 3 — Criar o ADLS Gen2

1. Pesquisa **"Storage accounts"** no portal
2. Clica em **"+ Criar"** — escolhe a versão **não clássica**

| Campo | Valor |
|---|---|
| Resource group | `rg-market-pulse-pipeline` |
| Storage account name | `marketpulsedatalake` |
| Region | (Europe) West Europe |
| Performance | Standard |
| Redundancy | LRS |

3. No separador **"Advanced"**:
   - **Hierarchical namespace** → **Enable** ✅ ← transforma em ADLS Gen2

---

## Passo 4 — Criar os containers Medallion

1. Vai ao recurso `marketpulsedatalake`
2. Menu lateral → **"Containers"**
3. Cria 3 containers com **Public access level: Private**:

| Container | Propósito |
|---|---|
| `bronze` | Dados raw — imutável, append-only |
| `silver` | Dados limpos e validados |
| `gold` | Métricas e agregações finais |

> **Nota:** O Bronze é sagrado — nunca é alterado. É o sistema of record do Data Lake.

---

## Passo 5 — Criar o Azure Databricks Workspace

1. Pesquisa **"Azure Databricks"** no portal
2. Clica em **"+ Criar"**

| Campo | Valor |
|---|---|
| Resource group | `rg-market-pulse-pipeline` |
| Workspace name | `market-pulse-databricks` |
| Region | (Europe) West Europe |
| Pricing tier | **Premium** ← obrigatório para Unity Catalog e DLT |

3. Aguarda 3-5 minutos
4. Clica em **"Launch Workspace"** para abrir o workspace

> **Nota:** O Azure Databricks tem URL própria (`adb-XXXXX.azuredatabricks.net`) — não é acessível via community.cloud.databricks.com

---

## Passo 6 — Ligar o GitHub ao Databricks

1. No workspace Databricks → canto superior direito → **Settings**
2. **Linked accounts** → **"Add Git credential"**
3. Git provider: **GitHub**
4. Escolhe **"Link Git account"**
5. Clica **"Link"** e autoriza no GitHub
6. Vai a **Workspace → Repos → Add repo**
7. Cola o URL: `https://github.com/martalimas/market-pulse-pipeline`
8. Clica **"Create Repo"**
9. Instala a **Databricks GitHub App** no repositório quando pedido
10. Testa com **"Pull"** — deve ser bem sucedido

---

## Passo 7 — Criar o Access Connector

1. Pesquisa **"Access Connector for Azure Databricks"** no portal
2. Clica em **"+ Criar"**

| Campo | Valor |
|---|---|
| Resource group | `rg-market-pulse-pipeline` |
| Name | `market-pulse-connector` |
| Region | (Europe) West Europe |

---

## Passo 8 — Dar permissão ao Access Connector no ADLS

1. Vai ao recurso `marketpulsedatalake`
2. **Access Control (IAM)** → **"+ Add"** → **"Add role assignment"**
3. Role: **Storage Blob Data Contributor**
4. Assign access to: **Managed identity**
5. Selecciona: **Access Connector for Azure Databricks** → `market-pulse-connector`

---

## Passo 9 — Criar a Storage Credential no Databricks

1. No Databricks → **Catalog** → **External data** → **Credentials**
2. Clica em **"Create credential"**

| Campo | Valor |
|---|---|
| Credential type | Azure Managed Identity |
| Credential name | `market-pulse-credential` |
| Access connector ID | Resource ID do `market-pulse-connector` |

---

## Passo 10 — Criar o External Location

1. **Catalog** → **External data** → **External Locations**
2. Clica em **"Create external location"**

| Campo | Valor |
|---|---|
| External location name | `market-pulse-storage` |
| URL | `abfss://bronze@marketpulsedatalake.dfs.core.windows.net/` |
| Storage credential | `market-pulse-credential` |

3. Clica **"Create"** — se aparecer warning de File Events, clica **"Force create"**
4. Validação esperada: ✅ Read, ✅ List, ✅ Write, ✅ Delete, ✅ Hierarchical Namespace

---

## Passo 11 — Testar a ligação Databricks ↔ ADLS

No Databricks, cria um notebook e corre:

```python
# Testar acesso ao ADLS
files = dbutils.fs.ls("abfss://bronze@marketpulsedatalake.dfs.core.windows.net/")
for f in files:
    print(f)
```

Resultado esperado: lista vazia sem erros ✅

---

## Passo 12 — Criar o Azure Key Vault

1. Pesquisa **"Key vaults"** no portal
2. Clica em **"+ Criar"**

| Campo | Valor |
|---|---|
| Resource group | `rg-market-pulse-pipeline` |
| Key vault name | `mktpulse-kv` |
| Region | West Europe |
| Pricing tier | Standard |

---

## Passo 13 — Dar permissões no Key Vault

### À tua conta (para gerir secrets):
1. `mktpulse-kv` → **Access Control (IAM)** → **Add role assignment**
2. Role: **Key Vault Secrets Officer**
3. Assign to: o teu email `martalimas@gmail.com`

### Ao AzureDatabricks (para ler secrets):
1. `mktpulse-kv` → **Access Control (IAM)** → **Add role assignment**
2. Role: **Key Vault Secrets User**
3. Assign to: **Service principal** → pesquisa `AzureDatabricks`

---

## Passo 14 — Criar o Secret Scope no Databricks

1. No browser vai a:
```
https://adb-XXXXXXXX.azuredatabricks.net/#secrets/createScope
```

| Campo | Valor |
|---|---|
| Scope name | `market-pulse-secrets` |
| DNS Name | URI do Key Vault (ex: `https://mktpulse-kv.vault.azure.net/`) |
| Resource ID | Resource ID do Key Vault |

---

## Passo 15 — Guardar a API key no Key Vault

1. Vai ao `mktpulse-kv` → **Secrets**
2. Clica **"+ Generate/Import"**

| Campo | Valor |
|---|---|
| Upload options | Manual |
| Name | `alphavantage-api-key` |
| Secret value | a tua API key da Alpha Vantage |

---

## Passo 16 — Testar o Secret no Databricks

No notebook corre:

```python
api_key = dbutils.secrets.get(scope="market-pulse-secrets", key="alphavantage-api-key")
print("API key carregada:", api_key[:5] + "****")
```

Resultado esperado: `API key carregada: XXXXX****` ✅

---

## Arquitectura final da infraestrutura

```
GitHub (market-pulse-pipeline)
        ↕ Git Folders
Azure Databricks (market-pulse-databricks)
        ↕ Access Connector + Storage Credential
ADLS Gen2 (marketpulsedatalake)
    ├── bronze/
    ├── silver/
    └── gold/

Azure Key Vault (mktpulse-kv)
    └── alphavantage-api-key
        ↕ Secret Scope
Azure Databricks
```

---

## Próximos passos

- [ ] Notebook Bronze — chamar Alpha Vantage API e guardar no ADLS
- [ ] Auto Loader — detectar ficheiros novos no bronze
- [ ] Notebook Silver — DLT + Data Quality Expectations
- [ ] Notebook Gold — métricas e agregações
- [ ] Azure Function — micro-batch cada 5 minutos
- [ ] Event Hubs — streaming producer
- [ ] Lakeflow Jobs — orquestração
- [ ] Dashboard — Power BI ou Databricks SQL

---
# Error Handling & Retry Patterns
**market-pulse-pipeline · Stage 3**

---

## O problema

A maioria dos erros em pipelines de dados são **temporários**:

```
Rate limit da API    → espera uns segundos → resolve
Timeout de rede      → tenta de novo → resolve
Serviço indisponível → espera → resolve
```

Sem retry, um erro temporário mata o pipeline inteiro. Com retry, o pipeline recupera sozinho.

---

## Exponential Backoff

```
Tentativa 1 falhou → espera 1s  → tenta de novo
Tentativa 2 falhou → espera 2s  → tenta de novo
Tentativa 3 falhou → espera 4s  → tenta de novo
Tentativa 4 falhou → desiste
```

Cada retry espera o **dobro** do anterior — dá tempo ao sistema externo (API, rede) de recuperar.

**Porquê não esperar sempre o mesmo tempo?**

```
Espera fixa de 5s:
  Rate limit → espera 5s → ainda em rate limit → espera 5s → ainda...
  Pode nunca resolver se o problema persistir

Exponential backoff:
  Rate limit → espera 1s → espera 2s → espera 4s → provavelmente resolvido
  Progressivamente mais paciente — resolve a maioria dos problemas temporários
```

**Fórmula:**
```
espera = base_delay * (2 ** tentativa)

tentativa 0 → 1 * 2^0 = 1s
tentativa 1 → 1 * 2^1 = 2s
tentativa 2 → 1 * 2^2 = 4s
tentativa 3 → 1 * 2^3 = 8s
```

---

## Tipos de erro — nem todos merecem retry

```
Rate limit      → RETRY com backoff (temporário, vai resolver)
Timeout de rede → RETRY com backoff (temporário, vai resolver)
Stock inválido  → SKIP imediatamente (permanente, retry não adianta)
API key inválida→ FAIL imediatamente (configuração errada, retry não resolve)
```

Fazer retry num erro permanente é desperdiçar tempo e requests.

---

## Os 4 pilares do Error Handling robusto

**1. Retry automático com backoff**
```python
→ se AAPL falhou por rate limit, tenta de novo 3x antes de desistir
→ cada tentativa espera o dobro da anterior
```

**2. Tipos de erro diferentes**
```python
→ rate limit      → espera e retry
→ stock inválido  → skip imediatamente
→ network error   → retry com backoff
→ API key inválida → fail imediatamente (não adianta retry)
```

**3. Alertas**
```python
→ se mais de X stocks falharam → envia notificação
→ em produção: email, Slack, PagerDuty
→ no portfólio: log de WARNING na tabela de observabilidade
```

**4. Resultado estruturado**
```python
→ em vez de só lista de erros, devolve relatório detalhado:
  {
    "total": 6,
    "succeeded": 5,
    "failed": 1,
    "errors": [{"symbol": "EDP.LS", "attempts": 3, "error": "rate limit"}]
  }
```

---

## Retry a dois níveis

Em produção há retry em dois níveis diferentes:

| Nível | Responsável | Scope | Quando usar |
|---|---|---|---|
| Task retry | Databricks Lakeflow Job | Notebook inteiro | Falha catastrófica do notebook |
| Stock retry | Código Python | Stock individual | Erro temporário num stock específico |

```
Retry do Job (Databricks nativo):
  Notebook falha completamente → Job tenta de novo o notebook inteiro
  → todos os stocks recomeçam do zero

Retry por stock (código Python):
  AAPL falha → retry só o AAPL → os outros 5 continuam
  → mais eficiente, não repete o que já funcionou
```

Para poucos stocks (6) o retry do Job é suficiente.
Para centenas de stocks em produção, o retry por stock é essencial.

---

## Implementação — Python

```python
import time

def fetch_with_retry(
    symbol: str,
    api_key: str,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> dict:
    """
    Fetches stock data with exponential backoff retry.
    Distinguishes between retryable and non-retryable errors.
    """
    for attempt in range(max_retries + 1):
        try:
            return fetch_stock(symbol, api_key)

        except ValueError as e:
            error_msg = str(e)

            # Rate limit → retryable
            if "Rate limit" in error_msg:
                if attempt < max_retries:
                    wait = base_delay * (2 ** attempt)
                    logging.warning(f"Rate limit for {symbol}, retry {attempt+1}/{max_retries} in {wait}s")
                    time.sleep(wait)
                    continue

            # Invalid symbol → not retryable
            if "API error" in error_msg:
                raise  # fail immediately

            raise  # other errors — fail

    raise ValueError(f"Max retries exceeded for {symbol}")
```

---

## Em produção — bibliotecas especializadas

Em empresas grandes usam bibliotecas dedicadas:

```python
# tenacity — retry library
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def fetch_stock_with_retry(symbol, api_key):
    return fetch_stock(symbol, api_key)
```

O decorator `@retry` elimina o boilerplate — declaras o comportamento, a biblioteca trata do resto.

*Última actualização: Abril 2026*