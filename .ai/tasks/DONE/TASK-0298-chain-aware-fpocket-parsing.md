# TASK-0298 — Chain-aware fpocket parsing, and re-quantify the ceiling

- Status: Done
- Priority: **High — the published ceiling 0.1649 rests on candidate residue sets that are wrong for 9 of the frozen 20**
- Filed: 2026-08-30 by Reviewer thread (D1 from [[TASK-0297]]; defect originally found by the external distal-pockets session)
- Related: [[TASK-0297]], [[TASK-0282]], [[TASK-0287]], [[TASK-0292]], [[TASK-0293]]

## The defect

`task0242_two_stage_dryrun.fpocket_candidates` parses pocket residues as
`int(line[22:26])`, discarding the chain. Every consumer then builds
`idx_of = {int(r): i for i, r in enumerate(resn)}`, which on a
multi-chain selection **keeps only the last chain's index** per residue
number. A pocket lining chain A silently maps onto chain B's coordinates.

## Exposure

Nine targets carry cross-chain residue-number collisions, **all of them in
[[TASK-0282]]'s frozen 20**: `GAC_BPTES` (406), `GAC_CPD12` (405),
`PKR_MITAPIVAT`/`PKR_AG946` (422), `PF_ATCASE` (328), `FBPASE_95S` (310),
`SUMO_E1_FHJ` (280), `TRP_SYNTHASE_F6F`/`F19` (253).

Unlike the seed defect ([[TASK-0297]] D2), **this one has no
homo-oligomer exemption**: even when both chains are the same protein, a
specific fpocket cavity lines *one* of them, and mapping it to the other
is wrong regardless.

## Scope

- [x] Key fpocket residues on `(chain, resnum)`; parse `line[21]`
      alongside `line[22:26]`. Build `idx_of` on the same compound key.
      Done in `task0242_two_stage_dryrun.fpocket_candidates` (the source)
      and `.run()`'s own `idx_of`/`seedset`/`truth` construction.
- [x] Audit every other `int(line[22:26])` / resnum-only `idx_of` in the
      scripts tree — this pattern is likely copied. **11 direct callers
      of `fpocket_candidates` found and fixed** (see Done). Two
      INDEPENDENT fpocket parsers exist elsewhere (`task0163_external_
      baseline_scoring.py`, `src/allostery/consensus_labels.py`) — both
      were **already chain-correct** (`(chain, resnum)` tuples under a
      `"residues"` key), confirmed by direct inspection, not assumed. The
      defect was isolated to `task0242`'s own function, not copied as
      widely as feared.
- [x] **Re-run [[TASK-0282]]'s ceiling** and report the corrected mean EH
      against the published **0.1649**, per-target. See Done — **it
      collapses**.
- [x] Re-run [[TASK-0287]] Part C, [[TASK-0292]] Parts A–C, and
      [[TASK-0293]]'s LOTO on corrected candidates. See Done.
- [x] Fix `DHPS_GC7`'s config: chains `[A, B]` but 1RLZ deposits only A.
      Verified live (1RLZ genuinely single-chain, 6P4V has both) —
      restricted to `["A"]` throughout, matching KSHV_PROTEASE's own
      established monomer-configuration pattern.

## Constraint

Report the corrected ceiling **whichever way it moves**. If it rises,
that is not a licence to re-open the CTQW comparison without re-running
the CTQW arm on the same corrected candidates.

## Note

[[TASK-0297]] found the analogous seed defect moved exactly one target.
The likeliest outcome here is similarly small — but "likeliest" is not
"measured", and the ceiling is quoted in the collaborator brief.

## Done (2026-08-30, Implementer B)

