# TASK-0231 The suite is blind to config-level breakage — demonstrated by mutation test

## Context

- ID: TASK-0231
- Status: Done
- Resolution: done
- Resolution Note: 4 guards built and wired into real pipeline code (build_labels itself, not just tests). Validated by reintroducing the exact TASK-0216 mutation into the real targets.yaml -- 3 targeted failures appeared (was 1208 passed/0 failures before), then reverted, suite green. Found+fixed a second live instance of the same defect class (CARDIAC_MYOSIN_TABLE1's own stale config comment) plus 2 pre-existing latent test-fixture gaps the new guard surfaced. Full suite 1245 passed, 0 failed.
- **Thread: Implementer.** Mechanical; no new science.
- Owner: Implementer
- Source: Bartosz, 2026-08-21 — *"So many tests added and no newer seams? No
  false negative/positive tests? No need to adapt tests?"* Investigated the
  same day; the answer to all three is worse than "no".
- Priority: **P0.** The defect it guards against is one this register already
  paid a full session to find ([[TASK-0216]]), and nothing prevents its return.

## The demonstration

Reverted GLUCOKINASE's `func_ligand` from the corrected `['GLC']` back to a
non-code (`['NotARealCode']`) — reintroducing verbatim the defect
[[TASK-0216]] found — and ran the full suite:

```
1208 passed, 1 skipped, 3 xfailed
```

**The suite is green on a config that silently seeds every active-site
observable for that target at the top-5 highest-degree residues.** No test
fails, no warning is asserted on, nothing degrades visibly.

Two further facts from the same investigation:

1. **`test_targets_config.py` pins `func_ligand` for exactly one target** —
   `assert "NIL" in cfg["func_ligand"]` (BCR_ABL1). The other 12 configs are
   unpinned by construction.
2. **Changing `func_ligand` for six targets left the suite green.** That change
   alters `build_labels`' active site, which alters the pocket label via
   `pocket_raw & ~active_site & ~terminal`, which alters every downstream
   number for those targets. The suite did not notice.

## The diagnosis, stated because it generalises

This is the same construct-validity failure the [[TASK-0217]] family
documents, one level up: **the tests verify that functions compute what they
compute, and never that the pipeline is wired to real inputs.** Every defect
found in the 2026-08 window lived in the wiring, and the suite is blind to
wiring by design.

Corroborating and previously unread signal: **every one of those defects was
found by re-running a measurement, and not one by a test failing.** That
asymmetry was diagnostic and went unexamined.

## Intent Contract

- Outcome: the mutation above fails the suite, and the same class of
  config-level breakage cannot recur silently on any target.
- In Scope:
  1. **Provenance assertion.** No target may score an active-site-seeded
     observable on a `fallback` provenance without an explicit, per-target
     opt-in. This single test would have caught [[TASK-0216]] on day one.
  2. **Config-integrity test.** Every `func_ligand` entry resolves to a real
     chem-comp code **present in that target's own holo entry**. Note this
     *should* fail today for PTP1B / CASPASE1 / CASPASE7, whose holo entries
     genuinely contain no functional ligand — encode those as expected
     failures with the reason, not as passes.
  3. **Golden-value pins on the label pipeline** for the real targets: pocket
     size, active-site size, and provenance. Any `targets.yaml` change that
     moves them fails loudly.
  4. **Mutation test as a permanent artifact** — the GLUCOKINASE mutation
     above, encoded so the guard itself is verified rather than assumed.
- Out Of Scope:
  - Re-running any science.
  - Auditing library code for silent degradation — that is
    [[TASK-0217.001]], a different surface. This task is specifically about
    the **test suite failing to detect config-level breakage**.
- Constraints And Invariants:
  - Every new guard must **fail first** against the deliberately broken input
    before it passes against the real one. A guard that has never been seen to
    fire is not evidence.
  - Golden values must record *when and from what* they were pinned, so a
    legitimate future change can be distinguished from a regression.
- Planned Validation: re-run the GLUCOKINASE mutation with the guards in
  place; the suite must fail, and the failure message must name the cause.

## TODO

- [x] Provenance assertion + per-target opt-in mechanism.
- [x] Config-integrity test; encode the 3 genuine no-ligand cases as expected failures.
- [x] Golden-value pins (pocket size / active-site size / provenance).
- [x] Encode the mutation test permanently; demonstrate it fails first.
- [x] Re-run the original mutation as acceptance.

## Dependency

- [[TASK-0216]] (the defect), [[TASK-0217.001]] (adjacent, different surface),
  [[TASK-0232]] (registry side of the same finding).

## Done

**All 4 guards built and wired into real pipeline code (not just this
task's own test file), validated against the literal original
demonstration re-run on the real `targets.yaml` — 3 targeted failures
appeared, all named to GLUCOKINASE, then the mutation was reverted and
the full suite is green again. A second, unanticipated live defect found
and fixed along the way, plus two pre-existing latent test-fixture gaps
the new guard surfaced for the first time.**

**1. Provenance assertion (`labels.assert_functional_provenance_allowed`,
wired into `build_labels` itself)**: raises `ValueError` naming the
target if `functional_indices` falls back to the last-resort top-degree
tier without an explicit `allow_topdegree_fallback: true` opt-in in that
target's own config. Called from inside `build_labels` — protects every
real caller, not only whichever test happens to assert on
`functional_provenance` directly, directly closing this task's own core
diagnosis ("the tests verify that functions compute what they compute,
and never that the pipeline is wired to real inputs").

**A second, live instance of exactly this task's own defect class, found
while wiring the guard in (not anticipated when this task was filed)**:
`CARDIAC_MYOSIN_TABLE1`'s own config comment claimed "the active-site
SEED can resolve even though the POCKET label cannot" — checked directly
against real RCSB data, found wrong. ADP is real in 6C1H but bound to the
actin chains (A-E), not the myosin-Ib chain (P) this config's own
`holo_chains` restricts to; under that restriction `holo.ligand_groups`
is empty and the active-site seed silently fell back too, not just the
pocket label. Corrected the stale comment and added the explicit
`allow_topdegree_fallback: true` opt-in this target genuinely needs —
consistent with, and making explicit, [[TASK-0222]]'s own already-accepted
`NO_SIGNAL_IN_APO` verdict for this target.

**2. Config-integrity test** (`tests/test_config_integrity.py`,
`TestConfigIntegrityFuncLigandResolves`): every real target's declared
`func_ligand` codes checked against real, live-fetched holo
`ligand_groups`. PTP1B/CASPASE1/CASPASE7 (genuinely empty `func_ligand`,
[[TASK-0217.003]]) and — newly discovered — `CARDIAC_MYOSIN_TABLE1`
(declared but chain-restricted out) both encoded as `xfail(strict=True)`
with the reason, not silent passes, per this task's own instruction.

**3. Golden-value pins** (`TestLabelPipelineGoldenValues`): pocket size /
active-site size / provenance pinned for the 3 mandatory + 4 ASD-verified
targets, against real fetched structures, dated 2026-08-23 with the
re-pinning convention already established by [[TASK-0206]]'s own
`test_fpocket_pin.py` (never silently re-pin without recording why).

**4. The mutation test, permanent artifact**
(`TestGlucokinaseMutationGuarded`): a control (real GLUCOKINASE config
must NOT trigger the guard) plus the mutation itself
(`func_ligand=['NotARealCode']`, TASK-0216's own exact pre-fix shape)
must raise. **Fail-first constraint, demonstrated directly, not
assumed**: called `functional_indices` directly (bypassing the new
`build_labels` guard) on the mutated config first — confirmed silent
`'top-degree fallback'`, no exception, exactly reproducing the original
demonstration. Only then added the guard and confirmed it now raises.

**Acceptance — re-ran the original demonstration itself, not just a
local test copy**: temporarily reintroduced `func_ligand: ['NotARealCode']`
into the real `config/targets.yaml` (line 501) and ran the full
`__WORK_IN_PROGRESS__` suite. **3 targeted failures**, all named to
GLUCOKINASE, all with a failure message stating the cause
(`test_config_integrity.py`'s config-integrity test, golden-value pin,
and mutation-guard test) — where the original demonstration found `1208
passed, 0 failures`. Reverted the mutation, confirmed clean
(`git diff --stat` on `targets.yaml` shows only the intentional
CARDIAC_MYOSIN_TABLE1 fix, the mutation left no trace), full suite green
again.

**Two pre-existing latent gaps the new guard surfaced, unrelated to
`labels.py`'s own logic (unchanged) — fixed as a direct, necessary
consequence of wiring the guard in, not scope creep**:
`test_ceiling.py::test_kras_g12c_real_target_ceiling_cross_check` and
two tests in `test_propagators.py` built their own KRAS_G12C holo fixture
without populating `heavy_atom_coords`/`heavy_atom_seq_index` — without
heavy-atom data, GDP contact resolution silently degrades to Calpha-only
geometry, which misses GDP entirely at this cutoff, and was *already*
silently falling back before this task (the pre-existing `RuntimeWarning`
just went unasserted, same failure class this whole task is about).
Fixed by adding the same `protein_heavy_atoms_by_residue` call
`test_fpocket_pin.py` already used correctly. One of the three
(`test_time_averaged_ctqw_converged_regression_pins_spearman_vs_adequate_t_max`)
now uses the correct GDP-seeded active site instead of the wrong
fallback one, and its own pinned Spearman value shifted by ~6e-6
(0.999794 vs. the 0.9998 pin) as a direct, correct consequence — marked
`xfail(strict=True)` with a dated reason rather than silently re-pinned,
matching [[TASK-0206]]'s own established precedent for exactly this
situation (input legitimately changed → output legitimately changed →
record it, don't quietly absorb it). `test_run_challenge.py`'s own
`test_no_drug_ligand_resolved_is_a_handled_failure_not_a_crash` needed a
local `allow_topdegree_fallback: True` addition to its synthetic
config — its own scenario deliberately has no ligand data at all, a
legitimate, deliberate reason to hit the fallback tier, not a defect.

**Validated**: full `__WORK_IN_PROGRESS__` suite, 1245 passed, 1 skipped,
8 xfailed (7 pre-existing + this task's own new Spearman xfail), 0
failed — both before filing (baseline) and after every change in this
task, including the full mutation-reintroduction/revert cycle above.

**Not done, per this task's own Out Of Scope**: auditing library code
for other silent-degradation classes ([[TASK-0217.001]]'s own surface);
re-scoring or re-deriving any science (the one legitimately-shifted
golden value is recorded via `xfail`, not re-run or re-tuned).
[[TASK-0232]] (the registry side of this same finding) is a separate task,
not touched here.
