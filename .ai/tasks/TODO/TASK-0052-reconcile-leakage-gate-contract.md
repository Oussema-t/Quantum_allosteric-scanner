# TASK-0052 Reconcile `test_leakage_gate.py`'s assumed contract against the actual shipped `labels.py`/`protocol.py` API

## Context

- ID: TASK-0052
- Title: `test_leakage_gate.py` (relocated from `__WORK_IN_PROGRESS__/` to
  `__WORK_IN_PROGRESS__/tests/`) assumes a `build_labels(...) -> Labels`
  API and a `FrozenConfig`/`lopo` API that **do not exist** in the actual
  shipped `labels.py`/`protocol.py` (both TASK-0004/TASK-0006, Done). Wire
  the file into the test runner, then reconcile the contract against
  reality — implement the missing assembly step or rewrite the contract
  tests against the real API, whichever is correct once actually checked.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: user request, 2026-07-11 session — see [[TASK-0050]]'s Source.
  This task exists because reading the file against the live tree (not
  the file's own comments) turned up a real discrepancy, not because the
  source request named one.
- Crit Ref: this task is the named owner of [[TASK-0050]]'s seed
  `SEAM-0003` ("pocket ↔ functional/terminal — assembled pocket excludes
  both — OPEN, no assembly step exists"). It is also independently
  corroborated by [[TASK-0047]] (Reviewer A's Foundation Review, P2:
  `labels.py` has no committed network-gated integration test matching
  its own Intent Contract's promise) — two different investigations
  converging on the same real gap in the same module.

## Intent Contract

- Outcome: `test_leakage_gate.py` runs under `pytest_local.py`, and every
  one of its CONTRACT stub tests (`test_labels_allosteric_ligand_only`,
  `test_labels_alignment_not_resnum`, `test_protocol_lopo_seals_heldout_labels`)
  either passes for real against actual `allostery` code, or is rewritten
  to test the real API with an equivalent guarantee — not left `xfail`
  forever with a stale contract nobody notices doesn't match reality.
- In Scope:
  - relocate the file -> `__WORK_IN_PROGRESS__/tests/test_leakage_gate.py`
    — **done, this commit** (by the filing thread, mechanical move only).
  - add it to `.ai/tools/pytest_local.py`'s preset set (new preset, e.g.
    `wip-leakage-gate`, or folded into `wip-all` — Toolsmith/Implementer's
    call at execution time, name it in `.ai/reference/CAPABILITIES.md`
    either way per that table's existing documentation discipline)
  - run the file's non-contract tests first (`test_meta_permutation_detector_discriminates`,
    the `FrozenConfig`/`_SealedLabels` reference-mechanics tests,
    `test_degree_confound_flags_disguised_degree`, the floor/ceiling
    tests) — these are genuinely pipeline-agnostic and self-validating,
    confirmed by reading the file; they should pass standalone with zero
    changes and are not what this task's real work is about
  - for the 3 CONTRACT stubs, resolve the actual discrepancy found:
    - `from allostery.labels import build_labels` — **does not exist.**
      The real `labels.py` exports `holo_pocket_mask`, `functional_indices`,
      `terminal_mask`, `pick_drug` as separate functions, never assembled
      into one `Labels` object with `.pocket`/`.active_site`/
      `.provenance`. This is `SEAM-0003` itself, made concrete: decide
      whether to (a) add a thin `build_labels()` assembly function to
      `labels.py` that calls the existing pieces and asserts
      `pocket ∩ (functional ∪ terminal) == ∅` — the seam invariant,
      finally executable — or (b) rewrite the 3 contract tests to call
      the real functions directly and assert the same exclusion
      manually. Recommend (a): the seam's whole point is that the
      exclusion currently has *no assembly step to test at all*; adding
      one is what actually closes the seam, not just relabeling the test.
    - `from allostery.protocol import lopo` — the real function is
      `leave_one_protein_out` (`protocol.py:175`). Simple rename in the
      test, confirm behavior matches.
    - `protocol.FrozenConfig` / the `_SealedLabels` runtime tripwire — the
      real `protocol.py` uses a different but plausibly-equivalent design
      (`ProtocolContext`/`frozen_context`/`assert_readable`,
      `protocol.py:44-108`). Verify equivalence explicitly (does
      `assert_readable` actually raise on every held-out-label read
      `_SealedLabels` would catch, not just the ones `protocol.py`'s own
      tests happened to exercise?) rather than assume "different design,
      probably fine."
- Out Of Scope:
  - the doc-level Seam/Invariance Protocol adoption itself —
    [[TASK-0050]]/[[TASK-0051]], separate tasks this one's findings feed.
  - reopening TASK-0004/TASK-0006 — they're Done; this task is a
    follow-up, same "record vs. execute, decide vs. remediate" split this
    scaffold already uses elsewhere (TASK-0018, TASK-0023).
- Constraints And Invariants:
  - the permutation-null detector (GATE-B4) is explicitly named in the
    file's own docstring as "the load-bearing detector" that "catches
    [a leak] regardless of *where* the leak entered" — if time is short,
    prioritize getting `test_meta_permutation_detector_discriminates`
    running for real over the 3 contract stubs; it's the cheapest, most
    general check of the group.
  - do not weaken any existing `labels.py`/`protocol.py` test to make
    this pass — if a genuine conflict is found between the two designs,
    that's a finding to report, not a green-bar to force.
- Acceptance Scenarios:
  - Given `pytest_local.py wip-leakage-gate` (or wherever it lands), when
    run, then the file's self-validating meta-tests pass and every
    CONTRACT test either passes for real or is explicitly, correctly
    rewritten — no test silently stays `xfail` against a contract that
    was simply wrong.
- Planned Validation: run the relocated file both standalone
  (`python test_leakage_gate.py`, per its own docstring) and under
  `pytest_local.py`; report pass/fail per test, not an aggregate.

## In Progress

None

## TODO

- [x] Relocate the file.
- [x] Diff the file's CONTRACT section against the real `labels.py`/
      `protocol.py` APIs (`grep -n "^def |^class "` both files) —
      confirmed `build_labels`/`Labels`/`FrozenConfig`/`lopo` do not
      exist under those names.
- [ ] Add a `pytest_local.py` preset for this file (or fold into
      `wip-all` — confirm it doesn't need network access by default; the
      3 contract stubs' network-gated real-target checks should follow
      the same `pytest.importorskip("prody")` pattern TASK-0005 already
      uses, not a hard dependency).
- [ ] Decide + implement (a) vs (b) above for the `build_labels` gap.
- [ ] Fix the `lopo` -> `leave_one_protein_out` rename.
- [ ] Verify `frozen_context`/`assert_readable` equivalence to the
      `FrozenConfig`/`_SealedLabels` reference spec; report any real gap
      found rather than assuming equivalence.
- [ ] Run the full file, report per-test pass/fail.
- [ ] Update `SEAM-0003`'s status (from [[TASK-0050]]) once the assembly
      step lands — `OPEN` -> `VERIFIED` only if a seam-test actually
      passes, not on landing alone.

## Dependency

- [[TASK-0004]] (Done) — `labels.py`, the module with the actual gap.
- [[TASK-0006]] (Done) — `protocol.py`, the module with the plausibly-
  equivalent-but-unverified firewall design.
- [[TASK-0047]] — independent corroborating finding (missing integration
  test), read together with this task's finding rather than duplicated.
- [[TASK-0050]] — this task is `SEAM-0003`'s named owner; that record
  must exist before this task's status update to it makes sense.

## Open Questions

- Is `frozen_context`/`assert_readable`'s design a deliberate, reviewed
  improvement over the `FrozenConfig` reference spec, or an independent
  reinvention that happens to cover similar ground? Neither TASK-0004 nor
  TASK-0006's Done sections mention the leakage-gate file at all (checked
  — zero hits), so this is genuinely unknown, not just undocumented.
- If `build_labels()` is added (option a), should it live in `labels.py`
  itself or in a new thin `assembly.py`? Recommend `labels.py` — it's a
  composition of that module's own existing functions, not a new concern.

## Done

(not yet)
