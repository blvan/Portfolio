from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from robot_arm_rl.config import load_config  # noqa: E402
from robot_arm_rl.envs import make_single_env  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run random actions in FetchPickAndPlace.")
    parser.add_argument("--config", default="configs/PPO/ppo_dense.yaml")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--render", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    env = make_single_env(
        config,
        seed=int(config["seed"]),
        render_mode="human" if args.render else None,
    )
    observation, info = env.reset(seed=int(config["seed"]))
    print("Observation keys:", sorted(observation.keys()))
    print("Action space:", env.action_space)

    for step in range(args.steps):
        action = env.action_space.sample()
        observation, reward, terminated, truncated, info = env.step(action)
        print(
            f"step={step:03d} reward={float(reward): .3f} "
            f"success={float(info.get('is_success', 0.0)):.0f} "
            f"grasp={float(info.get('episode_grasp_success', 0.0)):.0f} "
            f"collisions={float(info.get('episode_collision_count', 0.0)):.0f}"
        )
        if terminated or truncated:
            observation, info = env.reset()
    env.close()


if __name__ == "__main__":
    main()
