from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import gymnasium as gym
import gymnasium_robotics
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecEnv

from robot_arm_rl.wrappers import (
    AirGoalConfig,
    AirGoalWrapper,
    EPISODE_TRACKING_INFO_KEYS,
    MetricsConfig,
    PickPlaceMetricsWrapper,
    ShapedPickPlaceRewardWrapper,
    ShapedRewardConfig,
    StepTraceWrapper,
)


REWARD_TO_ENV_IDS = {
    "sparse": ("FetchPickAndPlace-v4", "FetchPickAndPlace-v3"),
    "dense": ("FetchPickAndPlaceDense-v4", "FetchPickAndPlaceDense-v3"),
    "shaped": ("FetchPickAndPlaceDense-v4", "FetchPickAndPlaceDense-v3"),
    "penalized": ("FetchPickAndPlaceDense-v4", "FetchPickAndPlaceDense-v3"),
}

MONITOR_INFO_KEYWORDS = (
    "is_success",
    "episode_success",
    "episode_grasp_success",
    "episode_pick_success",
    "episode_collision_count",
    *EPISODE_TRACKING_INFO_KEYS,
)

_REGISTERED = False


class GoalAwareMonitor(Monitor):
    """SB3 Monitor that keeps GoalEnv methods visible for HER replay buffers."""

    def compute_reward(self, achieved_goal, desired_goal, info):
        return self.env.compute_reward(achieved_goal, desired_goal, info)

    def compute_terminated(self, achieved_goal, desired_goal, info):
        return self.env.compute_terminated(achieved_goal, desired_goal, info)

    def compute_truncated(self, achieved_goal, desired_goal, info):
        return self.env.compute_truncated(achieved_goal, desired_goal, info)


def register_robotics_envs() -> None:
    global _REGISTERED
    if not _REGISTERED:
        gym.register_envs(gymnasium_robotics)
        _REGISTERED = True


def resolve_env_id(reward_name: str, explicit_env_id: str | None = None) -> str:
    if explicit_env_id:
        return explicit_env_id

    if reward_name not in REWARD_TO_ENV_IDS:
        raise ValueError(
            f"Unknown reward variant '{reward_name}'. Use sparse, dense, shaped, or penalized."
        )

    registered_ids = set(gym.envs.registry.keys())
    for env_id in REWARD_TO_ENV_IDS[reward_name]:
        if env_id in registered_ids:
            return env_id

    candidates = ", ".join(REWARD_TO_ENV_IDS[reward_name])
    raise ValueError(f"No Fetch pick-and-place environment found. Tried: {candidates}")


def make_single_env(
    config: dict[str, Any],
    *,
    seed: int,
    rank: int = 0,
    render_mode: str | None = None,
    render_width: int | None = None,
    render_height: int | None = None,
    monitor_dir: str | Path | None = None,
    trace_dir: str | Path | None = None,
    trace_log_every: int = 1,
    trace_max_rows: int | None = None,
) -> gym.Env:
    register_robotics_envs()

    env_config = config.get("env", {})
    reward_name = str(env_config.get("reward", "dense")).lower()
    env_id = resolve_env_id(reward_name, env_config.get("id"))

    gym_kwargs: dict[str, Any] = {
        "max_episode_steps": int(env_config.get("max_episode_steps", 50)),
        "render_mode": render_mode,
    }
    if render_width is not None:
        gym_kwargs["width"] = int(render_width)
    if render_height is not None:
        gym_kwargs["height"] = int(render_height)

    env = gym.make(env_id, **gym_kwargs)
    env.action_space.seed(seed + rank)
    env.observation_space.seed(seed + rank)

    air_goal_config = AirGoalConfig(**env_config.get("air_goal", {}))
    if air_goal_config.enabled:
        env = AirGoalWrapper(env, air_goal_config)

    if reward_name in {"shaped", "penalized"}:
        reward_config = ShapedRewardConfig(**env_config.get("shaped_reward", {}))
        env = ShapedPickPlaceRewardWrapper(env, reward_config)

    metrics_config = MetricsConfig(**env_config.get("metrics", {}))
    env = PickPlaceMetricsWrapper(env, metrics_config)

    if trace_dir is not None:
        trace_path = Path(trace_dir)
        trace_path.mkdir(parents=True, exist_ok=True)
        env = StepTraceWrapper(
            env,
            trace_path / f"env_{rank}.steps.csv",
            log_every=trace_log_every,
            max_rows=trace_max_rows,
        )

    if monitor_dir is not None:
        monitor_path = Path(monitor_dir)
        monitor_path.mkdir(parents=True, exist_ok=True)
        filename = monitor_path / f"env_{rank}.monitor.csv"
        env = GoalAwareMonitor(env, str(filename), info_keywords=MONITOR_INFO_KEYWORDS)

    return env


def make_env_factory(
    config: dict[str, Any],
    *,
    seed: int,
    rank: int = 0,
    render_mode: str | None = None,
    render_width: int | None = None,
    render_height: int | None = None,
    monitor_dir: str | Path | None = None,
    trace_dir: str | Path | None = None,
    trace_log_every: int = 1,
    trace_max_rows: int | None = None,
) -> Callable[[], gym.Env]:
    def _init() -> gym.Env:
        env = make_single_env(
            config,
            seed=seed,
            rank=rank,
            render_mode=render_mode,
            render_width=render_width,
            render_height=render_height,
            monitor_dir=monitor_dir,
            trace_dir=trace_dir,
            trace_log_every=trace_log_every,
            trace_max_rows=trace_max_rows,
        )
        env.reset(seed=seed + rank)
        return env

    return _init


def make_vec_env(
    config: dict[str, Any],
    *,
    seed: int,
    monitor_dir: str | Path | None = None,
    trace_dir: str | Path | None = None,
) -> VecEnv:
    env_config = config.get("env", {})
    trace_config = config.get("train", {}).get("tracking", {}).get("step_trace", {})
    trace_enabled = bool(trace_config.get("enabled", False))
    resolved_trace_dir = trace_dir if trace_enabled else None
    n_envs = int(env_config.get("n_envs", 1))
    factories = [
        make_env_factory(
            config,
            seed=seed,
            rank=rank,
            monitor_dir=monitor_dir,
            trace_dir=resolved_trace_dir,
            trace_log_every=int(trace_config.get("log_every", 1)),
            trace_max_rows=trace_config.get("max_rows"),
        )
        for rank in range(n_envs)
    ]

    if n_envs > 1 and env_config.get("vec_env", "dummy") == "subproc":
        return SubprocVecEnv(factories)
    return DummyVecEnv(factories)
