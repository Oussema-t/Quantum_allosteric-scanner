# TASK-0285 — Dockerize the vendored external tools (fpocket, EvoEF2, P2Rank; validate PocketMiner)

- Status: Done
- Assignee: Implementer C
- Priority: High — a real, already-documented reproducibility bug (see below), and the recurring source of this session's installability failures
- Filed: 2026-08-28 by Bartosz (via Implementer C)
- Related: [[TASK-0163]], [[TASK-0206]], [[TASK-0204]], [[TASK-0260]], [[TASK-0269]], [[TASK-0268]]

## Why

Bartosz: *"We want our agentic tools (evoef2, p2rank, pocketminer, etc)
working using dockerization."*

This register has four vendored external tools, each currently installed a
different, host-dependent way:

| tool | current install method | known problem |
|---|---|---|
| `fpocket` | compiled from source on each machine, gitignored binary | **[[TASK-0206]] already caught two machines producing bit-different binaries with DIFFERENT AUCs** (0.8348/0.8596/0.5345 vs 0.7910/0.8618/0.5303 on the same 3 targets) — a real, on-record cross-machine drift bug, not a hypothetical one |
| `EvoEF2` | compiled from source on each machine, gitignored | same class of risk as fpocket, never checked — no `PROVENANCE.json` exists for it |
| `P2Rank` | prebuilt JVM release, fetched fresh, needs a host JVM | lower risk (binary bytes come from a pinned upstream release URL, not locally compiled) but still a host-JVM dependency this register has to assume is present |
| `PocketMiner` | **already Dockerized** ([[TASK-0269]]) | the reference case — Python 3.7-3.9 + TensorFlow ≤2.9 could not install natively on this machine's Python 3.13 toolchain at all; Docker was the only route that worked |

