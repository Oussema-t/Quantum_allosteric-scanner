#!/bin/bash
# TASK-0159: run the 5-target finite-time convergence check sequentially
# (not 5-way parallel -- that caused 5-26x contention slowdown on the
# first attempt) and OS-detached (nohup/disown -- harness-tracked
# background execution does not survive a session/process teardown,
# which killed the first attempt ~15-18min in with zero targets
# completed). Sequential total estimate ~4.45h at solo-calibrated rates.
set -e
cd "$(dirname "$0")/.."
for target in KRAS_G12C BCR_ABL1 CARDIAC_MYOSIN PTP1B CASPASE7; do
  echo "=== starting $target at $(date) ==="
  ../.venv/bin/python scripts/task0159_finite_time_convergence_check.py --target "$target"
  echo "=== finished $target at $(date) ==="
done
echo "=== ALL TARGETS DONE at $(date) ==="
