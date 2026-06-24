# SAC Curriculum Run Summary

Run folder: `artifacts/runs_sac_curriculum/20260510_003902_sac_curriculum_air`

## Training Outcome

- Algorithm: SAC
- Reward: shaped air-goal curriculum
- Requested timesteps: 1,200,000
- Actual timesteps: 400,000
- Stop reason: early stop, `pick_success_rate=1.0000`
- Training time: 5,079.1 seconds

## 100-Episode Evaluation

- Mean reward: 309.93
- Goal success: 100/100
- Grasp success: 100/100
- Pick-and-place success: 100/100
- Collisions: 0 total
- Mean final object-goal distance: 0.0237 m
- Mean gripper-object minimum distance: 0.0094 m
- Mean max object lift: 0.1911 m

## Progress Snapshots

- 100k: reward -11.45, pick success 0.00
- 200k: reward 84.56, pick success 0.50
- 300k: reward 277.03, pick success 1.00
- 400k: reward 318.78, pick success 1.00

## Key Visual Artifacts

- `time_reward.png`
- `timestep_reward.png`
- `entity_reward_components.png`
- `success_collision_over_time.png`
- `stage_behavior.png`
- `step_trace_diagnostics.png`
- `progress_eval_snapshots.png`
- `videos/training_progress_sequence.mp4`
- `videos/training_progress_grid.mp4`
- `videos/training_progress_sequence.gif`
- `goal_scenarios/final_model_goal_scenarios_sequence.mp4`
- `goal_scenarios/final_model_goal_scenarios_sequence.gif`
- `goal_scenarios/final_model_air_goals_grid.mp4`
- `../../Compare/rich_process_comparison/algorithm_reward_comparison.png`
- `../../Compare/final_visual_board/visual_board.png`
- `../../Compare/final_visual_board/index.html`

## Interpretation

The first curriculum attempt over-rewarded lifting and produced a failure mode where the
cube was lifted very high without being placed. The fixed reward caps lift reward at the
target height and penalizes height overshoot, so the agent learns placement instead of
launching. After the fix, SAC reached stable pick-and-place success by 300k-400k steps.
