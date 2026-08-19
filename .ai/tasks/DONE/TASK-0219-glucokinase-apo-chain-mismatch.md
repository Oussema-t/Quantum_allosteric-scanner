# TASK-0219 `backend/systems.py`'s GLUCOKINASE `chain="X"` is wrong for the apo structure

## Context

- ID: TASK-0219
- Title: GLUCOKINASE's single `chain` field in `backend/systems.py` is set
  to `"X"`, but the configured apo PDB (1V4S) only has chain A —
  `data_layer.load_structure("1V4S", "X")` returns `None`, so the live
  backend cannot currently score this target's apo structure at all.
- Status: Done
- Resolution: done
- Resolution Note: GLUCOKINASE apo/holo chain-letter mismatch fixed via apo_chain/holo_chain per-role override (reused TASK-0127's targets.yaml pattern). Audited all 6 SYSTEMS targets live -- GLUCOKINASE is the only mismatch. 5 new regression tests, all backend tests pass (36/36).
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

- [x] Audit all `SYSTEMS` targets for apo/holo chain-letter mismatches
      (not just GLUCOKINASE).
- [x] Add per-role chain override to `systems.py`'s schema (reuse the
      `targets.yaml` `apo_chains`/`holo_chains` pattern).
- [x] Update `backend/` call sites that read `["chain"]`.
- [x] Fix GLUCOKINASE's entry specifically (apo→A, holo→X).
- [x] Add regression test(s).
- [x] Re-run `backend/` test suite; confirm no regression.

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

**Fix landed, reusing the precedent exactly as instructed. Audit confirmed
GLUCOKINASE is the only apo/holo chain-letter mismatch among all 6
`SYSTEMS` targets — verified live, not assumed.**

**Audit (In Scope item 1)**: fetched every target's apo/holo structures
live via `backend/rcsb.chain_summary` and compared against the configured
chain. Results (`apo_ok`/`holo_ok`, first-letter of `chain` present in the
structure's actual chains):

| Target | apo chains found | holo chains found | mismatch? |
|---|---|---|---|
| KRAS_G12C | A, B | A | no |
| BCR_ABL1 | A, B | A | no |
| CARDIAC_MYOSIN | A–F | A,B,C,D,E,P,R | no |
| MYC_MAX | A,B,D,E,F,G,H,J | (no holo) | no (verified=False, notes' "A,D" is a separate multi-chain-selection recommendation, not an apo/holo role mismatch — left alone, out of scope per this task's own "chain-letter correctness only") |
| PTP1B | A | A | no |
| **GLUCOKINASE** | **A** | **X** | **yes — configured `chain="X"` fails apo, matches holo only** |

Confirms the task's own prediction ("very plausibly the only live
instance... but that should be verified, not assumed").

**Schema fix (In Scope item 2)**: `backend/systems.py` gains optional
`apo_chain`/`holo_chain` per-target override fields, reusing
`__WORK_IN_PROGRESS__/config/targets.yaml`'s already-proven
`apo_chains`/`holo_chains`-with-shared-fallback pattern (TASK-0127) —
same design, not re-derived. `resolve_systems()` now computes
`c["apo_chain"] = c.get("apo_chain", c.get("chain"))` and
`c["holo_chain"] = c.get("holo_chain", c.get("chain"))` for every target,
so any target that only ever set `chain` resolves identically to before
(verified directly: `TestPerRoleChainFallback` asserts this for all 5
other targets). The pre-existing `holo_validation_chain` override (used
by CARDIAC_MYOSIN) was also corrected to only affect `holo_chain`, not
the shared `chain` field it was silently clobbering before (harmless
today since both values happen to be `"B"`, but the same latent bug class
this task fixes — recorded, not left as a second silent trap).

**GLUCOKINASE entry**: `chain="X"` kept unchanged (back-compat), `apo_chain="A"`
added.

**Call sites updated (In Scope item 3)**, found via `grep -rn
'\["chain"\]\|\.get("chain"' backend/`, each checked for which role it
actually needs:
- `backend/pipeline.py:85` (`build_view`'s holo-chain resolution for
  `complete_apo`) — was `cfg.get("chain")`, now `cfg.get("holo_chain")`.
- `backend/discovery.py:142` (`find_holo_candidates`'s `benchmark_holo`
  dict, describes the *holo* structure) — was `cfg.get("chain")`, now
  `cfg.get("holo_chain")`.
- `backend/main.py:108` (`/api/targets` response) — kept `"chain"`
  unchanged (back-compat), ADDED `"apo_chain"`/`"holo_chain"` fields.
- `frontend/app.js:60` (`onTargetChange`, prefills the apo-load "chains"
  input from `/api/targets`' response — this is the actual live failure
  path: GLUCOKINASE's old `chain="X"` was prefilled as the *apo* chain) —
  now prefers `t.apo_chain`, falling back to `t.chain` then `"A"`.
- `backend/rcsb_extract.py:294-295` and `backend/rcsb.py`'s internal
  `d["chain"]` uses — checked, confirmed unrelated (a `__main__` demo
  dict and PDB-structure-discovery chain data, neither reads `SYSTEMS`).
- `backend/test_analysis_characterization.py` — checked, only exercises
  KRAS_G12C (single-chain, unaffected); left unchanged, not in scope to
  touch a passing characterization test for an untouched target.

**Regression tests (In Scope item 4)**: new `backend/test_systems.py`, 5
tests, all against real fetched RCSB data (not mocked), matching this
task's own Planned Validation ("fetch both apo and holo PDBs live"):
`TestPerRoleChainFallback` (every other target's `apo_chain`/`holo_chain`
resolve identically to before; GLUCOKINASE's override + unchanged
`holo_chain`/`chain`), `TestGlucokinaseApoLoadLive` (the exact live
reproduction from this task's Source — `apo_chain` loads successfully;
the old shared `chain` field alone still fails, documented so a future
"simplification" can't quietly re-break this), `TestNoOtherRoleMismatch`
(the full audit table above, as an executable assertion against live
data, so a future target addition with the same mismatch fails CI
instead of shipping silently).

**Validated**: `python3 -m pytest backend/ -q` → 36 passed, 0 skipped
(all live network fetches succeeded this run), no regressions.
`/api/targets`'s actual response logic verified directly against
`resolve_systems()`'s output (the substantive logic — the FastAPI layer
itself couldn't be exercised end-to-end: `fastapi`/`uvicorn` are not
installed in the local `.venv`, a pre-existing environment gap unrelated
to this change, not fixed here).

No behavior change for any target other than GLUCOKINASE and (silently,
harmlessly) CARDIAC_MYOSIN's now-more-correct `holo_validation_chain`
scoping — verified via `TestPerRoleChainFallback`. ADD-only per
Constraints: no existing field removed or repurposed, `chain` kept as
back-compat default throughout.
