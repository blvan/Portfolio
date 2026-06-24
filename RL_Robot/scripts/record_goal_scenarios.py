from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


SCENARIOS = (
    ("air_left_mid", "air left/mid", (1.20, 0.62, 0.56)),
    ("air_right_mid", "air right/mid", (1.42, 0.68, 0.58)),
    ("air_front_high", "air front/high", (1.32, 0.88, 0.64)),
    ("air_back_high", "air back/high", (1.16, 0.82, 0.62)),
    ("table_left", "table left", (1.20, 0.62, 0.42)),
    ("table_center", "table center", (1.32, 0.68, 0.42)),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record final-model videos for fixed goal scenarios.")
    parser.add_argument("--run-dir", required=True, help="Training run directory.")
    parser.add_argument("--output-dir", default=None, help="Directory for scenario videos.")
    parser.add_argument("--format", choices=["mp4", "gif"], default="mp4")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--width", type=int, default=720)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--hold-start-seconds", type=float, default=0.25)
    parser.add_argument("--hold-final-seconds", type=float, default=0.25)
    parser.add_argument("--title-seconds", type=float, default=0.35)
    parser.add_argument("--no-compose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    run_dir = Path(args.run_dir).resolve()
    output_dir = Path(args.output_dir or run_dir / "goal_scenarios").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    clips = []
    labels = []
    rows = []
    for index, (slug, label, goal) in enumerate(SCENARIOS, start=1):
        output_name = f"{index:02d}_{slug}"
        command = [
            sys.executable,
            "-m",
            "robot_arm_rl.visualize",
            "--run-dir",
            str(run_dir),
            "--episodes",
            "1",
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
            "--goal",
            *[str(value) for value in goal],
        ]
        print("$", " ".join(command), flush=True)
        subprocess.run(command, cwd=root, check=True)
        clip_path = output_dir / f"{output_name}.{args.format}"
        clips.append(clip_path)
        labels.append(label)
        rows.append(
            {
                "index": index,
                "slug": slug,
                "label": label,
                "goal_x": goal[0],
                "goal_y": goal[1],
                "goal_z": goal[2],
                "clip_path": clip_path,
            }
        )

    manifest_path = output_dir / "goal_scenarios_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["index", "slug", "label", "goal_x", "goal_y", "goal_z", "clip_path"],
        )
        writer.writeheader()
        writer.writerows(rows)

    if not args.no_compose:
        sequence_path = output_dir / f"final_model_goal_scenarios_sequence.{args.format}"
        _compose(root, clips, labels, sequence_path, args.format, args.fps, args.title_seconds, "sequence")

        grid_clips = clips[:4]
        grid_labels = labels[:4]
        grid_path = output_dir / f"final_model_air_goals_grid.{args.format}"
        _compose(root, grid_clips, grid_labels, grid_path, args.format, args.fps, args.title_seconds, "grid")

    print(f"manifest {manifest_path}")


def _compose(
    root: Path,
    clips: list[Path],
    labels: list[str],
    output_path: Path,
    fmt: str,
    fps: int,
    title_seconds: float,
    layout: str,
) -> None:
    command = [
        sys.executable,
        str(root / "scripts" / "compose_training_video.py"),
        "--clips",
        *[str(path) for path in clips],
        "--labels",
        *labels,
        "--output",
        str(output_path),
        "--layout",
        layout,
        "--fps",
        str(fps),
        "--title-seconds",
        str(title_seconds),
    ]
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=root, check=True)
    print(f"composed {output_path}")


if __name__ == "__main__":
    main()
