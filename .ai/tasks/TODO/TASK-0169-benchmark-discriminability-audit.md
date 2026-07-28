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
- Status: TODO
- Owner: Architect/Planner (analysis + writing; little new computation)
- Claimed By: —
- Claimed At: —
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

- [ ] Re-verify 6C1H ligand content directly on RCSB (**load-bearing**).
- [ ] Re-verify 5TBY method/resolution and the 8QYP replacement.
- [ ] Re-verify KRAS Switch-II / active-site residue overlap from the labels.
- [ ] Re-verify BCR-ABL1 myristoyl pocket is pre-formed in 1OPL.
- [ ] Consolidate [[TASK-0163]]'s fpocket/PocketMiner numbers into the table.
- [ ] Write the per-target 3-axis (or 4-axis) verdict.
- [ ] Write the certifying-benchmark specification.
- [ ] Promote to a top-level `RESULTS.md` section + `COMPETENCE_MAP.md` row.

## Dependency

- [[TASK-0124]], [[TASK-0163]], [[TASK-0164]], [[TASK-0104]], [[TASK-0094]] (all Done).
- [[TASK-0167.002]] — soft; adds axis 4 if available.

## Open Questions

- Does the c-Myc/1NKP target belong in this audit? It has no ground truth by
  design (scored on consensus + docking viability), so the discriminability
  question is different in kind. Recommend a separate short paragraph rather
  than a table row.
- How hard to push the fpocket finding? It is the most damaging single result
  for the challenge's premise and the most valuable for the paper's honesty.
  Recommend: report it prominently and without editorializing. The numbers
  are self-explanatory and any framing weakens them.

## Done

(not yet)
