# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtual environment (WSL/Linux)
source .venv/bin/activate

# Install dependencies
pip install pandas>=2.0 pyarrow>=14.0 streamlit>=1.30

# Run the ETL pipeline (must be run from src/ — imports are relative)
cd src && python pipeline.py

# Run the Streamlit dashboard (from project root)
streamlit run dashboard/dashboard.py

# Quick test to verify parquet output
python test_parquet.py
```

## Architecture

The pipeline is **chunk-based**: it reads `data/raw/yellow_tripdata_2015-01.csv` in 50k-row chunks (`CHUNKSIZE` in `src/pipeline.py`), processes each chunk through Extract → Transform → Validate → Load, then generates analytics aggregations (gold layer) **once** after the full loop completes by reading the consolidated `trips.parquet`.

```
CSV (50k chunks)
  → transform()   # derive 5 columns: trip_duration_min, avg_speed_mph, tip_pct, pickup_hour, pickup_date
  → validate()    # 13 rules; returns (df_valid, df_bad, dq_score)
  → load_chunk()  # append to trips.parquet / bad_rows.parquet
  ↓ (after full loop)
  → create_gold() # reads trips.parquet once; generates summary, by_day, by_hour, by_vendor
  → load_gold()   # saves each gold table as {name}.parquet
```

**Parquet append strategy** (`src/load.py`): there is no native append mode — `load_chunk` reads the existing file, concatenates via `pa.concat_tables`, and rewrites it. For large datasets this gets slow; reduce `CHUNKSIZE` to trade throughput for memory.

**Dashboard dependency**: `dashboard/dashboard.py` reads four parquets from `data/processed/`: `trips`, `summary`, `by_day`, `by_hour`. These must exist (i.e., pipeline must have run successfully) before launching the dashboard.

**DQ score in summary**: `gold._summary` checks for `dq_score_lote` column in `trips.parquet` to populate `dq_score`. This column is only present if `pipeline.py` attaches the per-chunk score back to `chunk_valido` before saving — verify this wiring if `dq_score` shows `None` in the dashboard.

## Key paths

| Path | Purpose |
|------|---------|
| `src/pipeline.py` | Entry point — must be run from `src/` |
| `data/raw/` | Source CSVs (gitignored, never modified) |
| `data/processed/` | All parquet outputs (gitignored) |
| `dashboard/dashboard.py` | Streamlit app |
