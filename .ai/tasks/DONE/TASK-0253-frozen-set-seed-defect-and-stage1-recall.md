# TASK-0253 — TASK-0243's frozen set: an unresolvable seed, a contradicted claim, and 36% stage-1 loss

- Status: Done
- Assignee: unassigned (suggest whoever owns [[TASK-0243]]'s curation)
- Priority: **High — the frozen set is now the evidentiary basis for TASK-0249's headline and for the joint experiment**
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0243]], surfaced by [[TASK-0249]]
- Related: [[TASK-0242]], [[TASK-0216]], [[TASK-0217.003]]

## Two defects, one already found and one measured here

**1. Unresolvable active-site seed, contradicting the curation's own claim.**
[[TASK-0249]] found `HIV_INTEGRASE_MUT871` and `HIV_INTEGRASE_MUT916` (apo
`1M9D`) have an **empty active-site seed on all four chains** — confirmed
directly. [[TASK-0243]]'s Done section states "zero fell back to a top-degree
proxy". Both cannot be true. The pair was handled correctly downstream
(counted as attempted-target failures, kept in every denominator), but the
curation's own claim needs correcting at the source.

**2. Stage-1 recall is 64%, and it reproduces exactly.**
In [[TASK-0249]]'s two-stage arm, **14 of 22** attempted targets survived —
fpocket never proposed the true pocket for the other 8. [[TASK-0242]] measured
**7 of 11** on a completely different target set. Two independent sets, same
64%. This is a stable property of the pipeline, not sampling noise.

That matters because a within-candidate ranking metric is **blind to those 36%
by construction**. [[TASK-0249]] handled it correctly (denominator = targets
attempted). Any future run, ours or the collaborating thread's, must do the
same — and the joint pre-registration should name it explicitly.

## Scope

- [x] Re-verify the seed for every target in the frozen set, not just the two
      that failed. State the method and show the count. Correct
      [[TASK-0243]]'s "zero fell back" claim to whatever is true.
- [x] For `1M9D` specifically: determine whether a usable apo exists for HIV
      integrase, or whether the pair should be dropped. Do not substitute a
      structure without the [[TASK-0209]] VALID check and a live RCSB
      confirmation ([[TASK-0169]] is the precedent for why). **Dropped, not
      replaced** — root cause found (see Done), replacement is a separate
      curation effort left for a follow-up task.
- [x] Characterise the 8 stage-1 failures: is fpocket missing the pocket, or
      is `MIN_HOP` filtering it out after fpocket found it? These are very
      different problems and the current pipeline reports them identically.
- [x] If `MIN_HOP` is removing true pockets, report how often — that would make
      the distality filter itself a source of false negatives, and it is a
      parameter the joint protocol proposes to freeze.
- [x] Publish stage-1 recall as a standing pipeline metric alongside any
      two-stage result, so it is never implicit again. (Published here;
      making it a standing/automated metric in every future run is a
      process note, not code — flagged below, not built as a new gate.)

## Acceptance

- [x] Seed provenance table for all 22 targets, with the corrected claim.
- [x] Verdict on the HIV integrase pair: **dropped** (root cause: wrong
      protein domain, not a fixable seed-detection issue).
- [x] Stage-1 failures decomposed into fpocket-miss vs MIN_HOP-removal.
- [x] [[TASK-0243]]'s Done section amended rather than left contradicted.

## Constraint

[[TASK-0249]]'s headline is not in question here — it handled both defects
correctly. This is about the frozen set being trustworthy for everything that
comes next, including a jointly-signed experiment where a curation error found
later would discredit both threads' result at once.

## Done

**2026-08-24, Implementer D.**

New `scripts/task0253_seed_and_stage1_audit.py`, reusing
[[TASK-0242]]'s own `run()`/`CAND`-swap pattern and
`backend.active_site.detect_active_site` directly (the exact call
`prep()` itself makes) — no seed or candidate logic re-derived.

