# Artifacts

Training runs write models, monitor logs, evaluation outputs, checkpoints, and traces
under this directory.

Most artifact folders are ignored by git because they can become very large. Selected
compact runs may be preserved when they are needed for reports or demonstrations.

Local cleanup folders:

- `old_runs/`: older root-level run folders moved out of the project root.
- `old_reports/`: legacy generated report outputs that are no longer part of `report/`.
