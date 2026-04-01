import pandas as pd

def extract(file_path):
    print(f"Lendo: {file_path}")
    return pd.read_csv(file_path, nrows=100_000)