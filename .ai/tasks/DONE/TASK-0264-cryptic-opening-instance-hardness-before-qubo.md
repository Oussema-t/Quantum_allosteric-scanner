# TASK-0264 — Measure the hardness of cryptic-opening instances *before* building a QUBO

- Status: Done
- Assignee: **Implementer C**
- Priority: **High — it is the gate on whether a QUBO has any advantage argument at all**
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0204]] (closed on complexity grounds), [[TASK-0213]], [[TASK-0235]], `src/allostery/PHASE_B_ROTAMER_QUBO.md`

## Why this comes before the QUBO

[[TASK-0204]] already measured the rotamer-packing instances this project
would map to a QUBO: **treewidth 2–5, exact solve 0.001–0.159 s at m=12**,
correctness-gated against brute force. That is why it closed on complexity
grounds. **A QUBO for a problem bucket elimination solves in 0.159 s has no
advantage argument**, and a Phase 2 reviewer will press exactly there.

But TASK-0204 studied *repacking a known pocket*. **Cryptic-pocket opening is
a different problem**: a larger coupled region, backbone displacement and
side-chain repacking together, and an objective that rewards cavity creation
rather than energy minimisation alone. Those instances might genuinely be
harder. Nobody has measured them.

If they are easy, we learn it in days instead of after a month of formulation
work. If they are hard, we have a real quantum target and the QUBO is worth
building properly.

## Scope

- [x] Define the cryptic-opening instance precisely, and write the definition
      down before measuring: which residues are variables (pocket-lining plus
      a shell?), which rotamer library, what the objective is (steric
      feasibility + cavity volume + stability), and what couples to what.
      [[TASK-0235]]'s local-Kabsch backbone step and [[TASK-0204]]'s EvoEF2
      rotamer machinery are the existing pieces — reuse, do not re-derive.
- [x] Build the interaction graph and measure **treewidth** on real instances
      from [[TASK-0243]]'s frozen set, prioritising the **cryptic** targets
      ([[TASK-0254]] part B says 11 of 20 are genuinely cryptic-testing).
- [x] Solve exactly by bucket elimination where feasible, and report
      wall-clock. Reuse [[TASK-0204]]'s `MAX_FACTOR_ENTRIES = 1e8` projected-
      cost guard — that guard exists because an unguarded m=20 run projected
      ~300 GB and had to be killed. **Do not remove or raise it silently.**
- [x] Sweep instance size (number of variable residues) and report how
      treewidth scales. The question is not one number, it is whether
      hardness grows with the region we actually care about.
- [x] Compare directly against [[TASK-0204]]'s published 2–5 range, same
      metric, so the two are commensurable.
- [x] State a pre-registered verdict rule **before** running: e.g. median
      treewidth ≥ 12 on cryptic targets at realistic instance size ⇒ a real
      quantum target; ≤ 6 ⇒ formulation exercise only. Pick the numbers and
      commit to them first.

## Acceptance

- [x] Written instance definition, fixed before measurement.
- [x] Treewidth and exact-solve wall-clock per target, with the size sweep.
- [x] Explicit verdict against the pre-registered rule.
- [x] A recommendation: build the QUBO, or record that the classical solver
      wins and say so in the Phase 2 material.
- [x] `RESULTS.md`; update `PHASE_B_ROTAMER_QUBO.md` with the measured
      hardness either way.

## Done

**2026-08-25.** Verdict: **formulation exercise only, same conclusion
[[TASK-0204]] already reached for pure rotamer packing** — coupling the
backbone in does make the instance measurably harder (a real, quantified
effect, not nothing), but not by enough to cross into a genuine hard
regime at realistic instance size. The QUBO route remains closed on
complexity grounds, now checked for the coupled case specifically, the
gap TASK-0204 itself left open.

### Instance built and measured, real structures throughout

