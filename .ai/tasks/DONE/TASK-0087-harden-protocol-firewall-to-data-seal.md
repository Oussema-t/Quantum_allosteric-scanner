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
- Status: Done
- Resolution: done
- Resolution Note: Cooperative-gate design re-affirmed (option b), checked rationale landed in protocol.py's own docstring. Real gap found while checking (GATE-B4 not wired into real pipeline) filed as TASK-0218, not silently absorbed.
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

**Verdict: option (b) — the cooperative-gate design is explicitly
re-affirmed, not hardened into a data-seal, with a checked (not assumed)
rationale landed in `protocol.py`'s own module docstring. A real,
connected gap found while deciding was surfaced and filed separately
([[TASK-0218]]), not silently absorbed or fixed inline.**

**Why option (a) — a hard data-seal — was rejected, reasoned through, not
just asserted:**

1. **The Open Question's own proposed shape doesn't close the named gap.**
   A seal applied at `protocol.get_*`'s own return-value boundary (wrap
   what `get_pocket_mask` etc. hand back) only protects a call that
   already went *through* the gate. The actual named threat is a caller
   that never calls `protocol.get_*` at all — it imports `labels.py`
   directly. Sealing a return value nobody asked for provides zero
   additional protection against that. Worked through explicitly before
   rejecting it, not dismissed by assumption.
2. **The only design that actually closes it inverts a clean dependency.**
   `labels.py`/`superpose.py` would need to import `protocol.py` and
   check `current_context()` internally — today `protocol.py` imports
   *them* (one-way), and neither currently knows this bookkeeping layer
   exists (by design, per this module's own pre-existing "not a
   retroactive lock" framing).
3. **Trust boundary is reviewed code, not adversarial input** — FROZEN-
   path callers are `select.py`/`analysis.py`, written and reviewed in
   this repo, not third-party.
4. **Checked directly, not assumed: no live leak exists today.** Read
   `run_challenge.py::_make_candidates_builder` (the only real production
   code the gate's `frozen_context` actually polices) — it reads only
   `apo.coords`/`apo.bfactors`, never labels, "leak-safe by construction"
   per its own comment. Confirmed by reading the actual shipped code, not
   inferred from the docstring's claim.

**Real, connected finding while checking rationale item 5 (GATE-B4 as a
backstop) — surfaced, not silently used to strengthen the case anyway.**
`diagnostics.detect_permutation_leak` (GATE-B4) is documented as an
entry-point-agnostic catch-all for exactly this class of unforeseen leak.
Grepped for its actual call sites before citing it: `detect_permutation_
leak` (the real function, not the generic "permutation_null" phrase many
unrelated scripts also use) appears **only** in its own test file
(`test_diagnostics.py`) — never wired into `run_challenge.py` or any real
pipeline script. The "cooperative gate is fine, a structural backstop
covers the gap" argument was about to be strengthened by this, and would
have been resting on a design intent, not an operational fact. Filed as
[[TASK-0218]] instead of quietly citing it as settled, and instead cited
in the docstring below with that exact caveat attached.

**Landed, not left as the only signal (this task's own Constraint)**:
`protocol.py`'s module docstring now carries an explicit "TASK-0087 --
cooperative gate, not a hard data-seal, decided explicitly" section
covering all four points above, replacing the previous framing (accurate
about *scope*, silent about whether that scope was a deliberate choice).

**Demonstrated, not just documented (Planned Validation)**: `test_protocol
.py::TestCooperativeGateAcceptedGap`, 3 new tests — a direct `labels.
build_labels` call and a direct `labels.holo_pocket_mask` call, both
inside an active `frozen_context` for the target being read, both
succeed without raising (the accepted gap, empirically real); a third
test confirms the *gated* accessor (`protocol.get_pocket_mask`) still
correctly raises for the identical read, so the record shows the gap is
specifically "bypass via direct import," not "the gate does nothing."
Full local suite re-run clean after the change: no regression.

**Retrospective note for whoever revisits this**: if a future
`candidates_builder`-shaped function ever needs to read holo-derived data
inside a `frozen_context` for a legitimate reason (not the current,
label-free `_make_candidates_builder`), that is exactly the moment this
decision should be re-opened, not assumed still valid — rationale item 4
above is a fact about *today's* shipped code, not a permanent guarantee.

Follow-up filed, not attempted here: [[TASK-0218]] (wire GATE-B4 into the
real pipeline, converting rationale item 5 from "available" to
"operational").
