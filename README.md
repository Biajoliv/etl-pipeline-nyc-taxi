# 🚕 NYC Taxi ETL Pipeline

Pipeline ETL para processar o dataset público NYC Yellow Taxi (Jan/2015)
do Kaggle. Projeto desenvolvido no contexto do **Dados por Todos**, com
foco em aprendizado prático de engenharia de dados.

---

## Objetivo

Construir um pipeline completo que:
- Extrai dados brutos de um CSV grande (~12 milhões de linhas)
- Valida a qualidade dos dados com regras de negócio
- Transforma e enriquece os dados com novas métricas
- Persiste em Parquet para análise eficiente
- Visualiza os resultados em um dashboard interativo

---

## Estrutura do projeto
```
desafio_dados_etl/
├── data/
│   ├── raw/                          ← CSV original do Kaggle (nunca modificado)
│   │   └── yellow_tripdata_2015-01.csv
│   └── processed/                    ← saídas geradas pelo pipeline
│       ├── trips.parquet             ← corridas válidas consolidadas
│       ├── bad_rows.parquet          ← registros inválidos para auditoria
│       ├── summary.parquet           ← KPIs gerais do mês
│       ├── by_day.parquet            ← agregação diária
│       ├── by_hour.parquet           ← agregação por hora
│       ├── by_vendor.parquet         ← comparativo por fornecedor
│       ├── by_payment.parquet        ← por tipo de pagamento
│       ├── by_day_of_week.parquet    ← padrão semanal
│       ├── by_week.parquet           ← tendência semanal
│       ├── by_vendor_turno.parquet   ← vendor x turno do dia
│       ├── by_turno_payment.parquet  ← turno x pagamento
│       ├── percentis.parquet         ← P50, P90, P95
│       └── dq_por_regra.parquet      ← score de qualidade
├── src/
│   ├── extract.py                    ← leitura do CSV em chunks
│   ├── transform.py                  ← tipos, colunas derivadas, enriquecimento
│   ├── validate.py                   ← 13 regras de qualidade + score DQ
│   ├── gold.py                       ← métricas e agregações analíticas
│   └── load.py                       ← persistência em Parquet via PyArrow
├── dashboard/
│   └── dashboard.py                  ← dashboard Streamlit com 6 views
├── pipeline.py                       ← orquestrador principal
├── CLAUDE.md                         ← contexto para o Claude Code
├── requirements.txt                  ← dependências do projeto
└── README.md
```

---

## Dataset

**NYC Yellow Taxi Trip Records — Janeiro 2015**

- Fonte: NYC Taxi & Limousine Commission (TLC)
- Kaggle: https://www.kaggle.com/datasets/elemento/nyc-yellow-taxi-trip-data
- Tipo: apenas Yellow Taxis
- Período: janeiro/2015
- Volume: ~12 milhões de corridas

Baixe o arquivo `yellow_tripdata_2015-01.csv` e coloque em `data/raw/`.

---

## Instalação
```bash
# clone o repositório
git clone https://github.com/seu-usuario/desafio-dados-etl.git
cd desafio-dados-etl

# crie e ative o ambiente virtual com uv
uv venv .venv
source .venv/bin/activate        # Linux/Mac/WSL
.venv\Scripts\activate           # Windows

# instale as dependências
uv pip install -r requirements.txt
```

---

## ▶Como executar

### 1. Rodar o pipeline
```bash
python pipeline.py
```

Processa o CSV em chunks de 50.000 linhas para controle de memória.
Ao final imprime o score de qualidade e salva todos os Parquets em
`data/processed/`.

### 2. Abrir o dashboard
```bash
streamlit run dashboard/dashboard.py
```

Acesse em `http://localhost:8501` no navegador.

> **WSL**: o navegador não abre automaticamente.
> Copie e cole o endereço manualmente no navegador do Windows.

---

## Fluxo do pipeline
```
CSV bruto (data/raw/)
        │
        ▼
   extract.py       → lê em chunks com pd.read_csv(chunksize=50k)
        │
        ▼
   transform.py     → converte tipos, cria colunas derivadas
        │
        ▼
   validate.py      → aplica 13 regras → separa válidos e bad_rows
        │
   ┌────┴────┐
   ▼         ▼
trips.parquet  bad_rows.parquet
        │
        ▼ (após loop)
    gold.py          → lê trips.parquet e gera agregações
        │
        ▼
   load.py           → salva cada tabela gold em parquet separado
        │
        ▼
  dashboard.py       → Streamlit lê processed/ e exibe visualizações
```

---

## Regras de validação (`validate.py`)

