import pandas as pd

df = pd.read_parquet("data/processed/yellow_tripdata.parquet")

print(df.head())
print(len(df))