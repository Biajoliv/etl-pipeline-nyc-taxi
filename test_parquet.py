# =============================================================================
# test_parquet.py — INSPEÇÃO DOS PARQUETS
# Mostra o conteúdo de cada arquivo gerado pelo pipeline.
# Execute com: python test_parquet.py
# =============================================================================

import os
import pandas as pd

PROC = os.path.join(os.path.dirname(__file__), "data", "processed")

arquivos = [
    "summary",
    "by_day",
    "by_hour",
    "by_vendor",
    "by_payment",
    "by_day_of_week",
    "by_week",
    "by_vendor_turno",
    "by_turno_payment",
    "percentis",
    "dq_por_regra",
]

for nome in arquivos:
    path = os.path.join(PROC, f"{nome}.parquet")

    if not os.path.exists(path):
        print(f"\n❌ {nome}.parquet — NÃO ENCONTRADO")
        continue

    df = pd.read_parquet(path)

    print(f"\n{'='*60}")
    print(f"📄 {nome}.parquet")
    print(f"   linhas={len(df)} | colunas={list(df.columns)}")
    print(df.to_string(index=False))