| Regra | Critério |
|---|---|
| Geográfica | Lat/lon de pickup e dropoff dentro do bbox de NYC |
| Distância | Entre 0.1 e 100 milhas |
| Passageiros | Entre 1 e 6 |
| Tarifa | Entre $2.50 e $500.00 |
| Duração | Entre 1 e 180 minutos |
| Velocidade | Máximo 120 mph |
| Ordem temporal | Dropoff posterior ao pickup |
| Mês de referência | Pickup dentro de janeiro/2015 |
| VendorID | Valores permitidos: {1, 2} |
| Tipo de pagamento | Valores permitidos: {1, 2, 3, 4, 5, 6} |
| Nulos críticos | Sem nulos em datas, distância, tarifa e passageiros |
| Consistência financeira | `total_amount` bate com soma dos componentes |
| Duplicatas | Combinação de datetime + vendor + distância + tarifa |

Cada lote recebe um **score DQ de 0 a 100** com base no percentual de
registros que passam em todas as regras.

---

## Transformações (`transform.py`)

| Coluna criada | Descrição |
|---|---|
| `trip_duration_min` | Duração da corrida em minutos |
| `avg_speed_mph` | Velocidade média em mph |
| `tip_pct` | Gorjeta como % da tarifa base |
| `revenue_per_min` | Receita por minuto de corrida |
| `revenue_per_mile` | Receita por milha percorrida |
| `pickup_hour` | Hora do pickup |
| `pickup_date` | Data do pickup (string para Parquet) |
| `pickup_day_of_week` | Dia da semana |
| `pickup_week` | Número da semana do ano |
| `faixa_distancia` | curta / média / longa |
| `faixa_duracao` | muito curta / normal / longa |
| `turno` | madrugada / manhã / tarde / noite |
| `flag_anomalia` | True se velocidade alta + tarifa baixa |
| `is_weekend` | True se sábado ou domingo |
| `is_holiday` | True se feriado federal |

---

## Tabelas analíticas (`gold.py`)

| Tabela | Descrição |
|---|---|
| `summary` | KPIs gerais do mês (uma linha) |
| `by_day` | Total de corridas e receita por dia |
| `by_hour` | Volume e tarifa por hora do dia |
| `by_vendor` | Comparativo entre fornecedores |
| `by_payment` | Participação por tipo de pagamento |
| `by_day_of_week` | Padrão por dia da semana |
| `by_week` | Tendência e variação semanal |
| `by_vendor_turno` | Performance por vendor e turno |
| `by_turno_payment` | Pagamento por turno do dia |
| `percentis` | P50, P90, P95 de duração, distância e tarifa |
| `dq_por_regra` | Score de qualidade consolidado |

---

## Views do dashboard

| Aba | Conteúdo |
|---|---|
| Por Hora | Picos de demanda e tarifa ao longo do dia |
| Por Fornecedor | Volume, receita e desempenho por vendor |
| Por Pagamento | Participação e gorjeta por forma de pagamento |
| Por Dia da Semana | Padrão semanal de uso |
| Tendência Diária | Evolução diária de corridas e receita |
| Explorar | Filtro por distância + tabela de corridas individuais |

---

## Ajuste de memória (WSL)

O `CHUNKSIZE` padrão é **50.000 linhas (~10 MB por chunk)**.
Se o WSL travar, reduza em `pipeline.py`:
```python
CHUNKSIZE = 25_000   # mais lento, menos memória
CHUNKSIZE = 10_000   # para máquinas muito limitadas
```

Após o loop, o pipeline também chama `gc.collect()` explicitamente
para forçar a liberação de memória — necessário no WSL.

---

## requirements.txt
```
pandas>=2.2,<3
pyarrow>=19.0.0
streamlit>=1.44.1
ipykernel>=7.2.0
```

---

## Stack utilizada

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Processamento | Pandas ≥ 2.2 |
| Serialização | PyArrow ≥ 19.0 |
| Visualização | Streamlit ≥ 1.44 |
| Ambiente | WSL Ubuntu + uv |
| Editor | VS Code + Claude Code |

---

## Conceitos praticados

- Leitura de CSV grande com `chunksize` para controle de memória
- Pipeline modular com separação de responsabilidades por arquivo
- Validação de dados com máscaras booleanas combinadas
- Score de qualidade de dados (DQ score 0–100)
- Quarentena de registros inválidos para auditoria
- Persistência eficiente em Parquet com append via PyArrow
- Camadas de dados: `raw` → `processed`
- Colunas derivadas: faixas, turnos, flags, rentabilidade
- Agregações analíticas com `groupby` e percentis
- Dashboard interativo com múltiplas views em Streamlit

---

## Projeto

Desenvolvido como parte do **Desafio Técnico 02 — ETL Simples com Dados
de Táxi de NYC** do ecossistema **Dados por Todos**.