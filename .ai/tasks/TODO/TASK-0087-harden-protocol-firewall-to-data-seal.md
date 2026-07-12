# TASK-0087 Harden protocol.py's firewall from a cooperative gate to a hard data-seal

## Context

- ID: TASK-0087
- Title: `protocol.py`'s `frozen_context`/`assert_readable` firewall is an
  **opt-in, cooperative** gate — it only blocks reads that go through
  `protocol.get_pocket_mask`/`get_labels`/`get_functional_indices`/
  `get_superpose_report`. FROZEN-path code that imports `labels.py`/
  `superpose.py` directly bypasses it entirely, with no error. The
  reference spec `test_leakage_gate.py::_SealedLabels` is structurally
  stronger: it wraps the *data itself* (`__array__`/`__getitem__` both
  raise), so no caller, however written, can read a sealed array by any
  means. Decide whether to harden `protocol.py` to match, or explicitly
  accept the weaker guarantee and document why.
- Status: TODO
- Owner: Implementer
- Source: TASK-0052 (leakage-gate contract reconciliation) — its own TODO
  item "verify `frozen_context`/`assert_readable` equivalence to the
  `FrozenConfig`/`_SealedLabels` reference spec... rather than assume
  'different design, probably fine'" was checked for real, and a genuine
  (not hypothetical) gap was found. TASK-0006's own Open Question already
  named this exact fork ("Should the leakage guard be enforced by static
  wrapping... or by a lint-style check?") without an empirical answer at
  the time; this task has one now.

## Intent Contract

- Outcome: either (a) `protocol.py`'s gate becomes a hard data-seal
  (wrapping the *return value* of `labels.py`/`superpose.py`'s
  holo-derived functions themselves, not just gating a parallel accessor
  function next to them — the actual data object, wherever it flows,
  refuses to be read while sealed, matching `_SealedLabels`), or (b) the
  cooperative-gate design is explicitly re-affirmed as sufficient with a
  written rationale (e.g. "every FROZEN-path caller is reviewed code in
  this repo, not third-party input, so cooperation is an acceptable
  trust boundary") — not silently left as an undocumented assumption
  either way.
- In Scope: `protocol.py`'s gating mechanism; a test that a *direct*
  `labels.holo_pocket_mask`/`build_labels` call (bypassing
  `protocol.get_*`) on a held-out target either raises (if hardened) or
  is explicitly documented as an accepted gap (if not).
- Out Of Scope: rewriting `labels.py`/`superpose.py`'s own APIs; this is
  about the boundary/wrapping mechanism, not the underlying functions.
- Constraints And Invariants: whichever option is chosen, do not leave
  the module docstring's current framing ("this is an opt-in firewall...
  not a retroactive lock") as the only signal — that line is honest about
  *scope* but doesn't say whether the scope was a deliberate risk
  acceptance or an unexamined gap. This task exists to make it one or the
  other, explicitly.
- Planned Validation: a test demonstrating the chosen behavior (raises on
  direct bypass, or documented pass-through) against a real held-out
  target scenario matching `test_leakage_gate.py::
  test_protocol_lopo_seals_heldout_labels`'s shape.

## Dependency

- [[TASK-0006]] (Done) — `protocol.py`, the module in question.
- [[TASK-0052]] — found this gap while verifying equivalence to
  `test_leakage_gate.py`'s reference spec.

## Open Questions

- Is a full data-seal wrapper (returning a `_SealedLabels`-like object
  from `labels.py`'s own functions when called under a `frozen_context`)
  architecturally sound, or does it fight `labels.py`'s designed
  independence from `protocol.py` (today `labels.py` doesn't import
  `protocol.py` at all — a data-seal implemented in `labels.py` would
  need to know about frozen-context state, coupling a module that
  currently doesn't depend on the firewall at all)? A wrapper applied at
  the `protocol.get_*` boundary (sealing the *return value* before
  handing it to the caller) avoids that coupling but still doesn't stop
  a direct `labels.holo_pocket_mask` call from succeeding unsealed —
  worth resolving which failure mode actually matters before picking an
  implementation.

## Done

(not yet)
