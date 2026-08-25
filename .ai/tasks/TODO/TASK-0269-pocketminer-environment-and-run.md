# TASK-0269 — Unblock and run PocketMiner: the untested half of TASK-0260

- Status: TODO
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

- [ ] Get PocketMiner running. Documented routes, cheapest first: a container
      with an older base image (Debian bullseye / Ubuntu 20.04 ship the right
      OpenSSL), or a from-source OpenSSL 1.1 build for pyenv. **Do not** spend
      more than a bounded effort on the pyenv route — the container is the
      known-good path.
- [ ] Repo: `Mickdub/gvp`, `pocket_pred` branch, per [[TASK-0260]]'s own
      verified finding (README + `pocketminer.yml`).
- [ ] Citation is already verified: Meller, Ward, Borowsky, Kshirsagar,
      Lotthammer, Oviedo, Ferres, Bowman (2023), *Nature Communications*
      14:2135, doi:10.1038/s41467-023-36699-3. Do not re-verify.
- [ ] **Constraint-3 status, already ruled**: legal under the literal reading
      (MD used only for the external authors' training labels; our inference
      supplies zero trajectories), but flagged as the closest call of the four
      and escalated to [[TASK-0221]] as organiser question (f). **Check
      whether an organiser answer has arrived before publishing any result
      that depends on it.**
- [ ] Run on the **apo** structures of [[TASK-0243]]'s frozen set, 20/20.
- [ ] Score as an attribution block; report **added last** on top of
      geometry + fpocket + CTQW, reusing [[TASK-0260]]'s own n-block Shapley
      routine (already generalised to 4 blocks there — do not rewrite it).
- [ ] **The pre-registered prediction, unchanged from [[TASK-0260]]**: a
      genuine cryptic-opening specialist's gain should concentrate on the
      **cryptic** targets. P2Rank failed this. If PocketMiner also leans
      toward the already-open targets, the whole "purpose-built predictor"
      family behaves like fpocket and the residual is not addressable by
      static prediction at all — which is itself the answer.
- [ ] Cluster-robust significance ([[TASK-0261]]'s method).

## Acceptance

- [ ] PocketMiner running, with the environment recipe written down so the
      next thread does not repeat the OpenSSL archaeology.
- [ ] Attribution block, added-last value, crypticity-stratified split.
- [ ] An explicit number: how much of the 27–29% residual survives.
- [ ] `RESULTS.md`; update `documentation/CTQW_CONTRIBUTION_BRIEF.html` §08
      — but coordinate, see the batch parallelisation note ([[TASK-0265]] owns
      the brief for the current batch).

## Constraint

Both outcomes are decisive and both must be reported with equal prominence.
If PocketMiner closes the residual, the residual was a solved classical
problem we had not applied, and any quantum proposal must beat it. If it does
not, there is genuinely unmodelled signal in the cryptic regime — which is the
strongest motivation for Phase 2 this project has.
