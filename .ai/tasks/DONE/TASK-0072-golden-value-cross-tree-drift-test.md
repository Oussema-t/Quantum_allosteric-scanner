# TASK-0072 Golden-value cross-tree drift test

## Context

- ID: TASK-0072
- Title: Fix a reference structure and assert `backend/` and `allostery/`
  produce numerically identical output for every shared-primitive pair,
  so "ported, not cross-imported" code cannot silently diverge again.
- Status: Done (2026-08-02) — both trees bit-for-bit identical on a fixed synthetic reference structure; drift detector constructed and confirmed to fire
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 2, item 2.3 — "The
  anti-drift mechanism [TASK-0066] needs: fix a reference structure,
  assert both trees produce numerically identical output. Without it
  'ported' decays back into 'duplicated' — exactly how 8.0 vs 10.0
  happened." Must land after TASK-0067 (2.1, picks the constant) and
  alongside/after TASK-0066 (2.2, extracts the shared helper).

## Intent Contract

- Outcome: a test (or test suite) that runs both `backend/`'s and
  `allostery/`'s implementation of each shared primitive (Kirchhoff/GNM
  context, DCC, z-score, and whatever else TASK-0066 covers) on the same
  fixed reference structure and asserts the numeric outputs match within
  float tolerance. Runs in CI so any future edit to either side that
  breaks parity is caught immediately, not rediscovered by another
  architecture-reconciliation pass.
- In Scope: the primitives TASK-0066 identifies and ports (Kirchhoff
  context, DCC, z-score helper) plus the GNM cutoff constant TASK-0067
  resolves.
- Out Of Scope: this is not itself the dedup (TASK-0066) — it's the
  regression guard that keeps the dedup honest going forward. Can be
  written test-first, alongside TASK-0066's implementation.
- Acceptance Scenarios:
  - Given the fixed reference structure, when `backend`'s and
    `allostery`'s versions of a shared primitive both run, then their
    outputs are numerically identical within a stated float tolerance.
  - Given a deliberate one-line divergence introduced into either side
    (e.g. change a constant), when the test suite runs, then it fails —
    proving the test actually detects drift rather than trivially
    passing.
