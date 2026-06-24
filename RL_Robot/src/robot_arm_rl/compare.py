from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from robot_arm_rl.paths import DEFAULT_COMPARE_REPORT_DIR, DEFAULT_RUN_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare trained robot-arm RL runs.")
    parser.add_argument(
        "--runs-dir",
        default=str(DEFAULT_RUN_ROOT),
        help="Directory containing train.py runs.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_COMPARE_REPORT_DIR),
        help="Directory for comparison outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs_dir = Path(args.runs_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for run_dir in sorted(path for path in runs_dir.glob("*") if path.is_dir()):
        metadata_path = run_dir / "metadata.json"
        if not metadata_path.exists():
            continue

        with metadata_path.open("r", encoding="utf-8") as handle:
            metadata = json.load(handle)

        row: dict[str, Any] = {
            "run": run_dir.name,
            "algorithm": metadata.get("algorithm"),
            "reward": metadata.get("reward"),
            "seed": metadata.get("seed"),
            "total_timesteps": metadata.get("total_timesteps"),
            "train_seconds": metadata.get("train_seconds"),
        }
        row.update(_load_eval_summary(run_dir))
        row.update(_load_monitor_summary(run_dir))
        rows.append(row)

    if not rows:
        raise SystemExit(f"No completed runs found in {runs_dir}")

    df = pd.DataFrame(rows)
    csv_path = output_dir / "comparison.csv"
    df.to_csv(csv_path, index=False)

    plot_path = output_dir / "comparison.png"
    _plot_comparison(df, plot_path)

    print(df.to_string(index=False))
    print(f"Saved {csv_path}")
    print(f"Saved {plot_path}")


def _load_eval_summary(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "eval" / "summary.json"
    if not summary_path.exists():
        return {}
    with summary_path.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    return {f"eval_{key}": value for key, value in summary.items()}


def _load_monitor_summary(run_dir: Path) -> dict[str, Any]:
    monitor_files = sorted((run_dir / "monitor").glob("*.monitor.csv"))
    if not monitor_files:
        return {}

    frames = []
    for monitor_file in monitor_files:
        frames.append(pd.read_csv(monitor_file, comment="#"))
    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        return {}

    df = df.sort_values("t").reset_index(drop=True)
    df["cumulative_timesteps"] = df["l"].cumsum()
    rolling_reward = df["r"].rolling(window=20, min_periods=5).mean()
    summary: dict[str, Any] = {
        "train_episodes": int(len(df)),
        "train_mean_reward": float(df["r"].mean()),
        "train_last20_mean_reward": float(df["r"].tail(20).mean()),
        "train_reward_rolling_std20": float(rolling_reward.std(skipna=True)),
    }
    for column in ("episode_success", "episode_grasp_success", "episode_pick_success"):
        if column in df:
            summary[f"train_{column}_rate"] = float(df[column].mean())
            summary[f"train_last20_{column}"] = float(df[column].tail(20).mean())
            summary[f"train_last100_{column}"] = float(df[column].tail(100).mean())
            first_index = _first_positive_index(df[column])
            if first_index is not None:
                prefix = column.replace("episode_", "first_")
                summary[f"train_{prefix}_episode"] = int(first_index + 1)
                summary[f"train_{prefix}_timestep"] = int(df.loc[first_index, "cumulative_timesteps"])
                summary[f"train_{prefix}_seconds"] = float(df.loc[first_index, "t"])

    if "episode_collision_count" in df:
        summary["train_total_collision_count"] = float(df["episode_collision_count"].sum())
        summary["train_mean_collision_count"] = float(df["episode_collision_count"].mean())
        summary["train_last20_episode_collision_count"] = float(
            df["episode_collision_count"].tail(20).mean()
        )
        summary["train_last100_episode_collision_count"] = float(
            df["episode_collision_count"].tail(100).mean()
        )
    return summary


def _first_positive_index(series: pd.Series) -> int | None:
    positive_indices = series[series > 0].index
    if positive_indices.empty:
        return None
    return int(positive_indices[0])


def _plot_comparison(df: pd.DataFrame, output_path: Path) -> None:
    labels = df["algorithm"].astype(str) + " / " + df["reward"].astype(str)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    _bar(axes[0], labels, df.get("train_seconds"), "Training seconds")
    _bar(axes[1], labels, df.get("eval_goal_success_rate"), "Eval goal success")
    _bar(axes[2], labels, df.get("eval_mean_collision_count"), "Eval collisions")

    for axis in axes:
        axis.tick_params(axis="x", labelrotation=45)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _bar(axis, labels, values, title: str) -> None:
    if values is None:
        values = [0.0] * len(labels)
    axis.bar(labels, values)
    axis.set_title(title)


if __name__ == "__main__":
    main()
