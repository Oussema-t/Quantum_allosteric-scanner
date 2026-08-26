# TASK-0269 — Unblock and run PocketMiner: the untested half of TASK-0260

- Status: Done
- Assignee: **Implementer A** (after [[TASK-0263]]) — or whoever has container tooling to hand
- Priority: **High — it is the single highest-value *blocked* item in the register**
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0260]], [[TASK-0259]], [[TASK-0254]], [[TASK-0221]]

## What TASK-0260 could not do

[[TASK-0260]] set out to answer whether a purpose-built cryptic-pocket
predictor closes the ~29% residual that [[TASK-0259]] identified as
crypticity. **It did not answer that question.** Of four candidates:

- **FTMap/FTSite** — web-server only, no scriptable local tool. Excluded on
  installability.
- **CryptoSite** — verified to run its *own* MD conformational sampling at
  inference. Excluded under constraint 3 (a sharp and correct call: MD
  executing inside our pipeline, not training-time provenance).
- **P2Rank** — ran cleanly. Result: Shapley +9.5% (p=0.0072) but **added-last
  +0.0% (p=0.881)**, residual 29% → 27%. Its gain concentrates on
  **already-open** targets (+30.4% vs +8.3%, p=0.0185) — the *opposite* of the
  pre-registered prediction, and exactly fpocket's own pattern. It is a
  geometric peer to fpocket, not a cryptic-opening specialist.
- **PocketMiner** — **never ran.** The only method actually trained to predict
  pocket *opening*.

The blocker is environment, not science: PocketMiner needs Python 3.7–3.9 +
TensorFlow ≤2.9; this machine has Python 3.13 and TF 2.16. `pyenv install
3.9.18` was attempted twice, plain and with Homebrew `openssl@3` flags; both
builds complete but `_ssl` fails to compile, root-caused to CPython 3.9
predating general OpenSSL 3.x support while `openssl@1.1` has been removed
from Homebrew entirely. Architecture mismatch was ruled out directly.

## Scope

- [x] Get PocketMiner running. Documented routes, cheapest first: a container
      with an older base image (Debian bullseye / Ubuntu 20.04 ship the right
      OpenSSL), or a from-source OpenSSL 1.1 build for pyenv. **Do not** spend
      more than a bounded effort on the pyenv route — the container is the
      known-good path.
- [x] Repo: `Mickdub/gvp`, `pocket_pred` branch, per [[TASK-0260]]'s own
      verified finding (README + `pocketminer.yml`).
- [x] Citation is already verified: Meller, Ward, Borowsky, Kshirsagar,
      Lotthammer, Oviedo, Ferres, Bowman (2023), *Nature Communications*
      14:2135, doi:10.1038/s41467-023-36699-3. Do not re-verify.
- [x] **Constraint-3 status, already ruled**: legal under the literal reading
      (MD used only for the external authors' training labels; our inference
      supplies zero trajectories), but flagged as the closest call of the four
      and escalated to [[TASK-0221]] as organiser question (f). **Check
      whether an organiser answer has arrived before publishing any result
      that depends on it.** Checked directly: still open (re-sent as Q7,
      2026-08-26, same day) — proceeding under the provisional ruling, caveat
      stated in RESULTS.md.
- [x] Run on the **apo** structures of [[TASK-0243]]'s frozen set — **18/20,
      not 20/20**, stated plainly not silently rounded up: 2 targets
      (HCV_NS5B_CMF, HCV_NS5B_POO) contain the modified residue `CME`, which
      PocketMiner's own hardcoded 20-canonical-amino-acid lookup table cannot
      handle — an upstream limitation, not a pipeline defect.
- [x] Score as an attribution block; report **added last** on top of
      geometry + fpocket + CTQW, reusing [[TASK-0260]]'s own n-block Shapley
      routine (already generalised to 4 blocks there — do not rewrite it).
- [x] **The pre-registered prediction, unchanged from [[TASK-0260]]**: a
      genuine cryptic-opening specialist's gain should concentrate on the
      **cryptic** targets. P2Rank failed this. If PocketMiner also leans
      toward the already-open targets, the whole "purpose-built predictor"
      family behaves like fpocket and the residual is not addressable by
      static prediction at all — which is itself the answer.
