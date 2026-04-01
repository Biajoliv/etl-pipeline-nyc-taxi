# =============================================================================
# views_sql.py — CONSULTAS SQL COM DUCKDB
# DuckDB permite escrever SQL diretamente nos arquivos Parquet,
# sem precisar carregar tudo na memória como o pandas faz.
# É a ponte entre o ETL local e o BigQuery na cloud.
# =============================================================================

import duckdb
import os

# caminho para os parquets gerados pelo pipeline
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIPS      = os.path.join(BASE_DIR, "data", "processed", "trips.parquet")


def conectar():
    """
    Cria uma conexão DuckDB em memória.
    Não precisa de servidor — funciona como SQLite.
    """
    con = duckdb.connect()

    # registra o parquet como uma tabela virtual chamada 'trips'
    # a partir daqui você escreve SQL como se fosse uma tabela real
    con.execute(f"""
        CREATE VIEW trips AS
        SELECT * FROM read_parquet('{TRIPS}')
    """)

    print("✅ Conexão DuckDB criada | view 'trips' registrada")
    return con


def view_por_hora(con) -> object:
    """Corridas, tarifa e velocidade média por hora do dia."""
    return con.execute("""
        SELECT
            pickup_hour,
            COUNT(*)                    AS total_trips,
            ROUND(AVG(fare_amount), 2)  AS avg_fare,
            ROUND(AVG(avg_speed_mph), 2) AS avg_speed,
            ROUND(AVG(tip_pct), 2)      AS avg_tip_pct
        FROM trips
        GROUP BY pickup_hour
        ORDER BY pickup_hour
    """).df()


def view_por_dia(con) -> object:
    """Receita e volume por dia do mês."""
    return con.execute("""
        SELECT
            pickup_date,
            COUNT(*)                     AS total_trips,
            ROUND(SUM(total_amount), 2)  AS total_revenue,
            ROUND(AVG(total_amount), 2)  AS ticket_medio,
            ROUND(AVG(tip_pct), 2)       AS avg_tip_pct
        FROM trips
        GROUP BY pickup_date
        ORDER BY pickup_date
    """).df()


def view_por_vendor(con) -> object:
    """Comparativo entre fornecedores."""
    return con.execute("""
        SELECT
            VendorID,
            COUNT(*)                     AS total_trips,
            ROUND(SUM(total_amount), 2)  AS total_revenue,
            ROUND(AVG(avg_speed_mph), 2) AS avg_speed,
            ROUND(AVG(tip_pct), 2)       AS avg_tip_pct
        FROM trips
        GROUP BY VendorID
        ORDER BY VendorID
    """).df()


def view_por_turno(con) -> object:
    """Volume e receita por turno do dia."""
    return con.execute("""
        SELECT
            turno,
            COUNT(*)                     AS total_trips,
            ROUND(SUM(total_amount), 2)  AS total_revenue,
            ROUND(AVG(fare_amount), 2)   AS avg_fare,
            ROUND(AVG(tip_pct), 2)       AS avg_tip_pct
        FROM trips
        GROUP BY turno
        ORDER BY total_trips DESC
    """).df()


def view_por_pagamento(con) -> object:
    """Participação e gorjeta por tipo de pagamento."""
    return con.execute("""
        SELECT
            payment_type,
            COUNT(*)                    AS total_trips,
            ROUND(AVG(tip_pct), 2)      AS avg_tip_pct,
            ROUND(SUM(total_amount), 2) AS total_revenue,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_trips
        FROM trips
        GROUP BY payment_type
        ORDER BY total_trips DESC
    """).df()


def view_anomalias(con) -> object:
    """Corridas marcadas como suspeitas."""
    return con.execute("""
        SELECT
            tpep_pickup_datetime,
            trip_distance,
            fare_amount,
            avg_speed_mph,
            tip_pct,
            turno
        FROM trips
        WHERE flag_anomalia = TRUE
        ORDER BY avg_speed_mph DESC
        LIMIT 100
    """).df()


def view_percentis(con) -> object:
    """Distribuição real de duração, distância e tarifa."""
    return con.execute("""
        SELECT
            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP
                (ORDER BY trip_duration_min), 2) AS duracao_p50,
            ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP
                (ORDER BY trip_duration_min), 2) AS duracao_p90,
            ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP
                (ORDER BY trip_duration_min), 2) AS duracao_p95,

            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP
                (ORDER BY trip_distance), 2)     AS distancia_p50,
            ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP
                (ORDER BY trip_distance), 2)     AS distancia_p90,

            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP
                (ORDER BY fare_amount), 2)       AS tarifa_p50,
            ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP
                (ORDER BY fare_amount), 2)       AS tarifa_p90
        FROM trips
    """).df()


# ── Execução direta para testar ───────────────────────────────────────────────

if __name__ == "__main__":
    con = conectar()

    print("\n📊 Por hora:")
    print(view_por_hora(con).to_string(index=False))

    print("\n📅 Por dia:")
    print(view_por_dia(con).head(5).to_string(index=False))

    print("\n🚖 Por vendor:")
    print(view_por_vendor(con).to_string(index=False))

    print("\n🌙 Por turno:")
    print(view_por_turno(con).to_string(index=False))

    print("\n💳 Por pagamento:")
    print(view_por_pagamento(con).to_string(index=False))

    print("\n⚠️ Anomalias (top 5):")
    print(view_anomalias(con).head(5).to_string(index=False))

    print("\n📈 Percentis:")
    print(view_percentis(con).to_string(index=False))

    con.close()