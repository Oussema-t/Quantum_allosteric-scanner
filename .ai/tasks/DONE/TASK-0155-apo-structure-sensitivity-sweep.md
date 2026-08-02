# TASK-0155 Apo-structure sensitivity sweep (is any result a lucky structural draw?)

## Context

- ID: TASK-0155
- Title: for a target with many deposited apo structures (KRAS G12C
  first), run the existing scoring pipeline across SEVERAL apo inputs of
  the same protein and report the DISTRIBUTION of AUC / P@5 / floor-clear,
  rather than the single point estimate from one hardcoded structure.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised by the orchestrating collaborator (Oussama), 2026-07,
  observing that `config/targets.yaml` hardcodes exactly one apo/holo
  pair per target and nothing sweeps the input structure.
- Priority: **P1 — high information, low cost. This stress-tests the one
  marginal surviving result (KRAS) directly.**

## Why this matters — the project already proved the point accidentally

[[TASK-0124]] replaced cardiac myosin's apo from 5TBY (20 A cryo-EM) with
a real X-ray structure (8QYP) and the AUC collapsed 0.79 -> 0.52 — the
target's only positive vanished. That was treated as a one-target data-
quality fix. The general lesson was not drawn: **every result in the
register is currently conditioned on a single, arbitrary structural
draw, and that sensitivity has never been measured.** The pipeline has
swept the ENM cutoff ([[TASK-0113]]), the pocket-contact cutoff
([[TASK-0114]]), the propagation time ([[TASK-0119]]), and the seed
convention — but never the input apo structure. KRAS is the ideal test:
it has many deposited apo structures AND it is the one target with a
marginal surviving signal (converged-limit point estimate clears floor,
CI-overlapping, ceiling p=0.045 uncorrected). A distribution of AUCs
across apo structures answers directly: is KRAS's result structure-robust,
or a lucky draw? Either answer is publishable.

## Intent Contract

- Outcome: a table of the existing scored observable's AUC / P@5 /
  floor-clear across >= 5 (target: 8-12) distinct apo structures of KRAS
  G12C, same holo ground truth (6OIM) and same pipeline, reported as a
  distribution (median, spread, fraction clearing floor) — plus a
  one-line verdict on structure-robustness.
- Why required, not assumed: TASK-0124 shows one swap can move AUC by
  ~0.27 and erase a headline; the sensitivity of the *surviving* result
  (KRAS) to this choice is unmeasured and is a liability a reviewer finds
  immediately.
- In Scope:
  - Assemble a list of valid KRAS G12C apo structures from RCSB — verify
    each on RCSB before use (correct protein, apo i.e. no orthosteric/
    allosteric ligand at the Switch-II site, resolvable catalytic
    domain). Candidate seeds to CHECK (do not assume valid): 4OBE
    (current), 4DSN, 3GFT, and other apo G12C/WT entries — the
    implementer verifies each on RCSB and states which were included/
    excluded and why. NOTE: `36OL`/`36OM`-style codes floated informally
    are almost certainly typos; verify every PDB ID on RCSB before use.
  - Run the existing `clean_from_config` -> `build_H_new` ->
    scored-observable pipeline unchanged per structure; only the apo
    input varies.
  - Handle NMR structures explicitly: they carry no crystallographic
    B-factors, on which V_B/V_T in `H_new` depend — either exclude them
    (stated) or document the degraded-operator handling. Do not silently
    feed zero/absent B-factors.
  - Report the AUC/P@5/floor-clear distribution + median + spread, with
    CIs per structure.
- Out Of Scope:
  - Changing the holo ground truth or the operator (this isolates the
    APO-structure variable only).
  - Re-running the ENM/pocket/time sweeps (already done; this is the
    orthogonal, missing axis).
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: identical pipeline, holo, cutoffs, seed
  convention across all apo inputs; the ONLY varied quantity is the apo
  structure. Label-blind throughout.
- Planned Validation: the distribution itself IS the result; no synthetic
  gate needed (this is a robustness measurement of an existing observable,
  not a new observable). Optionally extend to BCR-ABL1 / PTP1B if KRAS
  shows large spread.

## In Progress

None

## TODO

- [x] Assemble + RCSB-verify a list of valid KRAS G12C apo structures
      (state inclusions/exclusions and why).
- [x] Run the existing pipeline unchanged per apo structure.
- [x] Handle NMR / missing-B-factor structures explicitly.
- [x] Report AUC/P@5/floor-clear distribution + median + spread + per-
      structure CIs.