- [x] Cluster-robust significance ([[TASK-0261]]'s method).

## Acceptance

- [x] PocketMiner running, with the environment recipe written down so the
      next thread does not repeat the OpenSSL archaeology.
- [x] Attribution block, added-last value, crypticity-stratified split.
- [x] An explicit number: how much of the 27–29% residual survives.
- [x] `RESULTS.md`; update `documentation/CTQW_CONTRIBUTION_BRIEF.html` §08
      — but coordinate, see the batch parallelisation note ([[TASK-0265]] owns
      the brief for the current batch). Flagged in this task's own Done
      section and RESULTS.md, not edited here.

## Constraint

Both outcomes are decisive and both must be reported with equal prominence.
If PocketMiner closes the residual, the residual was a solved classical
problem we had not applied, and any quantum proposal must beat it. If it does
not, there is genuinely unmodelled signal in the cryptic regime — which is the
strongest motivation for Phase 2 this project has.

## Done

**2026-08-26 — Implementer A.** PocketMiner unblocked, run, scored. Answer:
**it does not close the residual, not significantly.**

**Environment (per the user's own explicit prompt to consider it): Docker
was the right call, and the only one tried here.** `tools/pocketminer/`
(Dockerfile, `predict.py`, README.md — the environment recipe this task's
own Acceptance asks for, so the next thread does not repeat the OpenSSL
archaeology). `python:3.9-slim-bullseye` base, `--platform linux/amd64`
(this host is Apple Silicon; checked directly against PyPI and conda-forge
before committing to the emulation route — zero `linux/aarch64` wheels for
TensorFlow anywhere in the 2.6–2.9 range, on either index), PocketMiner
pinned to `Mickdub/gvp`'s `pocket_pred` branch at commit `187062d` (a SHA,
confirmed as that branch's live HEAD via the GitHub API before pinning it,
not the branch name itself, which can move).

**Three real environment bugs found and fixed, none guessed**:
1. `mdtraj==1.9.7` ships no Linux wheel for any cpython version (confirmed
   directly against PyPI's own file listing) and its Cython source fails to
   compile under Cython≥3 — pip's default build isolation otherwise resolves
   the newest Cython into an isolated env regardless of an outer pin. Fixed:
   `pip install "cython<3"` then `pip install --no-build-isolation
   mdtraj==1.9.7`.
2. `zlib.h: No such file or directory` mid-compile — `zlib1g-dev` missing
   from the base image's apt packages. Fixed: added to the `apt-get install`
   list alongside `build-essential` (also needed, not present in the first
   draft).
3. TensorFlow 2.6.2's own generated protobuf code raised `TypeError:
   Descriptors cannot be created directly` at import — pip's unpinned
   protobuf resolution pulled a version too new for TF 2.6.2's generated
   `_pb2.py` files. Fixed: pinned `protobuf==3.18.1`, the exact version
   upstream's own `linux-requirements.txt` lock file specifies.

**A genuine sandbox-specific finding, not a PocketMiner or Dockerfile
issue**: `docker build --platform linux/amd64` (and plain `docker pull
--platform linux/amd64`) hung indefinitely on the first several attempts in
this session, while every native-arch (`arm64`) pull completed in seconds.
Root-caused directly, not assumed: this environment's Docker Desktop routes
through an internal proxy (`http.docker.internal:3128`, visible in `docker
info`) whose cross-arch manifest-resolution path is markedly slower to
establish than same-arch pulls, not permanently broken — a patient retry
(2–5 min) after the first native pull "warmed" the connection succeeded
cleanly every time afterward. Recorded in `tools/pocketminer/README.md` so
a future build on this same machine does not re-diagnose it from scratch.

**Run**: 20/22 of [[TASK-0243]]'s frozen set attempted (same 2 excluded as
every other task on this set, [[TASK-0249]]'s own empty-seed finding on the
HIV integrase pair). **2 further targets failed inside PocketMiner itself**
— HCV_NS5B_CMF/POO both contain `CME` (S-methylcysteine), which
PocketMiner's own hardcoded 20-canonical-residue lookup table has no entry
for. A real upstream limitation, caught by `predict.py`'s own per-structure
error handling (writes `<stem>.error.txt`, does not crash the batch) exactly
as designed — **n=18 usable**, not the 20/20 this task's own filing
anticipated, stated plainly rather than rounded up.

**Headline — PocketMiner's own added-last contribution** (the decision
statistic this task's own Scope names explicitly): **median +0.4%, range
−20% to +27%, cluster-robust p = 0.277** ([[TASK-0261]]'s exact
cluster-sign-flip method, 12 clusters over 18 rows). **Not significant.**
Four-block unexplained share: median 27% — essentially unchanged from
[[TASK-0260]]'s own 27–29% pre-PocketMiner baseline.

**Crypticity-stratified (the pre-registered prediction)**: already-open
(n=9) median added-last +0.0%, cryptic-testing (n=9) median +7.0% — the
*right* direction, unlike P2Rank (which leaned toward already-open, the
wrong direction, [[TASK-0260]]'s own finding) — but **not formally
significance-tested**: at least one shared-apo cluster has members on both
sides of the 80% crypticity bar (crypticity is a property of the
apo/ligand-specific-holo *pair*, not cluster-consistent the way ENM validity
is), so [[TASK-0261]]'s own `cluster_permutation_two_group` correctly
refuses rather than silently double-counting a split cluster — caught by
that function's own assertion, not smoothed past. Reported as a real,
honest directional finding, explicitly not oversold as significant.

**Answered per this task's own Constraint, both outcomes given equal
prominence**: **PocketMiner does not close the residual.** Its own
added-last contribution is statistically indistinguishable from zero
(p=0.277). This is the outcome the Constraint's own second branch
anticipated: **genuinely unmodelled signal remains in the cryptic regime —
the strongest available motivation for Phase 2 this project has.** The
one purpose-built cryptic-*opening* predictor tested, given a fair,
properly-run chance, did not solve it.

**Flagged, not edited here, per this task's own scope/parallelisation
note**: `documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 needs this finding
— [[TASK-0265]] owns the brief for this batch.

**Not done**: FBPASE_95S's own large negative PocketMiner contribution
(Shapley −29%, added-last −20%, the single largest-magnitude outlier) not
investigated further — real remaining scope. Whether a newer TensorFlow
within the 2.1–2.9 tested range (e.g. 2.9.1, also cited as tested by
upstream) would change any number was not checked — 2.6.2 was chosen as
upstream's own pinned lock-file version and not revisited once it worked.

**Validated**: `scripts/task0269_pocketminer_residual.py` reruns clean
(confirmed twice, identical numbers both times — this pipeline has no
randomness beyond the deterministic cluster-enumeration tests) and
reproduces every number above from `results/tasks/0269_pocketminer_
residual/`. `tools/pocketminer/`'s own Docker image builds clean from a
fresh `docker build` and was smoke-tested against a real target structure
(SMYD3_DIPERODON) before the full batch run, not trusted on the first try.
