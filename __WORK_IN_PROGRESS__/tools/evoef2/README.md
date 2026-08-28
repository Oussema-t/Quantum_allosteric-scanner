# EvoEF2 (TASK-0204 external dependency)

Vendored classical side-chain rotamer packer — MIT licensed (Xiaoqiang Huang,
Univ. of Michigan), source: https://github.com/tommyhuangthu/EvoEF2. Uses a
real backbone-dependent Dunbrack 2010 rotamer library (`dun2010bb*.lib`,
shipped in its own `library/` directory) and a real pairwise/self energy
function (van der Waals + electrostatics + solvation + H-bond terms) —
sourced, not invented, per this task's own In-Scope requirement to prefer
vendoring an existing solver over hand-rolling an energy function.

Built from source, no root/`sudo` needed — mirrors `tools/fpocket/`'s own
convention. `src/`, `library/`, `wread/`, and the built `EvoEF2` binary are
all gitignored (the `library/` rotamer data alone is ~140 MB, far too large
to commit); rebuild locally with:

```bash
git clone --depth 1 https://github.com/tommyhuangthu/EvoEF2.git evoef2_upstream
cd evoef2_upstream
git apply ../task0204_single_pass_repack.patch
g++ -O3 -o EvoEF2 src/*.cpp
cp EvoEF2 ../EvoEF2
cp -r library wread src ../
```

**The binary must be run from this directory** (`tools/evoef2/`), or with
this directory as the working directory — EvoEF2 resolves `library/`,
`wread/`, and its output filenames via relative paths from its own current
working directory, not from an installed/absolute location (confirmed
directly: running it from elsewhere fails with `IOError` opening
`./wread/weight_EvoEF2.txt`). `scripts/task0204_rotamer_repack_baseline.py`
always invokes it with `cwd=tools/evoef2/`.

## The patch

`task0204_single_pass_repack.patch` adds two new CLI commands,
`GreedyRepack` and `RandomRepack`, alongside EvoEF2's own shipped
`SideChainRepack` (which does full simulated-annealing rotamer
optimization). **Both new commands reuse EvoEF2's own pre-existing,
already-shipped functions** —
`SequenceGenerateInitialSequenceSeed` (lowest-self-energy-per-site,
ignoring pairwise terms — exactly this task's own "greedy" baseline
definition) and `SequenceGenerateRandomSeed` (uniform-random rotamer per
site — this task's own negative control) — which the original
`SideChainRepack` command already computes internally, only as an SA
*starting point*, before immediately overwriting it via simulated
annealing. The patch's only change is skipping the annealing loop and
writing that seed straight out as the final structure. No new energy
function, no new rotamer geometry, no new library data — a minimal
dispatch change to the vendored tool's own existing code, not new physics.
Full rationale in the patch's own code comments
(`src/EnergyOptimization.h`/`.cpp`).

Verify the patch applies cleanly and the binary reports all three commands
before trusting any output:

```bash
./bin/EvoEF2 --command=SideChainRepack   # optimized (SA), shipped unmodified
./bin/EvoEF2 --command=GreedyRepack      # this patch
./bin/EvoEF2 --command=RandomRepack      # this patch
```

Used by `scripts/task0204_rotamer_repack_baseline.py`
(`EVOEF2_BIN = tools/evoef2/EvoEF2`).

## Docker (TASK-0285)

`EvoEF2` (this directory's own top-level copy — the path every caller's
own `EVOEF2_BIN` actually points to) is now a small Python wrapper, not
the native binary — a drop-in replacement, no caller changes. The
original native binary is kept at `EvoEF2.native-backup` (host-local,
gitignored, not relied on by anything).

Build:

```bash
cd tools/evoef2
docker build --platform linux/amd64 -t qas-evoef2:task0204 .
```

Same pinned recipe as above (clone, apply
`task0204_single_pass_repack.patch`, `g++ -O3`), inside a
`debian:bookworm-slim` base pinned by digest (see
`tools/fpocket/Dockerfile`'s own comment for why tag-only pinning is not
enough).

**The confirmed relative-argv0 quirk is preserved, not accidentally
broken.** `_run_evoef2` invokes this file as `./EvoEF2` with `cwd=`
this directory — EvoEF2 SIGSEGVs if its own argv[0] is a long/absolute
path (see the calling script's own comment for the full story). The
wrapper honors that contract on the outside (it *is* invoked as
`./EvoEF2`) and reproduces it on the inside too: the container creates a
short relative symlink to its own baked-in binary and execs through
*that*, not through an absolute container path — see the wrapper's own
docstring for exactly why it can't reuse the name `EvoEF2` for that
symlink (it would overwrite this same file via the live bind mount).

`library/`/`wread/` (the ~140 MB Dunbrack rotamer library data, already
gitignored, already built by the existing native recipe) are **not**
baked into the image — the container reads them from the host via a bind
mount of this whole directory, exactly as the native binary already did
via relative paths from its own cwd. Only the compiled binary itself
comes from the image.
