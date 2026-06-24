# scripts/now_playing_bronze_to_silver.py
from pathlib import Path
from datetime import date
import json, pandas as pd
import pyarrow as pa, pyarrow.parquet as pq
import os
from src.storage_io import is_adls_enabled, adls_prefix, glob as fs_glob, open_file, ensure_dir, join, exists


# Обрабатываем все доступные ingest_date, чтобы не терять данные за дни.
BRONZE_ROOT = Path("datalake/bronze/now_playing")


def _collect_bronze_files_all_dates():
    """Собираем все jsonl в bronze, сгруппированные по ingest_date=YYYY-MM-DD."""
    files_by_dt = {}

    if is_adls_enabled():
        base = adls_prefix()
        # Глобим все ingest_date=* во всех вложенных папках
        patterns = [
            join(base, "bronze", "now_playing", "*", "*", "ingest_date=*", "*.jsonl"),
            join(base, "bronze", "now_playing", "*", "ingest_date=*", "*.jsonl"),
            join(base, "bronze", "now_playing", "ingest_date=*", "*.jsonl"),
        ]
        all_files = []
        for p in patterns:
            all_files.extend(list(fs_glob(p)))
    else:
        all_files = []
        all_files += list(BRONZE_ROOT.glob("*/*/ingest_date=*/*.jsonl"))
        all_files += list(BRONZE_ROOT.glob("*/ingest_date=*/*.jsonl"))
        all_files += list((BRONZE_ROOT / "").glob("ingest_date=*/*.jsonl"))

    for fp in all_files:
        fp_str = str(fp)
        # Ищем подстроку ingest_date=YYYY-MM-DD
        if "ingest_date=" not in fp_str:
            continue
        dt_part = fp_str.split("ingest_date=")[-1].split("/")[0]
        files_by_dt.setdefault(dt_part, []).append(fp)
    return files_by_dt


def _process_date(dt_str: str, files):
    rows = []
    for fp in sorted(files):
        with open_file(fp, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    print(f"[dt={dt_str}] files: {len(files)}, rows: {len(rows)}")
    if not rows:
        return None

    df = pd.DataFrame(rows)
    df["snapshot_ts"] = pd.to_datetime(df.get("snapshot_ts"), utc=True, errors="coerce")
    df["started_at"] = pd.to_datetime(df.get("started_at"), utc=True, errors="coerce")
    # Добавляем dt и load_date, чтобы downstream мог партиционировать
    if "dt" not in df.columns:
        df["dt"] = df["started_at"].dt.date.astype(str)
    # record_date фиксирует дату записи (из started_at) для downstream
    df["record_date"] = df["started_at"].dt.date.astype(str)
    df["load_date"] = dt_str

    # Приводим потенциально строковые числовые поля в nullable-инты
    for col in ["season", "episode", "program_id"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    # Рейтинг оставим как float
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    # Ensure key columns exist (even if empty) for downstream consistency
    for col in ["original_title", "programtype", "year", "season", "episode"]:
        if col not in df.columns:
            df[col] = None

    # ВАЖНО: не дедуплицируем. Сохраняем все 5-минутные строки.
    return df


def main():
    files_by_dt = _collect_bronze_files_all_dates()
    if not files_by_dt:
        print("no bronze files found -> exit"); return

    if is_adls_enabled():
        base = adls_prefix()
    for dt_str, files in sorted(files_by_dt.items()):
        df = _process_date(dt_str, files)
        if df is None:
            continue

        if is_adls_enabled():
            silver_dir = join(base, "silver", "now_playing", f"load_date={dt_str}")
            ensure_dir(silver_dir)
            out_path = join(silver_dir, "part.parquet")
            with open_file(out_path, "wb") as sink:
                pq.write_table(pa.Table.from_pandas(df, preserve_index=False), sink)
            print("silver wrote:", out_path)
        else:
            silver_dir = Path(f"datalake/silver/now_playing/load_date={dt_str}")
            silver_dir.mkdir(parents=True, exist_ok=True)
            pq.write_table(pa.Table.from_pandas(df, preserve_index=False), silver_dir / "part.parquet")
            print("silver wrote:", (silver_dir / "part.parquet").resolve())


if __name__ == "__main__":
    main()