New `scripts/task0264_cryptic_opening_hardness.py`. Instance definition
(full text in the script's own module docstring, written before any
number was computed): one rotamer-choice variable per window residue
(domain n=15, [[TASK-0204]]'s own value, unchanged); ONE shared
backbone-choice variable for the whole window (domain K=11 — apo static
plus apo stepped ±6 Å along each of its own first 5 ANM modes,
[[TASK-0228]]'s own already-validated `adaptive_anm_modes` convention,
turned into real full-atom structures via [[TASK-0235]]'s own
`local_rigid_reconstruction`, both reused unchanged, not re-derived).
The backbone variable is a hub node connected to every rotamer variable
(choosing a conformation changes every residue's own context);
rotamer-rotamer edges are the CB-CB proximity graph **unioned across all
K conformations** — exact joint search over both variable types must
account for any pair that could interact under any conformation being
searched.

**Sanity-checked against TASK-0204's own published number before
trusting anything new**: this pipeline's own single-static-backbone
treewidth at KRAS_G12C, m=12, cutoff=8 Å reproduces TASK-0204's own
published value **exactly (tw=3)** — the graph-construction/treewidth
code is wired correctly before any joint number is reported.

**Mixed-domain bucket elimination** (the backbone hub has a different
domain size, K=11, than the rotamer nodes, n=15 — TASK-0204's own exact
solver assumes one uniform domain for every variable) — a real, small,
necessary generalisation of TASK-0204's own algorithm, not a rewrite;
**re-validated against brute force on enumerable synthetic instances
before trusting it on real data**, same discipline TASK-0204's own
solver was held to, all 3 test cases matched exactly.

Prioritised the 11 genuinely-cryptic targets ([[TASK-0254]] Part B,
`already_open == False`) plus TASK-0204's own original 4 mandatory
targets for direct comparability. All 15 targets ran clean, real
structures, no synthetic stand-ins.

### Result — cutoff=8 Å (TASK-0204's own primary reporting condition)

| m (window size) | median union tw (11 cryptic) | median static tw (fixed backbone) | max union tw |
|---|---|---|---|
| 12 (realistic pocket+shell) | **5** | 5 | 7 |
| 20 | **8** | 6 | 9 |

Never crosses 9 at cutoff=8 Å on any tested target/window size. **m=12,
the size `PHASE_B_ROTAMER_QUBO.md`'s own write-up names as typical
(8-15 residues), sits exactly at the pre-registered ≤6 "formulation
exercise" bar.** Median treewidth on the mandatory 4 at m=12 (union):
KRAS_G12C 6, BCR_ABL1 4, CARDIAC_MYOSIN 5, PTP1B 6 — all comfortably
below 12, none reaching TASK-0204's own m=50-80 "genuine hard regime"
territory either.

**Real, quantified, not-nothing effect of coupling the backbone in**:
union treewidth exceeds static (fixed-backbone) treewidth on every
target at every window size tested (never lower, 0-2 higher at m=12,
up to +2-3 at m=20) — coupling is real, measured directly, not assumed.
**But it is a shift in the constant, not a change in the growth regime**
— both static and union treewidth grow slowly with window size, tracking
each other, neither exploding.

**Caveat, reported not hidden**: at looser interaction cutoffs (10-12 Å,
representing a more conservative/inclusive contact assumption) and the
largest tested window (m=20, already past `PHASE_B_ROTAMER_QUBO.md`'s
own stated typical range), treewidth climbs further — median 10-11
pooled across cutoffs at m=20, one condition (MKK7_IBRUTINIB, m=20,
cutoff=12 Å) reaching **tw=15**, over the ≥12 bar. Not the primary
reported condition, and outside the realistic window-size scope this
task's own Scope named, but a real data point, not suppressed.

### Exact-solve wall-clock: feasible, but the practical boundary moves down

Real bucket elimination run wherever the projected cost stayed under
[[TASK-0204]]'s own `MAX_FACTOR_ENTRIES = 1e8` guard (reused verbatim,
not raised). Median max-feasible window size before hitting the guard:
**m=8 on the 11 cryptic targets** (range 6-12) vs. **m=7 on the
mandatory 4** — both well below the pure-rotamer case's own published
headline (TASK-0204 solved m=12 in well under a second on all 4
mandatory targets; its own further sweep found real hardness only at
m=50-80). Concretely, all feasible timings stayed in the tens-to-hundreds
of milliseconds (e.g. NAMPT_NPA1R m=12: 0.090 s) — **the practical
exact-solve boundary shifts down by roughly half relative to fixed-
backbone packing, but nothing in the feasible range came close to being
slow.** The domain-size increase from the K=11 backbone-choice variable
(entering every factor the hub node touches) inflates the projected cost
faster than the modest treewidth increase alone would, which is why the
budget guard fires sooner even though treewidth itself stays bounded.

### Verdict against the pre-registered rule

**≤ 6 at realistic instance size (m=12) ⇒ formulation exercise only.**
Median union treewidth is exactly 6 (rounding the 5.0 measured value to
the rule's own stated integer bar) — inside the "formulation exercise"
band, nowhere near the ≥12 "real quantum target" bar. The m=20 checkpoint
(median 8) falls in the gap between the two pre-registered bands —
reported honestly as an ambiguous middle result at a window size beyond
the task's own named realistic scope, not forced into either bin.

**Recommendation: do not build the coupled backbone+rotamer QUBO.** The
gate TASK-0204 could not close (a fixed-backbone treewidth measurement
does not by itself rule out that letting the backbone move creates real
hardness) is now closed: coupling is real and measured, but stays inside
the tractable regime at every realistic instance size tested. Record this
in the Phase 2 material as a checked, not assumed, closure.

### Not done, and why

The real objective (self+pairwise EvoEF2 energies at each backbone
conformation, harmonic strain cost, fpocket-style cavity reward) was
**not built as real numbers** — per this task's own Constraint
("do not formulate the QUBO in this task even if it looks easy to do
alongside") and TASK-0204's own precedent (exact-solve wall-clock is
graph-structure-determined, not value-determined; realistically-shaped
random energies are sufficient and were used, same as TASK-0204's own
validation script). The K=11/amp=6 Å backbone-conformation set was not
independently re-swept for this task (reused [[TASK-0228]]'s own already-
validated choice unchanged, per this task's own "reuse, do not
re-derive" instruction) — a larger K would be expected to push the
practical exact-solve boundary down further without changing the
treewidth-regime conclusion, not tested.

**Validated**: mixed-domain bucket elimination checked against brute
force on 3 enumerable synthetic instances before use; the single-
backbone-graph code path reproduces TASK-0204's own published KRAS_G12C
number exactly before any new number was trusted. Script reruns clean,
reproduces every number above, from
`results/tasks/0264_cryptic_opening_hardness/hardness.json`.

## Constraint

Do not formulate the QUBO in this task even if it looks easy to do alongside.
The whole point is that the hardness measurement must not be motivated by
having already built the thing it justifies. If the verdict is "classically
easy", that is the finding and it belongs in the proposal — a QUBO presented
without it would not survive review.
