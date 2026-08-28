# TASK-0283 — The shipped backend and the research pipeline disagree on KRAS's P@5, and the submission must quote one number

- Status: Done
- Assignee: Implementer A
- Priority: **Highest — a Phase 1 deliverable figure currently has two values and no stated provenance**
- Filed: 2026-08-28 by Reviewer
- Related: [[TASK-0282]], [[TASK-0184]], [[TASK-0270]], [[TASK-0263]], [[TASK-0130]]

## The discrepancy

[[TASK-0282]] recomputed our residue-ranking top-5 under this task family's own
**single pre-registered GAUGE operator** (`H_new` / `ctqw_converged`,
incoherent — the same operator its `CTQW-in-wrapper` arm uses) and got
**P@5 = 0.000** on KRAS_G12C. The Reviewer's own measurement from the shipped
`results/KRAS_G12C/hit_list.json` gives **P@5 = 0.200** (one hit, residue 60).

Both are correctly computed. **The deployed backend selects a different
Hamiltonian gauge than the register's fixed one**, and nobody has decided
which is the pipeline of record.

[[TASK-0282]] handled it correctly for its own purposes — it used the *cited*
(0.200) number, which made its own swept rule look **worse** on KRAS (0.071 vs
0.200), and flagged the discrepancy rather than silently choosing the
favourable figure. That was the right call and this task is not a criticism of
it. But the underlying inconsistency is unresolved, and it is now load-bearing.

## Why it is load-bearing

