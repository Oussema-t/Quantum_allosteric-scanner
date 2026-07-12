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
- Status: Done
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

## TODO (resolved 2026-07-12, Implementer A)

- [x] Relocate the file.
- [x] Diff the file's CONTRACT section against the real `labels.py`/
      `protocol.py` APIs (`grep -n "^def |^class "` both files) —
      confirmed `build_labels`/`Labels`/`FrozenConfig`/`lopo` do not
      exist under those names.
- [x] Add a `pytest_local.py` preset for this file (or fold into
      `wip-all` — confirm it doesn't need network access by default; the
      3 contract stubs' network-gated real-target checks should follow
      the same `pytest.importorskip("prody")` pattern TASK-0005 already
      uses, not a hard dependency).
  - Already inside `wip-all`'s scan (the file lives under
    `__WORK_IN_PROGRESS__/tests/`) — no new preset needed, confirmed by
    running `pytest_local.py wip-all` and seeing it collected. The
    network-gated real-target test does not import `pytest` at all (the
    file supports standalone `python test_leakage_gate.py` execution per
    its own docstring, so `pytest.importorskip` would break that mode) —
    uses a local `_skip()` helper (try/except around the prody import and
    the fetch) that degrades gracefully in both run modes instead.
- [x] Decide + implement (a) vs (b) above for the `build_labels` gap.
  - (a), already landed by TASK-0070 (this task's own named dependency).
  - This task rewrote the CONTRACT header comment block to describe the
    *real* API (`target_config: dict`, not `allosteric_ligand`/
    `func_ligands` positional args) instead of leaving the original
    (now-known-wrong) assumption in place — "docstring ≠ contract" cuts
    both ways; a stale contract comment is exactly the smell
    `SEAM_PROTOCOL.md` warns about.
- [x] Fix the `lopo` -> `leave_one_protein_out` rename.
  - Done in `test_protocol_lopo_seals_heldout_labels`, rewritten to
    exercise the real mechanism (`leave_one_protein_out` +
    `frozen_context` + `assert_readable`) rather than a bare rename of an
    unused import.
- [x] Verify `frozen_context`/`assert_readable` equivalence to the
      `FrozenConfig`/`_SealedLabels` reference spec; report any real gap
      found rather than assuming equivalence.
  - **Real gap found, not assumed equivalent.** `_SealedLabels` wraps the
    *data itself* (`__array__`/`__getitem__` both raise) — no caller,
    however written, can read a sealed array. `protocol.py`'s
    `frozen_context`/`assert_readable` is an **opt-in, cooperative**
    gate: it only blocks reads that go through `protocol.get_pocket_mask`/
    `get_labels`/`get_functional_indices`/`get_superpose_report`.
    FROZEN-path code that imports `labels.py`/`superpose.py` directly
    bypasses it entirely, with no error — a caller-discipline requirement,
    not a structural guarantee. `protocol.py`'s own module docstring
    already says this is deliberate scope ("an opt-in firewall... not a
    retroactive lock"), but that line is honest about *scope*, not about
    whether the resulting weaker guarantee was a reviewed risk acceptance
    or an unexamined gap — TASK-0006's own Open Question left this exact
    question unanswered ("Should the leakage guard be enforced by static
    wrapping... or by a lint-style check?"). Filed [[TASK-0087]] to
    resolve it explicitly (harden to a real data-seal, or document the
    weaker guarantee as an accepted trust boundary) rather than silently
    closing this task on "different design, probably fine."
- [x] Run the full file, report per-test pass/fail.
  - Both modes, all 12 tests, 0 xfail (down from 3):
    `pytest tests/test_leakage_gate.py -v` -> 12 passed. Standalone
    `python test_leakage_gate.py` (its own docstring's other supported
    invocation) -> `12 passed, 0 failed`, including the two real
    network-gated checks (`test_labels_allosteric_ligand_only` actually
    fetched 1OPL/5MO4 and resolved AY7, did not skip).
  - Full suite (`python3 .ai/tools/pytest_local.py wip-all`, minus
    `test_viz.py`/`test_seam_0006_pathways_viz.py` — TASK-0014's own
    concurrent, unrelated `matplotlib` gap): 370 passed (368 -> 370, the
    2 tests this task fixed), 1 pre-existing xfail, 1 pre-existing xpass,
    no regressions.
- [x] Update `SEAM-0003`'s status (from [[TASK-0050]]) once the assembly
      step lands — `OPEN` -> `VERIFIED` only if a seam-test actually
      passes, not on landing alone.
  - Done: `.ai/seams/SEAM-0003-pocket-excludes-functional-terminal.md`
    updated to `VERIFIED`, listing the real passing seam-test plus the
    corroborating `test_labels.py::TestBuildLabels` tests (synthetic
    overlapping case + two independent real targets).

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
  - **Resolved:** independent reinvention, not a reviewed match — and not
    fully equivalent (see TODO section: real gap found, TASK-0087 filed).
    `FrozenConfig`'s three GATE-B1 mechanics tests (immutable-after-freeze,
    no-eval-before-freeze, hash-is-fingerprint) remain valid as
    pipeline-agnostic reference tests in their own right — they were never
    claiming to test `protocol.py` directly (no CONTRACT stub referenced
    `FrozenConfig` by name), so nothing needed fixing there.
- If `build_labels()` is added (option a), should it live in `labels.py`
  itself or in a new thin `assembly.py`? Recommend `labels.py` — it's a
  composition of that module's own existing functions, not a new concern.
  - **Resolved by TASK-0070:** lives in `labels.py`, as recommended.

## Done

- `test_leakage_gate.py`'s CONTRACT header comment rewritten to describe
  the real `labels.py`/`protocol.py` API (was describing an API that
  never shipped) — "docstring ≠ contract" applies to this file's own
  header too, not just to `labels.py`/`protocol.py`'s docstrings.
- All 3 CONTRACT stub tests rewritten to call the real API for real (no
  more `except Exception: return _xfail(...)` branches):
  - `test_labels_allosteric_ligand_only` — real network-gated BCR_ABL1
    check (1OPL apo / 5MO4 holo), `target_config={"drug_ligand": "AY7",
    "func_ligand": ["NIL"]}` (AY7 is the real RCSB code the original
    "ASCIMINIB" placeholder was superseded by, TASK-0003) — passes for
    real, not skipped, in this environment.
  - `test_labels_alignment_not_resnum` — new synthetic +19-offset test
    (fast, no network) confirming `build_labels`' sequence-alignment
    mapping, not resnum equality, is what actually runs end-to-end.
  - `test_protocol_lopo_seals_heldout_labels` — rewritten around the real
    `leave_one_protein_out` + `frozen_context` + `assert_readable`
    mechanism, confirming the GATE-B2 guarantee (held-out label
    unreadable during selection) holds for real, through the actual
    firewall.
- `SEAM-0003` closed to `VERIFIED` with the passing seam-test named.
- Real gap found and filed as [[TASK-0087]]: `protocol.py`'s firewall is
  an opt-in/cooperative gate, not a hard data-seal like the reference
  `_SealedLabels` — direct `labels.py`/`superpose.py` calls bypass it
  with no error. Not fixed in this task (Out Of Scope: this task
  reconciles the contract test, not the firewall's own design) — recorded
  and handed off explicitly rather than silently assumed equivalent.
- Full file: 12/12 passing under both `pytest` and standalone `python
  test_leakage_gate.py` (this file's own two documented invocation
  modes), 0 xfail. Full suite: 370 passed (368 -> 370), 1 pre-existing
  xfail, 1 pre-existing xpass, no regressions (excluding TASK-0014's own
  unrelated `matplotlib` collection gap in two other files).
