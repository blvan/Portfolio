"""Source definitions and mappers for now_playing ingestion."""
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Bratislava")
UTC = ZoneInfo("UTC")

def _parse_dt_to_utc_iso(date_str: str | None, time_str: str | None) -> str | None:
    if not date_str and not time_str:
        return None
    t = time_str or "00:00:00"
    if len(t) == 5:
        t = f"{t}:00"
    try:
        dt_local = datetime.fromisoformat(f"{date_str}T{t}").replace(tzinfo=TZ)
        return dt_local.astimezone(UTC).replace(microsecond=0).isoformat()
    except Exception:
        return None

def _coerce_to_utc_iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        d = value.get("date") or value.get("day") or value.get("d")
        t = value.get("time") or value.get("start_time") or value.get("t")
        # If only time is provided, assume today in local TZ
        if (not d) and t:
            d = datetime.now(TZ).date().isoformat()
        # Normalize date format: DD-MM-YYYY -> YYYY-MM-DD
        if d and isinstance(d, str) and len(d) == 10 and d[2] == '-' and d[5] == '-':
            try:
                day, month, year = d.split('-')
                d = f"{year}-{month}-{day}"
            except Exception:
                pass
        return _parse_dt_to_utc_iso(d, t)
    if isinstance(value, (int, float)):
        try:
            v = value / 1000.0 if value > 10_000_000_000 else value
            dt = datetime.fromtimestamp(v, tz=TZ)
            return dt.astimezone(UTC).replace(microsecond=0).isoformat()
        except Exception:
            return None
    if isinstance(value, str):
        s = value.strip()
        # DD-MM-YYYY HH:MM format (team2 style)
        if len(s) >= 16 and s[2] == '-' and s[5] == '-' and s[13] == ':':
            try:
                parts = s.split()
                if len(parts) == 2:
                    date_part = parts[0]  # DD-MM-YYYY
                    time_part = parts[1]  # HH:MM
                    day, month, year = date_part.split('-')
                    iso_date = f"{year}-{month}-{day}"
                    return _parse_dt_to_utc_iso(iso_date, time_part)
            except Exception:
                pass
        # некоторые отдают только время -> считаем сегодня локальной датой
        if len(s) in (5, 8) and s[2] == ":":
            today = datetime.now(TZ).date().isoformat()
            return _parse_dt_to_utc_iso(today, s)
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ)
            return dt.astimezone(UTC).replace(microsecond=0).isoformat()
        except Exception:
            return None
    return None

def map_universal_now(r: dict) -> dict:
    """
    Universal mapper for all single-record responses (our team, team1, team3, team4).
    Handles:
    - Our team: {"time": "HH:MM", "title": "...", "year": "...", ...}
    - Team1 (TUKE): {"date": "YYYY-MM-DD", "start_time": "HH:MM", "station_slug": "...", ...}
    - Team3: {"date": "YYYY-MM-DD", "start": "HH:MM", "startDate": "ISO", "channel": "...", "rating": "...", "year": "...", ...}
    - Team4: generic format

    Returns all available fields from source, ensuring channel/title/started_at are normalized.
    """
    if not r or (isinstance(r, dict) and r.get("error")):
        return {}

    # Handle list responses (extract first item)
    rec = None
    if isinstance(r, list):
        for it in r:
            if isinstance(it, dict):
                rec = it
                break
    elif isinstance(r, dict):
        rec = r

    if not isinstance(rec, dict):
        return {}

    # Start with all fields from source
    result = dict(rec)

    # Extract channel from various field names (normalize to 'channel')
    channel = (
        rec.get("channel") or
        rec.get("station") or
        rec.get("station_slug") or
        rec.get("ch") or
        rec.get("channel_name")
    )
    result["channel"] = (channel or "").strip() or None

    # Extract title from various field names (normalize to 'title')
    title = (
        rec.get("title") or
        rec.get("program") or
        rec.get("name") or
        rec.get("current_title") or
        rec.get("title_original") or
        ""
    )
    result["title"] = (title or "").strip() or None

    # Handle time: try direct ISO field first, then construct from date+time
    started = (
        rec.get("startDate") or      # Team3: ready ISO string
        rec.get("started_at") or     # Generic
        rec.get("timeStart")         # Alternative
    )

    if not started:
        # Construct from date + time fields
        date_val = rec.get("date")
        time_val = (
            rec.get("start_time") or  # Team1 (TUKE)
            rec.get("start") or       # Team3 local time
            rec.get("time")           # Our team
        )
        started = {"date": date_val, "time": time_val}

    started_iso = _coerce_to_utc_iso(started)
    result["started_at"] = started_iso

    # Remove duplicate/redundant fields to avoid confusion
    # Keep original field names for reference, but prioritize normalized ones
    cleanup_fields = ["station", "station_slug", "ch", "channel_name", "program", "name",
                      "current_title", "startDate", "timeStart", "start_time", "start"]
    for field in cleanup_fields:
        result.pop(field, None)

    return result

def map_viewership(r: dict) -> dict:
    """
    Universal mapper for viewership data.
    Handles viewership metrics from all sources.
    """
    if not r or (isinstance(r, dict) and r.get("error")):
        return {}

    rec = None
    if isinstance(r, list):
        for it in r:
            if isinstance(it, dict):
                rec = it
                break
    elif isinstance(r, dict):
        rec = r

    if not isinstance(rec, dict):
        return {}

    # Start with all fields from source
    result = dict(rec)

    # Normalize channel
    channel = (
        rec.get("channel") or
        rec.get("station") or
        rec.get("station_slug") or
        rec.get("ch") or
        rec.get("channel_name")
    )
    result["channel"] = (channel or "").strip() or None

    # Normalize title
    title = (
        rec.get("title") or
        rec.get("program") or
        rec.get("name") or
        ""
    )
    result["title"] = (title or "").strip() or None

    # Normalize timestamp
    timestamp = (
        rec.get("timestamp") or
        rec.get("recorded_at") or
        rec.get("measured_at")
    )
    if timestamp:
        result["measured_at"] = _coerce_to_utc_iso(timestamp)

    # Normalize viewership metrics
    viewership = (
        rec.get("viewership") or
        rec.get("viewers") or
        rec.get("audience")
    )
    if viewership:
        result["viewership"] = viewership

    return result