[[TASK-0268]] hit the same class of problem a third way (`frustratometer`'s
own `llvmlite` dependency needing a system LLVM toolchain absent here) and
had to fall back to a from-scratch reimplementation instead of the real
tool. Docker is the fix that generalizes across all of these: pin the OS,
compiler, and runtime once, in a version-controlled recipe, and every
machine that can run Docker gets byte-identical results — closing exactly
the class of bug [[TASK-0206]] already found and had to work around by
hand (a `PROVENANCE.json` SHA256 pin plus "kept both AUC sets on record,
neither silently overwritten").

## Scope

- [x] **fpocket**: Dockerfile using the *same pinned recipe* already in
      `tools/fpocket/README.md` (`git clone --branch 4.2.3 --depth 1`,
      `make`) — this is a chance to test, not just assert, that a
      containerized build reproduces (or doesn't) [[TASK-0206]]'s own
      pinned SHA256/AUC set. Report whichever way it lands.
- [x] **EvoEF2**: Dockerfile using the same pinned recipe already in
      `tools/evoef2/README.md` (clone, apply
      `task0204_single_pass_repack.patch`, `g++ -O3`). Must preserve the
      confirmed, load-bearing quirk documented in
      `task0204_rotamer_repack_baseline.py::_run_evoef2` — **`argv[0]` must
      be a relative `./EvoEF2`, not an absolute path, or the binary
      SIGSEGVs** — and the working-directory-relative resolution of
      `library/`/`wread/`.
- [x] **P2Rank**: Dockerfile with a pinned JVM base image + the same pinned
      release URL already in `tools/p2rank/README.md`.
- [x] **PocketMiner**: not rebuilt — [[TASK-0269]]'s own image
      (`qas-pocketminer:pocket_pred`) already exists and already produced
      real, committed results. Validate it still builds/runs, don't
      duplicate the work.
- [x] **Zero changes to the 12 existing call sites.** `EVOEF2_BIN`,
      `FPOCKET_BIN`, `P2RANK_BIN` are referenced by
      `task0163_external_baseline_scoring.py`,
      `task0204_rotamer_repack_baseline.py`,
      `task0260_cryptic_predictor_residual.py`, and 9 other scripts that
      import from those three, all via
      `subprocess.run([BIN_PATH, ...], cwd=..., ...)` at fixed paths. A
      thin executable wrapper at the *exact same path* the real binary
      currently occupies (`tools/fpocket/bin/fpocket`,
      `tools/evoef2/EvoEF2`, `tools/p2rank/p2rank_2.5.1/prank`) that
      transparently proxies to `docker run` — same argv, same cwd
      semantics, same stdout/stderr/exit code — is an ADD-only migration
      per this project's own convention; rewriting 12 call sites to speak
      Docker directly is not.
- [x] **Verify each wrapper end-to-end against a real target**, not just a
      smoke test of the binary's own `--help`/version banner — run the
      actual downstream script (or the wrapper directly, replicating that
      script's own exact call shape) on at least one real structure per
      tool and confirm the output is well-formed and sane.
- [x] `README.md` in each `tools/<name>/` directory updated with the Docker
      build/run instructions, matching `tools/pocketminer/README.md`'s own
      established structure and level of detail (pins, why-Docker
      rationale, Constraint-3 status where applicable).
- [x] A `PROVENANCE.json` for fpocket's *containerized* build (new pin,
      compared against [[TASK-0206]]'s existing native-build pin — same
      no-silent-overwrite treatment if they differ) and for EvoEF2 (new,
      none existed before).

## Acceptance

- [x] Three new Dockerfiles (`tools/fpocket/Dockerfile`,
      `tools/evoef2/Dockerfile`, `tools/p2rank/Dockerfile`), each building
      cleanly on this machine.
- [x] Three wrapper executables, each verified against a real, current
      call site with real output, not fabricated.
- [x] PocketMiner's own existing image confirmed still functional (a real
      run, not assumed from its own prior task's record).
- [x] fpocket's containerized-vs-native reproducibility question answered
      with a real number (matches [[TASK-0206]]'s pin, or doesn't — both
      are a real, reportable finding).
- [x] READMEs updated; `RESULTS.md`.

## Constraint

**ADD-only.** No existing script's call signature, working directory
assumption, or output-file location may change. If a wrapper cannot
faithfully replicate the real binary's own interface (the EvoEF2
relative-argv0 quirk is the sharpest risk here), that is a blocking defect
to fix in the wrapper, not a reason to touch the 12 calling scripts.

Do not assume Docker reproducibility just because the recipe is pinned —
check the actual output (fpocket's own AUC set, EvoEF2's own repack
result) against what the native binary already produces, the same
discipline [[TASK-0206]] already established for this exact tool.

## Done (2026-08-28, Implementer C)

**All four tools now run via Docker; all three new wrappers verified
end-to-end against real targets through the real, unmodified calling
code; zero call sites changed.**

### The wrapper pattern, one design for all three

`tools/{fpocket/bin/fpocket, evoef2/EvoEF2, p2rank/p2rank_2.5.1/prank}`
are now small Python scripts (not binaries) at the *exact* paths
`FPOCKET_BIN`/`EVOEF2_BIN`/`P2RANK_BIN` already pointed to — every one of
the 12 existing call sites (`subprocess.run([BIN_PATH, ...], cwd=...,
...)`) works completely unmodified. Two of the three (fpocket, p2rank)
mount this repo's own root + the system temp root 1:1 (host path ==
container path) so no argument rewriting is needed, since every real
caller stages I/O under `tempfile.TemporaryDirectory()` or
`results/tasks/...`. EvoEF2 is different — its own callers already stage
input/output inside `tools/evoef2/` itself and require `cwd=` that same
directory, so its wrapper mounts just that one directory and preserves
the **confirmed relative-argv0 SIGSEGV quirk** by having the container
exec through a short relative symlink to its own baked-in binary — deliberately
NOT named `EvoEF2`, since that name is the wrapper's own path inside the
same live bind mount and would overwrite itself (caught before shipping,
by reasoning through the mount semantics, not by trial and error).

