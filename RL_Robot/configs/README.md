# Configs

Training configs are split by algorithm:

- `PPO/` contains PPO experiments.
- `SAC/` contains SAC experiments.

Use paths such as `configs/PPO/ppo_shaped_air.yaml` and `configs/SAC/sac_shaped_air.yaml`
when running `robot_arm_rl.train`.

`configs/SAC/sac_curriculum_air.yaml` is the recommended SAC research config for final
experiments. It uses an air target, staged shaped rewards, 8 parallel environments,
step tracing, periodic evaluation snapshots, checkpointing, adaptive stage advancement,
and early stopping.

The main early-stopping knobs are under:

```yaml
train:
  tracking:
    progress_eval:
      early_stopping:
        enabled: true
        min_timesteps: 300000
        metric: pick_success_rate
        target: 0.95
        patience_metric: mean_reward
        patience_evals: 4
```

This means the run can stop when pick-and-place success is stable, or when evaluation
reward no longer improves after several long evaluation windows.

Stage advancement is configured on individual stages with `advance_when`. For example,
the reach stage can move on once the gripper-object distance is low enough:

```yaml
advance_when:
  enabled: true
  metric: mean_gripper_object_distance_min
  mode: min
  target: 0.07
```

The shaped SAC reward caps lift reward at the desired goal height. This prevents the
agent from learning the bad local optimum where it lifts the cube very high instead of
moving it to the target. Use `height_overshoot_penalty_weight` in final placement stages
to punish going above the target height.
