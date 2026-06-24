from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_SEEDS = [42, 123, 2026]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and evaluate final SAC curriculum across seeds.")
    parser.add_argument("--config", default="configs/SAC/sac_curriculum_air.yaml", help="SAC config to train.")
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS, help="Seeds to run.")
    parser.add_argument("--run-root", default="artifacts/runs_sac_multiseed", help="Directory for seed runs.")
    parser.add_argument("--output-dir", default="report/SAC/multiseed_curriculum", help="Directory for summaries.")
    parser.add_argument("--device", default="auto", help="Torch device: auto, cpu, cuda.")
    parser.add_argument("--episodes", type=int, default=100, help="Evaluation episodes per seed.")
    parser.add_argument("--torch-threads", type=int, default=None, help="Optional PyTorch CPU thread limit.")
    parser.add_argument("--skip-train", action="store_true", help="Only evaluate/summarize completed seed runs.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip seed runs that already have final_model.zip.")
    parser.add_argument("--rich-report", action="store_true", help="Generate rich training process plots.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    run_root = root / args.run_root
    output_dir = root / args.output_dir
    run_root.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_dirs: list[Path] = []
    for seed in args.seeds:
        run_name = f"sac_curriculum_air_seed_{seed}"
        existing = _find_completed_run(run_root, run_name)
        if existing and (args.skip_existing or args.skip_train):
            print(f"Using completed run for seed {seed}: {existing}", flush=True)
            run_dirs.append(existing)
            continue

        if args.skip_train:
            print(f"No completed run found for seed {seed}; skipping because --skip-train is set.", flush=True)
            continue

        command = [
            sys.executable,
            "-m",
            "robot_arm_rl.train",
            "--config",
            args.config,
            "--run-root",
            args.run_root,
            "--run-name",
            run_name,
            "--seed",
            str(seed),
            "--device",
            args.device,
        ]
        if args.torch_threads is not None:
            command.extend(["--torch-threads", str(args.torch_threads)])

        _run(command, cwd=root)
        completed = _find_completed_run(run_root, run_name)
        if completed is None:
            raise SystemExit(f"Training finished but no completed run was found for seed {seed}.")
        run_dirs.append(completed)

    for run_dir in run_dirs:
        if not (run_dir / "eval" / "summary.json").exists():
            _run(
                [
                    sys.executable,
                    "-m",
                    "robot_arm_rl.evaluate",
                    "--run-dir",
                    str(run_dir),
                    "--episodes",
                    str(args.episodes),
                ],
                cwd=root,
            )

    _write_seed_summary(run_dirs, output_dir)

    if run_dirs:
        _run(
            [
                sys.executable,
                "-m",
                "robot_arm_rl.compare",
                "--runs-dir",
                args.run_root,
                "--output-dir",
                args.output_dir,
            ],
            cwd=root,
        )

    if args.rich_report and run_dirs:
        _run(
            [
                sys.executable,
                "-m",
                "robot_arm_rl.training_report",
                "--runs-dir",
                args.run_root,
                "--output-dir",
                str(Path(args.output_dir) / "training_process"),
            ],
            cwd=root,
        )


def _find_completed_run(run_root: Path, run_name: str) -> Path | None:
    if not run_root.exists():
        return None
    matches = [
        path
        for path in run_root.iterdir()
        if path.is_dir() and path.name.endswith(f"_{run_name}") and (path / "final_model.zip").exists()
    ]
    return sorted(matches)[-1] if matches else None


def _write_seed_summary(run_dirs: list[Path], output_dir: Path) -> None:
    rows = [_load_seed_row(run_dir) for run_dir in run_dirs]
    if not rows:
        print("No completed seed runs available for summary.", flush=True)
        return

    fieldnames = [
        "run",
        "seed",
        "total_timesteps",
        "train_seconds",
        "early_stop_reason",
        "eval_goal_success_rate",
        "eval_grasp_success_rate",
        "eval_pick_success_rate",
        "eval_mean_collision_count",
        "eval_mean_reward",
    ]
    csv_path = output_dir / "sac_multiseed_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    aggregate = _aggregate(rows)
    aggregate_path = output_dir / "sac_multiseed_aggregate.json"
    with aggregate_path.open("w", encoding="utf-8") as handle:
        json.dump(aggregate, handle, indent=2)

    md_path = output_dir / "sac_multiseed_summary.md"
    with md_path.open("w", encoding="utf-8") as handle:
        handle.write("# SAC Multi-Seed Summary\n\n")
        handle.write("| Seed | Steps | Train seconds | Goal success | Grasp success | Pick success | Mean collisions | Mean reward |\n")
        handle.write("| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        for row in rows:
            handle.write(
                f"| {row['seed']} | {row['total_timesteps']} | {float(row['train_seconds']):.1f} | "
                f"{float(row['eval_goal_success_rate']):.2f} | "
                f"{float(row['eval_grasp_success_rate']):.2f} | "
                f"{float(row['eval_pick_success_rate']):.2f} | "
                f"{float(row['eval_mean_collision_count']):.2f} | "
                f"{float(row['eval_mean_reward']):.2f} |\n"
            )
        handle.write("\n")
        handle.write("Aggregate mean +/- std:\n\n")
        for key, value in aggregate.items():
            handle.write(f"- `{key}`: {value}\n")

    print(f"Saved seed summary to {output_dir}", flush=True)


def _load_seed_row(run_dir: Path) -> dict[str, Any]:
    with (run_dir / "metadata.json").open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    with (run_dir / "eval" / "summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)

    return {
        "run": run_dir.name,
        "seed": metadata.get("seed"),
        "total_timesteps": metadata.get("total_timesteps"),
        "train_seconds": metadata.get("train_seconds"),
        "early_stop_reason": (metadata.get("early_stop") or {}).get("reason", ""),
        "eval_goal_success_rate": summary.get("goal_success_rate"),
        "eval_grasp_success_rate": summary.get("grasp_success_rate"),
        "eval_pick_success_rate": summary.get("pick_success_rate"),
        "eval_mean_collision_count": summary.get("mean_collision_count"),
        "eval_mean_reward": summary.get("mean_reward"),
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, str]:
    metric_names = [
        "train_seconds",
        "total_timesteps",
        "eval_goal_success_rate",
        "eval_grasp_success_rate",
        "eval_pick_success_rate",
        "eval_mean_collision_count",
        "eval_mean_reward",
    ]
    aggregate: dict[str, str] = {}
    for metric in metric_names:
        values = [float(row[metric]) for row in rows if row.get(metric) not in (None, "")]
        if not values:
            continue
        mean = statistics.fmean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        aggregate[metric] = f"{mean:.4f} +/- {std:.4f}"
    return aggregate


def _run(command: list[str], cwd: Path) -> None:
    print("\n$", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


if __name__ == "__main__":
    main()
