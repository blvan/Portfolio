import duckdb
import os

def _is_adls():
    return bool(os.getenv("ADLS_ACCOUNT") and os.getenv("ADLS_FILESYSTEM") and (os.getenv("ADLS_KEY") or os.getenv("ADLS_SAS")))

def main():
    db_path = os.getenv("WAREHOUSE_PATH", "warehouse.duckdb")
    con = duckdb.connect(db_path)
    if _is_adls():
        # Read from ADLS via pandas (supports globbing with fsspec under the hood)
        import pandas as pd
        storage_opts = {
            "account_name": os.getenv("ADLS_ACCOUNT"),
        }
        if os.getenv("ADLS_KEY"):
            storage_opts["account_key"] = os.getenv("ADLS_KEY")
        if os.getenv("ADLS_SAS"):
            storage_opts["sas_token"] = os.getenv("ADLS_SAS")

        pattern = f"abfs://{os.getenv('ADLS_FILESYSTEM')}/silver/now_playing/load_date=*/part.parquet"
        try:
            df_all = pd.read_parquet(pattern, storage_options=storage_opts)
            con.execute("DROP VIEW IF EXISTS now_playing;")
            con.execute("DROP TABLE IF EXISTS now_playing;")
            con.register("df", df_all)
            con.execute("CREATE OR REPLACE TABLE now_playing AS SELECT * FROM df;")
            print(f"DuckDB table now_playing updated with {len(df_all)} rows")
        except Exception as e:
            # No parquet yet or transient read issue -> create empty table
            print(f"No silver data found or read error ({e}), creating empty table")
            con.execute("DROP VIEW IF EXISTS now_playing;")
            con.execute("DROP TABLE IF EXISTS now_playing;")
            con.execute("CREATE TABLE now_playing (source TEXT, channel TEXT, snapshot_ts TIMESTAMP, started_at TIMESTAMP);")
    else:
        try:
            con.execute("CREATE OR REPLACE VIEW now_playing AS SELECT * FROM read_parquet('data_lake/silver/now_playing/load_date=*/*.parquet');")
            print("DuckDB view now_playing updated")
        except Exception as e:
            print(f"No silver data found or read error ({e}), creating empty view")
            con.execute("CREATE OR REPLACE VIEW now_playing AS SELECT 1 AS dummy WHERE 1=0;")
    # добавь здесь и другие VIEW, если нужно
    con.close()
    print(f"warehouse.duckdb updated at {db_path}")

if __name__ == "__main__":
    main()