**The fix.** `fpocket_candidates` (`task0242_two_stage_dryrun.py`) now
parses `(line[21], int(line[22:26]))` — chain kept, not discarded —
producing `p["resnums"]` as a set of `(chain, resnum)` tuples instead of
bare ints. Every direct consumer's own `idx_of`/`truth`/`seedset`
construction was updated to the same compound key: `task0242.run()`
itself, `task0282_pocket_selection_sweep.build_target`,
`task0287_local_structural_scale_probe.build`,
`task0292_fpocket_fragmentation_and_the_ceiling.build_cache`,
`task0255_hop_angstrom_calibration.build_candidates`,
`task0249_composite_dumb_baseline.fpocket_druggability_per_residue`
(gained a required `chain_ids` parameter, threaded through its own 3 call
sites plus `task0276_holo_only_structural_signature.fpocket_druggability`'s
own wrapper), `task0275_term_decomposition_apo_holo`,
`task0281_docked_undocked_capacity._fpocket_hits_switch_i_ii` (its own
hardcoded `("A", r)` re-tagging removed — `p["resnums"]` is already
correctly tagged now), `task0282_prior_lexicographic_probe` (historical/
superseded probe, fixed for consistency though its own 3 targets are
single-chain and were never exposed to the value bug), and
`task0291_one_drug_many_pockets_anatomy` (whose own 33-target sweep DOES
include several of the 9 exposed targets — fixed for correctness; not
one of this task's own explicit re-run list, so its own published numbers
are not re-verified here, flagged as a candidate follow-up).

**Two independent, already-correct fpocket parsers found during the
audit and left untouched**: `task0163_external_baseline_scoring.py` and
`src/allostery/consensus_labels.py` both already key on `(chain, resnum)`
under a `"residues"` field — verified by reading, not assumed from
sharing the `int(line[22:26])` substring my grep matched on. The defect
was NOT "likely copied" as broadly as feared; it was isolated to
`task0242`'s own function, which happened to be the most heavily reused
(11 direct callers).

**`DHPS_GC7` config fixed**, verified live: 1RLZ (apo) deposits only
chain A; `apo_chains: ["A","B"]` made chain B a silent no-op. Restricted
to `["A"]` throughout (`apo_chains`/`holo_chains`/`chains`), matching
`KSHV_PROTEASE_24Q`/`25G`'s own established "monomer configuration"
pattern for a homo-oligomer (2PBK/4P2T have 4/2 chains respectively; both
already restricted to `["A"]` only). Apo-only quantities (min_A) are
unaffected — chain B was never load-bearing (already established by
[[TASK-0297]]).

**Sanity check before trusting the fix at scale**: verified directly on
`KSHV_PROTEASE_24Q` (single-chain, not exposed) that the new compound-key
`idx_of` resolves 11/11 of one candidate pocket's own residues correctly
against `apo.chain_ids`/`apo.resnums`, and that a FIXED, unchanged rule
(`hop>=1hops + drug_alone`) applied to the corrected candidates reproduces
KSHV's own EH bit-for-bit (0.444/0.333) — confirming the fix is
surgically localized to the 9 exposed targets and does not perturb
anything else, before trusting the full re-runs below.

### The corrected ceiling — it does not just move, it collapses

**[[TASK-0282]]'s own two headline numbers, both reproduced from the
identical script (only the compound-key fix applied), both compared
directly against the originally-committed JSON (`f73c355`), not
re-derived from memory:**

