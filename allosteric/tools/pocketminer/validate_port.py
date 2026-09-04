#!/usr/bin/env python3
"""Does this TF-2.13 / legacy-optimizer port reproduce upstream PocketMiner?

Upstream pinned TensorFlow<=2.9; this environment runs 2.13 (no macOS arm64 wheel
exists below 2.13) and had to pass `tf.keras.optimizers.legacy.Adam` explicitly.
Both are real deviations from the published setup, so the port must be validated
against something external before any number it produces is trusted.

The repo ships its own held-out test set -- data/pm-dataset/{test_apo_ids_with_chainids,
test_label_dictionary}.npy plus the apo structures -- so this scores exactly those and
reports per-structure ROC-AUC against the authors' own labels. If the port is faithful,
the distribution should match the paper's reported held-out performance; if the weights
were silently not restored, or the preprocessing shifted, AUC would collapse to ~0.5.
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "gvp", "src"))
import numpy as np, mdtraj as md, tensorflow as tf, logging
tf.get_logger().setLevel(logging.ERROR)
from models import MQAModel
from validate_performance_on_xtals import process_strucs, predict_on_xtals
from sklearn.metrics import roc_auc_score

D = os.path.join(HERE, "gvp", "data", "pm-dataset")
ids = np.load(os.path.join(D, "test_apo_ids_with_chainids.npy"), allow_pickle=True)
lab = np.load(os.path.join(D, "test_label_dictionary.npy"), allow_pickle=True).item()
model = MQAModel(node_features=(8,50), edge_features=(1,32), hidden_dim=(16,100),
                 num_layers=4, dropout=0.1)
NN = os.path.join(HERE, "gvp", "models", "pocketminer")

aucs, skipped, pooled_y, pooled_p = [], [], [], []
n_scored = [0]
for pid in ids:
    f = os.path.join(D, "apo-structures", "%s_clean_h.pdb" % pid)
    if not os.path.exists(f):
        skipped.append((pid, "no structure file")); continue
    y = lab.get(pid) if pid in lab else lab.get(pid[:4])
    if y is None:
        skipped.append((pid, "no labels")); continue
    y = np.asarray(y).reshape(-1)
    try:
        X, S, mask = process_strucs([md.load(f)])
        p = np.asarray(predict_on_xtals(model, NN, X, S, mask,
                                        opt=tf.keras.optimizers.legacy.Adam()))[0].reshape(-1)
    except Exception as e:
        skipped.append((pid, "predict failed: %s" % type(e).__name__)); continue
    if len(p) != len(y):
        skipped.append((pid, "len %d vs %d" % (len(p), len(y)))); continue
    # Label convention is the authors' own, from src/test_performance_on_xtal_residues.py:
    #   test_label_mask = (l != 2)      -> label 2 means UNLABELLED, excluded from scoring
    # leaving {0 = negative, 1 = cryptic-site positive}. (Do not confuse this with
    # multiclass_train_fold.py's "pos_label is 2" -- that is a different label encoding
    # for a different task, not the one test_label_dictionary.npy uses.)
    keep = (y != 2)
    yb = (y[keep] == 1).astype(int); pk = p[keep]
    if keep.sum() == 0:
        skipped.append((pid, "all residues unlabelled (label 2)")); continue
    # Every structure contributes to the POOLED array. Per-protein AUC is undefined here
    # by construction: in this dataset a given protein's labelled residues are either all
    # positive (a cryptic-site structure) or all negative (a control), never both -- which
    # is precisely why the authors score one flat pooled array across proteins rather than
    # averaging per-protein AUCs.
    pooled_y.append(yb); pooled_p.append(pk)
    n_scored[0] += 1
    if 0 < yb.sum() < len(yb):
        aucs.append((pid, roc_auc_score(yb, pk), int(keep.sum()), int(yb.sum())))
    print("  %-8s labelled=%-4d pos=%-4d meanPred(pos)=%s meanPred(neg)=%s"
          % (pid, int(keep.sum()), int(yb.sum()),
             ("%.3f" % pk[yb == 1].mean()) if yb.sum() else "  -  ",
             ("%.3f" % pk[yb == 0].mean()) if (yb == 0).sum() else "  -  "), flush=True)

print("\n=== PORT VALIDATION on upstream's own held-out test set ===")
if pooled_y:
    print("scored %d/%d structures (per-protein AUC undefined here, see note above)"
          % (n_scored[0], len(ids)))
    Y = np.concatenate(pooled_y); P = np.concatenate(pooled_p)
    print("POOLED across proteins (the authors' own aggregation): AUC=%.3f on %d labelled "
          "residues, %d positive (%.1f%%)"
          % (roc_auc_score(Y, P), len(Y), int(Y.sum()), 100.0 * Y.mean()))
else:
    print("NOTHING SCORED -- port not validated")
if skipped:
    print("skipped %d:" % len(skipped))
    for pid, why in skipped[:12]: print("   %-10s %s" % (pid, why))
