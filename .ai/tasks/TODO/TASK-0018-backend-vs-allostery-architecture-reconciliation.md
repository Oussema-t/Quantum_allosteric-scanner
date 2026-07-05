# TASK-0018 Reconcile `backend/` (QAS) vs `__WORK_IN_PROGRESS__/src/allostery` (CCC) architecture

## Context

- ID: TASK-0018
- Title: Thorough structural/design-pattern comparison of the production
  physics code (`backend/analysis.py` et al.) against the research scaffold
  (`__WORK_IN_PROGRESS__/src/allostery/`), and a decision on what — if
  anything — should converge
- Status: TODO
- Owner: Architect/Planner
- Source: user request, 2026-07-04 session — "my feeling is that they have
  a different granularity and different design patterns... no thorough
  analysis yet." A quick (not thorough) check below confirms the feeling
  and surfaces evidence sharper than a feeling.
- Crit Ref: wraps `.claude/TASKS.md` **T-018** (benchmark GNM contact
  cutoff 7-10 Å) and **T-021** (benchmark the five contact-weighting
  schemes) — both still `TODO` in the closed ledger. Per the Task Ledger
  Boundary (`.ai/COMMON.md`, decided in TASK-0002): resuming a TODO row
  there means wrapping it in a `TASK-XXXX` that links back, not adding a
  new `T-NNN`. This task is that wrapper, plus broader structural scope
  T-018/T-021 don't cover.
- Scope: `backend/analysis.py`, `backend/systems.py` (cross-link
  TASK-0003), `backend/data_layer.py`, `backend/compare.py` vs
  `__WORK_IN_PROGRESS__/src/allostery/hamiltonians.py`, `potentials.py`,
  `propagators.py`, `metrics.py`, `data.py`, `clean.py`

## Intent Contract

- Outcome: a recorded decision — for each area of overlap, is the
  duplication intentional (production service vs offline research library,
  legitimately different constraints) or accidental drift that should
  converge on one implementation? Right now nobody has stated either.
- In Scope: the quick-check evidence below, expanded into a full
  side-by-side; a decision per overlap area; if convergence is chosen,
  a follow-up TASK for the actual code change (this task decides, doesn't
  necessarily execute).
- Out Of Scope: rewriting either codebase before the decision is recorded.
- Acceptance Scenarios:
  - Given any function that exists in both trees under a similar name,
    when compared, then this task states whether they're meant to be the
    same physics (and should converge) or different physics (documented
    why).
- Constraints And Invariants:
  - `backend/` is a live, deployed FastAPI service (Render, cold-start
    constraints, no heavy optional deps like fpocket/PocketMiner clients)
    — any convergence proposal must respect that it cannot inherit the
    research scaffold's leakage-firewall machinery or its heavier
    dependency footprint (TASK-0011's baselines.py external-server clients,
    for instance, have no business in the request path of a live app).
  - CLAUDE.md convention 4 applies: "ADD-only API changes where possible;
    don't break existing response shapes" — any convergence touching
    `backend/analysis.py` must not change what the frontend receives.
- Planned Validation: this task's output is a decision document (in its
  own Done section), not code — validation is "does every overlap area
  have a stated, justified decision," not a test suite.

## Quick-check evidence (not thorough — the actual analysis is this task's job)

Confirmed by direct comparison, not just a feeling:

1. **Naming collision, different content.** Both trees have an
   `analysis.py`. `backend/analysis.py` (655 lines) is the app's live GNM +
   quantum-seed-readiness + connectivity-change module.
   `__WORK_IN_PROGRESS__/src/allostery/analysis.py` (6-line stub, see
   TASK-0008) will hold quantum-vs-classical/ablation/dephasing-sweep
   analysis ported from the notebook. Same filename, unrelated content —
   a real footgun for anyone grepping "analysis.py" repo-wide, or for an
   agent asked to "fix analysis.py" without a fully-qualified path.

2. **The `.claude/TASKS.md` "QAS"/"CCC" naming is now resolved.** Group C's
   criticism (`CRIT-003`) compares "CCC's potential functions" against "the
   QAS reference implementation" without ever stating which files those
   are. Direct comparison confirms: **QAS = `backend/analysis.py`**,
   **CCC = `__WORK_IN_PROGRESS__/src/allostery/potentials.py`**. E.g.
   `backend/analysis.py::V_rigidity` already computes
   `z(degree) + z(clustering) - z(msf)` and `V_covariance` already computes
   the GNM-pseudo-inverse DCC — exactly the formulas T-019/T-020 (both
   DONE) ported *into* `potentials.py` to match. Record this naming
   resolution somewhere durable (this task's Done section, and/or a
   one-line gloss added to `.claude/TASKS.md`'s Group C header) so the
   next reader doesn't have to re-derive it.

3. **Independent CTQW Hamiltonian constructions.** `backend/analysis.py`
   has its own `_ctqw_build_H` (§5f: Gaussian-weighted graph Laplacian,
   `R_c=8.0, r0=7.0`, one formula, no variants) already live behind the
   "quantum-seed readiness" feature. `hamiltonians.py` in the research
   scaffold has thirteen named Hamiltonian variants (`H1`...`H13`) plus
   `build_H_new`/`build_H10`, all ported/portable from the notebook. These
   are not the same code path — worth deciding whether `backend`'s
   simplified builder is a deliberately cheap approximation for a live
   demo feature (plausible — README says full quantum-walk ranking "will
   be reintroduced on top of this data foundation," implying it isn't
   there yet) or a duplicate that should eventually call into
   `hamiltonians.build_H_new` once that's stable.

4. **Granularity is a real, not superficial, difference.**
   `backend/analysis.py` is one file mixing data-shaping-for-JSON-response
   concerns with physics; `__WORK_IN_PROGRESS__/src/allostery/` splits the
   same physics into ~8 single-concern files (`hamiltonians.py`,
   `potentials.py`, `propagators.py`, `metrics.py`, `clean.py`, `data.py`)
   plus 11 stub files for concerns `backend/` has no equivalent of at all:
   DEV/FROZEN leakage firewall, LOPO, unsupervised selection, ceiling,
   ablation, diagnostics, report generation. `backend/` has no notion of
   train/test leakage because it's a live interactive tool (the user picks
   apo+holo and sees both), not a scored blind-prediction pipeline — this
   may fully justify the granularity gap rather than indict it, but that
   justification has never been written down.

