# TASK-0124 Re-anchor or retire CARDIAC_MYOSIN: 5TBY cannot support a Cα contact graph

## Context

- ID: TASK-0124
- Title: CARDIAC_MYOSIN's apo structure (5TBY) is a **20 Å cryo-EM IHM
  assembly / docked homology model** — not a real crystallographic
  structure, its "B-factors" are not crystallographic, and its chain
  assignment is unverified against a 6-chain complex. This is currently
  the pipeline's one surviving positive result (0.786, floor-cleared)
  and it rests on the worst structure in the mandatory-target set. Find
  a real apo β-cardiac myosin motor-domain crystal structure, or
  explicitly report CARDIAC_MYOSIN as data-limited.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §1.2, §3
  (Weaknesses #4), §5 P1-8.
- Priority: **P1 — weeks 2-4.** Per the panel: "do not build the only
  positive on a 20 Å docked homology model."
- **New lead, 2026-07-20 (relayed via `.ai/reviews/2026-07-20/
  Mavacamten-fix.txt`, not yet independently verified by this
  Architect/Planner thread — no internet access confirmed available in
  this session):** this project's own prior finding that **6C1H (the
  challenge's own designated CARDIAC_MYOSIN holo structure) contains no
  mavacamten** is corroborated — the note states 6C1H has only ADP
  bound (the post-hydrolysis product), the inhibited conformation but
  not the drug-bound one. **A genuinely new candidate is proposed**:
  **PDB 9GZ1** (cryo-EM, reportedly April 2026, *Science Advances*,
  https://www.science.org/doi/10.1126/sciadv.aea9335) — claimed to
  contain mavacamten directly (ligand code `XB2`), compared against an
  apo structure to show the drug-induced conformational change. If
  this holds up under this task's own independent-verification
  discipline, it would be a real, concrete fix for CARDIAC_MYOSIN's
  holo side — not just the apo side this task was originally scoped
  around — and directly strengthens the existing "6C1H correction"
  finding the panel called "still under-sold."

## Intent Contract

- Outcome: either (a) a real, higher-resolution apo β-cardiac myosin
  motor-domain crystal structure is identified on RCSB, verified
  (resolution, chain assignment, B-factor provenance — same
  independent-verification discipline as [[TASK-0081]]'s ASD candidates),
  and substituted for 5TBY in `config/targets.yaml`, with the full
  pipeline re-run against it; or (b) CARDIAC_MYOSIN is explicitly
  reported in `RESULTS.md`/`COMPETENCE_MAP.md` as data-limited — its
  0.786 floor-clearing result caveated as resting on a structure whose
  B-factors are not crystallographic and whose chain assignment is
  unverified, not presented as a clean positive.
- Why this matters beyond one target: this is currently **the only
  target in the mandatory set with any positive headroom at all**
  (per TASK-0082's competence map) — if it does not survive scrutiny of
  its underlying structure, the submission currently has zero clean
  positives across all 3 mandatory targets. This needs to be known
  before Phase 1 submission, not discovered by a referee.
- In Scope:
  - RCSB search for alternative apo β-cardiac myosin (MYH7) motor-domain
    structures — crystallographic, verified chain ID and ligand records,
    same independent-verification discipline TASK-0081 already
    established for ASD candidates (don't trust `targets.yaml`'s
    existing entry uncritically).
  - **Independently verify PDB 9GZ1** (the 2026-07-20 lead above) with
    the same discipline: fetch directly, confirm it is a real deposited
    structure, confirm ligand `XB2` is present and matches mavacamten's
    real chemical identity (not assumed from the relayed note alone),
    confirm what apo structure it should be compared/aligned against
    (the note implies a companion apo structure was used in the citing
    paper — identify and verify it too, do not assume 5TBY is the right
    pairing for a 9GZ1-based holo). If verified, this becomes this
    task's own preferred holo replacement for 6C1H, addressed alongside
    (not instead of) the apo-side search above.
  - If a real apo replacement (and/or 9GZ1 as holo) is found: re-run the
    full pipeline (floor/ceiling/actual, per whatever seed/clock
    convention has landed by then — TASK-0118/0119/0130 are all Done)
    against the new structure(s).
  - If not found (either side): write the data-limited caveat into
    `RESULTS.md`/`COMPETENCE_MAP.md`, additive per the no-silent-
    overwrite convention, citing this task and the specific structural
    defects (20 Å resolution, non-crystallographic B-factors, unverified
    chain assignment against a 6-chain complex; 6C1H's own confirmed
    lack of mavacamten).
- Out Of Scope:
  - Re-deriving the `LARGE_N_THRESHOLD` correction (TASK-0101's
    2026-07-15 fix) — the panel confirms that correction was itself
    correct; it "removed two wrong reasons for caution and left the
    right one load-bearing" (structural quality, not size). Do not
    re-litigate the threshold value.
- Constraints And Invariants: any replacement structure must go through
  the same independent RCSB verification TASK-0081 applied (don't trust
  a single source's chain-ID/ligand guess).
- Planned Validation: if a replacement is found, the full re-run against
  it, checked against the proximity floor same as every other target;
  if not, the caveat text itself, checked for accuracy against the
  panel's specific structural claims (20 Å, IHM assembly, unverified
  6-chain assignment).

## In Progress

None

## TODO

- [ ] Search RCSB for alternative apo β-cardiac myosin (MYH7)
      motor-domain crystal structures.
- [ ] Independently verify PDB 9GZ1 (ligand `XB2`=mavacamten, its
      companion apo structure, resolution, chain composition) — the
      2026-07-20 lead, not yet checked by this thread.
- [ ] Independently verify any apo candidate (resolution, chain ID,
      B-factor provenance) before adopting it.
- [ ] If found (either side): substitute in `config/targets.yaml`,
      re-run full pipeline.
- [ ] If not found: write the data-limited caveat into `RESULTS.md`/
      `COMPETENCE_MAP.md`, citing this task.

## Dependency

- Soft: should ideally re-run under whatever seed/clock conventions
  [[TASK-0118]]/[[TASK-0119]] land, if this task starts after them.
- None hard — the RCSB search itself can start immediately.

## Open Questions

- Whether any real apo β-cardiac myosin motor-domain structure at
  usable resolution actually exists on RCSB at all — genuinely unknown
  until searched; if none exists, (b) (data-limited reporting) is the
  only honest option, stated as such.

## Done

**(1) Independently verified the relayed 2026-07-20 lead (PDB 9GZ1) before
touching anything** — live RCSB fetch (REST API + `prody.parsePDB`), not
assumed from the relayed note. Real, correctly described: "Beta-cardiac
myosin interacting heads motif complexed to mavacamten," cryo-EM, 3.70 Å,
*Homo sapiens*, XB2 (mavacamten) present (chains J/N of a 6-chain IHM
complex including light chains), McMillan et al., preprinted bioRxiv
10.1101/2025.02.12.637875 (PMID 39990378) and now published *Science
Advances* 2026-04-29 (doi:10.1126/sciadv.aea9335, confirmed via
WebSearch) — the note's citation was accurate, not an error, contrary to
this implementer's own initial suspicion (RCSB's own metadata still
cited the bioRxiv preprint at fetch time; a normal preprint-to-journal
lag, not a discrepancy).

**(2) Found the holo side was already solved, 13 days before the relayed
lead, and never needed 9GZ1** — `config/targets.yaml`'s `holo_pdb: 8QYR`
(with `drug_ligand: XB2`) was already in place from TASK-0003
(2026-07-06/07), independently confirmed real: 1.80 Å X-ray, *Bos
taurus*, mavacamten (XB2, C15H19N3O2) bound to chain B. **9GZ1 is not
adopted as a replacement** — 8QYR is higher resolution (1.80 Å X-ray vs.
3.70 Å cryo-EM) and a single motor domain rather than a 6-chain IHM
complex, the cleaner structure for this pipeline's Cα-only contact
graph. Recorded as independent corroboration (a second, different-
species, different-method structure confirms the same XB2/mavacamten
site), not a substitution — an Implementer's-call decision, stated here
with the reasoning.

**(3) The real open question was the apo side, and it had a much better
answer sitting one deposition away.** 5TBY's own sibling entries from
the *holo*'s own paper (Auguin, Robert-Paganin, Rety, Kikuti, David,
Theumer, Schmidt, Knolker & Houdusse, bioRxiv 2023,
doi:10.1101/2023.11.15.567213, PMID 38014327) include **8QYP**: "Beta-
cardiac myosin motor domain in the pre-powerstroke state" — real,
RCSB-verified directly (REST API + live `prody.parsePDB` fetch): X-ray,
2.759 Å, *Bos taurus*, single chain A (780 residues), ADP+vanadate
(VO4, an ATP-hydrolysis transition-state mimic) at the nucleotide site,
**no mavacamten** — a genuine drug-free apo state at the allosteric
pocket. Sequence-identical to 8QYR's own chain to 779/780 residues (one
terminal-residue offset) — same construct, same crystallization
campaign as the holo already in use. Chosen over the also-real, also-
verified human apo candidate 4P7H (Winkelmann et al. 2014, motor-
domain::GFP chimera, 3.20 Å) because 8QYP additionally fixes an
unremarked apo(human, 5TBY)/holo(bovine, 8QYR) **species mismatch** that
existed the entire time under 5TBY, at no cost — same species as the
holo, same paper, better resolution than the GFP-chimera alternative.

**(4) Verified data-feasibility directly before editing any config**,
per this project's own discipline: `clean()` on 8QYP (chain A) and 8QYR
(chain B) both succeed cleanly (704 / 709 residues, real per-residue
B-factors — 8QYP mean=75.8/std=17.5, not a homology-model flatline);
`build_labels` resolves a 13-residue pocket from XB2 contacts, correctly
projected onto the new apo via `labels.py`'s own sequence-alignment
correspondence (chain-letter-independent, confirmed by reading
`_needleman_wunsch_map`); `H13_3N_anm_hessian` on 8QYP gives exactly
`n_zero=6` rigid-body modes (vs. 5TBY's `n_zero=10`), resolving
[[TASK-0128]]'s floppy-mode workaround for this target as a side effect,
not by revisiting that task's own scope.

**(5) `config/targets.yaml` updated**: `apo_pdb: 5TBY` -> `apo_pdb:
8QYP`; `chains: ["B"]` -> `chains: null` + `apo_chains: ["A"]` +
`holo_chains: ["B"]` (TASK-0127's schema, since 8QYP/8QYR use different
author chain letters for the same biological chain); `confidence: 0.65`
-> `0.90` (parity with the other 3 mandatory targets, the concern it
was suppressing is resolved, not merely re-scored); original 5TBY
warning text preserved, not deleted, with a new dated resolution note
plus the 9GZ1-verification note appended, per this project's no-silent-
overwrite convention. `tests/test_targets_config.py`'s own pinned
`confidence < 0.9` assertion (encoding the now-resolved concern) updated
to assert the new state instead of being routed around.

**(6) Real re-run, current (TASK-0130 closed-form) convention**
(`scripts/closed_form_competence_map_rerun.py --target CARDIAC_MYOSIN`,
live fetch, `results_task0124_reanchor/closed_form_competence_8QYP.json`):

| | N | Floor (95% CI) | Ceiling (95% CI) | Actual (95% CI) | Diagnosis |
|---|---|---|---|---|---|
| 5TBY (old, TASK-0129/0130) | 950 | 0.7921 [0.577, 0.913] | 0.8439 | 0.7912 [decl. TASK-0129] | `BEATS_CHANCE_NOT_FLOOR` |
| 8QYP (new, this task) | 704 | 0.5679 [0.415, 0.735] | 0.6452 [0.360, 0.867] | 0.5176 [0.348, 0.768] | `NO_SIGNAL_IN_APO` |

**Headline, reported honestly per this project's own discipline —
this is not the outcome either disjunct in this task's own Intent
Contract anticipated.** Neither (a) "a real replacement structure exists
and the pipeline re-run against it" (implying the positive would likely
survive re-anchoring, since the task's title says "re-anchor **or**
retire") nor (b) "report as data-limited" (implying the structure
question stays open) captures what actually happened: the structure
question is resolved — 8QYP is real, verified, high-quality, same-
species, same-paper crystallography — and resolving it **removes the
result**. `NO_SIGNAL_IN_APO`, matching BCR_ABL1's own diagnosis.
Combined with KRAS_G12C ([[TASK-0130]]: CI still overlaps floor) and
BCR_ABL1 ([[TASK-0129]]/[[TASK-0131]]: inconclusive), **no mandatory
target has a decisive positive result under the fully corrected
pipeline** — this project's own "an honest NO is a publishable result"
convention applies to this target now as directly as it already applied
to the other two. A fresh permutation null on this target's own new
ceiling margin (+0.077 over floor) was not run — out of this task's own
scope (a structural swap, not a re-derivation of [[TASK-0131]]'s
permutation-null methodology) — flagged as a natural follow-up if that
margin is ever reported as a positive claim.

**(7) Real, separate gap found and filed, not fixed inline — TASK-0144.**
`scripts/learnability_gate.py`'s own CARDIAC_MYOSIN row ([[TASK-0120]]/
[[TASK-0133]], `LEARNABLE`) was computed against the now-retired 5TBY
apo and is stale. Attempted to re-run it against the new 8QYP/8QYR pair
and found `superpose.align_apo_holo`/`common_residues_by_resnum` match
apo/holo Cα atoms by the raw `(chain, resnum)` pair — with apo chain='A'
and holo chain='B' (different letters, same biological chain), the
correspondence is silently empty (`0` common residues, confirmed
directly), which `align_apo_holo` then turns into a `ValueError`. This
is the identical latent shape [[TASK-0127]]'s own `apo_chains`/
`holo_chains` override was built for (GLUCOKINASE: apo chain A, holo
chain X) — but that override only ever reached `clean_from_config`, not
`superpose.py`'s own alignment machinery, and GLUCOKINASE has never
actually been run through this gate to trigger it. **Not fixed inline
here**: `superpose.py`/`tests/test_superpose.py` had uncommitted changes
from a concurrent thread at the time this was found (confirmed via
`git status`), and the fix is real, separable, well-scoped work in its
own right (a `chain_map` parameter, additive, backward-compatible) —
filed as [[TASK-0144]] rather than risk clobbering concurrent work under
time pressure or silently leaving the gap undocumented. The main scoring
pipeline (`labels.py`'s sequence-alignment correspondence,
`protocol.run_frozen_verdict`) is unaffected — confirmed directly by
reading `labels.py` and by (6)'s own successful real re-run.

**(8) Docs updated additively**: `COMPETENCE_MAP.md`'s own CARDIAC_MYOSIN
section (new dated addendum + its "Open Questions" list entry marked
Done, both with the full before/after table); `RESULTS.md`'s "Index of
open questions" (new row 21); `EXECUTION_PLAN.md`'s own 1C.9 row;
`.claude/hypotheses/physics.md`'s HYP-P8 discussion (flagged, not
resolved — the RMSD/CO numbers there are 5TBY-era and stale pending
[[TASK-0144]]'s own re-run). Original numbers/text preserved everywhere,
not deleted, per this project's no-silent-overwrite convention.

**(9) Full test suite green** (799 passed, 2 xfailed, no regressions)
after the config change and the one pinned-assertion update in
`test_targets_config.py`.

**Not attempted, explicitly out of this task's own scope**: re-deriving
`LARGE_N_THRESHOLD` (per this task's own Out Of Scope — not re-
litigated); fixing `align_apo_holo`'s chain-letter matching inline
(filed as [[TASK-0144]] instead, see (7)); a fresh permutation null on
the new ceiling margin (see (6), flagged as a follow-up, not this task's
own required validation per its Intent Contract).
