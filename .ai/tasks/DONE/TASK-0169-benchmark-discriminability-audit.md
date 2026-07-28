# TASK-0169 Benchmark discriminability audit — can the mandatory target set certify *any* method?

## Context

- ID: TASK-0169
- **Renumbered 2026-07-28 (Architect/Planner)**: filed as TASK-0172 by
  `REVIEW-panel-2026-07-28-external.md`; see [[TASK-0167]]'s own provenance
  note for the full explanation. No content changed.
- Title: apply [[TASK-0167]]'s LOD, plus the project's already-established
  benchmark-integrity findings, to the challenge's own mandatory target set,
  and answer directly: **is this benchmark capable of distinguishing a working
  allosteric-site predictor from a broken one?**
- Status: Done
- Owner: Architect/Planner (analysis + writing; little new computation)
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-28 18:45
- Source: `REVIEW-panel-2026-07-28-external.md` §6 finding 4 and §7 item 3 —
  *"your most valuable and least-promoted finding."*
- Priority: **P1 — mostly synthesis of results already in hand (~1 day). This
  is the reframe that makes the submission a contribution rather than a
  report of failure.**
- Dependency: soft on [[TASK-0167.002]] (the LOD strengthens it but the audit
  stands without it).

## Why this matters — this is the paper's thesis

The project's current narrative is *"we could not find quantum advantage for
allosteric site prediction, and we built a rigorous apparatus that proves we
could not."* That is honest and defensible. It is also, as a contribution,
modest — a negative result about one team's approach.

The stronger claim is available and already evidenced across `RESULTS.md`,
currently scattered across a YAML comment, several open-questions rows, and
individual task Done sections:

> **The mandatory benchmark cannot currently certify a working method, and we
> can demonstrate that with our own apparatus.**

The evidence is already collected:

| Target | Established defect | Source |
|---|---|---|
| CARDIAC_MYOSIN | Challenge Table 1's validation structure **6C1H does not contain mavacamten** — the ground truth for the "mechanical site where mavacamten stabilizes the super-relaxed state" is not in the named structure | `targets.yaml` comment, flagged for promotion by `REVIEW-panel-2026-07-16-v2` |
| CARDIAC_MYOSIN | Challenge-specified apo **5TBY is a 20 Å docked homology model** with non-crystallographic B-factors; replacing it with a real X-ray structure (8QYP) erased the target's only positive result (0.79 → 0.52) | [[TASK-0124]] |
| KRAS_G12C | Switch-II pocket **overlaps the active site**, so a "distal" prediction task is partly a self-hit task; the proximity floor scores 0.798 unaided | [[TASK-0094]], `REVIEW-panel-2026-07-16-v2` |
| BCR_ABL1 | Myristoyl pocket is **pre-formed in the apo structure** — it is not cryptic, so the "blind-predict the cryptic pocket" framing does not apply | [[TASK-0104]] |
| All 3 | **fpocket, a 2009 classical geometric tool, beats every quantum-flavoured observable in this register on 2/3 targets** (0.835 / 0.860 vs floor 0.482 / 0.582) | [[TASK-0163]] |
| ASD extension | Generalization pool **fully exhausted** — 0 of 6 remaining draft configs are resolvable | [[TASK-0164]] |

The fpocket row is the sharpest. A purely geometric pocket detector with no
dynamics, no allostery model, and no quantum content wins decisively. Two
readings, and the benchmark cannot distinguish them: either (a) allosteric
pocket prediction on these targets is a **geometry** problem that dynamics
adds nothing to, or (b) the labels are drug-contact sets that geometry
trivially recovers, and the benchmark never tested allostery at all.

## Intent Contract

- Outcome: a single dated `RESULTS.md` section + a competence-map row
  consolidating every benchmark-integrity finding into one explicit verdict
  per mandatory target, plus a stated specification of what a benchmark that
  *could* certify an allosteric method would require.
- Why required, not assumed: these findings exist but are distributed across
  a YAML comment, 6 open-questions rows, and 5 task Done sections — no single
  artifact states the aggregate claim, and a referee will not assemble it.

