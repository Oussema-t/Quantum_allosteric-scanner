# TASK-0269 -- PocketMiner (Meller et al. 2023, Nat Commun 14:2135,
# doi:10.1038/s41467-023-36699-3) needs Python 3.7-3.9 + TensorFlow<=2.9.
# This machine's own toolchain is Python 3.13 / TensorFlow 2.16, and a
# native pyenv 3.9 build fails to compile _ssl (CPython 3.9 predates
# general OpenSSL 3.x support; Homebrew has removed openssl@1.1 entirely --
# see this task's own Done section for the two failed attempts). A
# container with an OS old enough to ship an OpenSSL 3.9 was built
# against sidesteps the problem entirely -- the route the task's own
# filing names as "the known-good path."
#
# Built and run with --platform linux/amd64 explicitly (see README.md):
# this host is Apple Silicon (arm64) and TensorFlow 2.6-2.9 wheels for
# linux/arm64 are not reliably available on PyPI for this Python/TF
# vintage; x86_64 wheels are guaranteed to exist, and Docker Desktop's
# Rosetta-backed emulation handles the architecture mismatch transparently
# at some (measured, see README.md) speed cost -- acceptable for a
# one-shot 20-structure inference batch, not a training workload.
FROM --platform=linux/amd64 python:3.9-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates build-essential zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Pinned to README.md's own tested range (2.1.0 minimum, "tested with
# 2.6.2 and 2.9.1 as well") -- 2.6.2 chosen as the exact version their own
# linux-requirements.txt lock file pins, the closest thing to an
# authoritative version this upstream repo provides. protobuf pinned
# separately: pip's own default resolution otherwise pulls a protobuf new
# enough that TensorFlow 2.6.2's *generated* _pb2.py files raise
# `TypeError: Descriptors cannot be created directly` at import time (a
# real, reproduced failure, not a guess) -- 3.18.1 is the exact version
# upstream's own linux-requirements.txt lock file pins.
RUN pip install --no-cache-dir \
    numpy==1.19.5 \
    scipy==1.5.4 \
    pandas==1.1.5 \
    protobuf==3.18.1 \
    tensorflow==2.6.2 \
    tqdm==4.62.3

# mdtraj==1.9.7 ships no manylinux wheel for any cp3x (confirmed directly
# against PyPI's own file listing before writing this, not assumed) --
# must build from its own Cython source. Its `.pyx` files fail to compile
# under Cython 3.x (a real, reproducible error, not a guess -- pip's
# default build-isolation otherwise pulls the newest Cython into an
# isolated env pip's own outer `cython<3` pin below cannot reach).
# `--no-build-isolation` makes the build see this environment's own
# pre-installed numpy/Cython instead of resolving its own isolated set,
# the standard workaround for exactly this class of old-package/
# new-build-tool incompatibility.
RUN pip install --no-cache-dir "cython<3" \
    && pip install --no-cache-dir --no-build-isolation mdtraj==1.9.7

# Pinned to the exact commit this task verified, not the branch head (a
# branch name can move under a later push; a commit SHA cannot) --
# `git ls-remote` / GitHub API confirmed 187062d... as pocket_pred's HEAD
# on 2026-08-26, recorded in this task's own Done section.
ARG POCKETMINER_COMMIT=187062df3c94127e991669768009141a08fd5d8b
RUN git clone https://github.com/Mickdub/gvp.git /opt/gvp \
    && cd /opt/gvp \
    && git checkout ${POCKETMINER_COMMIT}

# Model weights (models/pocketminer.{index,data-00000-of-00001}, ~9MB) are
# committed in the upstream repo itself -- no separate download needed,
# confirmed directly via the GitHub tree API before writing this
# Dockerfile, not assumed.

COPY predict.py /opt/predict.py

WORKDIR /opt/gvp/src
ENV PYTHONPATH=/opt/gvp/src
ENTRYPOINT ["python", "/opt/predict.py"]
