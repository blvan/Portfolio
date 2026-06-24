from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from robot_arm_rl.paths import DEFAULT_COMPARE_REPORT_DIR, DEFAULT_RUN_ROOT


DEFAULT_CONFIGS = [
    "configs/PPO/ppo_sparse.yaml",
    "configs/PPO/ppo_dense.yaml",
    "configs/PPO/ppo_shaped.yaml",
    "configs/SAC/sac_sparse_her.yaml",
    "configs/SAC/sac_dense.yaml",
    "configs/SAC/sac_shaped.yaml",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train, evaluate, and compare the experiment matrix.")
    parser.add_argument("--timesteps", type=int, default=50_000, help="Timesteps per training run.")
    parser.add_argument("--episodes", type=int, default=20, help="Evaluation episodes per run.")
    parser.add_argument(
        "--run-root",
        default=str(DEFAULT_RUN_ROOT),
        help="Directory where runs are saved.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_COMPARE_REPORT_DIR),
        help="Directory for comparison outputs.",
    )
    parser.add_argument("--device", default="auto", help="Torch device: auto, cpu, cuda.")
    parser.add_argument("--skip-train", action="store_true", help="Only evaluate/compare existing runs.")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip configs that already have a completed run in the run root.",
    )
    parser.add_argument(
        "--rich-report",
        action="store_true",
        help="Also generate detailed progress/reward-component plots.",
    )
    parser.add_argument("--configs", nargs="*", default=DEFAULT_CONFIGS, help="Config files to run.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    run_root = root / args.run_root
    before = _known_run_dirs(run_root)

    if not args.skip_train:
        for config in args.configs:
            experiment_name = Path(config).stem
            if args.skip_existing and _has_completed_run(run_root, experiment_name):
                print(f"Skipping {config}: completed run already exists.", flush=True)
                continue

            _run(
                [
                    sys.executable,
                    "-m",
                    "robot_arm_rl.train",
                    "--config",
                    config,
                    "--total-timesteps",
                    str(args.timesteps),
                    "--run-root",
                    args.run_root,
                    "--device",
                    args.device,
                ],
                cwd=root,
            )

    after = _known_run_dirs(run_root)
    new_runs = sorted(after - before)
    completed_runs = sorted(run_dir for run_dir in after if (run_dir / "final_model.zip").exists())
    if args.skip_train:
        runs_to_evaluate = completed_runs
    else:
        runs_to_evaluate = [
            run_dir
            for run_dir in completed_runs
            if run_dir in new_runs or not (run_dir / "eval" / "summary.json").exists()
        ]

    for run_dir in runs_to_evaluate:
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

    if args.rich_report:
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


def _known_run_dirs(run_root: Path) -> set[Path]:
    if not run_root.exists():
        return set()
    return {path.resolve() for path in run_root.iterdir() if path.is_dir()}


def _has_completed_run(run_root: Path, experiment_name: str) -> bool:
    if not run_root.exists():
        return False
    return any(
        run_dir.is_dir()
        and run_dir.name.endswith(f"_{experiment_name}")
        and (run_dir / "final_model.zip").exists()
        for run_dir in run_root.iterdir()
    )


def _run(command: list[str], cwd: Path) -> None:
    print("\n$", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


if __name__ == "__main__":
    main()
