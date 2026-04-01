# =============================================================================
# dashboard.py — VISUALIZAÇÃO
# Responsabilidade: carregar os Parquets e exibir o dashboard.
# Execute com: streamlit run dashboard/dashboard.py
# =============================================================================

import os
import pandas as pd
import streamlit as st

# ── Caminhos ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC     = os.path.join(BASE_DIR, "data", "processed")


@st.cache_data  # evita recarregar os dados a cada interação
def load_data():
    """Lê todos os Parquets da pasta processed."""
    def read(nome):
        path = os.path.join(PROC, f"{nome}.parquet")
        return pd.read_parquet(path) if os.path.exists(path) else pd.DataFrame()

    return {
        "trips":          read("trips"),
        "summary":        read("summary"),
        "by_day":         read("by_day"),
        "by_hour":        read("by_hour"),
        "by_vendor":      read("by_vendor"),
        "by_payment":     read("by_payment"),
        "by_day_of_week": read("by_day_of_week"),
        "by_week":        read("by_week"),
        "percentis":      read("percentis"),
    }


data = load_data()
s    = data["summary"].iloc[0] if not data["summary"].empty else {}
df   = data["trips"]

st.set_page_config(page_title="NYC Taxi Jan 2015", layout="wide")
st.title("🚕 NYC Taxi — Janeiro 2015")

# ── KPIs ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Corridas",         f"{int(s.get('total_trips', 0)):,}")
col2.metric("Receita total",    f"${s.get('total_revenue', 0):,.0f}")
col3.metric("Distância média",  f"{s.get('avg_distance', 0)} mi")
col4.metric("Duração média",    f"{s.get('avg_duration', 0)} min")
col5.metric("Gorjeta média",    f"{s.get('avg_tip_pct', 0)}%")
col6.metric("Score DQ",         f"{s.get('dq_score', 'N/A')}/100")

st.divider()

# ── Tabs — cada view em uma aba ───────────────────────────────────────────────
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "Por Hora", "Por Fornecedor", "Por Pagamento",
    "Por Dia da Semana", "Tendência Diária", "Explorar"
])

# ── View 1: Por hora ──────────────────────────────────────────────────────────
with aba1:
    st.subheader("Corridas e tarifa por hora do dia")
    if not data["by_hour"].empty:
        st.bar_chart(data["by_hour"].set_index("pickup_hour")["total_trips"])
        st.dataframe(data["by_hour"], use_container_width=True)

# ── View 2: Por fornecedor ────────────────────────────────────────────────────
with aba2:
    st.subheader("Comparativo entre fornecedores")
    if not data["by_vendor"].empty:
        st.bar_chart(data["by_vendor"].set_index("VendorID")["total_revenue"])
        st.dataframe(data["by_vendor"], use_container_width=True)

# ── View 3: Por pagamento ─────────────────────────────────────────────────────
with aba3:
    st.subheader("Participação por tipo de pagamento")
    if not data["by_payment"].empty:
        st.bar_chart(data["by_payment"].set_index("payment_type")["total_trips"])
        st.dataframe(data["by_payment"], use_container_width=True)

# ── View 4: Por dia da semana ─────────────────────────────────────────────────
with aba4:
    st.subheader("Padrão semanal de corridas")
    if not data["by_day_of_week"].empty:
        st.bar_chart(
            data["by_day_of_week"].set_index("pickup_day_of_week")["total_trips"]
        )
        st.dataframe(data["by_day_of_week"], use_container_width=True)

# ── View 5: Tendência diária ──────────────────────────────────────────────────
with aba5:
    st.subheader("Evolução diária de corridas e receita")
    if not data["by_day"].empty:
        st.line_chart(data["by_day"].set_index("pickup_date")["total_trips"])
        st.line_chart(data["by_day"].set_index("pickup_date")["total_revenue"])
        st.dataframe(data["by_day"], use_container_width=True)

# ── View 6: Explorar corridas ─────────────────────────────────────────────────
with aba6:
    st.subheader("Explorar corridas individuais")
    if not df.empty:
        min_d = float(df["trip_distance"].min())
        max_d = float(df["trip_distance"].max())
        dist_range = st.slider("Filtrar por distância (mi)", min_d, max_d, (min_d, 20.0))

        df_f = df[df["trip_distance"].between(*dist_range)]
        st.write(f"{len(df_f):,} corridas nesse range")

        # exibe só colunas que existem no parquet
        colunas = [c for c in [
            "tpep_pickup_datetime", "trip_distance", "fare_amount",
            "passenger_count", "tip_pct", "avg_speed_mph",
            "trip_duration_min", "turno", "faixa_distancia",
            "flag_anomalia", "is_weekend"
        ] if c in df_f.columns]

        st.dataframe(df_f[colunas].head(500), use_container_width=True)

        # percentis
        if not data["percentis"].empty:
            st.subheader("Distribuição real (percentis)")
            st.dataframe(data["percentis"], use_container_width=True)