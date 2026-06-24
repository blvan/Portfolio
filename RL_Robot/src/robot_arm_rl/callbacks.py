from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from stable_baselines3.common.callbacks import BaseCallback

from robot_arm_rl.envs import make_single_env


class ProgressEvalCallback(BaseCallback):
    """Periodic deterministic eval snapshots during training."""

    FIELDNAMES = (
        "timesteps",
        "training_stage_id",
        "training_stage_name",
        "episodes",
        "mean_reward",
        "goal_success_rate",
        "grasp_success_rate",
        "pick_success_rate",
        "mean_collision_count",
        "mean_object_goal_distance_final",
        "mean_gripper_object_distance_min",
        "mean_object_lift_max",
    )

    def __init__(
        self,
        config: dict[str, Any],
        output_path: str | Path,
        *,
        eval_freq: int,
        episodes: int = 5,
        deterministic: bool = True,
        early_stopping: dict[str, Any] | None = None,
        verbose: int = 0,
    ):
        super().__init__(verbose=verbose)
        self.config = config
        self.output_path = Path(output_path)
        self.eval_freq = max(1, int(eval_freq))
        self.episodes = max(1, int(episodes))
        self.deterministic = bool(deterministic)
        self.early_stopping = early_stopping or {}
        self.stop_reason: str | None = None
        self.stopped_at_timesteps: int | None = None
        self.best_metric_value: float | None = None
        self.best_metric_timesteps: int | None = None
        self.stage_stop_reason: str | None = None
        self._stage_index = 0
        self._stage_name = "default"
        self._stage_started_timesteps = 0
        self._stage_advance: dict[str, Any] = {}
        self._target_hits = 0
        self._stage_target_hits = 0
        self._no_improvement_evals = 0
        self._last_eval_timestep = 0
        self._env = None
        self._handle = None
        self._writer = None

    def _on_training_start(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        append = self.output_path.exists() and self.output_path.stat().st_size > 0
        self._handle = self.output_path.open("a" if append else "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._handle, fieldnames=self.FIELDNAMES)
        if not append:
            self._writer.writeheader()
        self._env = make_single_env(
            self.config,
            seed=int(self.config["seed"]) + 30_000,
            monitor_dir=None,
        )

    def _on_step(self) -> bool:
        if self.num_timesteps - self._last_eval_timestep < self.eval_freq:
            return True

        self._last_eval_timestep = int(self.num_timesteps)
        row = self._evaluate()
        row["timesteps"] = int(self.num_timesteps)
        row["training_stage_id"] = int(self._stage_index)
        row["training_stage_name"] = self._stage_name
        self._writer.writerow(row)
        self._handle.flush()
        if self.verbose:
            print(
                "[progress_eval] "
                f"timesteps={row['timesteps']} reward={row['mean_reward']:.3f} "
                f"goal={row['goal_success_rate']:.2f} pick={row['pick_success_rate']:.2f}"
            )
        if not self._check_stage_advance(row):
            return False
        return self._check_early_stopping(row)

    def set_stage_control(
        self,
        stage_index: int,
        stage_name: str,
        advance_when: dict[str, Any] | None = None,
    ) -> None:
        self._stage_index = int(stage_index)
        self._stage_name = str(stage_name)
        self._stage_started_timesteps = int(self.num_timesteps)
        self._stage_advance = advance_when or {}
        self._stage_target_hits = 0
        self.stage_stop_reason = None

    def clear_stage_stop(self) -> None:
        self.stage_stop_reason = None

    def _on_training_end(self) -> None:
        if self._env is not None:
            self._env.close()
            self._env = None
        if self._handle is not None:
            self._handle.close()
            self._handle = None
            self._writer = None

    def _evaluate(self) -> dict[str, float]:
        rewards = []
        goal_successes = []
        grasp_successes = []
        pick_successes = []
        collisions = []
        object_goal_distances = []
        gripper_object_distances = []
        object_lifts = []
        for episode_index in range(self.episodes):
            observation, _ = self._env.reset(seed=int(self.config["seed"]) + 30_000 + episode_index)
            done = False
            reward_sum = 0.0
            final_info: dict[str, Any] = {}
            while not done:
                action, _ = self.model.predict(observation, deterministic=self.deterministic)
                observation, reward, terminated, truncated, info = self._env.step(action)
                reward_sum += float(reward)
                done = bool(terminated or truncated)
                final_info = info

            rewards.append(reward_sum)
            goal_successes.append(float(final_info.get("episode_success", final_info.get("is_success", 0.0))))
            grasp_successes.append(float(final_info.get("episode_grasp_success", 0.0)))
            pick_successes.append(float(final_info.get("episode_pick_success", 0.0)))
            collisions.append(float(final_info.get("episode_collision_count", 0.0)))
            object_goal_distances.append(float(final_info.get("episode_object_goal_distance_final", 0.0)))
            gripper_object_distances.append(
                float(final_info.get("episode_gripper_object_distance_min", 0.0))
            )
            object_lifts.append(float(final_info.get("episode_object_lift_max", 0.0)))

        return {
            "episodes": float(self.episodes),
            "mean_reward": sum(rewards) / len(rewards),
            "goal_success_rate": sum(goal_successes) / len(goal_successes),
            "grasp_success_rate": sum(grasp_successes) / len(grasp_successes),
            "pick_success_rate": sum(pick_successes) / len(pick_successes),
            "mean_collision_count": sum(collisions) / len(collisions),
            "mean_object_goal_distance_final": sum(object_goal_distances)
            / len(object_goal_distances),
            "mean_gripper_object_distance_min": sum(gripper_object_distances)
            / len(gripper_object_distances),
            "mean_object_lift_max": sum(object_lifts) / len(object_lifts),
        }

    def _check_stage_advance(self, row: dict[str, Any]) -> bool:
        if not self._stage_advance.get("enabled", False):
            return True

        stage_elapsed = int(self.num_timesteps) - self._stage_started_timesteps
        min_timesteps = int(self._stage_advance.get("min_timesteps", 0))
        if stage_elapsed < min_timesteps:
            return True

        metric_name = str(self._stage_advance.get("metric", "mean_reward"))
        mode = str(self._stage_advance.get("mode", "max"))
        target = self._stage_advance.get("target")
        if target is None:
            return True

        metric_value = _metric_value(row, metric_name)
        target_patience = max(1, int(self._stage_advance.get("target_patience_evals", 1)))
        reached = _is_target_reached(metric_value, float(target), mode)
        self._stage_target_hits = self._stage_target_hits + 1 if reached else 0
        if self._stage_target_hits >= target_patience:
            self.stage_stop_reason = (
                f"stage_advance:{self._stage_name}:"
                f"{metric_name}={metric_value:.4f} target={float(target):.4f}"
            )
            if self.verbose:
                print(
                    "[stage_advance] "
                    f"timesteps={self.num_timesteps} reason={self.stage_stop_reason}"
                )
            return False

        return True

    def _check_early_stopping(self, row: dict[str, Any]) -> bool:
        if not self.early_stopping.get("enabled", False):
            return True

        min_timesteps = int(self.early_stopping.get("min_timesteps", 0))
        if self.num_timesteps < min_timesteps:
            return True

        mode = str(self.early_stopping.get("mode", "max"))
        metric_name = str(self.early_stopping.get("metric", "goal_success_rate"))
        metric_value = _metric_value(row, metric_name)

        target = self.early_stopping.get("target")
        if target is not None:
            target_patience = max(1, int(self.early_stopping.get("target_patience_evals", 1)))
            reached = _is_target_reached(metric_value, float(target), mode)
            self._target_hits = self._target_hits + 1 if reached else 0
            if self._target_hits >= target_patience:
                self._stop(
                    f"target_reached:{metric_name}={metric_value:.4f} "
                    f"target={float(target):.4f}"
                )
                return False

        patience_evals = int(self.early_stopping.get("patience_evals", 0))
        if patience_evals <= 0:
            return True

        patience_metric_name = str(self.early_stopping.get("patience_metric", metric_name))
        patience_metric_value = _metric_value(row, patience_metric_name)
        min_delta = float(self.early_stopping.get("min_delta", 0.0))

        if self.best_metric_value is None or _is_improved(
            patience_metric_value,
            self.best_metric_value,
            min_delta,
            mode,
        ):
            self.best_metric_value = patience_metric_value
            self.best_metric_timesteps = int(self.num_timesteps)
            self._no_improvement_evals = 0
            return True

        self._no_improvement_evals += 1
        if self._no_improvement_evals >= patience_evals:
            self._stop(
                f"plateau:{patience_metric_name}={patience_metric_value:.4f} "
                f"best={self.best_metric_value:.4f} "
                f"patience_evals={patience_evals}"
            )
            return False

        return True

    def _stop(self, reason: str) -> None:
        self.stop_reason = reason
        self.stopped_at_timesteps = int(self.num_timesteps)
        if self.verbose:
            print(f"[early_stop] timesteps={self.num_timesteps} reason={reason}")


def _metric_value(row: dict[str, Any], metric_name: str) -> float:
    if metric_name not in row:
        valid = ", ".join(sorted(row))
        raise ValueError(f"Unknown early-stopping metric `{metric_name}`. Valid metrics: {valid}")
    return float(row[metric_name])


def _is_target_reached(value: float, target: float, mode: str) -> bool:
    if mode == "min":
        return value <= target
    if mode == "max":
        return value >= target
    raise ValueError("early_stopping.mode must be `max` or `min`.")


def _is_improved(value: float, best: float, min_delta: float, mode: str) -> bool:
    if mode == "min":
        return value < best - min_delta
    if mode == "max":
        return value > best + min_delta
    raise ValueError("early_stopping.mode must be `max` or `min`.")
