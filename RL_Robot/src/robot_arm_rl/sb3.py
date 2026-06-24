from __future__ import annotations

from typing import Any

from stable_baselines3 import PPO, SAC


ALGORITHMS = {
    "PPO": PPO,
    "SAC": SAC,
}


def get_algorithm_class(name: str):
    try:
        return ALGORITHMS[name.upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported algorithm '{name}'. Use PPO or SAC.") from exc


def build_model_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    algorithm_config = config.get("algorithm", {})
    kwargs = dict(algorithm_config.get("kwargs", {}))

    if algorithm_config.get("name", "").upper() == "SAC" and algorithm_config.get("use_her", False):
        kwargs["replay_buffer_class"] = _load_her_replay_buffer()
        kwargs["replay_buffer_kwargs"] = dict(algorithm_config.get("her", {}))

    if "train_freq" in kwargs and isinstance(kwargs["train_freq"], list):
        kwargs["train_freq"] = tuple(kwargs["train_freq"])

    return kwargs


def _load_her_replay_buffer():
    try:
        from stable_baselines3 import HerReplayBuffer

        return HerReplayBuffer
    except ImportError:
        from stable_baselines3.her.her_replay_buffer import HerReplayBuffer

        return HerReplayBuffer
