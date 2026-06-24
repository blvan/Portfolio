# SAC Multi-Seed Summary

Final SAC curriculum results across three deterministic 100-episode evaluations.

| Seed | Steps | Train seconds | Goal success | Grasp success | Pick success | Mean collisions | Mean reward |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 42 | 400000 | 3281.8 | 1.00 | 1.00 | 1.00 | 0.00 | 309.93 |
| 123 | 500000 | 4477.1 | 1.00 | 1.00 | 1.00 | 0.00 | 301.33 |
| 2026 | 600000 | 8458.9 | 1.00 | 1.00 | 1.00 | 0.00 | 323.88 |

Aggregate mean +/- std:

- `train_seconds`: 5405.9183 +/- 2710.6506
- `total_timesteps`: 500000.0000 +/- 100000.0000
- `eval_goal_success_rate`: 1.0000 +/- 0.0000
- `eval_grasp_success_rate`: 1.0000 +/- 0.0000
- `eval_pick_success_rate`: 1.0000 +/- 0.0000
- `eval_mean_collision_count`: 0.0000 +/- 0.0000
- `eval_mean_reward`: 311.7116 +/- 11.3815

Conclusion: the final SAC curriculum reached stable goal, grasp, and pick success for
all tested seeds, with zero mean evaluation collisions.
