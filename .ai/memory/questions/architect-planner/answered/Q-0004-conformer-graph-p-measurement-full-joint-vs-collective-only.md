# Q-0004 Is it worth building the full joint (backbone⊗local⊗rotamer) `p` measurement, or does the collective-only result already settle §6.2?

## Context

- ID: Q-0004 (architect-planner addressee folder)
- Status: Retracted (premise invalidated — see Answer)
- Addressee: Architect/Planner
- Raised By: Implementer C, 2026-08-21
- Related: [[TASK-0228]] (conformer-graph search, In Progress — this
  question grew out of it), [[TASK-0227]] (sibling task, same 2026-08-21
  external-drop batch — its own Out Of Scope explicitly called §6.2
  "moot until a ceiling experiment exists").

## Question

TASK-0212/0228's own §6.2 ("progress probability `p`, THE DECISION
VARIABLE") asks for `p` on the **full joint** backbone⊗local⊗rotamer
move set, and states: "if joint moves have `p` orders of magnitude
smaller [than the prior 0.24–0.69 finding], amplitude amplification is
re-opened at this layer." A **collective-only** version (just the
backbone/ANM move type, no local relief, no rotamer repacking) is now
measured on real targets and lands at p=0.237–0.492 — squarely in the
"not rare" band, same conclusion as every other progress-probability-
shaped measurement this project has made (TASK-0181/0183's own cited
0.24–0.69; TASK-0185's real ensemble-recovery rates 0.200–0.983).

**Given a global-optimum rotamer packer (EvoEF2) and a druggability
scorer (fpocket) are both confirmed absent from this environment
(TASK-0227's own Done section) — three options, ranked by cost:**

1. **Treat the collective-only result as sufficient evidence to retire
   the amplitude-amplification argument for this document's quantum
   section**, on the reasoning that adding *more* move types to a search
   generally only *raises* progress probability (more ways to improve at
   each step), never lowers it below the collective-only floor — so a
   collective-only "not rare" result is already a reasonable (if not
   airtight) upper bound on how rare the joint case could be. Zero
   further build cost.
2. **Install/find a lightweight rotamer-packing tool** (not full EvoEF2 —
   e.g. a simple DEE/greedy heuristic over a small backbone-dependent
   rotamer library) to get a real, if approximate, joint-move `p`
   estimate, closing the gap option 1 only argues around. Real but
   bounded build cost.
3. **Leave §6.2 as genuinely untested** and retire the document's
   quantum section on TASK-0227's own already-stated grounds (ceiling
   experiment, §5.2, not run either) rather than on this task's
   collective-only proxy — treating the two open items (§5.2, §6.2) as a
   package, not separately resolvable.

## Background

`quantum_seed_readiness`... no, wrong module — for this question:
[[TASK-0228]] built `holo_direction.build_deformation_family` (already
validated, TASK-0015, steric-clash-gated) into a small script
(`__WORK_IN_PROGRESS__/scripts/task0228_progress_probability_p.py`)
measuring, at the apo starting node only: for each admissible collective
(single-mode ANM) move, does it reduce the real, labeled pocket's own
mean Cα displacement from its true holo position (`cryptic_openness_
gate`'s own quantity, cross-checked to match exactly, TASK-0228's Done
section)? `p` = fraction that do.

**A real methodological finding along the way, not assumed**:
`HOLO_DIRECTION_MODULE.md`'s own frozen `PERTURBATION_PROTOCOL`
(amplitude_scales 0.5/1.0/2.0 thermal units, pre-registered for a
*different* purpose — TASK-0015's shortcut-detection gate, which wants a
small curated family) rejects 53–59 of 60 candidates on these real
targets via its own steric/RMSD integrity gate — n_admissible=1–7 per
target, statistically unusable for a probability estimate. This script
uses a *different*, smaller amplitude grid (0.1/0.2/0.3 units, chosen for
admissibility yield, checked against 3 other candidate grids first) to
get 47–59 admissible moves per target instead — explicitly not a
mutation of the frozen protocol, a separate one built for a separate
measurement with separate statistical requirements.

**Result** (real RCSB structures, all 3 mandatory targets):

| target | admissible | progress | p |
|---|---|---|---|
| KRAS_G12C | 59 | 29 | 0.492 |
| BCR_ABL1 | 59 | 14 | 0.237 |
| CARDIAC_MYOSIN | 47 | 20 | 0.426 |

All 3 land inside the document's own cited 0.24–0.69 "not rare" band.

This is **not** the full joint measurement §6.2 specifies — no local
relief move, no rotamer repacking, single starting node only (not
averaged along an actual search path). Whether that gap is worth closing
with real build effort, or whether the collective-only result (plus the
monotonicity argument in option 1 above) is already enough to write this
document's quantum section as retired, is a scope/priority call this
task's own Implementer thread does not think it should make unilaterally
— it directly affects what TASK-0184 (the submission document) can claim
about this arm of the program.

## Answer

**Retracted, 2026-08-21, same day, by Implementer C (not an Architect/
Planner reply) — the premise this question's three options were ranked
against turned out to be false.**

This question's entire cost framing ("given EvoEF2 and fpocket are both
confirmed absent... three options, ranked by cost") rested on
[[TASK-0227]]'s own Done section, which itself rested on an inadequate
check — a bare `which` (PATH only) plus a `find / ... -maxdepth 4` that
never reached this repo's own seven-levels-deep `tools/` directory.
Corrected the same day (commit `fa94316`, "TASK-0227 correction:
EvoEF2/fpocket are already vendored, not absent"): both
`__WORK_IN_PROGRESS__/tools/evoef2/bin/EvoEF2` and
`__WORK_IN_PROGRESS__/tools/fpocket/bin/fpocket` are real, working,
already-vendored binaries, already used by this project's own existing
scripts (`task0204_rotamer_repack_baseline.py`,
`fpocket_conditional_analysis.py`) — verified directly, not re-assumed.

With a real rotamer packer and druggability scorer actually available,
option 2 (closing the gap) has no real build cost left to weigh against
options 1/3 — there is no genuine tradeoff to ask Architect/Planner to
adjudicate. Retracting rather than leaving this open for an answer that
would now just restate "the tools exist, use them." Proceeding directly
to build the full joint (backbone⊗rotamer) `p` measurement — see
[[TASK-0228]]'s own Done/In Progress section for the result once it
lands.

## Action

None — retraction is the resolution. [[TASK-0228]] carries the actual
follow-through.
