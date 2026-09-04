#!/usr/bin/env python3
"""Runs inside the pocketminer Docker image (see this directory's own
Dockerfile). Loads the pretrained PocketMiner model ONCE (upstream's own
`src/xtal_predict.py` reference code loads a fresh model per single-PDB
run -- this script reuses `xtal_predict.make_predictions` directly,
imported unmodified, just looping the model load outside the batch
instead of once per structure, per that script's own suggestion:
"we recommend looping over the entire main method if you would like to
make predictions for multiple structures").

Contract: every `*.pdb` file in /data/input is scored; one
`<stem>.txt` (one float per residue, upstream's own `xtal_predict.py`
output convention, `%.4g` newline-delimited) is written to
/data/output per input file. A structure that fails to parse or predict
writes `<stem>.error.txt` with the exception text instead of crashing the
whole batch -- one bad structure must not silently lose the other 19.
"""
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, "/opt/gvp/src")

import numpy as np
import tensorflow as tf
from models import MQAModel
from xtal_predict import make_predictions

IN_DIR = Path("/data/input")
OUT_DIR = Path("/data/output")

DROPOUT_RATE = 0.1
NUM_LAYERS = 4
HIDDEN_DIM = 100
NN_PATH = "/opt/gvp/models/pocketminer"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdb_paths = sorted(IN_DIR.glob("*.pdb"))
    print(f"found {len(pdb_paths)} structures in {IN_DIR}", flush=True)

    model = MQAModel(
        node_features=(8, 50), edge_features=(1, 32),
        hidden_dim=(16, HIDDEN_DIM), num_layers=NUM_LAYERS, dropout=DROPOUT_RATE,
    )

    n_ok = 0
    for pdb_path in pdb_paths:
        stem = pdb_path.stem
        try:
            preds = make_predictions([str(pdb_path)], model, NN_PATH)
            arr = np.asarray(preds[0]).reshape(-1)
            np.savetxt(OUT_DIR / f"{stem}.txt", arr, fmt="%.6g", delimiter="\n")
            print(f"{stem}: OK, n_residues={len(arr)}, mean={arr.mean():.4f}", flush=True)
            n_ok += 1
        except Exception:  # noqa: BLE001 -- one bad structure must not kill the batch
            (OUT_DIR / f"{stem}.error.txt").write_text(traceback.format_exc())
            print(f"{stem}: FAILED, see {stem}.error.txt", flush=True)

    print(f"\n{n_ok}/{len(pdb_paths)} succeeded", flush=True)
    return 0 if n_ok == len(pdb_paths) else 1


if __name__ == "__main__":
    raise SystemExit(main())
