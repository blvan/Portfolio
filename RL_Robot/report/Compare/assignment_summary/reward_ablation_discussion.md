# Reward Ablation Discussion

## Why 300k steps were not enough

The 300k reward-ablation runs are useful as an early-learning comparison, but they are
too short to judge final pick-and-place performance. At 300k steps, dense, shaped, and
penalized runs all still had very low final evaluation success:

| Algorithm | Reward | Eval goal success | Eval grasp success | Eval pick success | Last-100 training success |
| --- | --- | ---: | ---: | ---: | ---: |
| PPO | dense | 0.02 | 0.00 | N/A | 0.03 |
| PPO | shaped | 0.02 | 0.00 | N/A | 0.03 |
| PPO | penalized | 0.02 | 0.00 | 0.00 | 0.05 |
| SAC | dense | 0.02 | 0.00 | N/A | 0.08 |
| SAC | shaped | 0.02 | 0.00 | N/A | 0.09 |
| SAC | penalized | 0.03 | 0.00 | 0.00 | 0.08 |

This means the policies were mostly still in the reach/contact exploration phase.
They occasionally reached the goal condition, but they did not learn reliable grasping
or object lifting. Because the task has a multi-stage dependency chain, the final
success signal appears late: reach the cube, make useful gripper contact, lift it,
transport it, and place it near the target. If any early stage is unstable, the
evaluation success remains close to zero even when the reward curve improves.

The later SAC runs show why this matters. A longer shaped SAC run reached 100/100
success after 1M steps, and the curriculum SAC run reached 100/100 success with early
stopping at 400k steps. The difference was not only more compute, but also a reward
schedule that separated reaching, lifting, and placing. Therefore, the 300k ablation
should be interpreted as a stability and exploration comparison, not as a complete
answer about final task performance.

## Collision penalty impact

The collision penalty did reduce measured training contacts, but it did not improve
the final behavior at 300k steps.

| Algorithm | Base comparison | Training collision change | Eval success change | Grasp/pick result |
| --- | --- | ---: | ---: | --- |
| PPO | shaped -> penalized | 970 -> 254 contacts (-73.8%) | 0.02 -> 0.02 | 0.00 grasp, 0.00 pick |
| SAC | shaped -> penalized | 219 -> 143 contacts (-34.7%) | 0.02 -> 0.03 | 0.00 grasp, 0.00 pick |

The important detail is that final evaluation collisions were already zero or nearly
zero for the failed policies. In this setting, "no collisions" often means the arm
failed quietly, not that it learned safe manipulation. The penalty made policies more
conservative during training, but at 300k steps it did not produce a better grasping
strategy. For SAC, the penalized run slightly reduced contact count, but it also had
lower training grasp frequency than shaped reward. That suggests the penalty should be
introduced later, after the agent can already lift the object, or scaled more weakly so
it does not discourage useful gripper-object interaction.
