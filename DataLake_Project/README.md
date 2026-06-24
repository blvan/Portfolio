# Television Data Lake

University data engineering project for collecting, normalizing, enriching, and
querying television schedule data from heterogeneous team APIs.

## My contribution

I implemented the `datalake` branch end to end:

- collected now-playing and viewership data from five team API groups;
- normalized incompatible payloads, field names, date formats, and timestamps;
- stored immutable Bronze records as date-partitioned JSONL;
- transformed Bronze data into partitioned Silver Parquet datasets;
- enriched program metadata through TVMaze, OMDb, and TMDB;
- consolidated the result into a Gold Parquet dataset;
- exposed Silver data through DuckDB for SQL analytics;
- containerized and scheduled ingestion and transformation jobs;
- added local filesystem and Azure Data Lake Storage support;
- automated Azure deployment with Container Apps Jobs and persistent storage.

All ten commits in the original `datalake` branch were authored by me.

## Result

- **156,845 rows**
- **44 columns**
- date-partitioned Bronze and Silver layers
- consolidated Gold dataset
- scheduled Docker and Azure Container Apps Jobs
- local and ADLS-compatible storage abstraction

The generated datasets are intentionally excluded from this public portfolio
copy. The repository contains the pipeline code, deployment automation,
architecture documentation, and screenshots.

## Architecture

```text
Team APIs
   |
   v
Bronze: partitioned JSONL
   |
   v
Silver: normalized Parquet partitions
   |                    \
   v                     v
Gold: enriched Parquet   DuckDB / SQL
   |
   v
Analytics-ready dataset
```

## Technology

Python, pandas, PyArrow, Parquet, DuckDB, Docker, cron, Azure Data Lake Storage,
Azure Container Registry, Azure Container Apps Jobs, fsspec/adlfs, REST APIs.

## Main components

- `scripts/now_playing_pull.py` — API ingestion and Bronze JSONL writer.
- `src/now_playing_sources.py` — source-specific schema and timestamp mapping.
- `scripts/now_playing_bronze_to_silver.py` — normalization and Parquet partitioning.
- `scripts/enrich_fast_v4_fixed.py` — metadata enrichment and Gold consolidation.
- `scripts/finalize_gold.py` — canonical schema and type validation.
- `scripts/build_duckdb.py` — DuckDB analytical table/view creation.
- `src/storage_io.py` — transparent local or ADLS-backed file access.
- `azure/` — Azure infrastructure and scheduled job deployment.

## Running locally

Build and start the scheduled container:

```bash
docker compose up --build
```

Or run pipeline stages directly:

```bash
python -m scripts.now_playing_pull
python -m scripts.now_playing_bronze_to_silver
python -m scripts.enrich_fast_v4_fixed
python -m scripts.finalize_gold
python -m scripts.build_duckdb
```

Optional API and Azure credentials must be supplied through environment
variables. No credentials or generated datasets are included in this public
copy.
