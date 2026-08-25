# TASK-0264 — Measure the hardness of cryptic-opening instances *before* building a QUBO

- Status: TODO
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

- [ ] Define the cryptic-opening instance precisely, and write the definition
      down before measuring: which residues are variables (pocket-lining plus
      a shell?), which rotamer library, what the objective is (steric
      feasibility + cavity volume + stability), and what couples to what.
      [[TASK-0235]]'s local-Kabsch backbone step and [[TASK-0204]]'s EvoEF2
      rotamer machinery are the existing pieces — reuse, do not re-derive.
- [ ] Build the interaction graph and measure **treewidth** on real instances
      from [[TASK-0243]]'s frozen set, prioritising the **cryptic** targets
      ([[TASK-0254]] part B says 11 of 20 are genuinely cryptic-testing).
- [ ] Solve exactly by bucket elimination where feasible, and report
      wall-clock. Reuse [[TASK-0204]]'s `MAX_FACTOR_ENTRIES = 1e8` projected-
      cost guard — that guard exists because an unguarded m=20 run projected
      ~300 GB and had to be killed. **Do not remove or raise it silently.**
- [ ] Sweep instance size (number of variable residues) and report how
      treewidth scales. The question is not one number, it is whether
      hardness grows with the region we actually care about.
- [ ] Compare directly against [[TASK-0204]]'s published 2–5 range, same
      metric, so the two are commensurable.
- [ ] State a pre-registered verdict rule **before** running: e.g. median
      treewidth ≥ 12 on cryptic targets at realistic instance size ⇒ a real
      quantum target; ≤ 6 ⇒ formulation exercise only. Pick the numbers and
      commit to them first.

## Acceptance

- [ ] Written instance definition, fixed before measurement.
- [ ] Treewidth and exact-solve wall-clock per target, with the size sweep.
- [ ] Explicit verdict against the pre-registered rule.
- [ ] A recommendation: build the QUBO, or record that the classical solver
      wins and say so in the Phase 2 material.
- [ ] `RESULTS.md`; update `PHASE_B_ROTAMER_QUBO.md` with the measured
      hardness either way.

## Constraint

Do not formulate the QUBO in this task even if it looks easy to do alongside.
The whole point is that the hardness measurement must not be motivated by
having already built the thing it justifies. If the verdict is "classically
easy", that is the finding and it belongs in the proposal — a QUBO presented
without it would not survive review.
