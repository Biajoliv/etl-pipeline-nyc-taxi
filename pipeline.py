import os
import gc

# imports com prefixo src. — indica que os arquivos estão em src/
from src.extract   import extract_chunks
from src.transform import transform
from src.validate  import validate
from src.gold      import create_gold
from src.load      import load_chunk, load_gold

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
RAW       = os.path.join(BASE_DIR, "data", "raw", "yellow_tripdata_2015-01.csv")
PROC      = os.path.join(BASE_DIR, "data", "processed")
TRIPS_OUT = os.path.join(PROC, "trips.parquet")
BAD_OUT   = os.path.join(PROC, "bad_rows.parquet")
CHUNKSIZE = 50_000

print("🚀 INICIOU PIPELINE (modo chunk)")

total_lidas     = 0
total_validas   = 0
total_invalidas = 0
scores          = []
primeiro_chunk  = True

for i, chunk in enumerate(extract_chunks(RAW, CHUNKSIZE)):
    print(f"\n── chunk {i+1} | {len(chunk):,} linhas ──")

    chunk = transform(chunk)
    chunk_valido, chunk_bad, score = validate(chunk)

    load_chunk(chunk_valido, TRIPS_OUT, primeiro=primeiro_chunk)
    load_chunk(chunk_bad,    BAD_OUT,   primeiro=primeiro_chunk)
    primeiro_chunk = False

    total_lidas     += len(chunk)
    total_validas   += len(chunk_valido)
    total_invalidas += len(chunk_bad)
    scores.append(score)

    del chunk, chunk_valido, chunk_bad
    gc.collect()

print(f"\n✅ Loop concluído")
print(f"   lidas={total_lidas:,} | válidas={total_validas:,} | inválidas={total_invalidas:,}")
print(f"   score médio DQ: {sum(scores)/len(scores):.1f}/100")

gold = create_gold(TRIPS_OUT)
load_gold(gold, BASE_DIR)

print("\n🏁 PIPELINE FINALIZADO")