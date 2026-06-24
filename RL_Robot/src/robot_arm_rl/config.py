from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "seed": 42,
    "env": {
        "reward": "dense",
        "max_episode_steps": 50,
        "n_envs": 1,
        "vec_env": "dummy",
        "metrics": {
            "grasp_lift_threshold": 0.03,
            "grasp_distance_threshold": 0.07,
        },
    },
    "algorithm": {
        "name": "PPO",
        "kwargs": {},
        "use_her": False,
        "her": {},
    },
    "train": {
        "total_timesteps": 100_000,
        "checkpoint_freq": 25_000,
        "log_interval": 10,
    },
    "eval": {
        "episodes": 20,
        "deterministic": True,
    },
}


def deep_update(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_update(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    config = deep_update(DEFAULT_CONFIG, raw)
    config["_config_path"] = str(config_path)
    return config


def save_config(config: dict[str, Any], path: str | Path) -> None:
    clean_config = {key: value for key, value in config.items() if not key.startswith("_")}
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(clean_config, handle, sort_keys=False)