**1. Seed provenance, all 22 targets, corrected.** Live distribution:
**uniprot=18, ligand=2, pdb_site=0, none=2** — not [[TASK-0243]]'s own
claimed "20 uniprot / 2 ligand / zero fell back." The config file's own
per-target `active_site_source` field already disagreed with that prose
claim before any live check (it reads 18/4, not 20/2) — a static-field-
vs-prose inconsistency that predates this task and was never caught.
`HIV_INTEGRASE_MUT871`/`HIV_INTEGRASE_MUT916` (apo `1M9D`) are the two
`none` targets, confirming [[TASK-0249]]'s own finding exactly (empty
seed on every chain).

**2. `1M9D` root-caused, live-RCSB-confirmed, not assumed — verdict:
drop.** `1M9D` has two polymer entities: chains A/B = **Cyclophilin A**
(UniProt P62937), chains C/D = **HIV-1 Capsid** (UniProt P12497, RCSB's
own `pdbx_description`) — confirmed via direct `data.rcsb.org` polymer-
entity queries, not inferred. Capsid and integrase are both cleavage
products of the *same* Gag-Pol polyprotein (P12497), so `1M9D` was
curated into this pair by matching on that one shared parent accession
without checking that the specific domain/region resolved in `1M9D`
matches what the holo structures actually are. Independently confirmed
the holo side is genuinely correct: `8CBS`/`8CBV` are both real,
233-residue, single-entity "Integrase" structures (P12497), live-checked
the same way. **This is why every chain of `1M9D` fails seed detection**
— there is no HIV integrase catalytic-site annotation to find on a
capsid structure, in any of `_from_uniprot`/`_from_ligands`/
`_from_site_records`'s three tiers. Not a fixable seed-detection defect;
a wrong-structure curation error. **Verdict: drop the pair**, per this
task's own Scope ("determine whether a usable apo exists... or whether
the pair should be dropped") — replacing it would need a full
[[TASK-0209]]-VALID, live-RCSB-verified new curation cycle, out of
proportional scope here. A quick live search confirms real single-entity
HIV-1 integrase apo candidates exist (e.g. 1IHV, 1IHW, 1K6Y, 5OYM,
1WJF) — a starting point for whoever curates a genuine replacement next,
not independently verified or VALID-scored here.

**3. A real, previously-undiscovered correctness bug found and fixed —
this is the most consequential finding of this task.** Investigating why
`run()` "succeeded" on the two seed-empty targets instead of failing (an
empty seed should be a hard stop, not a scoreable result) found: with
`seed=[]`, `baselines.hop_from_seed` returns a **constant sentinel**
value for every residue (no real signal), and
`propagators.time_averaged_ctqw_converged` divides by `len(seed)==0`,
producing an **all-NaN** score array — confirmed directly, not assumed
(`RuntimeWarning: invalid value encountered in divide`). Neither raises.
`run()` then fed both straight into `np.argsort` for ranking, which
returns *some* index order for a NaN/constant array — not an error, not
a warning, a real-looking numeric rank. **This is not hypothetical: it
is already baked into [[TASK-0243]]'s own committed `stage1_rerun.json`**
— `HIV_INTEGRASE_MUT871` shows `ctqw` **rank 1** (looks like a near-perfect
hit), `MUT916` shows rank 22 (looks like the worst), both fabricated from
undefined arithmetic, both counted as ordinary stage-1 **successes**
(`K=26`/`K=24`) in that task's own reported 16/22 recall and its own
head-to-head Wilcoxon tables. Fixed at the source: `task0242_two_stage_
dryrun.run()` now checks `len(seed)==0` immediately after `prep()` and
returns a clear, explicit error instead of proceeding — a real behavior
change (not purely additive, unlike this file's own earlier `return_state`
extension), justified because the prior behavior was silently wrong, not
merely incomplete. Re-ran [[TASK-0243]]'s own full 22-target rerun with
the fix: **stage-1 recall corrects to 14/22 = 63.6%**, matching
[[TASK-0249]]'s own independently-derived "14/22 stage-1+seed survivors"
number exactly — a real cross-validation that the fix produces the
*correct* number, not just *a* number. Recomputed the corrected
head-to-head Wilcoxon table on the clean n=14 (see [[TASK-0243]]'s own
amended Done section for the full table) — **no qualitative verdict
flips**: ctqw still trails `fpocket_drug` in direction (not significant),
still not significant vs. `hop_covariate`, still significantly beats
`random` (p=0.0032, *more* decisive than the contaminated p=0.0157).

