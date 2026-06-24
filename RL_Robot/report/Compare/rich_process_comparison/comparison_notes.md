# Rich Comparison Notes

This report combines existing completed runs instead of launching another long matrix:

- PPO sparse/dense/shaped at 300k steps
- SAC sparse-HER/dense/shaped at 300k steps
- Old SAC shaped-air at 1M steps
- Fixed SAC curriculum-air at 400k steps

## Main Readout

- Basic PPO/SAC sparse/dense/shaped runs at 300k mostly stayed near 0.02 goal success.
- SAC sparse-HER reached 0.20 goal success at 300k, but was still unreliable.
- Old SAC shaped-air reached 1.00 pick success after 1M steps.
- Fixed SAC curriculum-air reached 1.00 pick success after 400k steps and stopped early.

## Why the New Reward Helped

The previous shaped-air run could solve the task, but it required a much longer run. During
the failed curriculum attempt, the agent exploited an unbounded lift reward and lifted the
cube too high instead of placing it. The fixed reward caps lift reward at the target height
and adds a height-overshoot penalty, which makes placement more attractive than launching.

## Graph Notes

- `algorithm_reward_comparison.png` is now useful because it includes eight completed runs.
- `entity_reward_components.png` now has both the full component view and a zoomed view
  without success bonus, so smaller penalties and distance terms are visible.
- Older runs do not have component-level reward tracking, so component bars are available
  mainly for the new curriculum run.
