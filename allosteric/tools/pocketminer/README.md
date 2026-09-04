# PocketMiner (vendored via Docker) — TASK-0269

**What this is.** Meller, Ward, Borowsky, Kshirsagar, Lotthammer, Oviedo,
Ferres, Bowman (2023), *Nature Communications* 14:2135,
doi:[10.1038/s41467-023-36699-3](https://doi.org/10.1038/s41467-023-36699-3).
The one purpose-built cryptic-pocket-*opening* predictor in this register's
own comparison set ([[TASK-0260]]) — trained on MD-derived labels, but its
own inference is MD-free (a single static structure in, a per-residue
opening-probability array out).

**Why Docker, not this repo's own `.venv`.** PocketMiner needs Python
3.7–3.9 + TensorFlow ≤2.9 (upstream's own `README.md`: tested down to
2.1.0, up through 2.6.2/2.9.1). This repo's toolchain is Python 3.13 /
TensorFlow 2.16. A native `pyenv install 3.9.18` was attempted twice
(plain, and with Homebrew `openssl@3` flags) — both builds complete but
`_ssl` fails to compile: CPython 3.9 predates general OpenSSL 3.x support,
and Homebrew has removed `openssl@1.1` entirely. A container with an OS old
enough to ship the right OpenSSL sidesteps the problem — the route this
task's own filing names as "the known-good path," and the one used here.

**Why `--platform linux/amd64`.** The build/run host is Apple Silicon
(arm64). TensorFlow 2.6.2 wheels are not reliably published for
`linux/arm64` on PyPI at this vintage; `linux/amd64` wheels are guaranteed
to exist. Docker Desktop's Rosetta-backed emulation handles the mismatch
transparently, at a real but bounded speed cost for a one-shot 20-structure
inference batch (not a training workload — timed directly, see this task's
own Done section for the measured wall-clock).

## Build

```
cd tools/pocketminer
docker build --platform linux/amd64 -t qas-pocketminer:pocket_pred .
```

Pins:
- Base image: `python:3.9-slim-bullseye`.
- PocketMiner: `Mickdub/gvp`, `pocket_pred` branch, commit
  `187062df3c94127e991669768009141a08fd5d8b` (confirmed as that branch's
  HEAD via the GitHub API on 2026-08-26 — a commit SHA, not a branch name,
  since a branch can move under a later push and a SHA cannot).
- Python deps: `numpy==1.19.5 scipy==1.5.4 pandas==1.1.5 tensorflow==2.6.2
  tqdm==4.62.3 mdtraj==1.9.7` — the exact versions upstream's own
  `linux-requirements.txt` lock file pins (the closest thing to an
  authoritative version this upstream repo provides), not the unpinned
  `pocketminer.yml`.
- Model weights: `models/pocketminer.{index,data-00000-of-00001}` (~9 MB)
  are committed in the upstream repo itself — confirmed directly via the
  GitHub tree API before writing the Dockerfile, no separate download
  needed.

## Run

`predict.py` (this directory, `COPY`'d into the image, the container's own
entrypoint) scores every `*.pdb` in a bind-mounted input directory and
writes one `<stem>.txt` (per-residue opening probability, one float per
line, upstream's own output convention) to a bind-mounted output
directory per input structure. A structure that fails writes
`<stem>.error.txt` instead of aborting the whole batch.

```
docker run --rm --platform linux/amd64 \
  -v /path/to/input:/data/input:ro \
  -v /path/to/output:/data/output \
  qas-pocketminer:pocket_pred
```

`scripts/task0269_pocketminer_residual.py` drives this end to end (exports
the frozen set's apo structures, invokes the container, reads the
per-residue arrays back, feeds them into the existing Shapley/cluster-robust
attribution pipeline) — see that script's own docstring, not duplicated
here.

## Constraint-3 status

Flagged to the organisers ([[TASK-0221]] item (f), re-sent standalone as
Q7 on 2026-08-26) — **still open as of this tool's first real run**.
Proceeding under this register's own provisional reading (MD used only for
the external authors' *training* labels; our own inference supplies zero
trajectories — legal under Constraint 3's literal text, the same reading
already applied to P2Rank/HYP-S7). Any result produced by this tool must
carry that caveat until an organiser answer arrives — do not cite it as
organiser-endorsed.

## Not vendored here

PocketMiner's own source is cloned fresh inside the Docker build (pinned by
commit SHA, see above) — not copied into this repository. Same convention
`tools/fpocket/`/`tools/p2rank/` already use for their own upstream
binaries: the *recipe* is version-controlled, the third-party payload is
not.
