from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any

import torch
from stable_baselines3.common.callbacks import CallbackList, CheckpointCallback

from robot_arm_rl.callbacks import ProgressEvalCallback
from robot_arm_rl.config import load_config, save_config
from robot_arm_rl.envs import make_vec_env
from robot_arm_rl.paths import DEFAULT_RUN_ROOT, make_run_dir
from robot_arm_rl.sb3 import build_model_kwargs, get_algorithm_class


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train PPO or SAC on FetchPickAndPlace.")
    parser.add_argument("--config", required=True, help="Path to a YAML config.")
    parser.add_argument(
        "--run-root",
        default=str(DEFAULT_RUN_ROOT),
        help="Directory where training runs and model artifacts are stored.",
    )
    parser.add_argument("--run-name", default=None, help="Override experiment name.")
    parser.add_argument("--seed", type=int, default=None, help="Override config seed.")
    parser.add_argument("--total-timesteps", type=int, default=None, help="Override training timesteps.")
    parser.add_argument("--device", default="auto", help="Torch device: auto, cpu, cuda.")
    parser.add_argument("--n-envs", type=int, default=None, help="Override number of parallel envs.")
    parser.add_argument("--vec-env", choices=["dummy", "subproc"], default=None, help="Override vec env type.")
    parser.add_argument(
        "--torch-threads",
        type=int,
        default=None,
        help="Limit PyTorch CPU threads. Use 1-4 when using many MuJoCo subprocesses.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    if args.seed is not None:
        config["seed"] = args.seed
    if args.total_timesteps is not None:
        if config.get("train", {}).get("stages"):
            _scale_stage_timesteps(config["train"]["stages"], args.total_timesteps)
        else:
            config["train"]["total_timesteps"] = args.total_timesteps
    if args.n_envs is not None:
        config["env"]["n_envs"] = args.n_envs
    if args.vec_env is not None:
        config["env"]["vec_env"] = args.vec_env
    if args.torch_threads is not None:
        os.environ["OMP_NUM_THREADS"] = str(args.torch_threads)
        os.environ["MKL_NUM_THREADS"] = str(args.torch_threads)
        torch.set_num_threads(args.torch_threads)
        try:
            torch.set_num_interop_threads(max(1, min(args.torch_threads, 4)))
        except RuntimeError:
            pass

    experiment_name = args.run_name or config.get("experiment_name") or Path(args.config).stem
    run_dir = make_run_dir(experiment_name, args.run_root)
    save_config(config, run_dir / "config.yaml")

    monitor_dir = run_dir / "monitor"
    trace_dir = run_dir / "trace"
    checkpoint_dir = run_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    env = make_vec_env(
        config,
        seed=int(config["seed"]),
        monitor_dir=monitor_dir,
        trace_dir=trace_dir,
    )
    algorithm_name = config["algorithm"]["name"].upper()
    algorithm_cls = get_algorithm_class(algorithm_name)
    model_kwargs = build_model_kwargs(config)

    model = algorithm_cls(
        "MultiInputPolicy",
        env,
        verbose=1,
        tensorboard_log=str(run_dir / "tensorboard"),
        seed=int(config["seed"]),
        device=args.device,
        **model_kwargs,
    )

    checkpoint_freq = max(1, int(config["train"].get("checkpoint_freq", 25_000)))
    n_envs = int(config.get("env", {}).get("n_envs", 1))
    callbacks = [
        CheckpointCallback(
            save_freq=max(1, checkpoint_freq // n_envs),
            save_path=str(checkpoint_dir),
            name_prefix="model",
            save_replay_buffer=algorithm_name == "SAC",
            save_vecnormalize=False,
        )
    ]
    progress_callback: ProgressEvalCallback | None = None
    progress_eval_config = config.get("train", {}).get("tracking", {}).get("progress_eval", {})
    if progress_eval_config.get("enabled", False):
        progress_callback = ProgressEvalCallback(
            config,
            run_dir / "progress" / "eval_snapshots.csv",
            eval_freq=int(progress_eval_config.get("eval_freq", checkpoint_freq)),
            episodes=int(progress_eval_config.get("episodes", 5)),
            deterministic=bool(progress_eval_config.get("deterministic", True)),
            early_stopping=progress_eval_config.get("early_stopping"),
            verbose=1,
        )
        callbacks.append(progress_callback)
    callback = CallbackList(callbacks)

    stages = _resolve_training_stages(config)
    requested_total_timesteps = sum(stage["timesteps"] for stage in stages)
    started = time.perf_counter()
    stage_metadata = []
    early_stop: dict[str, Any] | None = None
    for stage_index, stage in enumerate(stages):
        stage_started = time.perf_counter()
        stage_start_timesteps = int(model.num_timesteps)
        _apply_training_stage(env, stage_index, stage)
        if progress_callback:
            progress_callback.set_stage_control(
                stage_index,
                str(stage["name"]),
                stage.get("advance_when"),
            )
        model.learn(
            total_timesteps=int(stage["timesteps"]),
            callback=callback,
            log_interval=int(config["train"].get("log_interval", 10)),
            tb_log_name=experiment_name,
            reset_num_timesteps=stage_index == 0,
        )
        stage_seconds = time.perf_counter() - stage_started
        stage_model_path = checkpoint_dir / (
            f"stage_{stage_index + 1:02d}_{_slugify(stage['name'])}.zip"
        )
        model.save(str(stage_model_path))
        actual_stage_timesteps = int(model.num_timesteps) - stage_start_timesteps
        stage_stop_reason = progress_callback.stage_stop_reason if progress_callback else None
        stage_metadata.append(
            {
                "index": stage_index + 1,
                "name": stage["name"],
                "timesteps": actual_stage_timesteps,
                "requested_timesteps": int(stage["timesteps"]),
                "train_seconds": stage_seconds,
                "model_path": str(stage_model_path),
                "shaped_reward": stage.get("shaped_reward"),
                "advance_when": stage.get("advance_when"),
                "stop_reason": stage_stop_reason,
            }
        )
        if progress_callback and stage_stop_reason:
            progress_callback.clear_stage_stop()
            continue
        if progress_callback and progress_callback.stop_reason:
            early_stop = {
                "reason": progress_callback.stop_reason,
                "timesteps": progress_callback.stopped_at_timesteps,
                "best_metric_value": progress_callback.best_metric_value,
                "best_metric_timesteps": progress_callback.best_metric_timesteps,
            }
            break
    elapsed_seconds = time.perf_counter() - started

    model_path = run_dir / "final_model.zip"
    model.save(str(model_path))
    env.close()

    metadata: dict[str, Any] = {
        "run_dir": str(run_dir),
        "experiment_name": experiment_name,
        "algorithm": algorithm_name,
        "reward": config["env"]["reward"],
        "seed": int(config["seed"]),
        "total_timesteps": int(model.num_timesteps),
        "requested_total_timesteps": requested_total_timesteps,
        "n_envs": int(config.get("env", {}).get("n_envs", 1)),
        "vec_env": config.get("env", {}).get("vec_env", "dummy"),
        "device": args.device,
        "train_seconds": elapsed_seconds,
        "model_path": str(model_path),
        "stages": stage_metadata,
        "early_stop": early_stop,
    }
    with (run_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print(f"Saved run to {run_dir}")
    print(f"Training time: {elapsed_seconds:.1f} seconds")


def _resolve_training_stages(config: dict[str, Any]) -> list[dict[str, Any]]:
    configured_stages = config.get("train", {}).get("stages")
    if not configured_stages:
        return [
            {
                "name": "default",
                "timesteps": int(config["train"]["total_timesteps"]),
                "shaped_reward": None,
            }
        ]

    stages = []
    for index, stage in enumerate(configured_stages):
        if "timesteps" not in stage:
            raise ValueError(f"Training stage {index + 1} is missing required `timesteps`.")
        stages.append(
            {
                "name": str(stage.get("name", f"stage_{index + 1}")),
                "timesteps": int(stage["timesteps"]),
                "shaped_reward": stage.get("shaped_reward"),
                "advance_when": stage.get("advance_when"),
            }
        )

    return stages


def _scale_stage_timesteps(stages: list[dict[str, Any]], total_timesteps: int) -> None:
    original_total = sum(int(stage["timesteps"]) for stage in stages)
    if original_total <= 0:
        raise ValueError("Cannot scale train.stages because their total timesteps is zero.")

    allocated = 0
    for index, stage in enumerate(stages):
        if index == len(stages) - 1:
            stage["timesteps"] = max(1, int(total_timesteps) - allocated)
        else:
            scaled = max(1, round(int(stage["timesteps"]) * int(total_timesteps) / original_total))
            stage["timesteps"] = scaled
            allocated += scaled


def _apply_training_stage(env, stage_index: int, stage: dict[str, Any]) -> None:
    stage_name = str(stage["name"])
    try:
        env.env_method("set_training_stage", stage_index, stage_name)
    except AttributeError:
        pass

    shaped_reward = stage.get("shaped_reward")
    if shaped_reward:
        try:
            env.env_method("set_shaped_reward_config", shaped_reward)
        except AttributeError as exc:
            raise RuntimeError(
                "Config uses train.stages[].shaped_reward, but the environment does not "
                "expose set_shaped_reward_config(). Use reward: shaped/penalized."
            ) from exc


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower()).strip("_")
    return slug or "stage"


if __name__ == "__main__":
    main()
