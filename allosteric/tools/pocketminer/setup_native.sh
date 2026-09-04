#!/usr/bin/env bash
# PocketMiner WITHOUT Docker, on Apple Silicon macOS.  Verified working 2026-09-01.
#
# Why not the Docker recipe in this directory (Dockerfile/predict.py, from
# Oussema-t/Quantum_allosteric-scanner branch bartosz, TASK-0269)? That recipe is
# correct and still the fallback -- it was written on a host with python 3.13, where
# PocketMiner (needs 3.7-3.9) could not run natively at all. THIS host has
# /usr/bin/python3 == 3.9.6, already in range, so a container is unnecessary.
#
# Two dead ends were tried first and are recorded so nobody repeats them:
#  1. Rosetta/x86_64 (`arch -x86_64`), mirroring the Dockerfile's --platform linux/amd64.
#     Everything installs -- and then TensorFlow ABORTS on import:
#       "The TensorFlow library was compiled to use AVX instructions, but these aren't
#        available on your machine"  -> Abort trap: 6
#     Rosetta 2 does not emulate AVX, and every macOS x86_64 TF wheel requires it. Dead,
#     not fixable by pinning. (Docker's linux/amd64 path works because its emulation
#     does provide AVX.)
#  2. tensorflow<=2.9 native arm64: no such wheel exists. 2.13 is the oldest
#     tensorflow-macos with a macOS arm64 cp39 wheel.
#
# So: native arm64 + TF 2.13. That is ABOVE upstream's tested ceiling (<=2.9) and forces
# one code change (see predict_native.py: the checkpoint needs
# tf.keras.optimizers.legacy.Adam on TF>=2.11). Both deviations are validated end to end
# by validate_port.py, which scores upstream's own held-out test set and reproduces their
# published performance -- pooled AUC 0.868 over 35 structures / 1846 labelled residues,
# against ~0.87 reported in Meller et al. 2023 (Nat Commun 14:2135). Re-run it after any
# change to these pins; a broken restore or shifted preprocessing collapses it toward 0.5.
set -euo pipefail
cd "$(dirname "$0")"
V="$PWD/.venv-arm"
/usr/bin/python3 -m venv "$V"          # 3.9.6, native arm64
P="$V/bin/python"
"$P" -m pip install --upgrade pip -q
# numpy is pinned LAST on purpose: mdtraj's source build pulls numpy 1.26, which is newer
# than TF 2.13 accepts, so it gets rolled back afterwards. Both are numpy-1.x ABI, so the
# already-compiled mdtraj extension keeps working -- verified by importing both together.
"$P" -m pip install -q --only-binary=:all: \
  "numpy==1.24.3" "scipy==1.10.1" "tensorflow-macos==2.13.0" "tqdm" "scikit-learn"
"$P" -m pip install -q "mdtraj==1.10.3"     # no arm64 wheel: builds from source (~2 min)
"$P" -m pip install -q "numpy==1.24.3"      # roll back mdtraj's numpy bump, see above
[ -d gvp ] || git clone -q https://github.com/Mickdub/gvp.git gvp
git -C gvp checkout -q 187062df3c94127e991669768009141a08fd5d8b \
  || { echo "!! pinned commit gone; falling back to pocket_pred HEAD"; git -C gvp checkout -q pocket_pred; }
echo ">>> versions:"
"$P" -c "import platform,numpy,mdtraj,tensorflow as tf;print(' arch',platform.machine());\
print(' tf',tf.__version__);print(' numpy',numpy.__version__);print(' mdtraj',mdtraj.__version__)"
echo ">>> setup OK.  Next:"
echo "      ./.venv-arm/bin/python validate_port.py            # confirm the port (expect pooled AUC ~0.87)"
echo "      ./.venv-arm/bin/python predict_native.py input output"