- [x] One-line verdict: is KRAS's result structure-robust or a lucky draw?
- [x] Optionally extend to BCR-ABL1 / PTP1B if spread is large. (Not
      extended -- see Done section.)

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0112]] (Done) — bootstrap CI.
- [[TASK-0124]] (Done) — the myosin structure-swap that motivates this.
- [[TASK-0130]] (Done) — converged-limit propagator.

## Open Questions

- How many apo structures is "enough" for a stable distribution —
  Implementer's call, state the number and reasoning (>= 5 minimum).
  **Resolved: 10** — the full clean candidate pool (X-ray, GDP+Mg-only,
  true G12C) was 22; 10 was chosen to span the full 1.04-2.41 Å
  resolution range while comfortably clearing the task's own >=5 floor
  and sitting inside its own 8-12 target band. The result did not need
  more: 3/10 floor-clear, median indistinguishable from chance, P@5=0.000
  on all 10 — already decisive at n=10.
- Whether to include close homolog/mutant apo structures or restrict to
  G12C — state the inclusion rule. **Resolved: G12C only, GDP+Mg nucleotide
  state only** (matching both the current apo and the fixed holo's own
  nucleotide state), no bound small-molecule/inhibitor, X-ray only. Stated
  and enforced directly against RCSB metadata, not assumed from PDB ID
  naming conventions — this is exactly the check that caught 4OBE's own
  genotype error (see Done section).

## Done

**Resolved 2026-07-30: a lucky draw, decisively — and the apo structure
this project has always drawn from is not even the correct genotype.**

**Finding 0 (precedes the sensitivity question, more consequential than
it): `targets.yaml`'s current `apo_pdb: 4OBE` is wild-type KRAS, not
G12C.** Confirmed two independent ways before trusting it: (a) direct
sequence inspection via RCSB GraphQL — 4OBE's own deposited
`entity_poly.pdbx_seq_one_letter_code_can` has Gly, not Cys, at an
anchor-relative offset for position 12 (anchor `"TEYKLVVVG"`, tag-length-
agnostic; sanity-checked by confirming position 13 is Gly in all 118
matched entries, including 4OBE, ruling out an indexing bug); (b) 4OBE's
own `pdbx_database_related` RCSB metadata field cross-references 4NMM/
4LDJ as "G12C KRas inhibitor complex"/"G12C KRas" — i.e. RCSB's own
curation treats 4OBE as the wild-type structure those G12C entries are
*related to*, not as a G12C entry itself. 4OBE's own title is literally
"Crystal Structure of GDP-bound Human KRas" (no mutant named at all).
Every KRAS_G12C AUC/verdict this project has ever reported was therefore
computed against the wrong genotype for a target labeled "G12C." This is
independent of, and arguably more consequential than, this task's own
structural-sensitivity question — flagged here since it was found while
assembling this task's own candidate pool, escalated in `RESULTS.md`
alongside the sensitivity result, not filed as a separate task (a
one-line config/label-accuracy fact, not new work).

**RCSB verification of the task filing's own two other named candidates**
(both excluded): **4DSN** — sequence-confirmed Asp at position 12: a
**G12D** structure, wrong oncogenic mutant, excluded. **3GFT** — title
"Human K-Ras (Q61H) in complex with a GTP analogue"; sequence-confirmed
Gly (wild-type) at position 12 and a GNP (GTP analogue)-bound **Q61H**
mutant — wrong mutant AND wrong nucleotide/conformational state (active-
vs. inactive-like), excluded on both grounds.

