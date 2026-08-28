# fpocket (TASK-0163 external dependency)

Built from source, no root/`sudo` needed — `bin/` is gitignored (upstream's own
convention), rebuild locally with:

```bash
git clone --branch 4.2.3 --depth 1 https://github.com/Discngine/fpocket.git src
cd src
make
cp bin/{fpocket,tpocket,dpocket,mdpocket} ../bin/
```

The core `fpocket` binary only needs `libm`/`libstdc++`/`libc`/`libgcc_s`
(confirmed via `ldd`) — the project's own Docker recipe lists `libnetcdf-dev`,
but that's only needed for `mdpocket`'s trajectory-analysis mode, not the
core pocket-detection binary this project's scoring script calls.

Used by `scripts/task0163_external_baseline_scoring.py`
(`FPOCKET_BIN = tools/fpocket/bin/fpocket`).

## Pinning (TASK-0206)

`bin/` is gitignored -- **the binary itself is never version controlled,
only this build recipe is.** [[TASK-0163]]'s original AUCs (0.8348/0.8596/
0.5345, KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN) could not be reproduced by
[[TASK-0200]] on a different machine (0.7910/0.8618/0.5303) — root-caused
to exactly this: two machines, each with their own independently-built,
previously-unpinned `fpocket` binary. `allostery.baselines.
fpocket_provenance(path)` computes a SHA256 fingerprint of whatever binary
is currently at `bin/fpocket` — **do not trust the binary's own printed
version banner** (`fpocket 4.0`), it is stale/hardcoded across the whole
4.x release line, confirmed by comparing this build's own exposed flags
against upstream release notes.

The current pin (SHA256, hostname, and the authoritative AUC set) is
recorded in `PROVENANCE.json`, checked in alongside this README. After
any rebuild, regenerate and diff against that file before trusting a new
run — a changed SHA256 with an unchanged AUC set is fine; a changed SHA256
with a changed AUC set needs the same treatment TASK-0206 gave this one
(both numbers kept on record, dated, neither silently overwritten).

## Docker (TASK-0285)

`bin/fpocket` is now a small Python wrapper, not the native binary — it
shells out to `docker run` and is a drop-in replacement at the exact same
path `scripts/task0163_external_baseline_scoring.py`'s `FPOCKET_BIN`
already points to; no caller changes. The native binary is not required
on the host any more, only Docker.

Build:

```bash
cd tools/fpocket
docker build --platform linux/amd64 -t qas-fpocket:4.2.3 .
```

Same pinned source recipe as above (`git clone --branch 4.2.3`), inside a
`debian:bookworm-slim` base pinned by **digest**, not just tag — a
floating tag was tried first and produced a *third*, still-different AUC
set from both numbers already in `PROVENANCE.json` (see that file's own
`containerized_build_TASK_0285` entry) — real, on-record evidence that a
digest pin, not just "use Docker," is what this reproducibility problem
actually needs.

`--platform linux/amd64` is required even though the build host may be
arm64 (Apple Silicon) — matching `tools/pocketminer/`'s own established
reason: keeps every tool in this project on one known-working emulated
platform rather than chasing per-tool native-arch support.

The wrapper mounts this repository's own root and the system temp root
1:1 (host path == container path) so every existing caller's own
`tempfile.TemporaryDirectory()`-based I/O works unmodified — no argument
rewriting needed. See the wrapper script's own docstring for the exact
mechanism.
