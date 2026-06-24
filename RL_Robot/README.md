# Robot Arm RL

This project trains reinforcement-learning agents to control a Fetch robot arm in
Gymnasium-Robotics. The main task is to pick up a cube and move it to a target
position, then compare PPO and SAC across learning time, success rate, collisions,
and reward-function stability.

## Stack

- Environments: `FetchPickAndPlace-v4`, `FetchPickAndPlaceDense-v4`
- Algorithms: PPO and SAC from Stable-Baselines3
- Robotics backend: Gymnasium-Robotics and MuJoCo
- Reports: CSV summaries, training curves, reward-component plots, videos, and visual boards

Farama references:

- https://robotics.farama.org/index.html
- https://robotics.farama.org/envs/fetch/pick_and_place/
- https://robotics.farama.org/content/multi-goal_api/

## Layout

```text
configs/              PPO and SAC experiment configs
src/robot_arm_rl/     Training, evaluation, wrappers, tracking, reporting
scripts/              Experiment helpers and video/report utilities
artifacts/            Local run outputs and selected preserved model artifacts
report/               Curated experiment report outputs
```

`report/` is the only tracked report root. Legacy report outputs are parked under
`artifacts/old_reports/`.

## Setup

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

WSL or Linux:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

For offscreen MuJoCo rendering on WSL or headless machines:

```bash
export MUJOCO_GL=egl
```

## Smoke Test

```bash
python scripts/smoke_test.py --steps 20
```

The smoke test creates the environment, prints observation/action spaces, and steps a
random policy.

## Training

Short sanity runs:

```bash
python -m robot_arm_rl.train --config configs/PPO/ppo_dense.yaml --total-timesteps 10000
python -m robot_arm_rl.train --config configs/SAC/sac_sparse_her.yaml --total-timesteps 10000
```

SAC air-goal reward comparison:

```bash
python -m robot_arm_rl.train --config configs/SAC/sac_sparse_her_air_parallel.yaml --total-timesteps 400000 --run-root artifacts/runs_sac_compare --device cuda --torch-threads 2
python -m robot_arm_rl.train --config configs/SAC/sac_shaped_air.yaml --total-timesteps 400000 --run-root artifacts/runs_sac_compare --device cuda --torch-threads 2
python -m robot_arm_rl.train --config configs/SAC/sac_penalized_air.yaml --total-timesteps 400000 --run-root artifacts/runs_sac_compare --device cuda --torch-threads 2
```

Curriculum SAC run:

```bash
python -m robot_arm_rl.train --config configs/SAC/sac_curriculum_air.yaml --run-root artifacts/runs_sac_curriculum --device cuda --torch-threads 2
```

The curriculum config uses staged rewards for reaching, lifting, and placing. It also
enables parallel environments, checkpointing, step traces, periodic deterministic
evaluation, adaptive stage advancement, and early stopping.

Full matrix helper:

```bash
python scripts/run_experiment_matrix.py --timesteps 300000 --episodes 100 --skip-existing --rich-report
```

## Evaluation

Evaluate one trained run:

```bash
python -m robot_arm_rl.evaluate --run-dir artifacts/runs_sac_curriculum/RUN_DIR --episodes 100
```

Compare all completed runs in a folder:

```bash
python -m robot_arm_rl.compare --runs-dir artifacts/runs_sac_curriculum --output-dir report/SAC
```

Generate detailed process plots:

```bash
python -m robot_arm_rl.training_report --runs-dir artifacts/runs_sac_curriculum --output-dir report/SAC/curriculum_process
```

The rich report includes reward over time, reward over timesteps, reward components,
success and collision trends, behavior-stage fractions, step-trace diagnostics, and
periodic evaluation snapshots.

## Visualization

Record a policy:

```bash
python -m robot_arm_rl.visualize --run-dir artifacts/runs_sac_curriculum/RUN_DIR --episodes 1 --record --format mp4
```

Record multiple training checkpoints and compose them into one video:

```bash
MUJOCO_GL=egl python scripts/record_training_progress.py --run-dir artifacts/runs_sac_curriculum/RUN_DIR --samples 4 --episodes 1 --format mp4 --fps 12 --compose-layout sequence
```

Record fixed goal scenarios for the final model:

```bash
MUJOCO_GL=egl python scripts/record_goal_scenarios.py --run-dir artifacts/runs_sac_curriculum/RUN_DIR --output-dir report/SAC/curriculum_process/goal_scenarios
```

Build the combined visual board:

```bash
python scripts/build_visual_board.py --run-dir artifacts/runs_sac_curriculum/RUN_DIR --comparison-dir report/Compare/rich_process_comparison --curriculum-dir report/SAC/curriculum_process --scenario-dir report/SAC/curriculum_process/goal_scenarios --output-dir report/Compare/final_visual_board
```

## Multi-Seed SAC

Run the final SAC curriculum across several seeds and summarize mean/std metrics:

```bash
python scripts/run_sac_multiseed.py --seeds 42 123 2026 --run-root artifacts/runs_sac_multiseed --output-dir report/SAC/multiseed_curriculum --device cuda --torch-threads 2 --skip-existing --rich-report
```

The output includes per-seed success, grasp, pick, collision, reward, and training-time
tables under `report/SAC/multiseed_curriculum/`.

## Metrics

- Goal success: the environment reports `is_success` during the episode.
- Pick success: the cube reaches the target while both cube and target are above the table.
- Grasp success: the cube is lifted while staying close to the gripper.
- Collisions: unexpected robot/object contacts per episode, excluding normal gripper contact.
- Stability: reward variance and success trends over training windows.

Thresholds and reward weights are configured in `configs/**/*.yaml`.
