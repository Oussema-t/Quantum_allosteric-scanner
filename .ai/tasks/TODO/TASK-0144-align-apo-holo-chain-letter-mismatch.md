# TASK-0144 `superpose.align_apo_holo`/`common_residues_by_resnum` silently produce zero correspondence when apo/holo use different author chain letters for the same biological chain

## Context

- ID: TASK-0144
- Title: `superpose.common_residues_by_resnum` matches apo/holo Cα atoms by
  the raw `(chain_id, resnum)` pair. TASK-0127 added an `apo_chains`/
  `holo_chains` per-role config override specifically for targets where
  the same biological chain is deposited under different author chain
  letters in the apo vs. holo structure (its own worked example:
  GLUCOKINASE, apo 1V4S chain A, holo 3H1V chain X). That override is
  wired correctly into `clean_from_config`/`run_challenge._load_apo_holo`
  (confirmed by reading both), but `superpose.py`'s own
  `align_apo_holo`/`common_residues_by_resnum` never got the same
  treatment — they only ever compare (chain,resnum) pairs verbatim, so
  when apo chain='A' and holo chain='B' (different letters, same
  biological chain), the intersection is silently empty.
  Confirmed directly, not assumed: `common_residues_by_resnum` on
  TASK-0124's own new CARDIAC_MYOSIN apo/holo pair (apo=8QYP chain A,
  holo=8QYR chain B) returns 0 common residues, which makes
  `align_apo_holo` raise (`< 3 common Ca pairs`). GLUCOKINASE has the
  identical latent bug (apo chain A, holo chain X) but has never actually
  been run through `align_apo_holo` (not in TASK-0120/125/133's own
  target lists), so this was never triggered until now.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: found live while executing [[TASK-0124]] (CARDIAC_MYOSIN
  apo replacement 5TBY -> 8QYP), which needed the `apo_chains`/
  `holo_chains` override (TASK-0127 schema) and hit this exact gap.
  Not fixed inline by that task — see its own Done section for the
  reasoning (a concurrent thread had uncommitted changes in `superpose.py`
  at the time, and this is real, separable scope, not a blocker for
  TASK-0124's own core outcome, which does not depend on
  `align_apo_holo`).
- Priority: **P2.** Does not block the main scoring pipeline (`labels.py`
  uses its own sequence-alignment correspondence, `_needleman_wunsch_map`,
  which is chain-letter-independent — confirmed by reading `labels.py`
  and by a real dry run of `build_labels` on the CARDIAC_MYOSIN 8QYP/8QYR
  pair, which succeeded). Only the geometric cross-check apparatus
  (`cryptic_openness_gate`/`background_rmsd`/`learnability_verdict`/
  `cumulative_overlap`, i.e. the TASK-0120/124/133 learnability-gate
  family) is affected, plus any future target whose config uses
  `apo_chains`/`holo_chains`.

## Intent Contract

- Outcome: `common_residues_by_resnum`/`align_apo_holo` accept an optional
  chain-remapping so a target configured with `apo_chains`/`holo_chains`
  (TASK-0127) produces a correct, non-empty correspondence instead of a
  silent empty intersection or a confusing "too few points" `ValueError`
  with no hint at the real cause.
- Suggested shape (Implementer's own call, not prescribed): an optional
  `chain_map: dict[str, str] | None` parameter on both functions (holo
  chain letter -> apo chain letter), defaulting to `None` (today's exact
  behavior, fully backward compatible — every existing caller is
  unaffected). Callers that know their target's `apo_chains`/
  `holo_chains` (e.g. `scripts/learnability_gate.py`) build the map via
  `dict(zip(holo_chains, apo_chains))` when both are set on the target
  config, `None` otherwise.
- In Scope:
  - `superpose.common_residues_by_resnum`, `superpose.align_apo_holo`.
  - `scripts/learnability_gate.py` (and any other `align_apo_holo`
    caller — re-check the full caller list at pickup time, it may have
    grown) — thread the chain map through from target config.
  - A regression test mirroring GLUCOKINASE/CARDIAC_MYOSIN's real shape:
    two structures with the same resnum but different chain letters for
    the same residue, asserting the remapped correspondence is found.
  - Re-run `scripts/learnability_gate.py` for CARDIAC_MYOSIN under its
    new (TASK-0124) apo/holo pair once this lands, and update
    [[TASK-0120]]/[[TASK-0133]]'s own `RESULTS.md` entries additively —
    their existing CARDIAC_MYOSIN numbers were computed against the
    retired 5TBY apo and should be marked superseded, not silently left
    as the only entry once a reader can no longer tell which apo they
    describe.
  - Check GLUCOKINASE too while the fix is in hand — it has the same
    latent shape and has never been run through this gate at all; running
    it is a natural, low-cost validation of the fix on a second real case.
- Out Of Scope:
  - Any change to `labels.py`'s own sequence-alignment correspondence —
    unaffected by this bug, not touched.
  - Re-deriving `clean_from_config`'s `apo_chains`/`holo_chains` handling
    — already correct (TASK-0127), reuse directly.
- Constraints And Invariants: the default (`chain_map=None`) path must
  remain byte-identical to current behavior — this is an additive
  parameter, not a behavior change for any of the 3 mandatory targets
  (none of which use `apo_chains`/`holo_chains` as of this filing).
- Planned Validation: the new regression test (synthetic, mirrors the
  real bug shape) plus a real re-run of the learnability gate on
  CARDIAC_MYOSIN's new apo/holo pair and on GLUCOKINASE, both of which
  should now produce a real (not silently-empty) correspondence.

## In Progress

None

## TODO

- [ ] Add `chain_map` param to `common_residues_by_resnum`/
      `align_apo_holo`, default `None`, backward compatible.
- [ ] Thread it through `scripts/learnability_gate.py` (and any other
      real caller found at pickup time) from `apo_chains`/`holo_chains`.
- [ ] Regression test for the remapped-chain-letter case.
- [ ] Re-run the learnability gate for CARDIAC_MYOSIN (new 8QYP/8QYR
      pair) and GLUCOKINASE (never previously run); update `RESULTS.md`
      additively, flag TASK-0120/133's CARDIAC_MYOSIN rows as
      superseded by the apo replacement, not deleted.
- [ ] Full test suite green.

## Dependency

- [[TASK-0124]] — the real case this bug was found against (CARDIAC_MYOSIN
  apo replacement); this task's own re-run target.
- [[TASK-0127]] — the `apo_chains`/`holo_chains` schema this task extends
  coverage to.
- Soft: [[TASK-0120]]/[[TASK-0133]] — CARDIAC_MYOSIN rows in their own
  `RESULTS.md` sections become stale once TASK-0124 lands and should be
  updated once this task's re-run produces new numbers.

## Open Questions

- Whether any other `align_apo_holo` caller beyond the 4 found at filing
  time (`analysis.py` only mentions it in a docstring, not a real call —
  checked directly) needs the same threading; re-check at pickup time
  since new scripts land in this repo frequently.

## Done

(not yet)
