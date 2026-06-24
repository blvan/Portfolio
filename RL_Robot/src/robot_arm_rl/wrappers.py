from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np


TABLE_HEIGHT = 0.42

REWARD_COMPONENT_KEYS = (
    "reward_environment",
    "reward_total",
    "reward_goal_distance",
    "reward_gripper_distance",
    "reward_lift",
    "reward_height_overshoot",
    "reward_success_bonus",
    "reward_action_penalty",
    "reward_collision_penalty",
)

STATE_TRACKING_KEYS = (
    "object_goal_distance",
    "gripper_object_distance",
    "object_lift",
    "goal_lift",
    "action_norm",
)

EPISODE_TRACKING_INFO_KEYS = (
    "training_stage_id",
    "episode_object_goal_distance_mean",
    "episode_object_goal_distance_final",
    "episode_gripper_object_distance_mean",
    "episode_gripper_object_distance_min",
    "episode_gripper_object_distance_final",
    "episode_object_lift_mean",
    "episode_object_lift_max",
    "episode_object_lift_final",
    "episode_goal_lift_final",
    "episode_action_norm_mean",
    "episode_reward_environment_mean",
    "episode_reward_total_mean",
    "episode_reward_goal_distance_mean",
    "episode_reward_gripper_distance_mean",
    "episode_reward_lift_mean",
    "episode_reward_height_overshoot_mean",
    "episode_reward_success_bonus_mean",
    "episode_reward_action_penalty_mean",
    "episode_reward_collision_penalty_mean",
    "episode_stage_reach_fraction",
    "episode_stage_grasp_fraction",
    "episode_stage_transport_fraction",
    "episode_stage_success_fraction",
)


def call_goal_env_method(env: gym.Env, method_name: str, achieved_goal, desired_goal, info):
    method = getattr(env, method_name, None)
    if callable(method):
        return method(achieved_goal, desired_goal, info)

    get_wrapper_attr = getattr(env, "get_wrapper_attr", None)
    if callable(get_wrapper_attr):
        try:
            method = get_wrapper_attr(method_name)
        except AttributeError:
            method = None
        if callable(method):
            return method(achieved_goal, desired_goal, info)

    unwrapped = getattr(env, "unwrapped", None)
    method = getattr(unwrapped, method_name, None)
    if callable(method):
        return method(achieved_goal, desired_goal, info)

    raise AttributeError(f"{type(env).__name__} does not expose {method_name}().")


class GoalEnvPassthroughMixin:
    def compute_reward(self, achieved_goal, desired_goal, info):
        return call_goal_env_method(self.env, "compute_reward", achieved_goal, desired_goal, info)

    def compute_terminated(self, achieved_goal, desired_goal, info):
        return call_goal_env_method(self.env, "compute_terminated", achieved_goal, desired_goal, info)

    def compute_truncated(self, achieved_goal, desired_goal, info):
        return call_goal_env_method(self.env, "compute_truncated", achieved_goal, desired_goal, info)


@dataclass(frozen=True)
class MetricsConfig:
    grasp_lift_threshold: float = 0.03
    grasp_distance_threshold: float = 0.07
    place_lift_threshold: float = 0.08


@dataclass(frozen=True)
class AirGoalConfig:
    enabled: bool = False
    min_height_above_table: float = 0.10
    max_height_above_table: float = 0.25


@dataclass(frozen=True)
class ShapedRewardConfig:
    goal_distance_weight: float = 1.0
    gripper_distance_weight: float = 0.2
    lift_weight: float = 0.8
    height_overshoot_penalty_weight: float = 0.0
    success_bonus: float = 2.0
    action_penalty_weight: float = 0.01
    collision_penalty_weight: float = 0.0