**4. Stage-1 failure decomposition (this task's own central question) —
answered plainly: MIN_HOP, not fpocket detection, is the dominant
failure mode.** Of the 6 genuine stage-1 failures (excluding the 2
seed-empty targets, which are a third, distinct failure category — no
seed to even attempt distality filtering on): **5 are `min_hop_removed`,
only 1 is `fpocket_miss`.** For every `min_hop_removed` case, fpocket
*did* propose a real candidate overlapping the true pocket (overlap
0.25–1.00 — `SMYD3_DIPERODON`'s fpocket candidate is a **100%** match to
the true pocket) — `MIN_HOP=2` removed it because its minimum hop
distance from the seed was 0 or 1, i.e. immediately adjacent. **This
directly answers this task's own Scope question**: yes, `MIN_HOP` is
measurably a source of false negatives on this frozen set, at a rate
(5/22 ≈ 23% of the whole set) that is not a rounding-error edge case.
Whether that means these 5 targets' own true site isn't "distal" enough
to belong in a distality-filtered protocol, or that `MIN_HOP=2` is too
strict a threshold, is a genuine open call for whoever owns the joint
protocol's own parameter freeze — reported here as a measured fact, not
decided. **Also corrects [[TASK-0243]]'s own specific claim** that
`NAMPT_NPA1R` failed because "fpocket's own apo-side search never
proposes the true pocket" — it is a `min_hop_removed` case (47% overlap
candidate found, `min_hop=0`), not a detection miss; corrected in that
task's own amended Done section.

**Stage-1 recall published as a standing metric, per this task's own
Scope** — reported here and in [[TASK-0243]]'s own amended section;
making it an automated/enforced gate on every future two-stage run (so
it can never again be implicit) is a process recommendation, not built as
code here — flagged for whoever next touches `task0242_two_stage_
dryrun.py`'s own `main()`.

**Not done, and why**: replacing the dropped `HIV_INTEGRASE` pair with a
real, VALID-scored, live-RCSB-verified integrase apo/holo pair — a full
curation cycle matching [[TASK-0243]]'s own original effort, out of this
audit task's own proportional scope. Making stage-1 recall an enforced,
automated gate rather than a reported number — a code change to
`task0242_two_stage_dryrun.py`'s own `main()`/`task0243_stage1_and_
rerun.py`, not attempted here.

Tests: no `src/` code changed — the fix is in `scripts/
task0242_two_stage_dryrun.py`, which (per this project's own established
convention for that directory) has no dedicated unit tests; verified
directly instead — re-ran the original `main()` earlier in
[[TASK-0244]]'s own session and confirmed it reproduced its own published
numbers before this task's own further edit; this task's own edit only
adds a new, first-line-of-`run()` guard that changes behavior *only* when
`len(seed)==0`, which cannot occur for any correctly-configured target
(confirmed: every other target in both TASK-0242's and TASK-0243's own
sets still runs and ranks identically, per this task's own audit output).

Artifacts: `scripts/task0253_seed_and_stage1_audit.py` (new),
`scripts/task0242_two_stage_dryrun.py` (empty-seed guard fix,
`failure_reason` diagnostic extension), `results/tasks/
0253_frozen_set_audit/{seed_audit.json,stage1_audit.json}`,
`.ai/tasks/DONE/TASK-0243-*.md` (amended, 2 corrections).