def map_team2_now(r: dict) -> list[dict]:
    """
    Team2 returns nested items structure with multiple stations; return list of records.
    Preserves all available fields from source.
    """
    if not r or not isinstance(r, dict):
        return []
    items = r.get("items") or {}
    records = []
    for station_slug, programs in items.items():
        if isinstance(programs, list) and programs:
            prog = programs[0]  # take first program per station

            # Start with all fields from source
            result = dict(prog)

            # Normalize channel
            channel = prog.get("channel_name") or station_slug
            result["channel"] = channel

            # Ensure title exists
            result["title"] = prog.get("title") or ""

            # Parse started_at
            started = {"date": prog.get("date"), "time": prog.get("time")}
            started_iso = _coerce_to_utc_iso(started)
            result["started_at"] = started_iso

            # Remove redundant fields
            result.pop("channel_name", None)

            records.append(result)
    return records


# Sources: our team (ngrok base), TUKE team, and team4 (may timeout)
SOURCES: list[dict] = [
    # Our team - programs
    {"name": "ours_hbo_3",    "group": "ours", "url": "https://merry-briefly-dinosaur.ngrok-free.app/hbo_3/program",   "headers": {}, "map_fn": map_universal_now, "channel_fallback": "hbo_3"},
    {"name": "ours_cinemax",  "group": "ours", "url": "https://merry-briefly-dinosaur.ngrok-free.app/cinemax/program",  "headers": {}, "map_fn": map_universal_now, "channel_fallback": "cinemax"},
    {"name": "ours_cinemax_2","group": "ours", "url": "https://merry-briefly-dinosaur.ngrok-free.app/cinemax_2/program","headers": {}, "map_fn": map_universal_now, "channel_fallback": "cinemax_2"},

    # team1 generator
    {"name": "tuke_hbo",        "group": "team1",  "url": "http://91.99.234.80:5000/streaming?station=hbo",         "headers": {}, "map_fn": map_universal_now},
    {"name": "tuke_joj_cinema", "group": "team1",  "url": "http://91.99.234.80:5000/streaming?station=joj-cinema",  "headers": {}, "map_fn": map_universal_now},
    {"name": "tuke_film_plus",  "group": "team1",  "url": "http://91.99.234.80:5000/streaming?station=film-plus",   "headers": {}, "map_fn": map_universal_now},

    # Team 2 - separate endpoints per channel, but all return {"items": {...}} format
    {"name": "team2_hbo_2",        "group": "team2", "url": "http://37.9.171.199:8000/now?channel=hbo-2",       "headers": {}, "map_fn": map_team2_now, "channel_fallback": "hbo-2"},
    {"name": "team2_nova_cinema",  "group": "team2", "url": "http://37.9.171.199:8000/now?channel=nova-cinema", "headers": {}, "map_fn": map_team2_now, "channel_fallback": "nova-cinema"},
    {"name": "team2_filmbox",      "group": "team2", "url": "http://37.9.171.199:8000/now?channel=filmbox",     "headers": {}, "map_fn": map_team2_now, "channel_fallback": "filmbox"},

    # Team 3 - per-station endpoints with fallback slugs
    {"name": "team3_dajto",        "group": "team3", "url": "http://18.199.147.163:3000/dajto",         "headers": {}, "map_fn": map_universal_now, "channel_fallback": "dajto"},
    {"name": "team3_prima_sk",     "group": "team3", "url": "http://18.199.147.163:3000/prima-sk",      "headers": {}, "map_fn": map_universal_now, "channel_fallback": "prima-sk"},
    {"name": "team3_markiza_krimi","group": "team3", "url": "http://18.199.147.163:3000/markiza-krimi", "headers": {}, "map_fn": map_universal_now, "channel_fallback": "markiza-krimi"},

    # Team 4 - may timeout; handled by pull TIMEOUT
    {"name": "team4_now",      "group": "team4", "url": "http://dgx.uvt.tuke.sk:5001/now-playing",                   "headers": {}, "map_fn": map_universal_now},

    # ============== VIEWERSHIP DATA ==============
    # Our team - viewership
    {"name": "ours_viewership",   "group": "ours_viewership", "url": "https://merry-briefly-dinosaur.ngrok-free.app/pull", "headers": {}, "map_fn": map_viewership},

    # Team1 - viewership
    {"name": "team1_viewership",  "group": "team1_viewership", "url": "http://91.99.234.80:5000/pull",                    "headers": {}, "map_fn": map_viewership},

    # Team2 - viewership
    {"name": "team2_viewership",  "group": "team2_viewership", "url": "http://37.9.171.199:8000/pull",                     "headers": {}, "map_fn": map_viewership},

    # Team3 - viewership
    {"name": "team3_viewership",  "group": "team3_viewership", "url": "http://18.199.147.163:3000/pull",                    "headers": {}, "map_fn": map_viewership},

    # Team4 - viewership
    {"name": "team4_viewership",  "group": "team4_viewership", "url": "http://dgx.uvt.tuke.sk:5001/pull",                   "headers": {}, "map_fn": map_viewership},
]
