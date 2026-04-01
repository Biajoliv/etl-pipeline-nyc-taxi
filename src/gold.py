# =============================================================================
# gold.py — MÉTRICAS E AGREGAÇÕES
# Responsabilidade: transformar dados limpos em tabelas analíticas
# prontas para o dashboard. Roda UMA vez após o loop de chunks.
# =============================================================================

import pandas as pd
import numpy as np


def create_gold(trips_path: str) -> dict:
    """
    Lê o parquet consolidado e gera todas as tabelas analíticas.
    Retorna um dicionário: nome -> DataFrame.
    """
    print("\n📊 Gerando gold...")
    df = pd.read_parquet(trips_path)
    print(f"  {len(df):,} linhas carregadas")

    gold = {
        "summary":          _summary(df),
        "by_day":           _by_day(df),
        "by_hour":          _by_hour(df),
        "by_vendor":        _by_vendor(df),
        "by_payment":       _by_payment(df),
        "by_day_of_week":   _by_day_of_week(df),
        "by_week":          _by_week(df),
        "by_vendor_turno":  _by_vendor_turno(df),
        "by_turno_payment": _by_turno_payment(df),
        "percentis":        _percentis(df),
        "dq_por_regra":     _dq_por_regra(df),
    }

    for nome, tabela in gold.items():
        print(f"  {nome}: {len(tabela)} linhas")

    return gold


# ── Visão geral ───────────────────────────────────────────────────────────────

def _summary(df: pd.DataFrame) -> pd.DataFrame:
    """KPIs gerais do mês — uma linha só."""
    return pd.DataFrame([{
        "total_trips":     len(df),
        "total_revenue":   round(df["total_amount"].sum(), 2),
        "avg_distance":    round(df["trip_distance"].mean(), 2),
        "avg_fare":        round(df["fare_amount"].mean(), 2),
        "avg_duration":    round(df["trip_duration_min"].mean(), 2),
        "avg_speed":       round(df["avg_speed_mph"].mean(), 2),
        "avg_tip_pct":     round(df["tip_pct"].mean(), 2),
        "avg_rev_per_min": round(df["revenue_per_min"].mean(), 2),
        "avg_rev_per_mile":round(df["revenue_per_mile"].mean(), 2),
        "pct_card":        round((df["payment_type"] == 1).mean() * 100, 2),
        "pct_weekend":     round(df["is_weekend"].mean() * 100, 2),
        "dq_score":        round(df["dq_score_lote"].mean(), 2)
                           if "dq_score_lote" in df.columns else None,
    }])


# ── Por dia ───────────────────────────────────────────────────────────────────

def _by_day(df: pd.DataFrame) -> pd.DataFrame:
    """Evolução diária — base do gráfico de linha no dashboard."""
    return (
        df.groupby("pickup_date")
        .agg(
            total_trips   =("trip_distance",     "count"),
            total_revenue =("total_amount",      "sum"),
            ticket_medio  =("total_amount",      "mean"),
            avg_distance  =("trip_distance",     "mean"),
            avg_duration  =("trip_duration_min", "mean"),
            avg_tip_pct   =("tip_pct",           "mean"),
        )
        .round(2).reset_index()
    )


# ── Por hora ──────────────────────────────────────────────────────────────────

