from __future__ import annotations

import os
import platform

import torch


def main() -> None:
    print(f"Python: {platform.python_version()}")
    print(f"CPU logical cores visible: {os.cpu_count()}")
    print(f"PyTorch CPU threads: {torch.get_num_threads()}")
    print(f"CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        index = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(index)
        total_gb = props.total_memory / 1024**3
        print(f"CUDA device: {torch.cuda.get_device_name(index)}")
        print(f"CUDA memory: {total_gb:.1f} GB")
        print(f"CUDA capability: {props.major}.{props.minor}")
    else:
        print("CUDA device: none")

    print()
    print("Note: Stable-Baselines3/PyTorch/MuJoCo do not use the Ryzen AI NPU for this loop.")
    print("Use the NVIDIA GPU for neural-network updates and CPU subprocesses for MuJoCo envs.")


if __name__ == "__main__":
    main()
