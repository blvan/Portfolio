from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record videos from evenly spaced checkpoints and optionally compose them."
    )
    parser.add_argument("--run-dir", required=True, help="Training run directory.")
    parser.add_argument("--output-dir", default=None, help="Directory for progress videos.")
    parser.add_argument("--samples", type=int, default=4, help="Number of checkpoint samples.")
    parser.add_argument("--episodes", type=int, default=1, help="Episodes per checkpoint.")
    parser.add_argument("--format", choices=["mp4", "gif"], default="mp4")
    parser.add_argument("--fps", type=int, default=12, help="Lower fps makes behavior easier to see.")
    parser.add_argument("--width", type=int, default=720)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--success-only", action="store_true")
    parser.add_argument("--no-final", action="store_true", help="Do not append final_model.zip.")
    parser.add_argument("--hold-start-seconds", type=float, default=0.25)
    parser.add_argument("--hold-final-seconds", type=float, default=0.25)
    parser.add_argument("--title-seconds", type=float, default=0.35)
    parser.add_argument("--no-compose", action="store_true", help="Only record individual clips.")
    parser.add_argument("--compose-layout", choices=["sequence", "grid"], default="sequence")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    run_dir = Path(args.run_dir).resolve()
    output_dir = Path(args.output_dir or run_dir / "progress_videos").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoints = _select_checkpoints(run_dir, args.samples, include_final=not args.no_final)
    if not checkpoints:
        raise SystemExit(f"No checkpoints found in {run_dir / 'checkpoints'}")

    rows = []
    clips = []
    labels = []
    for index, checkpoint in enumerate(checkpoints, start=1):
        label = _checkpoint_label(checkpoint, index)
        output_name = f"{index:02d}_{label}"
        command = [
            sys.executable,
            "-m",
            "robot_arm_rl.visualize",
            "--run-dir",
            str(run_dir),
            "--model-path",
            str(checkpoint),
            "--episodes",
            str(args.episodes),
            "--record",
            "--format",
            args.format,
            "--fps",
            str(args.fps),
            "--width",
            str(args.width),
            "--height",
            str(args.height),
            "--hold-start-seconds",
            str(args.hold_start_seconds),
            "--hold-final-seconds",
            str(args.hold_final_seconds),
            "--output-dir",
            str(output_dir),
            "--output-name",
            output_name,
        ]
        if args.success_only:
            command.append("--success-only")

        print("$", " ".join(command), flush=True)
        subprocess.run(command, cwd=root, check=True)
        clip_path = output_dir / f"{output_name}.{args.format}"
        clips.append(clip_path)
        labels.append(label.replace("_", " "))
        rows.append({"index": index, "label": label, "model_path": checkpoint, "clip_path": clip_path})

    manifest_path = output_dir / "progress_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["index", "label", "model_path", "clip_path"])
        writer.writeheader()
        writer.writerows(rows)

    if not args.no_compose:
        composed = output_dir / f"training_progress_{args.compose_layout}.{args.format}"
        command = [
            sys.executable,
            str(root / "scripts" / "compose_training_video.py"),
            "--clips",
            *[str(path) for path in clips],
            "--labels",
            *labels,
            "--output",
            str(composed),
            "--layout",
            args.compose_layout,
            "--fps",
            str(args.fps),
            "--title-seconds",
            str(args.title_seconds),
        ]
        print("$", " ".join(command), flush=True)
        subprocess.run(command, cwd=root, check=True)
        print(f"composed {composed}")

    print(f"manifest {manifest_path}")


def _select_checkpoints(run_dir: Path, samples: int, include_final: bool) -> list[Path]:
    checkpoint_dir = run_dir / "checkpoints"
    checkpoints = sorted(
        checkpoint_dir.glob("model_*_steps.zip"),
        key=lambda path: _checkpoint_step(path),
    )
    stage_checkpoints = sorted(checkpoint_dir.glob("stage_*.zip"))
    candidates = checkpoints or stage_checkpoints
    selected = _evenly_spaced(candidates, samples)
    final_model = run_dir / "final_model.zip"
    if include_final and final_model.exists() and final_model not in selected:
        selected.append(final_model)
    return selected


def _evenly_spaced(items: list[Path], count: int) -> list[Path]:
    if len(items) <= count:
        return list(items)
    if count <= 1:
        return [items[-1]]
    indices = sorted({round(i * (len(items) - 1) / (count - 1)) for i in range(count)})
    return [items[index] for index in indices]


def _checkpoint_step(path: Path) -> int:
    match = re.search(r"model_(\d+)_steps", path.name)
    return int(match.group(1)) if match else 0


def _checkpoint_label(path: Path, index: int) -> str:
    if path.name == "final_model.zip":
        return "final_model"
    step = _checkpoint_step(path)
    if step:
        return f"{step // 1000:04d}k_steps"
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", path.stem) or f"checkpoint_{index:02d}"


if __name__ == "__main__":
    main()
