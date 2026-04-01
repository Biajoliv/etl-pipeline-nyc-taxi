# =============================================================================
# validate.py — VALIDAÇÃO E QUALIDADE DE DADOS
# Responsabilidade: identificar registros inválidos, separá-los em
# quarentena e calcular um score de qualidade por lote.
# =============================================================================

import pandas as pd

# ── Limites válidos para NYC Taxi jan/2015 ────────────────────────────────────
# Bounding box geográfico de Nova York
NYC_LAT        = (40.4,  40.9)
NYC_LON        = (-74.3, -73.6)

# Faixas plausíveis de negócio
DIST_MI        = (0.1,   100.0)   # milhas
DURATION_MIN   = (1.0,   180.0)   # minutos
FARE_USD       = (2.50,  500.0)   # dólares
SPEED_MAX_MPH  = 120.0            # acima disso é erro de GPS
PAX_MAX        = 6                # máximo de passageiros

# Mês de referência do dataset
MES_REF        = "2015-01"

# Domínios válidos de categorias
VENDOR_IDS     = {1, 2}
PAYMENT_TYPES  = {1, 2, 3, 4, 5, 6}

# Colunas que não podem ter nulos
COLS_CRITICAS  = [
    "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "trip_distance", "fare_amount", "passenger_count"
]


def validate(df: pd.DataFrame):
    """
    Aplica todas as regras de validação e retorna três valores:
    - df_valido: apenas os registros que passaram em tudo
    - df_bad:    registros inválidos para auditoria
    - score:     nota de qualidade de 0 a 100
    """
    print("🔍 Validando dados...")

    total = len(df)

    # cada máscara é True onde a linha é INVÁLIDA
    masks = {
        "geo":        _check_geo(df),
        "distancia":  ~df["trip_distance"].between(*DIST_MI),
        "passageiros":~df["passenger_count"].between(1, PAX_MAX),
        "tarifa":     ~df["fare_amount"].between(*FARE_USD),
        "duracao":    ~df["trip_duration_min"].between(*DURATION_MIN),
        "velocidade":  df["avg_speed_mph"] > SPEED_MAX_MPH,
        "ordem_tempo": df["tpep_dropoff_datetime"] <= df["tpep_pickup_datetime"],
        "mes_ref":     _check_mes(df),
        "vendor":     ~df["VendorID"].isin(VENDOR_IDS),
        "pagamento":  ~df["payment_type"].isin(PAYMENT_TYPES),
        "nulos":       df[COLS_CRITICAS].isnull().any(axis=1),
        "financeiro":  _check_financeiro(df),
        "duplicatas":  df.duplicated(
            subset=["tpep_pickup_datetime", "VendorID",
                    "trip_distance", "fare_amount"],
            keep="first"
        ),
    }

    # combina todas as máscaras com OR:
    # se qualquer regra falhar, a linha é inválida
    mask_invalido = masks["geo"]
    for mask in masks.values():
        mask_invalido = mask_invalido | mask

    # relatório: quantas linhas cada regra rejeitou
    print("  Inválidos por regra:")
    for nome, mask in masks.items():
        print(f"    {nome:15s}: {mask.sum():,}")

    # score = % de linhas válidas no lote
    validos = (~mask_invalido).sum()
    score   = round(validos / total * 100, 2)
    print(f"  Score DQ: {score}/100 ({validos:,} válidos de {total:,})")

    # separa válidos e inválidos
    df_valido         = df[~mask_invalido].copy()
    df_bad            = df[mask_invalido].copy()
    df_valido["dq_score_lote"] = score  # guarda o score no df

    return df_valido, df_bad, score


# ── Funções auxiliares de validação ──────────────────────────────────────────

def _check_geo(df: pd.DataFrame) -> pd.Series:
    """Verifica se pickup e dropoff estão dentro do bbox de NYC."""
    return (
        ~df["pickup_latitude"].between(*NYC_LAT)  |
        ~df["pickup_longitude"].between(*NYC_LON) |
        ~df["dropoff_latitude"].between(*NYC_LAT) |
        ~df["dropoff_longitude"].between(*NYC_LON)
    )


def _check_mes(df: pd.DataFrame) -> pd.Series:
    """Verifica se o pickup está dentro do mês de referência."""
    return (
        df["tpep_pickup_datetime"]
        .dt.to_period("M")
        .astype(str) != MES_REF
    )


def _check_financeiro(df: pd.DataFrame) -> pd.Series:
    """
    Verifica consistência financeira:
    total_amount deve bater com a soma dos componentes.
    Tolerância de $0.10 para arredondamentos.
    """
    total_calculado = (
        df["fare_amount"]           +
        df["extra"]                 +
        df["mta_tax"]               +
        df["tip_amount"]            +
        df["tolls_amount"]          +
        df["improvement_surcharge"]
    )
    return (total_calculado - df["total_amount"]).abs() > 0.10