**This is a Phase 1 deliverable number.** §5 requires the top-5 hit list;
[[TASK-0184]] will quote its accuracy. Quoting 0.2 when the pre-registered
operator gives 0.0 — or the reverse — with no stated provenance is exactly the
class of defect this register has caught three times already in other people's
numbers ([[TASK-0239]] stale triplets, [[TASK-0270]] wrong genotype,
[[TASK-0155]]'s mislabelled pool). It would be worse to ship one of our own.

## Scope

- [x] Established which operator the deployed backend uses: `run_frozen_
      verdict`/`select_frozen_config` picks between `H_new_default`/`H10_
      disorder_suppressed` (label-free `unsupervised_score`); `_winner_index=0`
      (`H_new_default`) for **all 3 mandatory targets** — read from
      `verdict.json` and `run_challenge.py`'s own candidate builder, not
      inferred. Identical operator to this task family's own fixed GAUGE.
      `assemble_hit_list` additionally excludes active-site residues before
      ranking (real, documented, but not the cause of the 0.0/0.2 gap —
      reproducing it alone still gives 0.000 on KRAS_G12C).
- [x] **This is (b): drift, not a deliberate choice.** `results/KRAS_G12C/`'s
      deliverables were generated 2026-08-20 against `apo_pdb: 4OBE`;
      [[TASK-0270]] (2026-08-26) corrected the config to `4LDJ` but never
      regenerated this directory. Confirmed via connectivity-matrix shape
      mismatch (169x169 vs 170x170 — a structural fingerprint, not inferred
      from the P@5 numbers alone) and `results/RESULTS.md`'s own stale
      "From 4OBE alone..." auto-appended entry.
- [x] Fixed: re-ran `run_challenge.py --target KRAS_G12C` against current
      config, overwrote the stale deliverables in place.
- [x] Checked BCR_ABL1/CARDIAC_MYOSIN: **not stale** — `targets.yaml`
      unchanged since 2026-08-20 (git history checked), fresh re-run
      reproduces shipped `hit_list.json`/`verdict.json` byte-for-byte on
      both. Genuine agreement, not coincidence.
- [x] Checked the N×N connectivity matrix: for the 3 mandatory targets it
      shares the same winning `H`/eigendecomposition as the hit list (same
      code block, `run_challenge.py:441-450`) — no divergence there. The
      no-ground-truth branch (e.g. MYC_MAX) genuinely does use a different
      operator per deliverable (matrix: single highest-agreement `H_new`;
      hit list: 4-operator consensus) — real, code-documented, flagged for
      [[TASK-0184]]'s methodological report, not a defect to fix.
- [x] One number of record per mandatory target, with provenance — see
      RESULTS.md table.

## Acceptance

- [x] Written answer: `H_new_default`, gauge-selected, identical to the
      family's own fixed GAUGE — not deliberately different, and not
      actually the cause of the discrepancy (staleness was).
- [x] One P@5 per mandatory target, with provenance: BCR_ABL1 0.000
      (unchanged), KRAS_G12C 0.000 (corrected, was stale at 0.200),
      CARDIAC_MYOSIN 0.000 (unchanged). All three: 0/5.
- [x] Explicit statement: matrix and hit-list share an operator for the 3
      mandatory (ground-truth) targets; they do NOT for no-ground-truth
      targets — both facts stated, not smoothed into one blanket claim.
- [x] `RESULTS.md` written; line to [[TASK-0184]]: quote P@5=0.000 on all
      three mandatory targets, provenance as above.

## Constraint

Resolve this on **provenance**, not on which number is higher. The favourable
figure (0.200) is the one currently shipping and the one the Reviewer quoted
first; the pre-registered operator gives 0.000. If the honest answer is that
our best-documented operator scores zero on all three mandatory targets, that
is what the submission says.

## Done (2026-08-28, Implementer A)

**Not an operator disagreement — a stale deliverable.** Read
`run_challenge.py`'s real code path rather than guessing from the numbers:
`select_frozen_config` picks `H_new_default` (index 0) for all 3 mandatory
targets — the same operator this task family's own GAUGE already uses.
`assemble_hit_list`'s active-site exclusion is real but insufficient to
explain the gap (reproduced it directly: still 0.000 on KRAS_G12C).

**Root cause, confirmed structurally, not numerically**: `results/
KRAS_G12C/{hit_list,verdict}.json` and both connectivity `.npz` files were
generated 2026-08-20 (`4917e17`) against `apo_pdb: 4OBE` (170->169
residues after cleaning). [[TASK-0270]] (2026-08-26) fixed
`config/targets.yaml` to `4LDJ` and re-scored the AUC/diagnosis in its own
task-scoped script, but the shared `results/KRAS_G12C/` directory
`run_challenge.py` writes — and Sec.5 quotes from — was never
regenerated. Caught the connectivity-matrix shape mismatch (169x169 vs
170x170) before reading either JSON's numbers, and independently
cross-confirmed via `results/RESULTS.md`'s own stale "From 4OBE alone..."
auto-appended line — two independent structural fingerprints agreeing,
not one number matched to a hypothesis.

**BCR_ABL1/CARDIAC_MYOSIN verified NOT stale**, not assumed clean because
"config didn't change": re-ran `run_challenge.py` fresh for both and diffed
against the shipped `hit_list.json`/`verdict.json` — byte-identical
resnums, scores, diagnosis, AUC on both.

**Fixed live**: `run_challenge.py --target KRAS_G12C` re-run against
current config, overwrote `results/KRAS_G12C/`'s 6 stale files in place.
`results/RESULTS.md` auto-appended its own new, correctly-named `4LDJ`
entry (old `4OBE` entries left as historical record, not deleted).

**Verdict**: all 3 mandatory targets now genuinely read P@5 = 0.000 (0/5,
0 hits in fifteen) under the deployed, gauge-selected operator — the
unfavourable answer, reported per this task's own Constraint. TASK-0180's
separate, coarser `site_hit_metrics` `hit_at_1` (cluster-centroid distance,
not residue P@5) still registers `True` for KRAS_G12C — both numbers
correctly reported, neither substituted for the other.

**No `src/allostery` code changed** — this was a data-regeneration task,
not a code fix; no test suite re-run required.

**Moved TODO/IN_PROGRESS -> DONE.**