class PickPlaceMetricsWrapper(GoalEnvPassthroughMixin, gym.Wrapper):
    """Adds project metrics to Farama Fetch pick-and-place environments."""

    def __init__(self, env: gym.Env, config: MetricsConfig | None = None):
        super().__init__(env)
        self.config = config or MetricsConfig()
        self._episode_goal_success = False
        self._episode_grasp_success = False
        self._episode_pick_success = False
        self._episode_collision_count = 0
        self._training_stage_id = 0
        self._training_stage_name = "default"
        self._reset_tracking_state()

    def reset(self, **kwargs: Any):
        self._episode_goal_success = False
        self._episode_grasp_success = False
        self._episode_pick_success = False
        self._episode_collision_count = 0
        self._reset_tracking_state()
        return self.env.reset(**kwargs)

    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        info = dict(info)
        reward_float = float(reward)

        info.setdefault("reward_environment", reward_float)
        info.setdefault("reward_total", reward_float)
        for component_key in REWARD_COMPONENT_KEYS:
            info.setdefault(component_key, 0.0)

        grasp_now = self._detect_grasp(observation)
        if grasp_now:
            self._episode_grasp_success = True

        goal_success_now = bool(float(info.get("is_success", 0.0)))
        if goal_success_now:
            self._episode_goal_success = True

        pick_success_now = self._detect_pick_success(observation, goal_success_now)
        if pick_success_now:
            self._episode_pick_success = True

        collision_count = self._count_unexpected_contacts()
        self._episode_collision_count += collision_count
        state_metrics = self._state_metrics(observation, action)
        behavior_stage = self._behavior_stage_id(
            state_metrics["gripper_object_distance"],
            state_metrics["object_lift"],
            goal_success_now,
        )
        self._update_tracking_state(state_metrics, info, behavior_stage)

        info["goal_success_now"] = float(goal_success_now)
        info["grasp_now"] = float(grasp_now)
        info["pick_success_now"] = float(pick_success_now)
        info["episode_success"] = float(self._episode_goal_success)
        info["episode_grasp_success"] = float(self._episode_grasp_success)
        info["episode_pick_success"] = float(self._episode_pick_success)
        info["collision_events_step"] = float(collision_count)
        info["episode_collision_count"] = float(self._episode_collision_count)
        info["training_stage_id"] = float(self._training_stage_id)
        info["behavior_stage_id"] = float(behavior_stage)

        for key, value in state_metrics.items():
            info[key] = float(value)
        info.update(self._episode_tracking_info())

        return observation, reward, terminated, truncated, info

    def set_training_stage(self, stage_id: int = 0, stage_name: str = "default") -> None:
        self._training_stage_id = int(stage_id)
        self._training_stage_name = str(stage_name)

    def _reset_tracking_state(self) -> None:
        self._episode_steps = 0
        self._state_sums = {key: 0.0 for key in STATE_TRACKING_KEYS}
        self._reward_sums = {key: 0.0 for key in REWARD_COMPONENT_KEYS}
        self._stage_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        self._object_goal_distance_final = 0.0
        self._gripper_object_distance_final = 0.0
        self._gripper_object_distance_min = float("inf")
        self._object_lift_final = 0.0
        self._object_lift_max = 0.0
        self._goal_lift_final = 0.0

    def _state_metrics(self, observation: dict[str, np.ndarray], action) -> dict[str, float]:
        raw_obs = observation.get("observation")
        achieved_goal = observation.get("achieved_goal")
        desired_goal = observation.get("desired_goal")
        if raw_obs is None or achieved_goal is None or desired_goal is None:
            return {key: 0.0 for key in STATE_TRACKING_KEYS}

        gripper_position = np.asarray(raw_obs[0:3], dtype=np.float64)
        object_position = np.asarray(achieved_goal, dtype=np.float64)
        goal_position = np.asarray(desired_goal, dtype=np.float64)

        return {
            "object_goal_distance": float(np.linalg.norm(object_position - goal_position)),
            "gripper_object_distance": float(np.linalg.norm(gripper_position - object_position)),
            "object_lift": float(object_position[2] - TABLE_HEIGHT),
            "goal_lift": float(goal_position[2] - TABLE_HEIGHT),
            "action_norm": float(np.linalg.norm(np.asarray(action, dtype=np.float64))),
        }

    def _behavior_stage_id(
        self,
        gripper_object_distance: float,
        object_lift: float,
        goal_success_now: bool,
    ) -> int:
        if goal_success_now:
            return 3
        if object_lift >= self.config.place_lift_threshold:
            return 2
        if gripper_object_distance <= self.config.grasp_distance_threshold:
            return 1
        return 0

    def _update_tracking_state(
        self,
        state_metrics: dict[str, float],
        info: dict[str, Any],
        behavior_stage: int,
    ) -> None:
        self._episode_steps += 1
        self._stage_counts[behavior_stage] += 1

        for key in STATE_TRACKING_KEYS:
            value = float(state_metrics.get(key, 0.0))
            self._state_sums[key] += value

        for key in REWARD_COMPONENT_KEYS:
            self._reward_sums[key] += float(info.get(key, 0.0))

        self._object_goal_distance_final = float(state_metrics["object_goal_distance"])
        self._gripper_object_distance_final = float(state_metrics["gripper_object_distance"])
        self._gripper_object_distance_min = min(
            self._gripper_object_distance_min,
            self._gripper_object_distance_final,
        )
        self._object_lift_final = float(state_metrics["object_lift"])
        self._object_lift_max = max(self._object_lift_max, self._object_lift_final)
        self._goal_lift_final = float(state_metrics["goal_lift"])

    def _episode_tracking_info(self) -> dict[str, float]:
        steps = max(1, self._episode_steps)
        return {
            "episode_object_goal_distance_mean": self._state_sums["object_goal_distance"] / steps,
            "episode_object_goal_distance_final": self._object_goal_distance_final,
            "episode_gripper_object_distance_mean": self._state_sums[
                "gripper_object_distance"
            ]
            / steps,
            "episode_gripper_object_distance_min": (
                0.0
                if self._gripper_object_distance_min == float("inf")
                else self._gripper_object_distance_min
            ),
            "episode_gripper_object_distance_final": self._gripper_object_distance_final,
            "episode_object_lift_mean": self._state_sums["object_lift"] / steps,
            "episode_object_lift_max": self._object_lift_max,
            "episode_object_lift_final": self._object_lift_final,
            "episode_goal_lift_final": self._goal_lift_final,
            "episode_action_norm_mean": self._state_sums["action_norm"] / steps,
            "episode_reward_environment_mean": self._reward_sums["reward_environment"]
            / steps,
            "episode_reward_total_mean": self._reward_sums["reward_total"] / steps,
            "episode_reward_goal_distance_mean": self._reward_sums["reward_goal_distance"]
            / steps,
            "episode_reward_gripper_distance_mean": self._reward_sums[
                "reward_gripper_distance"
            ]
            / steps,
            "episode_reward_lift_mean": self._reward_sums["reward_lift"] / steps,
            "episode_reward_height_overshoot_mean": self._reward_sums[
                "reward_height_overshoot"
            ]
            / steps,
            "episode_reward_success_bonus_mean": self._reward_sums[
                "reward_success_bonus"
            ]
            / steps,
            "episode_reward_action_penalty_mean": self._reward_sums[
                "reward_action_penalty"
            ]
            / steps,
            "episode_reward_collision_penalty_mean": self._reward_sums[
                "reward_collision_penalty"
            ]
            / steps,
            "episode_stage_reach_fraction": self._stage_counts[0] / steps,
            "episode_stage_grasp_fraction": self._stage_counts[1] / steps,
            "episode_stage_transport_fraction": self._stage_counts[2] / steps,
            "episode_stage_success_fraction": self._stage_counts[3] / steps,
        }

    def _detect_grasp(self, observation: dict[str, np.ndarray]) -> bool:
        raw_obs = observation.get("observation")
        achieved_goal = observation.get("achieved_goal")
        if raw_obs is None or achieved_goal is None:
            return False

        gripper_position = np.asarray(raw_obs[0:3], dtype=np.float64)
        object_position = np.asarray(achieved_goal, dtype=np.float64)
        object_lift = float(object_position[2] - TABLE_HEIGHT)
        gripper_object_distance = float(np.linalg.norm(gripper_position - object_position))

        return (
            object_lift >= self.config.grasp_lift_threshold
            and gripper_object_distance <= self.config.grasp_distance_threshold
        )

    def _detect_pick_success(
        self,
        observation: dict[str, np.ndarray],
        goal_success_now: bool,
    ) -> bool:
        achieved_goal = observation.get("achieved_goal")
        desired_goal = observation.get("desired_goal")
        if achieved_goal is None or desired_goal is None:
            return False

        object_position = np.asarray(achieved_goal, dtype=np.float64)
        goal_position = np.asarray(desired_goal, dtype=np.float64)
        object_lift = float(object_position[2] - TABLE_HEIGHT)
        goal_lift = float(goal_position[2] - TABLE_HEIGHT)

        return (
            goal_success_now
            and object_lift >= self.config.place_lift_threshold
            and goal_lift >= self.config.place_lift_threshold
        )

    def _count_unexpected_contacts(self) -> int:
        model = getattr(self.unwrapped, "model", None)
        data = getattr(self.unwrapped, "data", None)
        if model is None or data is None or not hasattr(data, "ncon"):
            return 0

        count = 0
        for index in range(int(data.ncon)):
            contact = data.contact[index]
            geom_a = self._geom_name(model, int(contact.geom1))
            geom_b = self._geom_name(model, int(contact.geom2))
            if self._is_unexpected_contact(geom_a, geom_b):
                count += 1
        return count

    @staticmethod
    def _geom_name(model, geom_id: int) -> str:
        try:
            name = model.geom(geom_id).name
            return name or f"geom_{geom_id}"
        except Exception:
            return f"geom_{geom_id}"

    @staticmethod
    def _is_unexpected_contact(geom_a: str, geom_b: str) -> bool:
        names = (geom_a.lower(), geom_b.lower())
        joined = " ".join(names)

        if "object0" not in joined or "robot0" not in joined:
            return False

        expected_pairs = (
            ("object0", "finger"),
            ("object0", "l_gripper"),
            ("object0", "r_gripper"),
            ("object0", "gripper"),
            ("object0", "grip"),
            ("object0", "table"),
            ("object0", "floor"),
        )
        for left, right in expected_pairs:
            if left in joined and right in joined:
                return False

        return True


