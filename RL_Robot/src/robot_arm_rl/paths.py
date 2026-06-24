from __future__ import annotations

from datetime import datetime
from pathlib import Path


DEFAULT_RUN_ROOT = Path("artifacts/runs")
DEFAULT_REPORT_ROOT = Path("report")
DEFAULT_COMPARE_REPORT_DIR = DEFAULT_REPORT_ROOT / "Compare"
DEFAULT_PPO_REPORT_DIR = DEFAULT_REPORT_ROOT / "PPO"
DEFAULT_SAC_REPORT_DIR = DEFAULT_REPORT_ROOT / "SAC"
DEFAULT_VIDEO_DIR = DEFAULT_COMPARE_REPORT_DIR / "videos"


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def make_run_dir(experiment_name: str, root: str | Path = DEFAULT_RUN_ROOT) -> Path:
    safe_name = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in experiment_name)
    run_dir = Path(root) / f"{timestamp()}_{safe_name}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir
