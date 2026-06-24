from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from robot_arm_rl.config import load_config
from robot_arm_rl.envs import make_single_env
from robot_arm_rl.sb3 import get_algorithm_class


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained robot-arm RL run.")
    parser.add_argument("--run-dir", required=True, help="Run directory created by train.py.")
    parser.add_argument("--episodes", type=int, default=None, help="Number of episodes.")
    parser.add_argument("--render", action="store_true", help="Render with MuJoCo human viewer.")
    parser.add_argument("--deterministic", action="store_true", help="Force deterministic actions.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)
    config = load_config(run_dir / "config.yaml")
    with (run_dir / "metadata.json").open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    episodes = int(args.episodes or config.get("eval", {}).get("episodes", 20))
    deterministic = bool(args.deterministic or config.get("eval", {}).get("deterministic", True))
    render_mode = "human" if args.render else None

    env = make_single_env(
        config,
        seed=int(config["seed"]) + 10_000,
        render_mode=render_mode,
        monitor_dir=None,
    )
    algorithm_cls = get_algorithm_class(metadata["algorithm"])
    model = algorithm_cls.load(str(run_dir / "final_model.zip"), env=env)

    rows: list[dict[str, Any]] = []
    for episode_index in range(episodes):
        observation, _ = env.reset(seed=int(config["seed"]) + 10_000 + episode_index)
        done = False
        episode_reward = 0.0
        episode_length = 0
        final_info: dict[str, Any] = {}

        while not done:
            action, _ = model.predict(observation, deterministic=deterministic)
            observation, reward, terminated, truncated, info = env.step(action)
            episode_reward += float(reward)
            episode_length += 1
            done = bool(terminated or truncated)
            final_info = info

        rows.append(
            {
                "episode": episode_index,
                "reward": episode_reward,
                "length": episode_length,
                "goal_success": float(final_info.get("episode_success", final_info.get("is_success", 0.0))),
                "grasp_success": float(final_info.get("episode_grasp_success", 0.0)),
                "pick_success": float(final_info.get("episode_pick_success", 0.0)),
                "collision_count": float(final_info.get("episode_collision_count", 0.0)),
                "object_goal_distance_final": float(
                    final_info.get("episode_object_goal_distance_final", 0.0)
                ),
                "gripper_object_distance_min": float(
                    final_info.get("episode_gripper_object_distance_min", 0.0)
                ),
                "object_lift_max": float(final_info.get("episode_object_lift_max", 0.0)),
                "reward_total_mean": float(final_info.get("episode_reward_total_mean", 0.0)),
            }
        )

    env.close()

    eval_dir = run_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    csv_path = eval_dir / "episodes.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    summary_path = eval_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"Saved evaluation to {eval_dir}")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rewards = np.array([row["reward"] for row in rows], dtype=np.float64)
    lengths = np.array([row["length"] for row in rows], dtype=np.float64)
    goal_successes = np.array([row["goal_success"] for row in rows], dtype=np.float64)
    grasp_successes = np.array([row["grasp_success"] for row in rows], dtype=np.float64)
    pick_successes = np.array([row["pick_success"] for row in rows], dtype=np.float64)
    collisions = np.array([row["collision_count"] for row in rows], dtype=np.float64)
    object_goal_final = np.array(
        [row["object_goal_distance_final"] for row in rows],
        dtype=np.float64,
    )
    gripper_object_min = np.array(
        [row["gripper_object_distance_min"] for row in rows],
        dtype=np.float64,
    )
    object_lift_max = np.array([row["object_lift_max"] for row in rows], dtype=np.float64)

    return {
        "episodes": len(rows),
        "mean_reward": float(rewards.mean()),
        "std_reward": float(rewards.std()),
        "mean_length": float(lengths.mean()),
        "goal_success_rate": float(goal_successes.mean()),
        "goal_success_count": int(goal_successes.sum()),
        "grasp_success_rate": float(grasp_successes.mean()),
        "grasp_success_count": int(grasp_successes.sum()),
        "pick_success_rate": float(pick_successes.mean()),
        "pick_success_count": int(pick_successes.sum()),
        "mean_collision_count": float(collisions.mean()),
        "total_collision_count": int(collisions.sum()),
        "mean_object_goal_distance_final": float(object_goal_final.mean()),
        "mean_gripper_object_distance_min": float(gripper_object_min.mean()),
        "mean_object_lift_max": float(object_lift_max.mean()),
    }


if __name__ == "__main__":
    main()
