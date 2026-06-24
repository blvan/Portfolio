from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw

from robot_arm_rl.config import load_config
from robot_arm_rl.envs import make_single_env
from robot_arm_rl.paths import DEFAULT_VIDEO_DIR
from robot_arm_rl.sb3 import get_algorithm_class
from robot_arm_rl.wrappers import TABLE_HEIGHT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch or record a trained Fetch pick-and-place agent.")
    parser.add_argument("--run-dir", help="Run directory created by train.py.")
    parser.add_argument("--model-path", default=None, help="Optional checkpoint/model zip to load.")
    parser.add_argument(
        "--config",
        default="configs/PPO/ppo_dense.yaml",
        help="Config for random policy mode.",
    )
    parser.add_argument("--random", action="store_true", help="Use random actions instead of a trained model.")
    parser.add_argument("--episodes", type=int, default=1, help="Episodes to show or record.")
    parser.add_argument("--max-attempts", type=int, default=50, help="Attempts for --success-only.")
    parser.add_argument("--success-only", action="store_true", help="Save only successful episodes.")
    parser.add_argument("--human", action="store_true", help="Open the MuJoCo live viewer.")
    parser.add_argument("--record", action="store_true", help="Save GIF/MP4 animations.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_VIDEO_DIR),
        help="Directory for recorded animations.",
    )
    parser.add_argument("--format", choices=["mp4", "gif"], default="mp4", help="Animation format.")
    parser.add_argument("--fps", type=int, default=25, help="Playback frames per second.")
    parser.add_argument("--width", type=int, default=720, help="Recorded frame width.")
    parser.add_argument("--height", type=int, default=720, help="Recorded frame height.")
    parser.add_argument("--seed", type=int, default=None, help="Override visualization seed.")
    parser.add_argument("--deterministic", action="store_true", help="Use deterministic model actions.")
    parser.add_argument("--stochastic", action="store_true", help="Use stochastic model actions.")
    parser.add_argument("--no-overlay", action="store_true", help="Do not draw metrics on recorded frames.")
    parser.add_argument("--output-name", default=None, help="Override output filename stem.")
    parser.add_argument("--hold-start-seconds", type=float, default=0.0, help="Pause on first frame.")
    parser.add_argument("--hold-final-seconds", type=float, default=0.0, help="Pause on final frame.")
    parser.add_argument(
        "--goal",
        nargs=3,
        type=float,
        metavar=("X", "Y", "Z"),
        default=None,
        help="Override desired goal position for every episode.",
    )
    parser.add_argument(
        "--goal-z",
        choices=["config", "air", "table"],
        default="config",
        help="Convenience override for goal height while keeping/resetting x and y.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.human and not args.record:
        args.record = True

    run_dir = Path(args.run_dir) if args.run_dir else None
    config, metadata = _load_config_and_metadata(run_dir, args.config)
    render_mode = "human" if args.human else "rgb_array"
    base_seed = int(args.seed if args.seed is not None else config["seed"] + 20_000)

    env = make_single_env(
        config,
        seed=base_seed,
        render_mode=render_mode,
        render_width=args.width if args.record else None,
        render_height=args.height if args.record else None,
        monitor_dir=None,
    )
    model = None if args.random else _load_model(run_dir, metadata, env, args.model_path)
    deterministic = _resolve_deterministic(args, config)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    recorded = 0
    attempts = 0
    while recorded < args.episodes and attempts < args.max_attempts:
        attempts += 1
        result = _run_episode(
            env=env,
            model=model,
            episode_index=attempts - 1,
            seed=base_seed + attempts - 1,
            deterministic=deterministic,
            record=args.record,
            human=args.human,
            fps=args.fps,
            overlay=not args.no_overlay,
            hold_start_seconds=args.hold_start_seconds,
            hold_final_seconds=args.hold_final_seconds,
            goal=args.goal,
            goal_z=args.goal_z,
        )
        if args.success_only and not result["goal_success"]:
            print(
                f"attempt={attempts} skipped: reward={result['reward']:.3f} "
                f"success=0 grasp={int(result['grasp_success'])}"
            )
            continue

        recorded += 1
        print(
            f"episode={recorded} attempt={attempts} reward={result['reward']:.3f} "
            f"success={int(result['goal_success'])} grasp={int(result['grasp_success'])} "
            f"collisions={int(result['collision_count'])}"
        )
        if args.record:
            output_path = _make_output_path(
                output_dir,
                run_dir,
                recorded,
                args.format,
                output_name=args.output_name,
            )
            _save_animation(result["frames"], output_path, fps=args.fps)
            print(f"saved {output_path}")

    env.close()
    if recorded == 0:
        raise SystemExit(f"No episodes recorded after {attempts} attempts.")


def _load_config_and_metadata(
    run_dir: Path | None,
    fallback_config: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if run_dir is None:
        return load_config(fallback_config), None

    config = load_config(run_dir / "config.yaml")
    with (run_dir / "metadata.json").open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    return config, metadata


def _load_model(run_dir: Path | None, metadata: dict[str, Any] | None, env, model_path: str | None):
    if run_dir is None or metadata is None:
        raise SystemExit("Use --random or provide --run-dir.")
    algorithm_cls = get_algorithm_class(metadata["algorithm"])
    resolved_model_path = Path(model_path) if model_path is not None else run_dir / "final_model.zip"
    return algorithm_cls.load(str(resolved_model_path), env=env)


def _resolve_deterministic(args: argparse.Namespace, config: dict[str, Any]) -> bool:
    if args.stochastic:
        return False
    if args.deterministic:
        return True
    return bool(config.get("eval", {}).get("deterministic", True))


def _run_episode(
    *,
    env,
    model,
    episode_index: int,
    seed: int,
    deterministic: bool,
    record: bool,
    human: bool,
    fps: int,
    overlay: bool,
    hold_start_seconds: float,
    hold_final_seconds: float,
    goal: list[float] | None,
    goal_z: str,
) -> dict[str, Any]:
    observation, _ = env.reset(seed=seed)
    observation = _override_goal(env, observation, goal=goal, goal_z=goal_z)
    frames: list[np.ndarray] = []
    episode_reward = 0.0
    step_index = 0
    final_info: dict[str, Any] = {}

    if record:
        _append_frame(
            frames,
            env,
            _label(episode_index, step_index, 0.0, {}),
            overlay=overlay,
        )
        _hold_last_frame(frames, hold_start_seconds, fps)

    done = False
    while not done:
        if model is None:
            action = env.action_space.sample()
        else:
            action, _ = model.predict(observation, deterministic=deterministic)

        observation, reward, terminated, truncated, info = env.step(action)
        episode_reward += float(reward)
        step_index += 1
        done = bool(terminated or truncated)
        final_info = info

        if record:
            _append_frame(
                frames,
                env,
                _label(episode_index, step_index, episode_reward, info),
                overlay=overlay,
            )
        if human:
            time.sleep(max(0.0, 1.0 / fps))

    if record:
        _hold_last_frame(frames, hold_final_seconds, fps)

    return {
        "reward": episode_reward,
        "length": step_index,
        "goal_success": bool(float(final_info.get("episode_success", final_info.get("is_success", 0.0)))),
        "grasp_success": bool(float(final_info.get("episode_grasp_success", 0.0))),
        "pick_success": bool(float(final_info.get("episode_pick_success", 0.0))),
        "collision_count": float(final_info.get("episode_collision_count", 0.0)),
        "frames": frames,
    }


def _override_goal(
    env,
    observation: dict[str, np.ndarray],
    *,
    goal: list[float] | None,
    goal_z: str,
) -> dict[str, np.ndarray]:
    if goal is None and goal_z == "config":
        return observation

    updated = dict(observation)
    desired_goal = np.asarray(updated["desired_goal"], dtype=np.float64).copy()
    if goal is not None:
        desired_goal = np.asarray(goal, dtype=np.float64)

    if goal_z == "table":
        desired_goal[2] = TABLE_HEIGHT
    elif goal_z == "air" and goal is None:
        desired_goal[2] = max(float(desired_goal[2]), TABLE_HEIGHT + 0.16)

    updated["desired_goal"] = desired_goal.astype(np.float64)
    unwrapped = getattr(env, "unwrapped", None)
    if unwrapped is not None and hasattr(unwrapped, "goal"):
        unwrapped.goal = desired_goal.copy()
    return updated


def _append_frame(frames: list[np.ndarray], env, label: str, *, overlay: bool) -> None:
    frame = env.render()
    if frame is None:
        return
    frame_array = np.asarray(frame)
    if overlay:
        frame_array = _annotate_frame(frame_array, label)
    frames.append(frame_array)


def _hold_last_frame(frames: list[np.ndarray], seconds: float, fps: int) -> None:
    if not frames or seconds <= 0:
        return
    repeats = int(round(seconds * fps))
    if repeats <= 0:
        return
    frames.extend([frames[-1].copy() for _ in range(repeats)])


def _annotate_frame(frame: np.ndarray, text: str) -> np.ndarray:
    image = Image.fromarray(frame.astype(np.uint8), mode="RGB").convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((8, 8, min(image.width - 8, 520), 58), fill=(0, 0, 0, 150))
    draw.text((18, 20), text, fill=(255, 255, 255, 255))
    return np.asarray(Image.alpha_composite(image, overlay).convert("RGB"))


def _label(episode_index: int, step_index: int, reward: float, info: dict[str, Any]) -> str:
    success = int(float(info.get("episode_success", info.get("is_success", 0.0))))
    grasp = int(float(info.get("episode_grasp_success", 0.0)))
    pick = int(float(info.get("episode_pick_success", 0.0)))
    collisions = int(float(info.get("episode_collision_count", 0.0)))
    return (
        f"episode {episode_index + 1} | step {step_index:02d} | reward {reward:.2f} | "
        f"success {success} | pick {pick} | grasp {grasp} | collisions {collisions}"
    )


def _make_output_path(
    output_dir: Path,
    run_dir: Path | None,
    episode_number: int,
    fmt: str,
    *,
    output_name: str | None = None,
) -> Path:
    if output_name:
        suffix = f"_{episode_number:03d}" if episode_number > 1 else ""
        return output_dir / f"{output_name}{suffix}.{fmt}"
    prefix = run_dir.name if run_dir is not None else "random_policy"
    return output_dir / f"{prefix}_episode_{episode_number:03d}.{fmt}"


def _save_animation(frames: list[np.ndarray], output_path: Path, *, fps: int) -> None:
    if not frames:
        raise ValueError("No frames captured. Try without --human or use --record.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".gif":
        imageio.mimsave(output_path, frames, fps=fps)
    else:
        try:
            imageio.mimsave(
                output_path,
                frames,
                fps=fps,
                codec="libx264",
                quality=8,
                macro_block_size=16,
            )
        except Exception as exc:
            raise RuntimeError(
                "Could not write MP4. Install the ffmpeg writer with "
                "`pip install imageio-ffmpeg` or rerun with `--format gif`."
            ) from exc


if __name__ == "__main__":
    main()
