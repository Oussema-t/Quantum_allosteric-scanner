# TASK-0287 — At what SCALE is an allosteric pocket's location structurally encoded?

- Status: Done
- Assignee: Reviewer thread
- Priority: High — retracts the strength of [[TASK-0284]] Finding B and corrects a design flaw shared by several nulls in this register
- Filed: 2026-08-28 by Reviewer thread (user-directed: "WHAT a protein does is encoded into its structure. Question is — at what level?")
- Related: [[TASK-0284]], [[TASK-0286]], [[TASK-0282]], [[TASK-0258]], [[TASK-0261]]

## Why

[[TASK-0284]] Finding B reported eight structural descriptors as null
against the near/far pocket split. Every one of the eight (`N`, `Rg`,
`compactness`, `helix_fraction`, `sheet_fraction`, `gnm_lambda1`,
`contact_order`, `mean_degree`) is a **whole-protein scalar**, constant
across every pocket of a given protein. Two problems follow:

1. **Scale mismatch.** A pocket is a local object. The question actually
   asked was "does this protein's *global* helix fraction predict where
   its pocket sits" — not the question the finding was read as answering.
2. **No positive control.** Eight nulls were reported without ever
   demonstrating the design could detect a descriptor known to work. An
   all-null table from an untested design is uninterpretable.

## What was done

**Part A — variance decomposition of the target variable.** ICC of `min_A`
within vs between apo structures.

**Part B — SS measurement validated before use.** Deposited HELIX/SHEET
records re-derived independently and compared per-residue against
[[TASK-0284]]'s own coarse Ramachandran-box assignment.

**Part C — within-protein stratified design.** Every fpocket candidate on
each apo is a row; the candidate with maximal overlap against the
labelled pocket is the positive, the rest decoys. 17 local structural
descriptors per candidate. Statistic = the true pocket's **within-protein
percentile**, tested against 0.5 by Wilcoxon signed-rank across targets
(n=31). Protein identity absorbed by construction — no pseudo-replication.
**Two positive controls** (min heavy-atom distance to seed, fpocket
druggability) ride in the same table under the same correction.

**Follow-up conditioning.** Each descriptor regressed on a control within
each protein; true pocket's percentile recomputed on the residual.

## Findings

**A. `min_A` is a protein-level quantity, not a pocket-level one.**
ICC = **1.000000** (within-structure sum of squares = 0.0 exactly); where the
register carries two ligands for one apo, `min_A` is bit-identical. Effective n
for any between-protein descriptor test is **28 structures**, not the 33
pocket rows Finding B quoted. [[TASK-0284]] Finding B's n is overstated.

**B. SS assignment is measured with substantial noise.** Records vs
Ramachandran agree on only **64.7%** of residues (range 0.57–0.77, n=31).
Any SS null in this register is **attenuated**, and must not be reported
as clean evidence of absence.

**C. The design has power** — `fpocket_drug` survives Bonferroni
(mean pct 0.701, p=0.0013, α=0.0029). Nulls in the table are therefore
interpretable, unlike [[TASK-0284]] Finding B's.

**D. Bonferroni survivors: `mean_degree` (0.647, p=0.0011), `mean_sasa`
(0.310, p=0.0006), `n_res` (0.691, p=0.0004) — plus the druggability
control. Conditioning shows these are ONE confound, pocket size.**
Residualising on `n_res` kills every one of them, the control included:

| descriptor | raw | \| fpocket_drug | \| n_res |
|---|---|---|---|
| fpocket_drug | 0.701 (p=0.0013) | — | 0.580 (p=0.10) |
| mean_degree | 0.647 (p=0.0011) | 0.602 (p=0.0068) | 0.533 (p=0.41) |
| mean_sasa | 0.310 (p=0.0006) | 0.388 (p=0.024) | 0.401 (p=0.069) |
| n_res | 0.691 (p=0.0004) | 0.553 (p=0.32) | — |
| **helix_frac** | **0.598 (p=0.038)** | **0.596 (p=0.047)** | **0.633 (p=0.011)** |

**fpocket's own druggability score, in this within-protein design, is
largely pocket size.** Any register claim resting on druggability as an
independent signal needs this caveat.

**E. Distance to the seed does NOT select the pocket among fpocket
candidates** (0.393, p=0.065 raw; 0.478, p=0.70 conditioned), and the
reason is now measured: **every target has fpocket candidates sitting on
its own active site** (median 9 within 4 Å, 31/31 targets), and on
average **35%** of a protein's candidates are closer to the seed than the
true pocket is. The orthosteric site is its own strongest decoy. This
reconciles the pocket-level result with [[TASK-0282]]'s residue-level one.

**F. `helix_frac` is the only descriptor that is not a restatement of
size — and it is a HYPOTHESIS, not a finding.** It is the sole descriptor
to survive both conditionings, and it *strengthens* under both (0.598 →
0.633 on `| n_res`). Restricting to residues where both SS methods agree
— reducing measurement noise — strengthens it again (0.598 → 0.612,
p 0.038 → 0.018), the direction attenuation predicts. Direction: the true
allosteric pocket is **more helical** than its own protein's other
candidate pockets. **It does not survive Bonferroni (α=0.0029) and is one
of 17 tests.** It must not be reported as a result.

## Constraint honoured

The conditioning analysis was specified before its result was seen (the
four raw survivors were suspected to be one confound on inspection of the
descriptor list, not after the p-values). The consensus-SS check has a
**predicted direction** (noise reduction strengthens a real effect), so
it discriminates rather than fishes. No further descriptor was added
after the table was read.

## Next

- `helix_frac` warrants **one pre-registered test** on held-out targets
  with a real DSSP assignment — not another sweep. Gated on a DSSP binary
  or `biotite`, neither available here (same gap as [[TASK-0286]]).
- [[TASK-0284]] Finding B's wording should be corrected wherever quoted:
  its n is 28, not 33, and it carries no positive control.