**Candidate pool assembly** (fresh, not from the filing text): RCSB
Search API (`full_text` "KRAS G12C" + `Homo sapiens` organism filter) →
123 raw hits → GraphQL batch fetch (method, resolution, bound-ligand set,
polymer sequence) for all 123 → sequence-filtered via the same
tag-agnostic anchor to 112 entries with a genuine Cys at position 12 →
by method: 109 X-ray, 3 cryo-EM, **0 NMR** (this task's own "handle NMR
explicitly" requirement is satisfied by confirming directly that the
case does not arise for this target, not by silently having no branch
for it) → restricted to X-ray only (keeps the comparison homogeneous
with holo's own X-ray method; the 3 EM entries are lower-resolution and
not needed given 22 clean X-ray candidates already clear the target
band) → restricted to `ligands == {GDP, MG}` exactly (excludes ~90
inhibitor- or GNP-bound structures — a bound Switch-II drug or a
different nucleotide state measurably remodels/reconformers the exact
region this sweep must not bake in as apo "structure") → **22 clean
candidates, 1.04-2.41 Å**. 10 selected, spanning that full resolution
range: 8AZX, 4LDJ, 7A1X, 8TXJ, 8QUG, 9UOH, 7YCE, 7MDP, 7RP3, 8AFC (all
single chain A, matching this target's own `chains: ["A"]` config).

**Pipeline**: new `scripts/apo_structure_sensitivity_sweep.py` reuses the
existing pipeline unmodified — `clean()` (the same function
`clean_from_config` itself calls) for each apo variant, holo (6OIM)
loaded once and held fixed exactly as `run_challenge._load_apo_holo`
already does it, `build_labels`, the 3-baseline floor pack
(`degree_centrality`/`euclid_from_seed_centroid`/`hop_from_seed`), and
`protocol.run_frozen_verdict` (candidate selection between `H_new`/`H10`,
the converged-limit CTQW score, `classify_failure` with block-bootstrap
CI) — the exact same call `run_challenge.run_target` makes, not a
parallel reimplementation. Sanity-checked first against the current
4OBE config (reproduces `AUC=0.590`, `NO_FAILURE_DETECTED`,
`ci_overlap=True` — consistent with every prior report of this number)
before running the 10 new candidates.

**Result — the distribution table**:

| Structure | Resolution | AUC | P@5 | Diagnosis |
|---|---|---|---|---|
| 4OBE (CURRENT, flagged WT) | 1.24 Å | 0.590 | 0.200 | NO_FAILURE_DETECTED |
| 8AZX | 1.04 Å | 0.408 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 4LDJ | 1.15 Å | 0.518 | 0.000 | NO_SIGNAL_IN_APO |
| 7A1X | 1.32 Å | 0.595 | 0.000 | NO_FAILURE_DETECTED |
| 8TXJ | 1.4 Å | 0.571 | 0.000 | NO_FAILURE_DETECTED |
| 8QUG | 1.56 Å | 0.439 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 9UOH | 1.75 Å | 0.446 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 7YCE | 1.8 Å | 0.437 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 7MDP | 1.96 Å | 0.442 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 7RP3 | 2.0 Å | 0.592 | 0.000 | NO_FAILURE_DETECTED |
| 8AFC | 2.41 Å | 0.549 | 0.000 | NO_SIGNAL_IN_APO |

Across the 10 true-genotype structures: AUC 0.408-0.595 (spread 0.187,
matching [[TASK-0124]]'s own 0.27 CARDIAC_MYOSIN swing), median 0.482
(below chance), mean 0.4996 (exactly chance). Floor-clear: **3/10
(30%)**. `NO_SIGNAL_IN_APO`: 2/10. `BEATS_CHANCE_NOT_FLOOR`: 5/10. **P@5
is exactly 0.000 on all 10** — no true G12C structure's top-5 ranked
residues include any real pocket residue; only the mislabeled 4OBE
achieves a nonzero P@5. Per-structure block-bootstrap CIs (`_diagnosis_
score_ci`/`_diagnosis_floor_ci`) recorded in the results JSON for each
cell.

**One-line verdict: KRAS_G12C's floor-clearing result is not
structure-robust — it is a lucky draw, and the structure it was drawn
from is not even the correct mutant.**

**Not extended to BCR-ABL1/PTP1B** (this task's own "optionally, if KRAS
shows large spread" condition) — the spread found is already large and
decisive, and per the review's own binding 2026-08-08 writing-freeze
constraint, extending to two targets whose own headline results are
already `NO_SIGNAL_IN_APO`/mixed (not this register's "marginal
surviving" case this task exists to stress-test) is not the highest-value
use of remaining time; stated as a scope decision, not silently skipped.

Docs updated additively: `RESULTS.md`'s new "Apo-structure sensitivity
sweep" section + open-questions row 48.

No new `src/allostery` module — this task composes only already-tested
existing primitives (`clean`, `build_labels`, `run_frozen_verdict`, the
floor baselines), matching the precedent of other real-run scoring
scripts in this register (e.g. `transfer_entropy_baseline.py`,
`ensemble_entropy_real_run.py`) that don't carry their own dedicated unit
test file. Full suite (unaffected, no `src/` change): 994 passed, 2
xfailed, 0 failed.