def _by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Padrão horário — identifica picos de demanda."""
    return (
        df.groupby("pickup_hour")
        .agg(
            total_trips  =("trip_distance",     "count"),
            avg_fare     =("fare_amount",        "mean"),
            avg_duration =("trip_duration_min",  "mean"),
            avg_speed    =("avg_speed_mph",       "mean"),
            avg_tip_pct  =("tip_pct",            "mean"),
        )
        .round(2).reset_index()
    )


# ── Por fornecedor ────────────────────────────────────────────────────────────

def _by_vendor(df: pd.DataFrame) -> pd.DataFrame:
    """Comparativo entre vendors."""
    return (
        df.groupby("VendorID")
        .agg(
            total_trips   =("trip_distance",      "count"),
            total_revenue =("total_amount",       "sum"),
            avg_tip_pct   =("tip_pct",            "mean"),
            avg_speed     =("avg_speed_mph",       "mean"),
            avg_duration  =("trip_duration_min",   "mean"),
        )
        .round(2).reset_index()
    )


# ── Por pagamento ─────────────────────────────────────────────────────────────

def _by_payment(df: pd.DataFrame) -> pd.DataFrame:
    """Participação por tipo de pagamento."""
    total = len(df)
    return (
        df.groupby("payment_type")
        .agg(
            total_trips  =("trip_distance",  "count"),
            total_revenue=("total_amount",   "sum"),
            avg_tip_pct  =("tip_pct",        "mean"),
        )
        .round(2)
        .reset_index()
        # % de participação em corridas
        .assign(pct_trips=lambda x: (x["total_trips"] / total * 100).round(2))
    )


# ── Por dia da semana ─────────────────────────────────────────────────────────

def _by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """Padrão semanal — seg a dom."""
    ordem = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    return (
        df.groupby("pickup_day_of_week")
        .agg(
            total_trips  =("trip_distance",     "count"),
            total_revenue=("total_amount",      "sum"),
            avg_fare     =("fare_amount",        "mean"),
            avg_tip_pct  =("tip_pct",           "mean"),
        )
        .round(2).reset_index()
        .assign(ordem=lambda x: x["pickup_day_of_week"].map(
            {d: i for i, d in enumerate(ordem)}
        ))
        .sort_values("ordem").drop(columns="ordem")
    )


# ── Por semana ────────────────────────────────────────────────────────────────

def _by_week(df: pd.DataFrame) -> pd.DataFrame:
    """Tendência e variação semanal."""
    return (
        df.groupby("pickup_week")
        .agg(
            total_trips  =("trip_distance",  "count"),
            total_revenue=("total_amount",   "sum"),
            ticket_medio =("total_amount",   "mean"),
            avg_tip_pct  =("tip_pct",        "mean"),
        )
        .round(2).reset_index()
    )


# ── Por vendor + turno ────────────────────────────────────────────────────────

def _by_vendor_turno(df: pd.DataFrame) -> pd.DataFrame:
    """Performance operacional por fornecedor e turno do dia."""
    return (
        df.groupby(["VendorID", "turno"])
        .agg(
            total_trips  =("trip_distance",     "count"),
            total_revenue=("total_amount",      "sum"),
            avg_speed    =("avg_speed_mph",      "mean"),
            avg_tip_pct  =("tip_pct",           "mean"),
        )
        .round(2).reset_index()
    )


# ── Por turno + pagamento ─────────────────────────────────────────────────────

def _by_turno_payment(df: pd.DataFrame) -> pd.DataFrame:
    """Como o método de pagamento muda ao longo do dia."""
    return (
        df.groupby(["turno", "payment_type"])
        .agg(
            total_trips  =("trip_distance", "count"),
            avg_tip_pct  =("tip_pct",       "mean"),
        )
        .round(2).reset_index()
    )


# ── Percentis ─────────────────────────────────────────────────────────────────

def _percentis(df: pd.DataFrame) -> pd.DataFrame:
    """
    P50, P90, P95 de duração, distância e tarifa.
    Percentis mostram a distribuição real — média pode esconder outliers.
    """
    cols = ["trip_duration_min", "trip_distance", "fare_amount"]
    rows = []
    for col in cols:
        rows.append({
            "coluna": col,
            "p50":    round(df[col].quantile(0.50), 2),
            "p90":    round(df[col].quantile(0.90), 2),
            "p95":    round(df[col].quantile(0.95), 2),
        })
    return pd.DataFrame(rows)


# ── Qualidade por regra ───────────────────────────────────────────────────────

def _dq_por_regra(df: pd.DataFrame) -> pd.DataFrame:
    """
    Percentual de registros válidos por regra de validação.
    Útil para monitorar quais regras rejeitam mais dados.
    """
    # Como os dados já estão limpos aqui, mostramos o score geral
    score = df["dq_score_lote"].mean() if "dq_score_lote" in df.columns else 100.0
    return pd.DataFrame([{
        "score_medio": round(score, 2),
        "total_validos": len(df),
    }])