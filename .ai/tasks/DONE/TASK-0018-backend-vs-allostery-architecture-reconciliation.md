# TASK-0018 Reconcile `backend/` (QAS) vs `__WORK_IN_PROGRESS__/src/allostery` (CCC) architecture

## Context

- ID: TASK-0018
- Title: Thorough structural/design-pattern comparison of the production
  physics code (`backend/analysis.py` et al.) against the research scaffold
  (`__WORK_IN_PROGRESS__/src/allostery/`), and a decision on what — if
  anything — should converge
- Status: Done
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

6. **Kabsch/SVD superposition is duplicated *inside* `backend/` itself,
   independent of the allostery-side question** (found 2026-07-05 while
   scoping TASK-0005): `backend/discovery.py::_kabsch` and
   `backend/analysis.py::_kabsch_rotate` are the same algorithm (SVD +
   `det(Vt.T@U.T)` reflection correction), written twice with different
   call signatures. A third, semantically different implementation
   (`backend/compare.py::align_and_compare`, Biopython `Superimposer`,
   whole-structure atom transforms for PDB-text export) is a superset
   problem, not a straight duplicate. TASK-0030 (new) deduplicates the two
   NumPy copies and is the reuse target for TASK-0005's own Kabsch step
   (port the math, don't import cross-package — same "port, don't share
   code across `backend/`↔`allostery/`" principle this task's Constraints
   section already states). This is a smaller, already-actionable instance
   of "break down the backend spaghetti" — worth treating as a proof of
   concept for whatever this task's full side-by-side turns up.

## In Progress

None

## TODO

- [x] Full side-by-side of every `backend/analysis.py` function against
      its nearest `allostery/` counterpart (or "no counterpart") — see
      Done section, evidence table.
- [x] Resolve T-018 (cutoff 7-10 Å benchmark) and T-021 (weight-scheme
      benchmark) — **not resolvable from static comparison alone**, needs
      a real benchmark run; current divergent values documented in Done
      section, benchmark execution filed as TASK-0067.
- [x] Decide, per overlap area (GNM/contact-matrix, potentials, CTQW
      Hamiltonian, morph/mode machinery): converge-on-one-implementation,
      or document-why-they-legitimately-differ — see Done section decision
      table.
- [x] If convergence is chosen anywhere, open a follow-up TASK for the
      actual refactor — TASK-0066 (shared Kirchhoff/DCC numeric helper)
      filed; no other convergence chosen (see decision table).
- [x] Add the QAS/CCC naming gloss to `.claude/TASKS.md`'s Group C header
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
- TASK-0030 (new, `backend/` Kabsch dedup) — not blocking; a small,
  concrete, already-scoped instance of evidence item 6 above. Its landed
  helper is also TASK-0005's recommended porting target.

## Open Questions

- ~~Is `backend/`'s simplified single-formula CTQW (`_ctqw_build_H`) meant
  to be replaced by the research scaffold's `build_H_new`...~~ **Answered
  below (Done, item 3).** Verdict: `_ctqw_build_H` is mathematically in the
  same family as `hamiltonians.H5_gaussian_elastic` (Gaussian-weighted
  combinatorial Laplacian) but structurally simpler than `build_H_new`
  (which additively layers four z/max-scored potential corrections on top
  of an exponential-decay Laplacian). Given the Constraints section's
  cold-start/no-heavy-deps requirement, this is judged a **deliberate live
  approximation, not an accidental duplicate** — document, don't converge
  now (see decision table).
- New, raised by the side-by-side: `_average_mixing_matrix` (closed-form
  analytic time-average) vs `propagators.time_averaged_ctqw` (numerical
  sampled time-average) compute conceptually the same quantity
  (time-averaged CTQW transition probability) by genuinely different
  methods. Nobody has checked whether they agree numerically. Not urgent —
  backend's feature works today — but if the allostery pipeline is later
  used to validate or replace backend's quantum-seed-readiness feature,
  this discrepancy should be checked first. No task filed; flagging for
  whoever picks up TASK-0008 (`allostery/analysis.py`) or a future
  Phase 2 quantum-solving task to notice.

## Done

**Decision table — one row per overlap area, converge or document:**

