#!/usr/bin/env python3
"""PocketMiner batch inference, native (no Docker).

Same contract as the Docker `predict.py` from TASK-0269 (repo
Oussema-t/Quantum_allosteric-scanner, branch bartosz): score every *.pdb in an
input dir, write one <stem>.txt per structure (one float per residue, one per
line) to an output dir; a structure that fails writes <stem>.error.txt instead
of killing the batch. Only the paths differ -- they come from argv here rather
than from /data/input and /data/output bind mounts.

The model is loaded ONCE and reused across structures, per upstream's own note in
src/xtal_predict.py ("we recommend looping over the entire main method if you
would like to make predictions for multiple structures").

Run it through the x86_64 venv, not the system python:
    arch -x86_64 .venv-x86/bin/python predict_native.py input output
"""
import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "gvp" / "src"))

import numpy as np                                    # noqa: E402
import mdtraj as md                                    # noqa: E402
import tensorflow as tf                                # noqa: E402
from models import MQAModel                            # noqa: E402
from validate_performance_on_xtals import process_strucs, predict_on_xtals   # noqa: E402

# Upstream's own make_predictions() calls predict_on_xtals() without an optimizer, so it
# falls back to that function's default `opt=tf.keras.optimizers.Adam()`. On TensorFlow
# >=2.11 restoring this checkpoint into the new-style optimizer raises
#   ValueError: You are trying to restore a checkpoint from a legacy Keras optimizer
#               into a v2.11+ Optimizer
# (a real, reproduced failure -- upstream pinned TF<=2.9, where the distinction did not
# exist). So we call process_strucs + predict_on_xtals ourselves, unmodified, and pass
# the legacy optimizer explicitly. The optimizer is inference-irrelevant -- it exists only
# because the checkpoint stores optimizer slots alongside the weights -- but the restore
# will not proceed without a compatible one. Verified directly: with legacy.Adam all
# 177/177 trainable variables change value on restore, and the only unmatched checkpoint
# object is `save_counter`, which is bookkeeping, not a weight.
_OPT = tf.keras.optimizers.legacy.Adam

# upstream's own hyperparameters (src/xtal_predict.py) -- do not tune, these
# describe the shape of the PRETRAINED network, they are not free parameters
DROPOUT_RATE = 0.1
NUM_LAYERS = 4
HIDDEN_DIM = 100
NN_PATH = str(HERE / "gvp" / "models" / "pocketminer")


def main(in_dir, out_dir):
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdbs = sorted(in_dir.glob("*.pdb"))
    print("found %d structures in %s" % (len(pdbs), in_dir), flush=True)

    model = MQAModel(node_features=(8, 50), edge_features=(1, 32),
                     hidden_dim=(16, HIDDEN_DIM), num_layers=NUM_LAYERS,
                     dropout=DROPOUT_RATE)

    n_ok = 0
    for pdb in pdbs:
        stem = pdb.stem
        err = out_dir / ("%s.error.txt" % stem)
        try:
            X, S, mask = process_strucs([md.load(str(pdb))])
            preds = predict_on_xtals(model, NN_PATH, X, S, mask, opt=_OPT())
            arr = np.asarray(preds)[0].reshape(-1)          # B=1 -> no L_max padding
            np.savetxt(out_dir / ("%s.txt" % stem), arr, fmt="%.6g", delimiter="\n")
            if err.exists():
                err.unlink()                          # a previous failure is now stale
            print("%s: OK, n_residues=%d, mean=%.4f, max=%.4f"
                  % (stem, len(arr), arr.mean(), arr.max()), flush=True)
            n_ok += 1
        except Exception:      # one bad structure must not lose the rest of the batch
            err.write_text(traceback.format_exc())
            print("%s: FAILED, see %s" % (stem, err), flush=True)

    print("\n%d/%d succeeded" % (n_ok, len(pdbs)), flush=True)
    return 0 if n_ok == len(pdbs) else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    raise SystemExit(main(a[0] if a else HERE / "input", a[1] if len(a) > 1 else HERE / "output"))
