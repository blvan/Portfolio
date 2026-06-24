# Final PPO vs SAC Table

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
