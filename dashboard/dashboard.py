import pandas as pd
import streamlit as st
import os

# ==============================
# 📁 CAMINHOS
# ==============================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "yellow_tripdata.parquet")
METRICS_PATH = os.path.join(BASE_DIR, "data", "processed", "metrics.parquet")

# ==============================
# 📥 LOAD
# ==============================

@st.cache_data
def load_data():
    df = pd.read_parquet(DATA_PATH)
    metrics = pd.read_parquet(METRICS_PATH)
    return df, metrics

df, metrics = load_data()

# ==============================
# 🎯 TÍTULO
# ==============================

st.title("🚕 Dashboard - NYC Taxi")

st.markdown("Análise de corridas de táxi com dados tratados em pipeline ETL")

# ==============================
# 📊 MÉTRICAS
# ==============================

st.subheader("📊 Métricas Gerais")

col1, col2 = st.columns(2)

col1.metric("Total de Corridas", int(metrics["total_trips"][0]))
col2.metric("Receita Total", f"${metrics['total_revenue'][0]:,.2f}")

# ==============================
# 🎛️ FILTROS
# ==============================

st.sidebar.header("🔎 Filtros")

min_distance = float(df["trip_distance"].min())
max_distance = float(df["trip_distance"].max())

distance_filter = st.sidebar.slider(
    "Distância",
    min_value=min_distance,
    max_value=max_distance,
    value=(min_distance, max_distance)
)

df_filtered = df[
    (df["trip_distance"] >= distance_filter[0]) &
    (df["trip_distance"] <= distance_filter[1])
]

# ==============================
# 📈 GRÁFICO - DISTÂNCIA
# ==============================

st.subheader("📈 Distribuição de Distância")

st.bar_chart(df_filtered["trip_distance"].value_counts().head(20))

# ==============================
# 📈 GRÁFICO - DURAÇÃO
# ==============================

st.subheader("⏱️ Duração das Corridas")

st.line_chart(df_filtered["trip_duration_min"].head(100))

# ==============================
# 📋 TABELA
# ==============================

st.subheader("📋 Dados")

st.dataframe(df_filtered.head(100))