- In Scope:
  - **Consolidate** the table above with direct citations, each independently
    re-verified against RCSB before publication (the 6C1H/mavacamten claim in
    particular is the load-bearing one and must be checked directly, not
    relayed — it is also the single most quotable finding in the submission).
  - **Per-target discriminability verdict** on three axes, stated plainly:
    1. *Is the ground truth valid?* (structure contains the ligand; label is
       the allosteric site, not a drug-contact proxy)
    2. *Is the task the stated task?* (pocket genuinely distal; genuinely
       cryptic in apo)
    3. *Is the task non-trivial?* (does a geometric/proximity baseline
       already solve it — [[TASK-0163]]'s fpocket numbers)
  - **If [[TASK-0167.002]] has landed:** add axis 4 — *is the task within our
    detection range?* For any target where the LOD exceeds plausible physical
    coupling, the negative result is uninformative about that target and this
    must be said.
  - **Specification of a certifying benchmark** — the constructive half, and
    the part that makes this a contribution rather than a complaint. At
    minimum: holo structures verified to contain the named ligand; pockets
    verified distal *and* verified absent in apo (a cryptic-pocket criterion,
    not a drug-contact criterion); a stated geometric-baseline floor per
    target; ≥1 target with mechanism-validated (not drug-derived) ground
    truth (see [[TASK-0170]]); and a published detection-limit for the
    scoring protocol.

- Out Of Scope:
  - New scored cells or observables.
  - Any suggestion that the challenge organizers erred. **Frame as
    measurement, not criticism** — these are structural properties of a
    benchmark assembled from available PDB entries, and identifying them is
    the useful output. The tone matters for how it is received.
  - Withdrawing the required deliverables. All three mandatory targets are
    still reported per §5 of the challenge statement; this is context
    alongside them, not a substitute.

- Constraints And Invariants:
  - Every claim independently re-verified against RCSB before publication.
    [[TASK-0132]] found a wrong author list in a filing task's own citation;
    [[TASK-0125]] found a resnum concern that turned out to be a non-issue.
    Verify, then publish.
  - No claim that the benchmark is "wrong" — the claim is that it is *not
    discriminating for the stated task*, which is a narrower, defensible, and
    fully evidenced statement.

- Planned Validation: each row must be traceable to a re-verified primary
  source (RCSB entry, or a named task's executed run). A row that cannot be
  re-verified is dropped, not softened.

## In Progress

None

## TODO

- [x] Re-verify 6C1H ligand content directly on RCSB (**load-bearing**).
- [x] Re-verify 5TBY method/resolution and the 8QYP replacement.
- [x] Re-verify KRAS Switch-II / active-site residue overlap from the labels.
- [x] Re-verify BCR-ABL1 myristoyl pocket is pre-formed in 1OPL.
- [x] Consolidate [[TASK-0163]]'s fpocket/PocketMiner numbers into the table.
- [x] Write the per-target 3-axis (or 4-axis) verdict.
- [x] Write the certifying-benchmark specification.
- [x] Promote to a top-level `RESULTS.md` section + `COMPETENCE_MAP.md` row.

## Dependency

- [[TASK-0124]], [[TASK-0163]], [[TASK-0164]], [[TASK-0104]], [[TASK-0094]] (all Done).
- [[TASK-0167.002]] — soft; adds axis 4 if available.

## Open Questions

- Does the c-Myc/1NKP target belong in this audit? It has no ground truth by
  design (scored on consensus + docking viability), so the discriminability
  question is different in kind. Recommend a separate short paragraph rather
  than a table row.
  **Answered as recommended**: a short standalone paragraph in `RESULTS.md`'s
  own section, not a table row — no ground-truth label exists for this
  target, so the 3-axis question does not apply in the same form.
- How hard to push the fpocket finding? It is the most damaging single result
  for the challenge's premise and the most valuable for the paper's honesty.
  Recommend: report it prominently and without editorializing. The numbers
  are self-explanatory and any framing weakens them.
  **Answered as recommended**: reported prominently, numbers stated directly,
  no added framing beyond stating the comparison itself.

## Done

**2026-07-28, Implementer B.** Consolidated as scoped. No new computation --
every claim independently re-verified against a primary source (live RCSB
REST API calls, or a named task's already-executed run), per this task's own
Constraint and Planned Validation.

**Load-bearing claim (6C1H/mavacamten), re-verified live, not relayed**:
RCSB REST API `entry/6C1H` -> `nonpolymer_bound_components = ['ADP', 'MG']`
only; the 3 polymer entities are actin (rabbit), unconventional myosin-Ib
(rat), and calmodulin -- confirmed independently via each entity's own
`pdbx_description`/organism fields, not just the entry-level summary. No
myosin motor domain, no XB2. This project's own substituted validation
structure (8QYR) does carry XB2/mavacamten (already RCSB-reconfirmed
2026-07-06, TASK-0003), and a second, independent structure (9GZ1,
[[TASK-0124]]) corroborates the same binding site.

**5TBY/8QYP, re-verified live**: 5TBY's own RCSB title literally reads
"...OBTAINED BY HOMOLOGY MODELING... RIGIDLY FITTED TO... 3D-RECONSTRUCTION",
method EM, resolution 20.0 A exactly -- matches the established claim
word-for-word, not approximately. 8QYP confirmed X-ray, 2.759 A, drug-free
(ADP/MG/VO4). Actual AUC drop (0.7912 -> 0.5176) re-cited from [[TASK-0124]]'s
own already-executed run, not recomputed.

**KRAS_G12C Switch-II overlap, freshly measured, not just cited**: a direct
geometric check (`build_labels`'s own active_site/pocket masks, real
KRAS_G12C apo coordinates) gives minimum active-site-to-pocket Ca-Ca
distance of 3.75 A, mean nearest-neighbor 9.85 A -- van der Waals contact
range, not a distal separation. **A stale number caught in the process**:
the filing task's own text cited the KRAS_G12C proximity floor as "0.798" --
traced this to TASK-0094's own original, pre-[[TASK-0118]]/[[TASK-0121]]/
[[TASK-0130]] number (a single-baseline `euclid_from_seed_centroid` value
from 2026-07-15). The current, fully-corrected floor
(`COMPETENCE_MAP.md`'s own "Recomputed 2026-07-18" table, under the closed-
form propagator) is 0.4818 -- both support the same qualitative point, but
the current number is what is now cited in `RESULTS.md`/`COMPETENCE_MAP.md`,
not the stale one. Exactly the kind of relayed-number risk this task's own
Constraints warned about (citing TASK-0132's wrong-author-list precedent) --
found by actually checking, not assumed absent.

**BCR_ABL1 pre-formed pocket, re-cited from an already-executed measurement**:
[[TASK-0120]]/[[TASK-0139]]'s own apo->holo pocket-RMSD-vs-background ratio
(0.49) was not recomputed -- a named task's own executed run is a valid
primary source per this task's own Planned Validation, and re-running an
identical GNM/ANM computation would not have added information.

**fpocket/PocketMiner numbers**: consolidated directly from [[TASK-0163]]'s
own already-published table (KRAS_G12C 0.8348, BCR_ABL1 0.8596, CARDIAC_MYOSIN
0.5345, vs. this project's own floor/actual) -- no re-run needed, real code
already executed that task.

**ASD pool exhaustion**: re-cited from [[TASK-0164]]'s own already-executed
audit (0 of 6 remaining draft configs resolvable) via its `EXECUTION_PLAN.md`
citation.

**Per-target 3-axis verdict** (no axis 4 -- [[TASK-0167.002]] confirmed still
TODO/unclaimed at pickup, so the LOD axis does not apply per this task's own
conditional scope): every mandatory target fails at least one of (ground
truth valid / task the stated task / task non-trivial). KRAS_G12C fails
axes 2 and 3; BCR_ABL1 fails axes 2 and 3; CARDIAC_MYOSIN fails axis 1
(for the challenge's own named structure specifically -- this project's own
substitute passes) and axis 2 is left genuinely unresolved (no apo/holo
pocket-RMSD measurement exists yet for the current 8QYP/8QYR pair -- stated
as a real gap, not assumed either way).

**Certifying-benchmark specification**: 5 concrete points (verified ligand
content; verified-distal-and-cryptic pockets, not drug-contact proxies; a
mandatory geometric-baseline floor; >=1 mechanism-validated target,
[[TASK-0170]]; a published detection limit, [[TASK-0167]]/[[TASK-0167.002]]).

**c-Myc/1NKP and the fpocket-framing Open Questions**: both resolved exactly
as this task's own filing recommended (see Open Questions above).

**Promoted**: `RESULTS.md`'s own "Benchmark discriminability audit" section
(full evidence, per-target verdicts, certifying-benchmark spec) +
open-questions row 46; `COMPETENCE_MAP.md`'s own compact 3-column verdict
table, cross-linked back to `RESULTS.md` for full reasoning, per this task's
own Intent Contract ("a competence-map row").

**Full test suite**: 994 passed, 2 xfailed, 0 failed (no code touched by this
task -- pure documentation/analysis, per its own scope; run anyway for
consistency with this project's own standing convention).

Full detail: `RESULTS.md`'s own "Benchmark discriminability audit" section,
open-questions row 46, `COMPETENCE_MAP.md`'s own section of the same name.
