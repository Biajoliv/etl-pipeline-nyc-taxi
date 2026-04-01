from extract import extract
from transform import transform
from validate import validate
from load import load, load_gold
from gold import create_gold

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

input_path = os.path.join(BASE_DIR, "data", "raw")
output_path = os.path.join(BASE_DIR, "data", "processed", "yellow_tripdata.parquet")

file = os.path.join(input_path, "yellow_tripdata_2015-01.csv")

print("🚀 INICIOU PIPELINE")

df = extract(file)
print("✅ EXTRACT:", len(df))

df = transform(df)
print("✅ TRANSFORM:", len(df))

df = validate(df)
print("✅ VALIDATE:", len(df))

# GOLD
metrics = create_gold(df)

# SAVE
load(df, output_path)
load_gold(metrics, BASE_DIR)

print("🎉 FINALIZADO")