# scripts/now_playing_pull.py
from pathlib import Path
from datetime import datetime, timezone, date
import json, requests, re, os
from src.dl_paths import BRONZE
from src.storage_io import is_adls_enabled, adls_prefix, ensure_dir, open_file, join
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Bratislava")

TIMEOUT = 5        # sec (per source)
RETRIES = 0        # no retries to avoid blocking

def utc_now_iso():
    # No microseconds in snapshot timestamp
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _slug(s: str | None) -> str:
    if not s:
        return "unknown"
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "unknown"

def bronze_file_for(group: str | None, channel: str | None, run_ts: str, today: str):
    team = _slug(group)
    ch = _slug(channel)

    # Map team name to team number
    team_numbers = {
        "ours": "0",
        "team1": "1",
        "team2": "2",
        "team3": "3",
        "team4": "4",
    }
    team_num = team_numbers.get(team, "0")

    if is_adls_enabled():
        base = adls_prefix()
        d = join(base, "bronze", "now_playing", team, ch, f"ingest_date={today}")
        ensure_dir(d)
        return join(d, f"TV{team_num}.{ch}-{run_ts}.jsonl")
    else:
        d = BRONZE / "now_playing" / team / ch / f"ingest_date={today}"
        d.mkdir(parents=True, exist_ok=True)
        return d / f"TV{team_num}.{ch}-{run_ts}.jsonl"

def fetch(src):
    for attempt in range(RETRIES + 1):
        try:
            url = src["url"]
            r = requests.get(url, headers=src.get("headers", {}), timeout=TIMEOUT, stream=True)
            r.raise_for_status()

            # Handle Server-Sent Events (SSE) format with "data: " prefix
            content_type = r.headers.get("content-type", "")
            if "text/event-stream" in content_type or url.startswith("http://3.79.27.222"):
                # SSE stream: read lines, extract JSON after "data: "
                for line in r.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        return json.loads(line[5:].strip())
                raise ValueError("No valid SSE data line found")

            return r.json()
        except Exception as e:
            if attempt == RETRIES:
                raise e

def normalize(src, payload):
    map_fn = src.get("map_fn") or (lambda x: x)
    mapped = map_fn(payload)

    # Handle mappers that return lists (e.g., team2 with multiple stations)
    if isinstance(mapped, list):
        return [
            {
                "source": src["name"],
                "snapshot_ts": utc_now_iso(),
                **rec,  # Include all fields from mapper
                "channel": rec.get("channel") or src.get("channel") or src.get("channel_fallback"),
            }
            for rec in mapped
        ]

    # Single record: merge all fields from mapper
    ch = mapped.get("channel") or src.get("channel") or src.get("channel_fallback")
    return {
        "source": src["name"],
        "snapshot_ts": utc_now_iso(),
        **mapped,  # Include all fields from mapper
        "channel": ch,  # Override channel with fallback if needed
    }

def main():
    # лениво импортируем конфиг источников
    from src.now_playing_sources import SOURCES
    today = date.today().isoformat()
    run_ts = datetime.now(TZ).strftime("%H")  # one file per hour

    # Buffer lines per target file to minimize open/write requests
    buffered: dict[str, list[str]] = {}
    wrote = []
    for src in SOURCES:
        group = src.get("group") or src.get("team") or src["name"]
        try:
            payload = fetch(src)
            records = normalize(src, payload)

            # Handle list of records (multi-station sources)
            if isinstance(records, list):
                for rec in records:
                    out_file = bronze_file_for(group, rec.get("channel"), run_ts, today)
                    buffered.setdefault(str(out_file), []).append(json.dumps(rec, ensure_ascii=False) + "\n")
                    wrote.append(out_file)
            else:
                # Single record
                out_file = bronze_file_for(group, records.get("channel"), run_ts, today)
                buffered.setdefault(str(out_file), []).append(json.dumps(records, ensure_ascii=False) + "\n")
                wrote.append(out_file)
        except Exception as e:
            # лог пишем в каталог команды (без канала)
            log_dir = BRONZE / "now_playing" / _slug(group)
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / f"errors-{today}.log", "a", encoding="utf-8") as lf:
                lf.write(f"{utc_now_iso()} {src['name']}: {e}\n")
    # Flush buffered writes: one open per file per run
    for path_str, lines in buffered.items():
        with open_file(path_str, "a", encoding="utf-8") as f:
            f.write("".join(lines))

    if wrote:
        print("bronze now_playing ->", ", ".join({str(p) for p in wrote}))
    else:
        print("bronze now_playing -> no writes")

    # simple run metric (append one line per run)
    try:
        # metrics and manifest (to avoid heavy globbing later)
        metrics_dir = (
            join(adls_prefix(), "logs", "jobs", "now_playing_pull", f"dt={today}")
            if is_adls_enabled()
            else Path("data_lake/logs/jobs/now_playing_pull") / f"dt={today}"
        )
        ensure_dir(metrics_dir)
        mfile = join(metrics_dir, f"{datetime.now(TZ).strftime('%H')}.jsonl") if is_adls_enabled() else metrics_dir / f"{datetime.now(TZ).strftime('%H')}.jsonl"
        rec = {
            "ts": utc_now_iso(),
            "written_files": len(set(map(str, wrote))),
        }
        with open_file(mfile, "a", encoding="utf-8") as mf:
            mf.write(json.dumps(rec, ensure_ascii=False) + "\n")

        # Append manifest entries with file paths written in this run
        manifest_dir = (
            join(adls_prefix(), "logs", "manifests", "bronze", "now_playing")
            if is_adls_enabled()
            else Path("data_lake/logs/manifests/bronze/now_playing")
        )
        ensure_dir(manifest_dir)
        manifest_file = join(manifest_dir, f"dt={today}.jsonl") if is_adls_enabled() else manifest_dir / f"dt={today}.jsonl"
        with open_file(manifest_file, "a", encoding="utf-8") as mfst:
            for p in sorted(set(map(str, wrote))):
                mfst.write(json.dumps({"path": p, "hour": run_ts, "ts": utc_now_iso()}) + "\n")
    except Exception:
        pass

if __name__ == "__main__":
    main()