5. **`systems.py` duplication is one instance of this same pattern**,
   already flagged in TASK-0003 (`backend/systems.py` vs
   `SYSTEMS_allosteric_corrected_v2.md`) — cross-link rather than
   re-litigate; TASK-0003 owns the targets-config side of this, this task
   owns the physics-code side.

## In Progress

None

## TODO

- [ ] Full side-by-side of every `backend/analysis.py` function against
      its nearest `allostery/` counterpart (or "no counterpart" — note
      those too, e.g. `connectivity_change`/`morph_frames` may have no
      research-scaffold equivalent at all and that might be fine, `backend`
      -only presentation logic).
- [ ] Resolve T-018 (cutoff 7-10 Å benchmark) and T-021 (weight-scheme
      benchmark) as part of this reconciliation, using both `backend`'s
      already-deployed choices and the research scaffold's benchmarks as
      cross-checks against each other, not just against B-factors in
      isolation.
- [ ] Decide, per overlap area (GNM/contact-matrix, potentials, CTQW
      Hamiltonian, morph/mode machinery): converge-on-one-implementation,
      or document-why-they-legitimately-differ.
- [ ] If convergence is chosen anywhere, open a follow-up TASK for the
      actual refactor — this task records the decision, a separate one
      executes it (keeps this task reviewable as a decision doc).
- [ ] Add the QAS/CCC naming gloss to `.claude/TASKS.md`'s Group C header
      (small, additive edit — doesn't violate the ledger being "closed to
      new entries," it's a clarifying note on existing entries).
- [x] Cross-check whether `backend/analysis.py`'s live
      `quantum_seed_readiness`/`_ctqw_build_H` means the README's "quantum
      prediction... not built yet" framing is now slightly stale (a partial
      quantum-walk-flavored feature *is* live) — if so, flag for a doc fix,
      don't silently rewrite the README from this task. **Confirmed
      independently by TASK-0020** (Product intent/feature inventory audit,
      2026-07-04, cross-linking thread — not a claim on this task): see
      [`.ai/reviews/PRODUCT_INTENT_MAP.md`](../../reviews/PRODUCT_INTENT_MAP.md)
      §1 (`connectivity-change` row) and §3 item 2. That audit reached the
      same conclusion from the Product-intent side (is this feature's
      purpose stated anywhere?) rather than the architecture side (does it
      duplicate `hamiltonians.py`?) — two independent routes to the same
      finding. TASK-0020 flags the doc-staleness as a still-open item; it
      did not fix `ARCHITECTURE.md`/`SOFTWARE.md`/`CLAUDE.md`'s "not built
      yet" wording itself, so that edit is still this task's (or a
      follow-up's) to make. Cross-links added: `ARCHITECTURE.md` new §5b,
      one line before `SOFTWARE.md` §4.

## Dependency

- TASK-0003 (`targets.yaml` reconciliation) — same QAS-vs-CCC duplication
  pattern, different artifact (config data vs physics code); read together.
- TASK-0008 (`analysis.py` in allostery) — whoever implements that stub
  should read this task's side-by-side first so the two `analysis.py`
  files' relationship (if any) is a decision, not an accident.
- Wraps `.claude/TASKS.md` T-018, T-021 (see Crit Ref above).
- TASK-0020 (Product intent/feature inventory, done) — not a blocking
  dependency, but its output
  ([`.ai/reviews/PRODUCT_INTENT_MAP.md`](../../reviews/PRODUCT_INTENT_MAP.md))
  independently confirms this task's quantum-seed-readiness staleness
  finding (see TODO above) and is worth reading alongside this task's own
  side-by-side once that's written.

## Open Questions

- Is `backend/`'s simplified single-formula CTQW (`_ctqw_build_H`) meant
  to be replaced by the research scaffold's `build_H_new` once TASK-0004
  through TASK-0008 land, or does the live app deliberately want a cheaper,
  single-formula version regardless of what the research pipeline settles
  on (Render free-tier latency/cold-start constraints)? This is the crux
  decision the whole task hinges on — recommend answering it first, before
  the full function-by-function side-by-side, since it determines whether
  most of the rest of this task is "converge" or "document the split."

## Done

(not yet)
