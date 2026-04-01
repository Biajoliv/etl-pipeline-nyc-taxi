# =============================================================================
# load.py — PERSISTÊNCIA EM PARQUET
# Responsabilidade: salvar os dados em disco no formato Parquet.
# Usa PyArrow para suportar append (Parquet não tem append nativo).
# =============================================================================

import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def load_chunk(df: pd.DataFrame, output_path: str, primeiro: bool):
    """
    Grava um chunk em Parquet.
    - Se for o primeiro chunk: cria o arquivo do zero.
    - Se não for: lê o arquivo existente e concatena.

    Isso simula um 'append' já que Parquet não suporta append nativo.
    """
    if df.empty:
        return  # não salva arquivos vazios

    # garante que a pasta existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # converte DataFrame para formato PyArrow
    tabela_nova = pa.Table.from_pandas(df, preserve_index=False)

    if primeiro or not os.path.exists(output_path):
        # primeiro chunk: cria o arquivo
        pq.write_table(tabela_nova, output_path)
    else:
        # chunks seguintes: lê e concatena com o existente
        tabela_existente = pq.read_table(output_path)
        tabela_final     = pa.concat_tables(
            [tabela_existente, tabela_nova],
            promote_options="default"
        )
        pq.write_table(tabela_final, output_path)


def load_gold(gold: dict, base_dir: str):
    """
    Salva cada tabela analítica do gold em um arquivo Parquet separado.
    Cada tabela vira um arquivo: summary.parquet, by_day.parquet, etc.
    """
    pasta = os.path.join(base_dir, "data", "processed")
    os.makedirs(pasta, exist_ok=True)

    for nome, df in gold.items():
        caminho = os.path.join(pasta, f"{nome}.parquet")
        df.to_parquet(caminho, index=False)
        print(f"  💾 Salvo: {caminho}")