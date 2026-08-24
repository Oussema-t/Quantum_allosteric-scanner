# TASK-0251 — H5: MWC / conformational selection, and whether the challenge's own scope truncates the mechanism

- Status: TODO
- Assignee: unassigned (suggest Explorer → Implementer)
- Priority: **High — H5.2 may invalidate a mandatory target by construction**
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0248]] (confirmed genuinely open by direct search)
- Reference: Changeux J-P, Edelstein SJ, *Science* 2005, "Allosteric Mechanisms of Signal Transduction", [10.1126/science.1108595](https://doi.org/10.1126/science.1108595)
- Related: [[TASK-0169]] (benchmark discriminability), [[TASK-0222]] (both Cardiac Myosin pairs), [[TASK-0236]] (mavacamten/SRX citation check)

## Hypotheses

- **H5.1** — Pre-existing equilibrium between states; **ligand selects rather
  than induces**. Directly contradicts the induced-fit/propagation framing our
  CTQW pipeline is built on, and is the same family as [[HYP-P13]] (allostery
  as stabilisation) which this register arrived at independently from data.
- **H5.2** — Allosteric transitions are **concerted across subunits** in
  oligomers.

## Why H5.2 is the urgent half

The challenge's own Scope note says *"Included: the catalytic domains"*. If a
target's real mechanism is **inter-subunit or inter-domain**, then scoping the
model to a single catalytic domain **removes the coupling from the model by
construction** — before any observable is computed. The target would then be
unscoreable in principle, not merely difficult, and a negative result on it
would carry no information about the method.

**CARDIAC_MYOSIN is the flagged candidate** (mavacamten / SRX / interacting-heads
biology). Flagged, not confirmed — confirming or refuting it is this task's job.
Note the target already has two known problems ([[TASK-0222]]: mandated pair
unscoreable; [[TASK-0169]]: 6C1H does not contain mavacamten). A third,
mechanistic one would settle whether it belongs in the benchmark at all.

## Scope

- [ ] Verify the Changeux & Edelstein citation directly before working against
      it (the family convention — [[TASK-0137]], and every TASK-0229 subtask).
- [ ] For each benchmark target, establish from primary literature whether the
      published mechanism is intra-domain, inter-domain, or inter-subunit.
      Record the citation per target; do not infer from structure alone.
- [ ] For any target whose mechanism is inter-subunit: determine whether our
      chain selection retains the coupling partners. If it does not, mark the
      target **unscoreable-by-construction** and say so wherever its results
      are reported.
- [ ] H5.1: state what would distinguish conformational selection from induced
      fit **using apo/holo structure pairs only** (no MD — constraint 3). If
      nothing available distinguishes them, say that plainly and close H5.1 as
      *not decidable with our inputs* rather than leaving it open forever.
- [ ] Connect to [[HYP-P13]]: H5.1 is the literature statement of the same
      idea. Either fold them together or state precisely how they differ.

## Acceptance

- [ ] Per-target mechanism table with citations: intra-domain / inter-domain /
      inter-subunit, and scope-retained yes/no.
- [ ] An explicit verdict on CARDIAC_MYOSIN.
- [ ] H5.1 either tested or formally closed as undecidable with our inputs.
- [ ] Register STATUS for H5 updated to cite this task.

## Constraint

If a mandatory target turns out unscoreable by construction, that goes in the
Phase 1 submission as a finding about the benchmark — not quietly into a
limitations paragraph. [[TASK-0169]] set that precedent and it was the right one.