class StepTraceWrapper(GoalEnvPassthroughMixin, gym.Wrapper):
    """Optionally writes sampled step-level diagnostics to CSV for deep visual analysis."""

    FIELDNAMES = (
        "episode",
        "episode_step",
        "global_step",
        "reward",
        "terminated",
        "truncated",
        "is_success",
        "episode_success",
        "episode_grasp_success",
        "episode_pick_success",
        "collision_events_step",
        "episode_collision_count",
        "training_stage_id",
        "behavior_stage_id",
        *STATE_TRACKING_KEYS,
        *REWARD_COMPONENT_KEYS,
    )

    def __init__(
        self,
        env: gym.Env,
        output_path: str | Path,
        *,
        log_every: int = 1,
        max_rows: int | None = None,
    ):
        super().__init__(env)
        self.output_path = Path(output_path)
        self.log_every = max(1, int(log_every))
        self.max_rows = int(max_rows) if max_rows is not None else None
        self._episode_index = 0
        self._episode_step = 0
        self._global_step = 0
        self._rows_written = 0
        self._handle = None
        self._writer = None

    def reset(self, **kwargs: Any):
        if self._global_step > 0 or self._episode_step > 0:
            self._episode_index += 1
        self._episode_step = 0
        return self.env.reset(**kwargs)

    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        self._episode_step += 1
        self._global_step += 1
        if self._should_write():
            self._write_row(reward, terminated, truncated, info)
        return observation, reward, terminated, truncated, info

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
            self._writer = None
        return self.env.close()

    def _should_write(self) -> bool:
        if self.max_rows is not None and self._rows_written >= self.max_rows:
            return False
        return self._global_step % self.log_every == 0

    def _ensure_writer(self):
        if self._writer is not None:
            return self._writer
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.output_path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._handle, fieldnames=self.FIELDNAMES)
        self._writer.writeheader()
        return self._writer

    def _write_row(self, reward, terminated, truncated, info: dict[str, Any]) -> None:
        writer = self._ensure_writer()
        row = {
            "episode": self._episode_index,
            "episode_step": self._episode_step,
            "global_step": self._global_step,
            "reward": float(reward),
            "terminated": int(bool(terminated)),
            "truncated": int(bool(truncated)),
        }
        for key in self.FIELDNAMES:
            if key in row:
                continue
            row[key] = float(info.get(key, 0.0))
        writer.writerow(row)
        self._rows_written += 1


