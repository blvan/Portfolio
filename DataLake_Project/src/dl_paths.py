# src/dl_paths.py
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_LAKE = PROJECT_ROOT / "data_lake"

BRONZE = DATA_LAKE / "bronze"
SILVER = DATA_LAKE / "silver"
GOLD   = DATA_LAKE / "gold"

TODAY = date.today().isoformat()