**A real near-miss, caught before it caused damage**: the first version of
this task overwrote the native, gitignored `tools/fpocket/bin/fpocket`
binary with the new wrapper *before* the Docker image had finished
building or been validated — a shared binary other concurrent threads
could have been calling mid-build. A local native rebuild attempt as a
safety net itself failed (a `libmolfile_plugin.a` arch-mismatch, unrelated
to this task, not investigated further since the Docker build finished
successfully in parallel and made the fallback moot) — the real fix
applied to EvoEF2 and P2Rank afterward was backing up the native binary
first (`EvoEF2.native-backup`, `prank.native-backup`) *before* replacing
it, every time.

**All four base images pinned by digest**, not just tag — `debian:
bookworm-slim` (fpocket, EvoEF2) and `eclipse-temurin:21-jre-jammy`
(P2Rank). This is not cosmetic: the first fpocket build (tag-only pin)
produced a THIRD, still-different AUC set from either number already in
`PROVENANCE.json` — real evidence a floating base-image tag defeats the
whole point of containerizing for reproducibility.

### Real end-to-end verification, not a `--help` smoke test

Ran the actual calling functions (`task0163_external_baseline_scoring.
_run_fpocket`, `task0204_rotamer_repack_baseline._run_evoef2`,
`task0260_cryptic_predictor_residual.run_p2rank`) on KRAS_G12C's own real
apo structure (`4LDJ`), unmodified except for pointing `*_BIN` at the new
wrapper paths (already their default):

- **fpocket**: 9 real pockets detected, first pocket druggability 0.682,
  18 residues — well-formed, sane output.
- **EvoEF2** (`GreedyRepack`): produced a real 107,203-byte
  `4LDJ_beststruct.pdb`.
- **P2Rank**: 170 real per-residue probability rows, well-formed CSV
  parse.
- **PocketMiner** (existing image, not rebuilt): real inference run,
  `4LDJ: OK, n_residues=170, mean=0.4902` — confirmed still functional,
  not assumed from [[TASK-0269]]'s own prior record.

### The reproducibility question, answered for both compiled tools

**EvoEF2 — clean positive.** `GreedyRepack` on the identical input PDB,
native macOS arm64 binary vs. this image's own Linux/amd64 binary:
**byte-identical output** (107,203 bytes, both arms). First provenance
record for this tool (`tools/evoef2/PROVENANCE.json`, none existed
before).

**fpocket — a real, decisive negative, reported not smoothed over.** The
containerized build reproduces [[TASK-0163]]'s own ORIGINAL (superseded)
AUCs exactly (BCR_ABL1 0.8596, CARDIAC_MYOSIN 0.5345) — **not**
[[TASK-0206]]'s own re-verified native-rebuild AUCs (0.8618/0.5303) on the
identical source tag. A third independent data point that does not
converge with either prior one. KRAS_G12C's own AUC is not a valid
comparison at all any more — [[TASK-0270]]'s apo swap (4OBE→4LDJ) changed
the input structure itself, independent of which fpocket binary scores
it. All three AUC sets kept on record in `tools/fpocket/PROVENANCE.json`'s
own `containerized_build_TASK_0285` entry, none silently preferred —
whether a *second*, independent Docker rebuild converges with this one
(now that the base image is digest-pinned) is a real, flagged follow-up,
not resolved here.

### Not done

A from-scratch multi-machine rebuild test (confirming the NOW
digest-pinned fpocket recipe is stable across repeated builds, not just
within one machine's Docker layer cache) was not run — a real, disclosed
gap, the natural next check on the open reproducibility question above.
`frustratometer` ([[TASK-0268]]'s own from-scratch-port fallback) was not
revisited — that tool is pure Python plus a missing system LLVM
toolchain, a different class of problem than these four (an
already-built-from-scratch replacement exists and works; Dockerizing the
real upstream tool would be new scope, not requested here).

**Scripts:** none — this task is infrastructure (Dockerfiles + wrapper
scripts), not a results-generating pipeline. **Verification data:** the
end-to-end runs above, reproduced directly against real target structures
during this task, not saved to `results/tasks/` (no numeric claim in this
task's own Done section needs a separate artifact beyond what's already
quoted here and in each tool's own `PROVENANCE.json`).