class AirGoalWrapper(GoalEnvPassthroughMixin, gym.Wrapper):
    """Forces Fetch pick-and-place goals above the table, preventing push-only success."""

    def __init__(self, env: gym.Env, config: AirGoalConfig | None = None):
        super().__init__(env)
        self.config = config or AirGoalConfig()

    def reset(self, **kwargs: Any):
        observation, info = self.env.reset(**kwargs)
        observation = dict(observation)
        observation["desired_goal"] = self._force_air_goal(observation["desired_goal"])
        return observation, info

    def _force_air_goal(self, desired_goal: np.ndarray) -> np.ndarray:
        goal = np.asarray(desired_goal, dtype=np.float64).copy()
        min_z = TABLE_HEIGHT + self.config.min_height_above_table
        max_z = TABLE_HEIGHT + self.config.max_height_above_table
        goal[2] = float(self.unwrapped.np_random.uniform(min_z, max_z))
        self.unwrapped.goal = goal.copy()
        return goal


class ShapedPickPlaceRewardWrapper(GoalEnvPassthroughMixin, gym.Wrapper):
    """Replaces the native reward with a simple dense shaping signal."""

    def __init__(self, env: gym.Env, config: ShapedRewardConfig | None = None):
        super().__init__(env)
        self.config = config or ShapedRewardConfig()

    def step(self, action):
        observation, native_reward, terminated, truncated, info = self.env.step(action)
        collision_count = self._count_unexpected_contacts()
        reward, components = self._compute_shaped_reward(
            observation,
            action,
            info,
            collision_count,
        )
        info = dict(info)
        info["reward_environment"] = float(native_reward)
        info["reward_total"] = float(reward)
        info.update(components)
        info["native_is_success"] = float(info.get("is_success", 0.0))
        info["shaped_reward"] = float(reward)
        info["shaped_collision_penalty"] = float(
            self.config.collision_penalty_weight * collision_count
        )
        return observation, reward, terminated, truncated, info

    def set_shaped_reward_config(self, config: dict[str, Any]) -> None:
        values = asdict(self.config)
        values.update(config)
        self.config = ShapedRewardConfig(**values)

    def compute_reward(self, achieved_goal, desired_goal, info):
        achieved_goal = np.asarray(achieved_goal)
        desired_goal = np.asarray(desired_goal)
        return -np.linalg.norm(achieved_goal - desired_goal, axis=-1)

    def _compute_shaped_reward(
        self,
        observation: dict[str, np.ndarray],
        action: np.ndarray,
        info: dict[str, Any],
        collision_count: int,
    ) -> tuple[float, dict[str, float]]:
        raw_obs = observation["observation"]
        achieved_goal = np.asarray(observation["achieved_goal"], dtype=np.float64)
        desired_goal = np.asarray(observation["desired_goal"], dtype=np.float64)
        gripper_position = np.asarray(raw_obs[0:3], dtype=np.float64)

        goal_distance = float(np.linalg.norm(achieved_goal - desired_goal))
        gripper_distance = float(np.linalg.norm(gripper_position - achieved_goal))
        lift = max(0.0, float(achieved_goal[2] - TABLE_HEIGHT))
        target_lift = max(0.0, float(desired_goal[2] - TABLE_HEIGHT))
        capped_lift = min(lift, target_lift)
        height_overshoot = max(0.0, lift - target_lift)
        action_penalty = float(np.linalg.norm(np.asarray(action, dtype=np.float64)))
        collision_penalty = float(collision_count)
        success = float(info.get("is_success", 0.0))

        components = {
            "reward_goal_distance": -self.config.goal_distance_weight * goal_distance,
            "reward_gripper_distance": -self.config.gripper_distance_weight
            * gripper_distance,
            "reward_lift": self.config.lift_weight * capped_lift,
            "reward_height_overshoot": -self.config.height_overshoot_penalty_weight
            * height_overshoot,
            "reward_success_bonus": self.config.success_bonus * success,
            "reward_action_penalty": -self.config.action_penalty_weight * action_penalty,
            "reward_collision_penalty": -self.config.collision_penalty_weight
            * collision_penalty,
        }
        return float(sum(components.values())), {key: float(value) for key, value in components.items()}

    def _count_unexpected_contacts(self) -> int:
        model = getattr(self.unwrapped, "model", None)
        data = getattr(self.unwrapped, "data", None)
        if model is None or data is None or not hasattr(data, "ncon"):
            return 0

        count = 0
        for index in range(int(data.ncon)):
            contact = data.contact[index]
            geom_a = PickPlaceMetricsWrapper._geom_name(model, int(contact.geom1))
            geom_b = PickPlaceMetricsWrapper._geom_name(model, int(contact.geom2))
            if PickPlaceMetricsWrapper._is_unexpected_contact(geom_a, geom_b):
                count += 1
        return count
