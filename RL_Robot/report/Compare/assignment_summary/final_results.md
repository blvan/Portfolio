# Robot Arm RL Final Results

## Final PPO vs SAC table

The equal-step comparison uses the same shaped air-goal setup for PPO and SAC at
1,000,000 training steps. The curriculum SAC row reports the final SAC implementation
as a three-seed mean with standard deviation.

| Model | Algorithm | Reward setup | Seed | Steps | Train time | Success rate | Grasp rate | Pick rate | Mean collisions |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PPO shaped air 1M | PPO | shaped air-goal | 42 | 1,000,000 | 265.6 s / 4.4 min | 0.00 | 0.00 | 0.00 | 0.00 |
| SAC shaped air 1M | SAC | shaped air-goal | 42 | 1,000,000 | 8,712.3 s / 145.2 min | 1.00 | 1.00 | 1.00 | 0.00 |
| SAC curriculum air multi-seed | SAC | curriculum shaped air-goal | 42, 123, 2026 | 500,000 +/- 100,000 | 5,405.9 +/- 2,710.7 s / 90.1 +/- 45.2 min | 1.00 +/- 0.00 | 1.00 +/- 0.00 | 1.00 +/- 0.00 | 0.00 +/- 0.00 |

Main reading: PPO was much faster per timestep, but it did not solve the strict
air-goal pick-and-place task. SAC required substantially more wall-clock time, but
it reached stable grasping, lifting, and placement success. The curriculum version
solved the task for all three tested seeds and early-stopped before the requested
1.2M-step budget.

## 1M air-goal shaped comparison

Same task setup for both algorithms: shaped reward, air-goal target, seed 42, 100 evaluation episodes.

| Algorithm | Reward | Steps | Train seconds | Mean reward | Goal success | Grasp success | Pick success | Mean collisions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PPO | shaped | 1000000 | 265.6 | -13.03 | 0/100 (0.00) | 0/100 (0.00) | 0/100 (0.00) | 0.00 |
| SAC | shaped | 1000000 | 8712.3 | 130.63 | 100/100 (1.00) | 100/100 (1.00) | 100/100 (1.00) | 0.00 |

Conclusion: PPO did not solve the stricter air-goal pick-and-place task after 1M steps. It reached 0/100 goal, grasp, and pick success on evaluation. SAC solved the same setup with 100/100 goal, grasp, and pick success.

## 300k reward ablation

Dense and shaped rows come from `report/Compare/reward_ablation_300k/comparison.csv`. Penalized rows were trained and evaluated from `artifacts/runs_reward_ablation_penalized` and saved under `report/Compare/reward_ablation_penalized_300k`.

| Algorithm | Reward | Steps | Train seconds | Mean reward | Goal success | Grasp success | Pick success | Mean collisions | Reward rolling std20 | Train last100 success |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PPO | dense | 300000 | 394.1 | -12.86 | 2/100 (0.02) | 0/100 (0.00) | N/A | 0.00 | 1.47 | 0.03 |
| PPO | shaped | 300000 | 401.0 | -12.19 | 2/100 (0.02) | 0/100 (0.00) | N/A | 0.00 | 4.61 | 0.03 |
| PPO | penalized | 300000 | 318.3 | -13.74 | 2/100 (0.02) | 0/100 (0.00) | 0/100 (0.00) | 0.00 | 4.57 | 0.05 |
| SAC | dense | 300000 | 3265.2 | -12.86 | 2/100 (0.02) | 0/100 (0.00) | N/A | 0.00 | 1.37 | 0.08 |
| SAC | shaped | 300000 | 3281.3 | -12.64 | 2/100 (0.02) | 0/100 (0.00) | N/A | 0.00 | 4.89 | 0.09 |
| SAC | penalized | 300000 | 2494.2 | -12.97 | 3/100 (0.03) | 0/100 (0.00) | 0/100 (0.00) | 0.00 | 4.93 | 0.08 |

Notes:

- Dense and shaped 300k runs were created before `pick_success` was added to the comparison CSV, so those pick-success cells are marked `N/A`.
- Penalized reward did not improve evaluation success in this setup: PPO penalized reached 2/100 goal success and SAC penalized reached 3/100 goal success, with 0/100 grasp and pick success for both.
- The penalized SAC training curve showed short improvement bursts, but they did not stabilize by the final evaluation.
- The strongest result remains SAC on the air-goal shaped 1M setup.

