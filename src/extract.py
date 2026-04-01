# =============================================================================
# extract.py — EXTRAÇÃO DE DADOS
# Responsabilidade: apenas ler o CSV e entregar os dados brutos.
# =============================================================================
import pandas as pd

def extract_chunks(file_path: str, chunksize: int):
    """
    Lê o CSV em pedaços (chunks) para não travar a memória.
    Em vez de carregar 12 milhões de linhas de uma vez (~2GB),
    processa 50k linhas por vez (~10MB).

    Retorna um iterador — cada 'next()' entrega um chunk.
    """
    print(f"📥 Abrindo arquivo: {file_path}")

    return pd.read_csv(
        file_path,
        chunksize=chunksize,  # quantas linhas por pedaço
        low_memory=False,     # evita warning de tipos mistos
    )