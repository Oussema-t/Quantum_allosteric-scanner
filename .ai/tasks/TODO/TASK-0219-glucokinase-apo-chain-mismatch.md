# TASK-0219 `backend/systems.py`'s GLUCOKINASE `chain="X"` is wrong for the apo structure

## Context

- ID: TASK-0219
- Title: GLUCOKINASE's single `chain` field in `backend/systems.py` is set
  to `"X"`, but the configured apo PDB (1V4S) only has chain A —
  `data_layer.load_structure("1V4S", "X")` returns `None`, so the live
  backend cannot currently score this target's apo structure at all.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: found incidentally while validating [[TASK-0033]] (verified
  directly: `1V4S.pdb`'s `ATOM` records only ever have chain id `A`;
  `load_structure(d["apo"], d["chain"])` returns `None` with the
  configured `chain="X"`, and succeeds with `chain="A"`), 2026-08-16.
- Priority: **P1** — this isn't a latent/theoretical bug, it's a live
  failure: any code path in `backend/` that calls
  `data_layer.load_structure("1V4S", "X")` (the exact call
  `systems.py`'s own config produces for GLUCOKINASE's apo role) gets
  `None` back today, on the currently-shipped config.

## Why this matters, and the precedent that already fixed it once

`__WORK_IN_PROGRESS__/src/allostery/clean.py::clean_from_config` hit and
fixed the *identical* mismatch (TASK-0127, that tree's own task history):
GLUCOKINASE's apo (1V4S) uses chain A, its holo (3H1V) uses chain X — two
individually-correct source documents, for two different structures, that
happen to disagree on which letter maps to the same biological chain.
That fix added a `{role}_chains` override (`apo_chains`/`holo_chains`)
falling back to a shared `chains` field, so both roles could be served
correctly without a schema break.

`backend/systems.py` still has only the single, pre-fix `chain` field
model — it was apparently never ported. `SYSTEMS["GLUCOKINASE"]["chain"]`
is `"X"`, which is holo-correct and apo-wrong. Every other verified
target in `systems.py` uses one chain letter for both roles (confirmed by
inspection while filing this task — not assumed), so this is very
plausibly the *only* live instance of the bug in this backend today, but
that should be verified, not assumed, as part of the fix (see Intent
Contract).

## Intent Contract

- Outcome: `backend/systems.py` correctly loads GLUCOKINASE's apo (1V4S,
  chain A) and holo (3H1V, chain X) structures, and any other target
  found to have the same per-role mismatch is fixed the same way — no
  target's apo or holo load silently fails due to a wrong chain letter.
- Why required, not assumed: confirmed directly, not inferred —
  `data_layer.load_structure("1V4S", "X")` returns `None` on real,
  fetched RCSB data (see Source above).
- In Scope:
  - Audit every `verified=True` (and, time permitting, `verified=False`)
    target in `SYSTEMS` for the same apo/holo chain-letter mismatch —
    fetch both PDBs, check which chains actually exist, compare against
    the configured `chain` field for both roles it's used for. Don't
    assume GLUCOKINASE is the only instance.
  - Fix `systems.py`'s schema to support a per-role override, mirroring
    `__WORK_IN_PROGRESS__/config/targets.yaml`'s already-proven
    `apo_chains`/`holo_chains`-with-shared-`chains`-fallback pattern
    (TASK-0127) — reuse that design, don't re-derive a new one.
  - Update every call site that currently reads `SYSTEMS[name]["chain"]`
    assuming a single value for both roles (`grep` for `["chain"]`/
    `.get("chain"` across `backend/` before assuming there's only one).
  - Add a regression test (real or fixture-backed) pinning that
    GLUCOKINASE's apo load succeeds and returns the expected chain.
- Out Of Scope:
  - Any change to `__WORK_IN_PROGRESS__/config/targets.yaml` or its own
    `clean.py` — that tree already has this fixed; this task is the live
    backend's own catch-up, not a re-verification of the research tree.
  - Any non-chain data-quality issue in `systems.py` (e.g. G12C/wild-type
    apo mismatches already tracked elsewhere in that file's own
    comments) — chain-letter correctness only.
- Constraints And Invariants: CLAUDE.md convention 4 — ADD-only where
  possible; existing single-`chain`-field targets must keep working
  unchanged (mirrors TASK-0127's own "every pre-existing target config...
  completely unaffected" constraint).
- Planned Validation: for every target touched, fetch both apo and holo
  PDBs live and confirm the resolved chain actually exists in each
  structure before/after the fix — not just that the code runs without
  raising.

## TODO

- [ ] Audit all `SYSTEMS` targets for apo/holo chain-letter mismatches
      (not just GLUCOKINASE).
- [ ] Add per-role chain override to `systems.py`'s schema (reuse the
      `targets.yaml` `apo_chains`/`holo_chains` pattern).
- [ ] Update `backend/` call sites that read `["chain"]`.
- [ ] Fix GLUCOKINASE's entry specifically (apo→A, holo→X).
- [ ] Add regression test(s).
- [ ] Re-run `backend/` test suite; confirm no regression.

## Dependency

- [[TASK-0033]] — this is where the bug was found (incidental, not that
  task's own scope).
- Reference precedent (different tree, don't touch): `__WORK_IN_PROGRESS__/
  src/allostery/clean.py::clean_from_config`'s `{role}_chains` pattern.

## Open Questions

- Is there a reason `backend/systems.py` and
  `__WORK_IN_PROGRESS__/config/targets.yaml` maintain two independent
  copies of per-target metadata at all (same question TASK-0018 raised
  for the module architecture generally)? Out of scope to resolve here,
  but worth flagging if it comes up again — this is now at least the
  second time a fix landed in one tree and not the other for the same
  underlying fact (GLUCOKINASE's chains).

## Done

(not yet)
