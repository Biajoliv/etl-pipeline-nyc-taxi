# =============================================================================
# transform.py — TRANSFORMAÇÃO DE DADOS
# Responsabilidade: corrigir tipos, criar colunas derivadas e enriquecer
# os dados. NÃO filtra linhas — isso é papel do validate.py.
# =============================================================================

import pandas as pd
import numpy as np

# Feriados federais de janeiro/2015 nos EUA
FERIADOS_JAN_2015 = [
    pd.Timestamp("2015-01-01"),  # Ano Novo
    pd.Timestamp("2015-01-19"),  # MLK Day
]


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe um chunk bruto e retorna com tipos corretos
    e colunas novas prontas para análise.
    """
    print("🔄 Transformando dados...")

    # cada função cuida de uma parte — fácil de debugar
    df = _converter_datas(df)
    df = _criar_metricas_tempo(df)
    df = _criar_metricas_financeiras(df)
    df = _criar_faixas(df)
    df = _criar_turnos(df)
    df = _criar_flags(df)
    df = _enriquecer_calendario(df)
    df = _ajustar_tipos_finais(df)

    return df


# ── DATAS ─────────────────────────────────────────────────────────────────────

def _converter_datas(df: pd.DataFrame) -> pd.DataFrame:
    """
    CSV lê tudo como texto. Aqui convertemos as datas para datetime
    para poder fazer cálculos como duração da corrida.
    errors='coerce' transforma datas inválidas em NaT (nulo de data)
    em vez de travar o pipeline.
    """
    df = df.copy()  # nunca modifique o df original — boa prática

    df["tpep_pickup_datetime"] = pd.to_datetime(
        df["tpep_pickup_datetime"], errors="coerce"
    )
    df["tpep_dropoff_datetime"] = pd.to_datetime(
        df["tpep_dropoff_datetime"], errors="coerce"
    )
    return df


# ── TEMPO ─────────────────────────────────────────────────────────────────────

def _criar_metricas_tempo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria colunas derivadas de tempo:
    duração da corrida, hora, data e dia da semana.
    """
    df = df.copy()

    # duração em minutos = diferença entre chegada e saída
    delta = df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    df["trip_duration_min"] = (delta.dt.total_seconds() / 60).round(2)

    # partes da data — úteis para agrupar nas agregações
    df["pickup_hour"]       = df["tpep_pickup_datetime"].dt.hour
    df["pickup_date"]       = df["tpep_pickup_datetime"].dt.date
    df["pickup_day_of_week"]= df["tpep_pickup_datetime"].dt.day_name()  # Monday, Tuesday...
    df["pickup_week"]       = df["tpep_pickup_datetime"].dt.isocalendar().week.astype(int)

    return df


# ── FINANÇAS ──────────────────────────────────────────────────────────────────

def _criar_metricas_financeiras(df: pd.DataFrame) -> pd.DataFrame:
    """
    Velocidade média e rentabilidade da corrida.
    Usamos replace + where para evitar divisão por zero,
    que quebraria o cálculo e geraria infinito.
    """
    df = df.copy()

    # velocidade: distância / tempo — cuidado com duração zero
    df["avg_speed_mph"] = (
        df["trip_distance"] /
        df["trip_duration_min"].replace(0, np.nan) * 60
    ).fillna(0).round(2)

    # gorjeta como % da tarifa base
    df["tip_pct"] = (
        df["tip_amount"] /
        df["fare_amount"].replace(0, np.nan) * 100
    ).fillna(0).round(2)

    # rentabilidade: quanto gerou por minuto e por milha
    df["revenue_per_min"] = (
        df["total_amount"] /
        df["trip_duration_min"].replace(0, np.nan)
    ).fillna(0).round(2)

    df["revenue_per_mile"] = (
        df["total_amount"] /
        df["trip_distance"].replace(0, np.nan)
    ).fillna(0).round(2)

    return df


# ── FAIXAS ────────────────────────────────────────────────────────────────────

def _criar_faixas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Segmenta distância e duração em categorias para facilitar análise.
    pd.cut divide um valor contínuo em intervalos (bins) com rótulos.
    """
    df = df.copy()

    # faixa de distância
def _criar_faixas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Segmenta distância e duração em categorias para facilitar análise.
    pd.cut divide um valor contínuo em intervalos (bins) com rótulos.
    """
    df = df.copy()

    df["faixa_distancia"] = pd.cut(
        df["trip_distance"],
        bins=[0, 2, 10, float("inf")],
        labels=["curta", "média", "longa"],
        right=True
    ).astype(str)

    df["faixa_duracao"] = pd.cut(
        df["trip_duration_min"],
        bins=[0, 5, 30, float("inf")],
        labels=["muito curta", "normal", "longa"],
        right=True
    ).astype(str)

    return df


# ── TURNOS ────────────────────────────────────────────────────────────────────

def _criar_turnos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Divide o dia em 4 turnos para análise operacional.
    np.select avalia uma lista de condições e retorna o valor
    correspondente à primeira que for verdadeira.
    """
    df = df.copy()

    hora = df["pickup_hour"]

    condicoes = [
        hora.between(0, 5),    # madrugada: 00h–05h
        hora.between(6, 11),   # manhã:     06h–11h
        hora.between(12, 17),  # tarde:     12h–17h
        hora.between(18, 23),  # noite:     18h–23h
    ]
    valores = ["madrugada", "manhã", "tarde", "noite"]

    df["turno"] = np.select(condicoes, valores, default="indefinido")

    return df


# ── FLAGS ─────────────────────────────────────────────────────────────────────

def _criar_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Marca corridas suspeitas com uma flag booleana.
    Combina múltiplas condições para identificar anomalias.
    """
    df = df.copy()

    # corrida suspeita: velocidade alta com tarifa baixa
    df["flag_anomalia"] = (
        (df["avg_speed_mph"] > 60) &   # muito rápido
        (df["fare_amount"]   < 5.0)    # tarifa muito baixa
    )

    return df


# ── CALENDÁRIO ────────────────────────────────────────────────────────────────

def _enriquecer_calendario(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona contexto de calendário: fim de semana e feriado.
    Útil para entender diferenças de comportamento entre dias úteis
    e dias de folga.
    """
    df = df.copy()

    # dayofweek: 0=segunda ... 5=sábado, 6=domingo
    df["is_weekend"] = df["tpep_pickup_datetime"].dt.dayofweek >= 5

    # verifica se a data está na lista de feriados
    df["is_holiday"] = df["tpep_pickup_datetime"].dt.normalize().isin(FERIADOS_JAN_2015)

    return df


# ── TIPOS FINAIS ──────────────────────────────────────────────────────────────

def _ajustar_tipos_finais(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parquet não salva bem o tipo 'date' do Python.
    Convertemos pickup_date para string para evitar erros na leitura.
    Também removemos as colunas de texto originais de timestamp
    pois já temos as versões datetime.
    """
    df = df.copy()

    # converte date para string antes de salvar em parquet
    df["pickup_date"] = df["pickup_date"].astype(str)

    return df