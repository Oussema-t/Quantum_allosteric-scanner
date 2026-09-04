#!/usr/bin/env bash
# Build + run PocketMiner over every *.pdb the notebook exported to ./input,
# writing one <TARGET>.txt (one score per residue) to ./output.
# Recipe from Oussema-t/Quantum_allosteric-scanner, branch bartosz,
# __WORK_IN_PROGRESS__/tools/pocketminer/ (TASK-0269). Do not edit the pins.
set -euo pipefail
cd "$(dirname "$0")"
command -v docker >/dev/null || { echo "docker not found -- install Docker Desktop first"; exit 1; }
n=$(ls input/*.pdb 2>/dev/null | wc -l | tr -d ' ')
[ "$n" -gt 0 ] || { echo "no structures in ./input -- run notebook cell 18 with PM_EXPORT=True"; exit 1; }
echo ">>> $n structure(s) to score"
docker build --platform linux/amd64 -t qas-pocketminer:pocket_pred .
docker run --rm --platform linux/amd64 \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  qas-pocketminer:pocket_pred
echo ">>> done. Re-run notebook cell 18 to load ./output/*.txt"
ls -la output/