- Constraints And Invariants: depends on TASK-0067's chosen cutoff
  constant being landed first (per the plan's explicit ordering) —
  otherwise this test pins the wrong number as "golden."
- Planned Validation: the acceptance scenarios above; include this suite
  in whatever CI TASK-0077 (Phase 3, one CI) eventually sets up.

## Dependency

- Depends on TASK-0067 (GNM cutoff benchmark — must resolve the constant
  first) and TASK-0066 (shared Kirchhoff/DCC helper — this task pins its
  output).
- Feeds TASK-0077 (single CI workflow) once that lands.

## Open Questions

- None yet — scope is fully determined by TASK-0066/0067's outputs; defer
  the exact primitive list until those land.

## Done

**Headline: both trees' shared Kirchhoff/DCC primitives are bit-for-bit identical
on a fixed reference structure, not just float-close — confirmed directly before
writing any assertion, not assumed.**

### Scope confirmed against current code, not the (much older) filing text

TASK-0066/TASK-0067 are both Done; `backend/` still exists as its own tree
(TASK-0018's boundary, unchanged). Re-read both Done sections and the current
source directly rather than trusting the old filing text's own primitive list:
`backend/analysis.py::_kirchhoff_eigh`/`_normalized_dcc` and
`allostery/potentials.py::_kirchhoff_eigh`/`_normalized_dcc` are the actual shared
core (TASK-0066); `gnm_context`'s own live `cutoff=8.0` default confirms
TASK-0067's resolved constant is still in effect, unchanged since that task
landed.

### Real (harmless) signature difference found and handled explicitly

`backend`'s `_kirchhoff_eigh` returns a 6-tuple (`A, deg, w, U, nz, winv`);
`allostery`'s returns a 5-tuple (`A, w, U, nz, winv`, `deg` omitted — trivially
`A.sum(1)` at any call site). Not itself a drift bug (each side's own return
shape is unchanged here, per this task's own Out Of Scope) — the new test suite
unpacks each side explicitly by name rather than comparing tuples positionally,
and includes its own check that `deg == A.sum(1)` so this difference doesn't
silently mask a real one.

### Fixed reference structure: synthetic, not RCSB

A deterministic 40-residue helical point cloud (`np.random.default_rng(42)`,
`test_golden_value_cross_tree_drift.py::_reference_structure`) — no network
fetch, so the suite runs fast and reliably in CI once TASK-0077 lands, unlike
`backend/test_analysis.py`'s own live-KRAS_G12C regression pin (network-gated,
skips cleanly if unreachable). A real protein-like fold (helical curvature +
per-residue jitter), not a degenerate line or bare ring — deliberately avoiding
`allostery.chiral`'s own documented "a ring is the wrong minimal topology"
lesson from an unrelated task, even though nothing here needs circulation; the
underlying point still applies (a degenerate fixture risks hiding real drift
behind an accidentally-trivial contact graph).

### Confirmed bit-identical, not merely tolerance-close

Checked directly before deciding the assertion strength: `A`, eigenvalues `w`,
eigenvectors `U`, the nonzero mask `nz`, `winv`, and the resulting normalized
DCC matrix are all `np.array_equal` (exact) between the two trees on the
reference structure — both sides build the identical Kirchhoff matrix from
identical coordinates via the identical formula and call the identical LAPACK
`eigh` routine, so there is no accumulated floating-point path difference to
tolerate. Exact equality is asserted throughout (a `float`-tolerance fallback
is documented as available but not needed here — using one anyway would only
mask a real, catchable drift).

### The drift detector has been seen to fire (TASK-0103's own discipline)

Per this task's own Acceptance Scenario ("a deliberate one-line divergence...
the test suite fails"), `TestDriftIsActuallyDetected` constructs two real
divergence classes without touching the shipped functions (avoiding a risky
monkeypatch that could leak into other tests): a mismatched cutoff (the exact
bug class TASK-0018 originally found — three live cutoffs, nothing catching a
fourth) and an unnormalized-covariance DCC (the one-line "forgot to divide by
`np.outer(d,d)`" bug), and asserts the same `np.array_equal` check the real
tests rely on correctly returns `False` for both. A detector never seen to
fire is not a detector.

### Wired into the existing whitelisted test runner, not a new CI workflow

TASK-0077 (single CI workflow) is still TODO — no GitHub Actions pytest step
exists yet to wire this into (confirmed: `.github/workflows/` has only a
keepalive job). Per this task's own Planned Validation ("include this suite in
whatever CI TASK-0077 eventually sets up"), the correct scope here is making
the suite runnable and discoverable now, not building CI infrastructure that's
a separate task's job. Added a new `cross-tree` preset to
`.ai/tools/pytest_local.py` (the project's own whitelisted pytest wrapper,
TASK-0026.004) and extended the existing `all` preset to include it —
`python3 .ai/tools/pytest_local.py cross-tree` or `all` both pick it up
immediately; whoever builds TASK-0077's workflow only needs to call the
already-existing `all` preset.

### Tests

11 new tests, `test_golden_value_cross_tree_drift.py` (repo root — needs both
trees importable at once, doesn't belong under either `backend/` or
`__WORK_IN_PROGRESS__/tests/` exclusively): 5 `_kirchhoff_eigh` parity checks,
2 `_normalized_dcc` parity checks (plus a self-correlation-diagonal sanity
check on both sides), 1 golden-cutoff-constant pin, 2 constructed-divergence
detection checks, 1 reference-structure-determinism sanity check.

**Full validation**: `python3 .ai/tools/pytest_local.py cross-tree --json` — 11
passed, 0 failed. `python3 .ai/tools/pytest_local.py all --json` (`wip-all` +
`backend` + `cross-tree`, all three real local test surfaces together) — 1096
passed, 2 xfailed, 0 failed.

**Cross-linked, 2026-08-03 ([[TASK-0073]]):** this test suite is now the
registered seam-test for two VERIFIED records — [[SEAM-0013]] (the
Kirchhoff/DCC primitive parity `TestKirchhoffEighCrossTreeParity`/
`TestNormalizedDccCrossTreeParity` establish) and [[SEAM-0014]] (the
resolved GNM cutoff `TestGoldenCutoffConstant` pins).
