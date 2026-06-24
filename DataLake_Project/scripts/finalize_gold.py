#!/usr/bin/env python3
"""
Final cleanup: ensure all canonical columns are present and properly typed.
Input: datalake/gold/all_teams/TV_data.parquet (from enrich_fast_v4_fixed)
Output: datalake/gold/all_teams/TV_data.parquet (finalized)
"""
import hashlib
from pathlib import Path
import pandas as pd

def canonical_id(row: pd.Series) -> str:
    for key in ["tmdb_id", "program_id", "csfd_id"]:
        if key in row and pd.notna(row[key]) and str(row[key]).strip() not in ("", "Not available", "nan"):
            return str(row[key])
    base = f"{row.get('title','')}-{row.get('year','')}"
    return "gen-" + hashlib.md5(base.encode("utf-8")).hexdigest()[:12]

def ensure_list(val):
    import numpy as np
    if isinstance(val, list):
        return val
    if isinstance(val, (tuple, set)):
        return list(val)
    if isinstance(val, np.ndarray):
        return [v for v in val.tolist() if str(v).strip()]
    try:
        if pd.isna(val):
            return []
    except Exception:
        pass
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    return []

def main():
    src = Path("datalake/gold/all_teams/TV_data.parquet")
    if not src.exists():
        raise SystemExit(f"File not found: {src}")
    df = pd.read_parquet(src)

    print(f"✅ Loaded {len(df):,} rows, {len(df.columns)} columns")
    print(f"   Columns: {list(df.columns)}")

    # Ensure canonical_id exists
    if "canonical_id" not in df.columns:
        df["canonical_id"] = df.apply(canonical_id, axis=1)

    # Ensure all key columns are present and properly typed
    for col in ["original_title", "programtype", "year"]:
        if col not in df.columns:
            df[col] = None

    # Ensure ID columns exist
    for col in ["imdb_id", "tmdb_id", "tvmaze_id", "csfd_id", "program_id"]:
        if col not in df.columns:
            df[col] = None

    # Coerce numeric columns
    df["season"] = df["season"].fillna(1).astype("Int64")
    df["episode"] = df["episode"].fillna(1).astype("Int64")
    df["runtime_minutes"] = df["runtime_minutes"].fillna(50).astype("Int64")

    # Coerce string columns
    for col in ["genre", "program_language", "directors", "writers", "actors", "producers"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str)
        else:
            df[col] = "Unknown"

    # Ensure list columns
    for col in ["cast_names", "cast_roles", "cast_genders", "crew_names", "crew_roles", "crew_genders"]:
        if col not in df.columns:
            df[col] = [[] for _ in range(len(df))]
        else:
            df[col] = df[col].apply(ensure_list)

    # Ensure rating is nullable numeric
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    else:
        df["rating"] = None

    # Ensure description exists
    if "description" not in df.columns:
        df["description"] = ""

    # Final column order
    canonical_cols = [
        "canonical_id",
        "imdb_id", "tmdb_id", "tvmaze_id", "csfd_id", "program_id",
        "dt", "record_date", "source_team", "channel", "title", "original_title", "programtype", "year",
        "season", "episode", "runtime_minutes", "genre", "program_language", "rating",
        "directors", "writers", "actors", "producers",
        "cast_names", "cast_roles", "cast_genders",
        "crew_names", "crew_roles", "crew_genders",
        "description",
    ]

    # Add any extra columns at the end
    extra_cols = [c for c in df.columns if c not in canonical_cols]
    all_cols = [c for c in canonical_cols if c in df.columns] + extra_cols
    df = df[all_cols]

    out = Path("datalake/gold/all_teams/TV_data.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, engine="pyarrow", index=False)
    print(f"\n✅ Saved {out}")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")

    # Validation
    print(f"\n📊 VALIDATION:")
    print(f"   original_title null: {df['original_title'].isna().sum():,}")
    print(f"   programtype null: {df['programtype'].isna().sum():,}")
    print(f"   year null: {df['year'].isna().sum():,}")
    print(f"   rating null: {df['rating'].isna().sum():,} ({100*df['rating'].notna().sum()/len(df):.1f}% populated)")
    print(f"   season unique: {df['season'].nunique()}")
    print(f"   episode unique: {df['episode'].nunique()}")
    print(f"   runtime_minutes unique: {df['runtime_minutes'].nunique()}")
    print(f"   cast_names empty: {(df['cast_names'].apply(len) == 0).sum():,}")
    print(f"   crew_names empty: {(df['crew_names'].apply(len) == 0).sum():,}")
    print(f"\n   ID COLUMNS:")
    print(f"   imdb_id: {df['imdb_id'].notna().sum():,}")
    print(f"   tmdb_id: {df['tmdb_id'].notna().sum():,}")
    print(f"   tvmaze_id: {df['tvmaze_id'].notna().sum():,}")
    print(f"   csfd_id: {df['csfd_id'].notna().sum():,}")
    print(f"   program_id: {df['program_id'].notna().sum():,}")

if __name__ == "__main__":
    main()