### Why 300k steps were not enough for reward ablation

The 300k reward-ablation runs are useful for comparing early learning, but they are
too short to judge final pick-and-place performance. All dense, shaped, and penalized
300k runs stayed near zero final evaluation success: PPO dense/shaped/penalized reached
only 2/100 goal success, SAC dense/shaped reached 2/100, and SAC penalized reached
3/100. More importantly, every row had 0/100 final grasp success, and the penalized
runs had 0/100 pick success.

This shows that the policies were still mostly in the reach/contact exploration phase.
The task has a long dependency chain: reach the cube, make useful gripper contact,
lift it, transport it, and place it near the target. If grasping and lifting are not
stable, the final success metric stays close to zero even when the reward curve or
last-100 training success improves slightly. For example, SAC shaped had 0.09 last-100
training success at 300k, but still only 2/100 deterministic evaluation success and
0/100 grasp success.

The later successful runs support this interpretation. The 1M shaped SAC run reached
100/100 success, and the curriculum SAC run reached 100/100 success with early stopping
at 400k by separating reaching, lifting, and placing. Therefore, the 300k ablation is
best treated as an early stability/exploration comparison, not as a final ranking of
reward functions.

### Collision penalty impact

The collision penalty reduced measured training contacts, but it did not improve the
final behavior at 300k steps.

| Algorithm | Base comparison | Training collisions | Change | Eval goal success | Eval grasp success | Eval pick success |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| PPO | shaped -> penalized | 970 -> 254 | -73.8% | 0.02 -> 0.02 | 0.00 -> 0.00 | N/A -> 0.00 |
| SAC | shaped -> penalized | 219 -> 143 | -34.7% | 0.02 -> 0.03 | 0.00 -> 0.00 | N/A -> 0.00 |

The main conclusion is that fewer contacts did not mean better manipulation. Final
evaluation collisions were already zero for the failed policies, because many episodes
ended without robust object interaction. In this setting, "no collisions" can mean the
arm failed quietly rather than learned safe pick-and-place behavior. The penalty made
training more conservative, but at 300k it did not create a stable grasping strategy.
For future runs, the collision penalty should be introduced after the agent can already
lift the cube, or kept weaker so it does not discourage useful gripper-object contact.

## Multi-seed SAC evaluation

The final SAC curriculum was evaluated across seeds `42`, `123`, and `2026` with
100 deterministic evaluation episodes per seed.

| Seed | Steps to stop | Train seconds | Goal success | Grasp success | Pick success | Mean collisions | Mean reward |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 42 | 400,000 | 3,281.8 | 1.00 | 1.00 | 1.00 | 0.00 | 309.93 |
| 123 | 500,000 | 4,477.1 | 1.00 | 1.00 | 1.00 | 0.00 | 301.33 |
| 2026 | 600,000 | 8,458.9 | 1.00 | 1.00 | 1.00 | 0.00 | 323.88 |

Aggregate result:

- Training steps: `500,000 +/- 100,000`
- Training time: `5,405.9 +/- 2,710.7 s`
- Goal success: `1.0000 +/- 0.0000`
- Grasp success: `1.0000 +/- 0.0000`
- Pick success: `1.0000 +/- 0.0000`
- Mean collision count: `0.0000 +/- 0.0000`
- Mean reward: `311.71 +/- 11.38`

The final SAC curriculum solved the task consistently across all tested seeds. The
number of training steps before early stopping varied, but the final evaluation metrics
were stable.

## Files

- `report/Compare/assignment_summary/ppo_vs_sac_air_shaped_1m_summary.csv`
- `report/Compare/assignment_summary/final_ppo_vs_sac_table.csv`
- `report/Compare/assignment_summary/reward_ablation_discussion.md`
- `report/Compare/assignment_summary/collision_penalty_impact.csv`
- `report/Compare/assignment_summary/sac_multiseed_evaluation.md`
- `report/SAC/multiseed_curriculum/sac_multiseed_summary.csv`
- `report/Compare/assignment_summary/reward_ablation_300k_summary.csv`
- `report/Compare/ppo_vs_sac_air_shaped_1m/comparison.csv`
- `report/Compare/ppo_vs_sac_air_shaped_1m/comparison.png`
- `report/Compare/reward_ablation_penalized_300k/comparison.csv`
- `report/Compare/reward_ablation_penalized_300k/comparison.png`
