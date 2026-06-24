# SAC Multi-Seed Evaluation

The final SAC curriculum was evaluated across three seeds using the same reward
schedule, environment configuration, and deterministic 100-episode evaluation protocol.

Seeds:

- `42`
- `123`
- `2026`

Execution command:

```bash
python scripts/run_sac_multiseed.py --seeds 42 123 2026 --run-root artifacts/runs_sac_multiseed --output-dir report/SAC/multiseed_curriculum --device cuda --torch-threads 2 --skip-existing --rich-report
```

## Results

| Seed | Steps | Train seconds | Goal success | Grasp success | Pick success | Mean collisions | Mean reward |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 42 | 400,000 | 3,281.8 | 1.00 | 1.00 | 1.00 | 0.00 | 309.93 |
| 123 | 500,000 | 4,477.1 | 1.00 | 1.00 | 1.00 | 0.00 | 301.33 |
| 2026 | 600,000 | 8,458.9 | 1.00 | 1.00 | 1.00 | 0.00 | 323.88 |

Aggregate mean +/- standard deviation:

- Training steps: `500,000 +/- 100,000`
- Training time: `5,405.9 +/- 2,710.7 s`
- Goal success: `1.0000 +/- 0.0000`
- Grasp success: `1.0000 +/- 0.0000`
- Pick success: `1.0000 +/- 0.0000`
- Mean collision count: `0.0000 +/- 0.0000`
- Mean reward: `311.71 +/- 11.38`

The final SAC curriculum solved the task consistently for all tested seeds. The number
of steps to early stopping varied by seed, but evaluation success, grasping, picking,
and collision metrics were stable.
