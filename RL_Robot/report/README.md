# Report

Curated assignment outputs live here. Keep this as the only tracked report root.

- `PPO/`: PPO evaluation outputs.
- `SAC/`: SAC evaluation outputs, videos, and process graphs.
- `Compare/`: cross-algorithm and reward-function comparisons.

The main written summary is `Compare/assignment_summary/final_results.md`.

Generate process visuals with:

```bash
python -m robot_arm_rl.training_report --runs-dir artifacts/runs_sac_curriculum --output-dir report/SAC/curriculum_process
```

Expected outputs include time-reward, timestep-reward, reward-component,
success/collision, behavior-stage, step-trace, and periodic-evaluation graphs.
