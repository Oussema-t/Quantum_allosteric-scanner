# REVIEW 2026-07-23 — register-hygiene audit + HYP-P12 gate correction

Cross-model audit pass (external reviewer via GitHub connector, read-only
over the `bartosz` branch). Scope note up front, per this project's own
cross-model-check discipline: this reviewer read the register, tasks,
reviews, and `config/targets.yaml`, and reasoned over them. It did **not**
execute the pipeline, run pytest, or re-fetch RCSB (no sandbox). So the
numeric findings below are documentation/algebra audits, not re-computed
results. Treat as corroboration and error-flagging, not independent
numerical reproduction.

## 1. One real mathematical error — HYP-P12 validity gate is wrong

HYP-P12 (topological void / persistent H2, gating TASK-0142) specifies a
validity check of the form `b1(ker L1) == E - N + C`.

That identity is the cycle rank of a **graph** (first Betti number of a
1-complex), and it holds only when there are **no 2-simplices**
(`d2 == 0`). But P12 requires persistent **H2**, which by definition
needs a complex with triangles and tetrahedra. On a correctly built
Vietoris-Rips / alpha complex,

  dim ker L1 = (E - N + C) - rank(d2),

which is **strictly less** than `E - N + C` whenever any triangle is
present. So the gate as written **fails on a correct complex** and
**passes only if 2-simplices are omitted** — in which case H2 is
identically zero and the hypothesis is untestable by construction.

Action: correct the gate to `dim ker L1 == (E - N + C) - rank(d2)`
(or drop the graph-cycle check entirely and validate H2 directly via
persistence), BEFORE any implementer picks up TASK-0142. Otherwise an
implementer builds the wrong complex to satisfy a wrong gate.

## 2. Confirms (does NOT duplicate) the 2026-07-22 Method-B finding

The 2026-07-22 review (`suggestions.txt` + `persistent_voids.py`) already
established, by *executed* synthetic test, that persistent H2 detects a
cavity whose lining residues are graph-adjacent (mean hop 1.44) — so the
openness-premise 0/7 failure (TASK-0143) did NOT correctly kill the
topological family; it falsified a graph-distance signature H2 never
depended on. This reviewer independently reached the same conclusion from
the algebra (item 1 is *why* a graph-cycle gate is the wrong test for an
H2 object). These are complementary: the 22nd's review shows the family
should not be gated; this note shows the specific validity formula in
HYP-P12 is also algebraically wrong. Both belong in the write-up's
"benchmark/methodology integrity" section.

## 3. Register-hygiene items (documentation drift, cheap to fix)

These are propagation lags between Done tasks and the register, each
found by reading, not running:

- **HYP-P11 status block.** TASK-0141 landed a clean NEGATIVE (ENAQT
  enhances transport 1.24-1.70x but degrades discrimination; no gamma
  clears the floor on any of the 3 mandatory targets). Confirm the
  physics-hypothesis register carries a dated status line for P11 the way
  P5/P6/P8/P9/P10 do — a reader should not conclude ENAQT is untested.
  (Note: this is the collaborator's own "Idea #1", filed as HYP-P11 and
  properly killed — worth recording as such.)

- **HYP-P8 / cardiac myosin.** If P8 still reads "blocked on TASK-0144",
  update it: TASK-0144 is Done and already produced the number
  (CARDIAC_MYOSIN 8QYP/8QYR resolves ~698/704, LEARNABLE; GLUCOKINASE
  ~446/448, UNLEARNABLE_FROM_APO — the project's first clean
  UNLEARNABLE_FROM_APO, worth surfacing).

- **HYP-P5 / H13 win on retired data.** H13-native's only positive
  (cardiac myosin, ~0.8513 vs H_new ~0.8297) was computed on 5TBY, which
  TASK-0124 retired (myosin collapsed 0.79->0.52 on 8QYP). Re-run the
  H13 comparison (TASK-0126 machinery) on 8QYP. If the win evaporates,
  P5 becomes a clean negative — a *better* write-up story than a messy
  target-dependent one.

- **HYP-P9 wording.** The sentence "an arbitrary initial phase on a
  real-symmetric H only reshuffles amplitudes" is imprecise and quotable
  by a referee. Relative phases across a multi-site initial state DO
  change finite-t dynamics; an initial state is not a gauge
  transformation. Correct framing: no physical principle FIXES those
  phases (so it is an arbitrary, label-leaking knob — which is exactly
  why the chiral flux is the justified substitute), and the CONVERGED
  limit is phase-free. Same conclusion, defensible reasoning.

## 4. New tasks filed alongside this review (this session)

- **TASK-0153** — control-effort scanning (the collaborator's phase-
  control hypothesis, reformulated to control-as-ruler; well-posed,
  non-circular, pre-registered distance kill-switch).
- **TASK-0154** — two-boson HOM interference (the one non-reducible
  multi-walker residual; fermion/co-occupation/anyon variants explicitly
  marked dead so none get re-run).
- **TASK-0155** — apo-structure sensitivity sweep (the missing robustness
  axis; stress-tests KRAS's marginal surviving result across many apo
  structures).

## 5. Physical-status caveat worth carrying into the six pages

Independent of the register, one framing point a physics referee will
test: allosteric signal propagation is a **classical** (micro-to-
millisecond, conformational-ensemble) process; electronic coherence in a
protein at physiological temperature decoheres on a ~femtosecond scale
(Duan et al. 2017, *PNAS* 114, 8493, on FMO — verify before quoting), a
gap of ~10 orders of magnitude. The project's CTQW is therefore a
**quantum-inspired graph algorithm applied to a classical problem**, not
a claim that biology is quantum — which is exactly what the challenge
asks ("can quantum information propagation identify pathways more
accurately/efficiently than classical diffusive models" — an algorithmic
claim). State this explicitly; do not let "biological signal is quantum"
stand anywhere, or the femtosecond number closes it instantly. This is
consistent with the register's own converged-limit-is-classical finding
and makes the honest version the strong one.