| Overlap area | backend/ | allostery/ | Verdict |
|---|---|---|---|
| **CTQW Hamiltonian** | `_ctqw_build_H` (analysis.py:139) — Gaussian-weighted Laplacian, `R_c=8.0, r0=7.0`, single formula | 13 named variants + `build_H_new`/`build_H10` (hamiltonians.py) | **Document, don't converge.** Same family as `H5_gaussian_elastic` (§1 below) but simpler than `build_H_new`; judged a deliberate cheap approximation for the live request path, not drift. Revisit only if/when Phase 2 quantum-solving work expands the live feature. |
| **GNM/Kirchhoff contact matrix** | `gnm_context` (analysis.py:37), binary contacts, cutoff=8.0 Å, reused at 3 call sites | `H8_gnm` (hamiltonians.py:124), binary, cutoff=7.5 Å default; `potentials.py`'s `_gnm_msf`/`V_R`/`V_C`/`V_M` callers pass cutoff=10.0 Å | **Can't converge or dismiss from static reading — needs a benchmark.** Same weighting scheme, three different cutoff numbers in active use (8.0 / 7.5 / 10.0). This *is* T-018 (still literally unresolved). Filed **TASK-0067** to actually run the cutoff-sweep benchmark against target proteins and pick one number (or document why contexts differ) — this task documents the divergence, TASK-0067 resolves it empirically. |
| **Potentials (`V_rigidity`/`V_covariance`/`V_modeparticipation` vs `V_R`/`V_C`/`V_M`)** | z-scored final outputs, positive-is-more-rigid sign convention | same core math (same 3 z-scored ingredients for rigidity; identical Kirchhoff-pseudo-inverse DCC for covariance) but max-normalized + negated final step, since these feed additively into `build_H_new` as energy-lowering diagonal terms | **Document the final-step divergence; it's a legitimate consumption-context difference** (backend needs an interpretable, comparable-across-proteins z-score for display; allostery needs a bounded, sign-consistent additive potential). **But the intermediate math (Kirchhoff pseudo-inverse, DCC, z-score helper) is identical and independently re-derived on both sides** — same pattern TASK-0030 already fixed for Kabsch. Filed **TASK-0066** to extract a shared, unit-tested "binary-Kirchhoff-context + DCC" numpy helper (ported into both trees, not cross-imported, per this task's own Constraints). Code-hygiene dedup, not a correctness fix — both sides currently produce correct, if independently-derived, results. |
| **Granularity / module count** (one 655-line `analysis.py` vs ~8 single-concern files + 11 DEV/FROZEN-pipeline-only stub files) | — | — | **Document — legitimately justified, not indicted.** `backend/` has no leakage-firewall/LOPO/ceiling/ablation/diagnostics/report machinery because it is a live interactive tool (user picks apo+holo, sees both), not a scored blind-prediction pipeline. No convergence proposed; this is the correct shape for what each tree is for. |
| **`_average_mixing_matrix` vs `propagators.time_averaged_ctqw`** | closed-form analytic degenerate-eigenspace projector | numerical sampled time-average loop | **Document as an open question, not a decision** (see Open Questions above) — same target quantity, different method, unverified agreement. No task filed; too speculative to own yet. |
| **`connectivity_change`/`morph_frames`/`site_potential_shift`/`quantum_seed_readiness`/`seed_readiness_shift`/`site_potentials`'s permutation enrichment/`_bootstrap_floor`/`_raw_shift`** | live, JSON-response-shaping + UI-animation logic | confirmed **no counterpart anywhere in allostery/** (repo-wide grep for `morph`, `DDM`, `rewire`, `keyframe`, `connectivity_change` — zero hits) | **Document — legitimately backend-only.** This is presentation/live-comparison-UI logic with no offline-research analog; nothing to converge. |
| **Kabsch/SVD superposition** | `backend/geometry.py` shared helper (`kabsch_fit`/`kabsch_apply`/`kabsch_align`), both former call sites updated, unit-tested | (separate axis — allostery's own `superpose.py` ported the math independently per this task's port-don't-import principle) | **Already resolved.** TASK-0030 confirmed Done; verified in this pass that `backend/analysis.py` and `backend/discovery.py` both import the shared helper with no residual local duplicate. No further action. |
| **Naming collision: two `analysis.py`** | `backend/analysis.py` (655 lines, live GNM+CTQW+connectivity module) | `allostery/analysis.py` (6-line stub, TASK-0008, unrelated quantum-vs-classical/ablation content) | **Document, no rename proposed** (renaming a live, deployed module is out of proportion to the footgun). Naming gloss added to `.claude/TASKS.md` Group C header (this commit) so the QAS/CCC identity is discoverable without re-deriving it. |

**Full function-by-function inventory** (backend/analysis.py's 25 top-level functions against their nearest allostery/ counterpart, or "no counterpart found") is preserved as working evidence rather than duplicated here — see the Explore-agent transcript this task's evidence was built from; the counterpart/no-counterpart call for every function is already reflected in the decision-table rows above (potentials, GNM, CTQW covered; the presentation-only functions — `site_potentials`, `_site_descriptors_z/_raw`, `quantum_seed_readiness`, `seed_readiness_shift`, `connectivity_change`, `morph_frames`, `_auto_intermediates`, `site_potential_shift`, `_bootstrap_floor`, `_raw_shift` — all confirmed "no counterpart found," rolled into the backend-only row above rather than one row each).

**T-018/T-021 status:** both remain technically open in `.claude/TASKS.md` — this task does not close them, it converts them from "vague, unlocated benchmark asks" into **TASK-0067** with the exact three candidate cutoffs (7.5 / 8.0 / 10.0 Å) and the existing 5-weight-scheme machinery (`hamiltonians.contact_matrix`) already available to run it against.

**Follow-ups filed:**
- **TASK-0066** — shared Kirchhoff-context + DCC numpy helper (dedup potentials.py `_gnm_msf`/`V_R`/`V_C`/`V_M` internals against backend's `gnm_context`/`_dcc`; TASK-0030-style port-not-import).
- **TASK-0067** — actually run the T-018 cutoff benchmark (7.5/8.0/10.0 Å) and T-021 weight-scheme benchmark against the target proteins in `config/targets.yaml`, using allostery's existing `hamiltonians.contact_matrix`/`baselines.py` machinery.

**Acceptance scenario check:** every function found in both trees under a similar name (or purpose) now has a stated verdict — same-physics-converge (none found to warrant immediate code convergence; only intermediate-math dedup, TASK-0066), or documented-legitimate-difference (CTQW, granularity, presentation-only functions), or empirical-question-deferred (GNM cutoff → TASK-0067; average-mixing-matrix methods → open question). No rewriting done in this task itself, per Out of Scope.
