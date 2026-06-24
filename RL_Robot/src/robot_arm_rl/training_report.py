from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from robot_arm_rl.paths import DEFAULT_COMPARE_REPORT_DIR, DEFAULT_RUN_ROOT


REWARD_COMPONENT_COLUMNS = {
    "goal distance": "episode_reward_goal_distance_mean",
    "gripper distance": "episode_reward_gripper_distance_mean",
    "lift": "episode_reward_lift_mean",
    "height overshoot": "episode_reward_height_overshoot_mean",
    "success bonus": "episode_reward_success_bonus_mean",
    "action penalty": "episode_reward_action_penalty_mean",
    "collision penalty": "episode_reward_collision_penalty_mean",
}

STAGE_COLUMNS = {
    "reach": "episode_stage_reach_fraction",
    "grasp": "episode_stage_grasp_fraction",
    "transport": "episode_stage_transport_fraction",
    "success": "episode_stage_success_fraction",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build richer learning-process reports from monitor/eval logs."
    )
    parser.add_argument(
        "--runs-dir",
        nargs="+",
        default=[str(DEFAULT_RUN_ROOT)],
        help="One or more directories containing training run folders.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_COMPARE_REPORT_DIR / "training_process"),
        help="Directory for generated CSV files and plots.",
    )
    parser.add_argument("--window", type=int, default=50, help="Rolling window in episodes.")
    parser.add_argument(
        "--last-episodes",
        type=int,
        default=100,
        help="Episodes used for final component/statistics summaries.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    runs = _load_runs([Path(path) for path in args.runs_dir])
    if not runs:
        raise SystemExit(f"No completed runs found in: {', '.join(args.runs_dir)}")

    monitor_frames = [run["monitor"] for run in runs if not run["monitor"].empty]
    curves = pd.concat(monitor_frames, ignore_index=True) if monitor_frames else pd.DataFrame()
    traces = pd.concat(
        [run["trace"] for run in runs if not run["trace"].empty],
        ignore_index=True,
    ) if any(not run["trace"].empty for run in runs) else pd.DataFrame()
    progress_evals = pd.concat(
        [run["progress_eval"] for run in runs if not run["progress_eval"].empty],
        ignore_index=True,
    ) if any(not run["progress_eval"].empty for run in runs) else pd.DataFrame()
    summaries = pd.DataFrame([_run_summary(run, args.last_episodes) for run in runs])

    curves_path = output_dir / "training_curves.csv"
    summary_path = output_dir / "run_summary.csv"
    curves.to_csv(curves_path, index=False)
    summaries.to_csv(summary_path, index=False)
    if not traces.empty:
        traces.to_csv(output_dir / "step_traces.csv", index=False)
    if not progress_evals.empty:
        progress_evals.to_csv(output_dir / "progress_eval_snapshots.csv", index=False)

    if curves.empty:
        _empty_plot(output_dir / "time_reward.png", "Time-Reward graph", "No monitor logs found.")
        _empty_plot(
            output_dir / "timestep_reward.png",
            "Timestep-Reward graph",
            "No monitor logs found.",
        )
        _empty_plot(
            output_dir / "success_collision_over_time.png",
            "Success and collision metrics",
            "No monitor logs found.",
        )
        _empty_plot(
            output_dir / "stage_behavior.png",
            "Training behavior stages",
            "No monitor logs found.",
        )
    else:
        _plot_time_reward(curves, output_dir / "time_reward.png", args.window)
        _plot_timestep_reward(curves, output_dir / "timestep_reward.png", args.window)
        _plot_success_collision(curves, output_dir / "success_collision_over_time.png", args.window)
        _plot_stage_behavior(curves, output_dir / "stage_behavior.png", args.window)
    _plot_entity_reward(summaries, output_dir / "entity_reward_components.png")
    _plot_algorithm_reward_comparison(summaries, output_dir / "algorithm_reward_comparison.png")
    _plot_step_trace_diagnostics(traces, output_dir / "step_trace_diagnostics.png")
    _plot_progress_eval(progress_evals, output_dir / "progress_eval_snapshots.png")

    manifest = {
        "runs": len(runs),
        "curves_csv": str(curves_path),
        "summary_csv": str(summary_path),
        "plots": [
            "time_reward.png",
            "timestep_reward.png",
            "entity_reward_components.png",
            "success_collision_over_time.png",
            "stage_behavior.png",
            "algorithm_reward_comparison.png",
            "step_trace_diagnostics.png",
            "progress_eval_snapshots.png",
        ],
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    print(json.dumps(manifest, indent=2))


def _load_runs(run_roots: list[Path]) -> list[dict[str, Any]]:
    runs = []
    for run_root in run_roots:
        if not run_root.exists():
            continue
        for run_dir in sorted(path for path in run_root.iterdir() if path.is_dir()):
            metadata_path = run_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            with metadata_path.open("r", encoding="utf-8") as handle:
                metadata = json.load(handle)
            monitor = _load_monitor(run_dir, metadata)
            trace = _load_trace(run_dir, metadata)
            progress_eval = _load_progress_eval(run_dir, metadata)
            eval_summary = _load_eval_summary(run_dir)
            runs.append(
                {
                    "run_dir": run_dir,
                    "metadata": metadata,
                    "monitor": monitor,
                    "trace": trace,
                    "progress_eval": progress_eval,
                    "eval": eval_summary,
                }
            )
    return runs


def _load_monitor(run_dir: Path, metadata: dict[str, Any]) -> pd.DataFrame:
    monitor_files = sorted((run_dir / "monitor").glob("*.monitor.csv"))
    frames = []
    for monitor_file in monitor_files:
        frame = pd.read_csv(monitor_file, comment="#")
        frame["monitor_file"] = monitor_file.name
        frames.append(frame)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        return df

    df = df.sort_values("t").reset_index(drop=True)
    df["episode"] = df.index + 1
    df["cumulative_timesteps"] = df["l"].cumsum()
    df["run"] = run_dir.name
    df["algorithm"] = metadata.get("algorithm", "unknown")
    df["reward"] = metadata.get("reward", "unknown")
    df["label"] = _run_label(metadata, run_dir)
    return df


def _load_trace(run_dir: Path, metadata: dict[str, Any]) -> pd.DataFrame:
    trace_files = sorted((run_dir / "trace").glob("*.steps.csv"))
    frames = []
    for trace_file in trace_files:
        frame = pd.read_csv(trace_file)
        frame["trace_file"] = trace_file.name
        frames.append(frame)
    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df["run"] = run_dir.name
    df["algorithm"] = metadata.get("algorithm", "unknown")
    df["reward"] = metadata.get("reward", "unknown")
    df["label"] = _run_label(metadata, run_dir)
    return df


def _load_progress_eval(run_dir: Path, metadata: dict[str, Any]) -> pd.DataFrame:
    eval_path = run_dir / "progress" / "eval_snapshots.csv"
    if not eval_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(eval_path)
    df["run"] = run_dir.name
    df["algorithm"] = metadata.get("algorithm", "unknown")
    df["reward"] = metadata.get("reward", "unknown")
    df["label"] = _run_label(metadata, run_dir)
    return df


def _load_eval_summary(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "eval" / "summary.json"
    if not summary_path.exists():
        return {}
    with summary_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _run_summary(run: dict[str, Any], last_episodes: int) -> dict[str, Any]:
    metadata = run["metadata"]
    monitor = run["monitor"]
    tail = monitor.tail(last_episodes) if not monitor.empty else monitor
    row: dict[str, Any] = {
        "run": run["run_dir"].name,
        "experiment_name": metadata.get("experiment_name", run["run_dir"].name),
        "label": _run_label(metadata, run["run_dir"]),
        "algorithm": metadata.get("algorithm"),
        "reward": metadata.get("reward"),
        "seed": metadata.get("seed"),
        "total_timesteps": metadata.get("total_timesteps"),
        "requested_total_timesteps": metadata.get("requested_total_timesteps"),
        "train_seconds": metadata.get("train_seconds"),
        "stages": len(metadata.get("stages", [])),
    }
    early_stop = metadata.get("early_stop") or {}
    row["early_stop_reason"] = early_stop.get("reason", "")
    row["early_stop_timesteps"] = early_stop.get("timesteps")
    for key, value in run["eval"].items():
        row[f"eval_{key}"] = value

    if not monitor.empty:
        row["train_episodes"] = int(len(monitor))
        row["last_reward_mean"] = float(tail["r"].mean())
        row["last_reward_std"] = float(tail["r"].std(skipna=True))
        row["first_success_timestep"] = _first_positive_timestep(monitor, "episode_success")
        for name, column in REWARD_COMPONENT_COLUMNS.items():
            row[f"last_component_{name}"] = (
                float(tail[column].mean()) if column in tail else 0.0
            )
        for name, column in STAGE_COLUMNS.items():
            row[f"last_stage_{name}_fraction"] = (
                float(tail[column].mean()) if column in tail else 0.0
            )
    return row


def _run_label(metadata: dict[str, Any], run_dir: Path) -> str:
    algorithm = str(metadata.get("algorithm", "unknown"))
    experiment_name = str(metadata.get("experiment_name") or run_dir.name)
    if experiment_name.lower().startswith(algorithm.lower()):
        return experiment_name
    return f"{algorithm} / {experiment_name}"


def _first_positive_timestep(df: pd.DataFrame, column: str) -> int | None:
    if column not in df:
        return None
    positive = df[df[column] > 0]
    if positive.empty:
        return None
    return int(positive.iloc[0]["cumulative_timesteps"])


def _plot_time_reward(df: pd.DataFrame, output_path: Path, window: int) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    for label, group in df.groupby("label"):
        smooth = group["r"].rolling(window=window, min_periods=_min_periods(window)).mean()
        ax.plot(group["t"], smooth, label=label)
    ax.set_title("Time-Reward graph")
    ax.set_xlabel("Training wall time [s]")
    ax.set_ylabel(f"Episode reward, rolling mean ({window})")
    ax.grid(alpha=0.25)
    ax.legend()
    _save(fig, output_path)


def _plot_timestep_reward(df: pd.DataFrame, output_path: Path, window: int) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    for label, group in df.groupby("label"):
        smooth = group["r"].rolling(window=window, min_periods=_min_periods(window)).mean()
        ax.plot(group["cumulative_timesteps"], smooth, label=label)
    ax.set_title("Timestep-Reward graph")
    ax.set_xlabel("Cumulative environment steps")
    ax.set_ylabel(f"Episode reward, rolling mean ({window})")
    ax.grid(alpha=0.25)
    ax.legend()
    _save(fig, output_path)


def _plot_entity_reward(summary: pd.DataFrame, output_path: Path) -> None:
    component_columns = [
        f"last_component_{name}" for name in REWARD_COMPONENT_COLUMNS
    ]
    if summary.empty or not any(column in summary for column in component_columns):
        _empty_plot(output_path, "Entity-Reward graph", "No reward component columns found.")
        return

    labels = summary["label"] if "label" in summary else summary["run"]
    x = range(len(labels))
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    width = 0.12
    offsets = [
        (index - (len(component_columns) - 1) / 2) * width
        for index in range(len(component_columns))
    ]
    for offset, name, column in zip(offsets, REWARD_COMPONENT_COLUMNS, component_columns):
        values = summary[column] if column in summary else [0.0] * len(summary)
        axes[0].bar([value + offset for value in x], values, width=width, label=name)

    zoom_columns = [
        column for name, column in zip(REWARD_COMPONENT_COLUMNS, component_columns)
        if name != "success bonus"
    ]
    zoom_names = [name for name in REWARD_COMPONENT_COLUMNS if name != "success bonus"]
    zoom_width = 0.12
    zoom_offsets = [
        (index - (len(zoom_columns) - 1) / 2) * zoom_width for index in range(len(zoom_columns))
    ]
    for offset, name, column in zip(zoom_offsets, zoom_names, zoom_columns):
        values = summary[column] if column in summary else [0.0] * len(summary)
        axes[1].bar([value + offset for value in x], values, width=zoom_width, label=name)

    axes[0].axhline(0, color="#111827", linewidth=0.8)
    axes[0].set_title("Entity-Reward graph: all reward components")
    axes[0].set_ylabel("Mean contribution")
    axes[1].axhline(0, color="#111827", linewidth=0.8)
    axes[1].set_title("Entity-Reward graph: zoom without success bonus")
    axes[1].set_ylabel("Mean contribution")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(labels, rotation=30, ha="right")
    for axis in axes:
        axis.grid(axis="y", alpha=0.25)
        axis.legend(ncol=3, fontsize=9)
    _save(fig, output_path)


def _plot_success_collision(df: pd.DataFrame, output_path: Path, window: int) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    success_columns = [
        ("goal", "episode_success"),
        ("grasp", "episode_grasp_success"),
        ("pick", "episode_pick_success"),
    ]
    for label, group in df.groupby("label"):
        for metric_name, column in success_columns:
            if column in group:
                smooth = group[column].rolling(window=window, min_periods=_min_periods(window)).mean()
                axes[0].plot(
                    group["cumulative_timesteps"],
                    smooth,
                    label=f"{label} {metric_name}",
                    linewidth=1.6,
                )
        if "episode_collision_count" in group:
            smooth_collision = group["episode_collision_count"].rolling(
                window=window,
                min_periods=_min_periods(window),
            ).mean()
            axes[1].plot(group["cumulative_timesteps"], smooth_collision, label=label)

    axes[0].set_title("Success metrics over training")
    axes[0].set_ylabel("Rolling success rate")
    axes[1].set_title("Collision count over training")
    axes[1].set_xlabel("Cumulative environment steps")
    axes[1].set_ylabel("Rolling collision count")
    for axis in axes:
        axis.grid(alpha=0.25)
        axis.legend(fontsize=8, ncol=2)
    _save(fig, output_path)


def _plot_stage_behavior(df: pd.DataFrame, output_path: Path, window: int) -> None:
    if not any(column in df for column in STAGE_COLUMNS.values()):
        _empty_plot(output_path, "Training behavior stages", "No stage fraction columns found.")
        return

    labels = list(df["label"].drop_duplicates())
    fig, axes = plt.subplots(len(labels), 1, figsize=(12, max(4, 3 * len(labels))), sharex=True)
    if len(labels) == 1:
        axes = [axes]

    for axis, label in zip(axes, labels):
        group = df[df["label"] == label]
        for stage_name, column in STAGE_COLUMNS.items():
            if column in group:
                smooth = group[column].rolling(window=window, min_periods=_min_periods(window)).mean()
                axis.plot(group["cumulative_timesteps"], smooth, label=stage_name)
        axis.set_title(f"Behavior stage fractions: {label}")
        axis.set_ylabel("Episode fraction")
        axis.grid(alpha=0.25)
        axis.legend(ncol=4, fontsize=9)

    axes[-1].set_xlabel("Cumulative environment steps")
    _save(fig, output_path)


def _plot_algorithm_reward_comparison(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        _empty_plot(output_path, "Algorithm/reward comparison", "No runs found.")
        return

    labels = summary["label"] if "label" in summary else summary["run"]
    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    fig.suptitle(
        "Algorithm/reward comparison"
        if len(summary) > 1
        else "Single-run scorecard; add more runs for comparison"
    )
    _bar(axes[0], labels, summary.get("train_seconds"), "Training seconds")
    _bar(axes[1], labels, summary.get("total_timesteps"), "Training steps")
    _bar(axes[2], labels, summary.get("eval_goal_success_rate"), "Eval goal success")
    _bar(axes[3], labels, summary.get("eval_pick_success_rate"), "Eval pick success")
    _bar(axes[4], labels, summary.get("eval_mean_collision_count"), "Eval collisions")
    for axis in axes:
        axis.tick_params(axis="x", labelrotation=45)
    _save(fig, output_path)


def _plot_step_trace_diagnostics(traces: pd.DataFrame, output_path: Path) -> None:
    if traces.empty:
        _empty_plot(output_path, "Step-trace diagnostics", "No step trace files found.")
        return

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    for label, group in traces.groupby("label"):
        sampled = group.sort_values("global_step")
        if len(sampled) > 5000:
            sampled = sampled.iloc[:: max(1, len(sampled) // 5000)]
        if "object_goal_distance" in sampled:
            axes[0].plot(sampled["global_step"], sampled["object_goal_distance"], label=label)
        if "gripper_object_distance" in sampled:
            axes[1].plot(sampled["global_step"], sampled["gripper_object_distance"], label=label)
        if "object_lift" in sampled:
            axes[2].plot(sampled["global_step"], sampled["object_lift"], label=label)
    axes[0].set_title("Object-to-goal distance per sampled step")
    axes[1].set_title("Gripper-to-object distance per sampled step")
    axes[2].set_title("Object lift per sampled step")
    axes[2].set_xlabel("Per-env sampled step")
    for axis in axes:
        axis.grid(alpha=0.25)
        axis.legend(fontsize=8)
    _save(fig, output_path)


def _plot_progress_eval(progress_evals: pd.DataFrame, output_path: Path) -> None:
    if progress_evals.empty:
        _empty_plot(output_path, "Periodic eval snapshots", "No progress eval snapshots found.")
        return

    fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
    for label, group in progress_evals.groupby("label"):
        axes[0].plot(group["timesteps"], group["mean_reward"], marker="o", label=label)
        for metric in ("goal_success_rate", "grasp_success_rate", "pick_success_rate"):
            if metric in group:
                axes[1].plot(group["timesteps"], group[metric], marker="o", label=f"{label} {metric}")
        for metric in (
            "mean_object_goal_distance_final",
            "mean_gripper_object_distance_min",
            "mean_object_lift_max",
        ):
            if metric in group:
                axes[2].plot(group["timesteps"], group[metric], marker="o", label=f"{label} {metric}")
    axes[0].set_title("Periodic evaluation reward")
    axes[0].set_ylabel("Mean eval reward")
    axes[1].set_title("Periodic evaluation success")
    axes[1].set_ylabel("Success rate")
    axes[2].set_title("Periodic evaluation state metrics")
    axes[2].set_xlabel("Training timesteps")
    axes[2].set_ylabel("Distance / lift [m]")
    for axis in axes:
        axis.grid(alpha=0.25)
        axis.legend(fontsize=8, ncol=2)
    _save(fig, output_path)


def _bar(axis, labels: pd.Series, values, title: str) -> None:
    if values is None:
        values = [0.0] * len(labels)
    axis.bar(labels, values)
    axis.set_title(title)
    axis.grid(axis="y", alpha=0.25)


def _min_periods(window: int) -> int:
    return max(1, min(int(window), max(3, int(window) // 5)))


def _empty_plot(output_path: Path, title: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_axis_off()
    ax.set_title(title)
    ax.text(0.5, 0.5, message, ha="center", va="center")
    _save(fig, output_path)


def _save(fig: plt.Figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
