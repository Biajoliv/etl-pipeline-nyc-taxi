# Pipeline de Engenharia de Dados com Dashboard Interativo

## Sobre o Projeto

Este projeto implementa um pipeline completo de engenharia de dados utilizando dados de corridas de táxi de Nova York (NYC Taxi Dataset).

O objetivo é demonstrar um fluxo end-to-end de dados, incluindo:

* Extração de dados em formato CSV
* Transformação e enriquecimento
* Validação de qualidade
* Persistência em formato otimizado (Parquet)
* Geração de métricas agregadas
* Visualização interativa com Streamlit

---

## Arquitetura

O pipeline segue o conceito de Medallion Architecture:

* Bronze (Raw): dados brutos em CSV
* Silver (Processed): dados tratados
* Gold (Analytics): métricas agregadas

Fluxo:

```
Extract → Transform → Validate → Load → Gold → Dashboard
```

---

## Estrutura do Projeto

```
desafio_dados_etl/

data/
  raw/
  processed/

src/
  extract.py
  transform.py
  validate.py
  gold.py
  load.py
  pipeline.py

dashboard/
  dashboard.py
```

---

## Tecnologias Utilizadas

* Python
* Pandas
* NumPy
* PyArrow
* Streamlit
* WSL (Linux)
* VS Code

---

## Persistência em Parquet

Os dados processados são armazenados em formato Parquet, que é otimizado para dados analíticos.

Principais vantagens:

* Armazenamento colunar
* Leitura seletiva de colunas
* Melhor performance em consultas
* Compressão eficiente

Esse formato é amplamente utilizado em pipelines de dados e permite integração com Python, SQL e ferramentas de BI.

---

## Pipeline

### Extract

* Leitura de arquivos CSV
* Uso de amostragem (nrows) para controle de memória

### Transform

* Conversão de datas
* Criação de métricas como duração da corrida

### Validate

* Estrutura preparada para validação de qualidade dos dados

### Load

* Persistência em formato Parquet

### Gold

* Geração de métricas agregadas como total de corridas e receita

---

## Resultados Gerados

```
data/processed/

yellow_tripdata.parquet
metrics.parquet
```

---

## Dashboard

O projeto inclui um dashboard interativo desenvolvido com Streamlit.

Funcionalidades:

* Visualização de métricas principais
* Filtro por distância
* Gráficos simples
* Visualização dos dados

Para executar:

```
streamlit run dashboard/dashboard.py
```

---

## Execução do Pipeline

```
uv pip install -r requirements.txt
uv run src/pipeline.py
```

---

## Diferenciais

* Pipeline ETL completo
* Estrutura modular
* Uso de formato columnar (Parquet)
* Controle de memória com amostragem
* Integração com dashboard
* Base pronta para escalabilidade

---

## Próximos Passos

* Implementar validações avançadas
* Processamento incremental com chunks
* Melhorar visualizações do dashboard
* Integração com data warehouse
* Orquestração com Airflow

---

## Autora

Bianca (Bia)
Engenharia e Análise de Dados
