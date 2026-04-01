import os

def load(df, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_parquet(output_path, index=False)

    print(f"💾 Salvo: {output_path}")


def load_gold(metrics, base_dir):
    output_path = os.path.join(base_dir, "data", "processed", "metrics.parquet")

    metrics.to_parquet(output_path, index=False)

    print("📊 Métricas salvas")