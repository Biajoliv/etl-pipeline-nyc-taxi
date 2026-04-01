import os
import duckdb
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIPS    = os.path.join(BASE_DIR, "data", "processed", "trips.parquet")


@st.cache_data
def query(sql: str):
    """Executa SQL direto no Parquet via DuckDB."""
    con = duckdb.connect()
    con.execute(f"CREATE VIEW trips AS SELECT * FROM read_parquet('{TRIPS}')")
    resultado = con.execute(sql).df()
    con.close()
    return resultado


@st.cache_data
def load_summary():
    return query("""
        SELECT
            COUNT(*)                     AS total_trips,
            ROUND(SUM(total_amount), 2)  AS total_revenue,
            ROUND(AVG(trip_distance), 2) AS avg_distance,
            ROUND(AVG(dq_score_lote), 2) AS dq_score
        FROM trips
    """)


st.set_page_config(page_title="NYC Taxi Jan 2015", layout="wide")
st.title("🚕 NYC Taxi — Janeiro 2015")

# ── KPIs ──────────────────────────────────────────────────────────────────────
s = load_summary().iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total corridas",  f"{int(s['total_trips']):,}")
col2.metric("Receita total",   f"${s['total_revenue']:,.0f}")
col3.metric("Distância média", f"{s['avg_distance']} mi")
col4.metric("Score DQ",        f"{s['dq_score']}/100")

st.divider()

# ── Gráficos via SQL ──────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Corridas por hora")
    df_hora = query("""
        SELECT pickup_hour, COUNT(*) AS total_trips
        FROM trips GROUP BY pickup_hour ORDER BY pickup_hour
    """)
    st.bar_chart(df_hora.set_index("pickup_hour")["total_trips"])

with col_b:
    st.subheader("Corridas por dia da semana")
    df_semana = query("""
        SELECT pickup_day_of_week, COUNT(*) AS total_trips
        FROM trips GROUP BY pickup_day_of_week
    """)
    st.bar_chart(df_semana.set_index("pickup_day_of_week")["total_trips"])

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Receita por fornecedor")
    df_vendor = query("""
        SELECT VendorID, ROUND(SUM(total_amount), 2) AS total_revenue
        FROM trips GROUP BY VendorID ORDER BY VendorID
    """)
    st.bar_chart(df_vendor.set_index("VendorID")["total_revenue"])

with col_d:
    st.subheader("Corridas por pagamento")
    df_pag = query("""
        SELECT payment_type, COUNT(*) AS total_trips
        FROM trips GROUP BY payment_type ORDER BY payment_type
    """)
    st.bar_chart(df_pag.set_index("payment_type")["total_trips"])

st.divider()

st.subheader("Evolução diária de corridas")
df_dia = query("""
    SELECT pickup_date, COUNT(*) AS total_trips
    FROM trips GROUP BY pickup_date ORDER BY pickup_date
""")
st.line_chart(df_dia.set_index("pickup_date")["total_trips"])