| quantity | published (buggy) | corrected | note |
|---|---|---|---|
| **LOTO cross-validated mean EH** (the true table headline, `results/RESULTS.md`'s own "swept rule (LOTO)" column mean) | **0.122** | **0.000** | every one of 20 folds now scores exactly zero |
| in-sample full-20-fit mean EH (what this task's own filing calls "the published ceiling 0.1649") | **0.1649** | **0.100** | |
| winning rule | `MIN_HOP>=1` + druggability alone | `MIN_HOP>=3` + `lex_far_first` | **the rule itself flips**, not just its score |

**Mechanism, traced not asserted.** The oracle ceiling (best-achievable
EH from fpocket's own candidate list, no rule involved) for the 9 exposed
targets:

| target | oracle (buggy) | oracle (corrected) |
|---|---|---|
| GAC_BPTES | **1.000** | 0.235 |
| GAC_CPD12 | 0.833 | 0.444 |
| PF_ATCASE | 0.444 | 0.571 |
| FBPASE_95S | 0.100 | 0.100 (unchanged) |
| SUMO_E1_FHJ | 0.308 | 0.154 |
| TRP_SYNTHASE_F6F/F19 | 0.583 | 0.093 |
| PKR_MITAPIVAT/AG946 | 0.727 / 0.636 | unchanged |

**GAC_BPTES's own oracle was a PERFECT 1.000 purely because a chain-B
candidate silently mapped onto chain-A ground-truth residues (or vice
versa) at the exact colliding resnums — an artefact of the bug, not a
real fpocket candidate finding the true pocket.** Raw (unfiltered, no
rule) oracle mean across all 20: 0.556 → 0.454 (`task0292` Part A,
`raw_oracle` field). This is the direct cause: the published rule-
selection procedure (LOTO, fit on N−1, scored on the held-out target)
picked a DIFFERENT rule once 9/20 targets' own true achievable ceiling
dropped — `MIN_HOP>=1 + drug_alone`'s own in-sample score fell from
0.1649 to 0.0899 (computed directly, verified against `task0292`'s own
independent `reimplemented` field: 0.0898578811369509, exact match to
15 digits), and `MIN_HOP>=3 + lex_far_first` edged it out at 0.1000 —
narrowly, but a genuine, non-tied win (`>` not `>=` in the selection
code, verified by reading `loto_sweep`/`fit_final_rule`). That new
rule then scores **exactly zero on every single held-out target**,
including non-exposed ones (verified directly: `KSHV_PROTEASE_24Q`/
`25G`/`SMYD3_DIPERODON`, none of which are among the 9 exposed, also
score 0.000 under the new rule applied directly — this is a genuinely
bad, narrow rule, not a symptom of remaining bugs in the 9 exposed
targets' own corrected data).

**[[TASK-0292]] Parts A–C, re-run**: qualitative conclusions unchanged,
absolute numbers move by a consistent, explained amount throughout.
`reimplemented` (druggability-alone, in-sample): 0.1649→0.0899.
`raw_oracle`: 0.556→0.454. Part B ("merging hurts at every criterion,
fpocket's splitting helps"): direction and ranking of every merge
criterion preserved (e.g. `dist 4A`: EH 0.0237→0.0206, still worse than
RAW). Part C ("druggability tracks size, not quality" — rho(size,EH)
positive, rho(size,druggability)=+0.24): both correlations essentially
unchanged (+0.116→+0.103; +0.239→+0.240) — **the size mechanism is not an
artefact of the 9 exposed targets**, it survives the correction intact.

**[[TASK-0287]] Part C, re-run**: the design's own positive control
(`fpocket_drug`) previously survived Bonferroni (`controls_surviving:
['fpocket_drug']`); under corrected candidates it **no longer does**
(`controls_surviving: []`) — the original verdict ("DESIGN UNDERPOWERED,
do not report structural nulls as findings") is unchanged, now on firmer
ground since even the positive control fails. `FBPASE_94D`/`TEM1_BLA_FTA`
skip identically before and after ("no candidate overlaps the labelled
pocket") — confirmed pre-existing, not introduced by this fix.

**[[TASK-0293]] LOTO, re-run**: verdict **unchanged** — `druggability/
size` still `DOES NOT SURVIVE` cluster-robust LOTO (p=1.0000, identical
to 15 significant figures pre/post-fix: `n_wins=2, n_ties=18, n_losses=0`
both times). Both arms' absolute EH drop by the same amount as
`MIN_HOP>=1+drug_alone`'s own shift (published 0.1649→0.0899, ratio
0.2649→0.1899) — a pure level shift, the comparison between the two
arms is untouched.

### Constraint compliance

Reported whichever way it moved — **it moved down, sharply, on the
true cross-validated number**. Per the Constraint's own second half: the
ceiling did not rise, so no CTQW re-comparison question arises. No rule
was tuned to produce this result; the winning rule for the corrected data
was selected by the SAME LOTO procedure, unmodified, that selected the
original one.

### Follow-ups, not this task's own scope

- `task0291_one_drug_many_pockets_anatomy.py` was fixed for correctness
  (its own resnum-only comparison would have silently broken) but its
  own already-published per-target `n_fpocket_overlapping`/
  `best_fpocket_coverage` numbers were not re-verified — several of its
  33 targets are among the 9 exposed. Candidate follow-up task.
- The submission-facing "0.1649" figure lives in an external
  collaborator brief this repo does not control — this task's own
  record (here, and `RESULTS.md`) is the correction of record; whoever
  maintains that brief needs to be told separately (not an edit this
  session can make).

**Suite**: no code in `src/allostery` was modified (only `__WORK_IN_
PROGRESS__/scripts/*.py` and one config file); no regression run
applicable.

**Data**: `results/tasks/{0282_pocket_level_top5_distance_druggability_
sweep,0287_local_structural_scale,0292_fpocket_fragmentation,
0293_loto_druggability_per_size}/*.json` all regenerated in place
(gitignored, not committed — compared against the git-history-committed
originals directly, cited above with exact values).

**Moved TODO → IN_PROGRESS → DONE.**
