# TASK-0312 — The observed CTQW active→pocket vs pocket→active asymmetry: artifact or bug?

- Status: TODO
- Priority: Medium — cheap, and it either retires a standing observation or finds a real defect
- Filed: 2026-09-01 by Reviewer thread
- Related: [[TASK-0308]], [[TASK-0118]], [[TASK-0140]]

## The claim to test

It has been observed in this project that the CTQW propagates differently
seeded from the active site toward the pocket than from the pocket toward
the active site.

**For our Hamiltonian, that should be impossible.** `H_new` is real and
symmetric (contact matrix plus diagonal potentials). For real symmetric
`H`, the propagator `U(t) = exp(−iHt)` is complex symmetric, so
`U_ij = U_ji` and therefore

```
|⟨j|U(t)|i⟩|²  =  |⟨i|U(t)|j⟩|²     exactly, for all i, j, t
```

Time-averaging preserves it. **Site-to-site transfer is exactly
symmetric; there is no directionality available.**

## The two hypotheses

1. **Normalisation artifact (expected).** Seeding from a set `S` and
   reading at set `T` sums `|U_ij|²` over `i∈S, j∈T` and divides by
   `|S|`. The reverse divides by `|T|`. With `|S| ≈ 20` active-site
   residues and `|T| ≈ 12` pocket residues, the two numbers differ for
   arithmetic reasons alone. **If so, the observation must be retired,
   not built on.**
2. **Implementation defect.** If the asymmetry survives matched
   normalisation, something in the propagator or the seeding is wrong,
   and that is worth finding.

## Scope

- [ ] On a handful of targets, compute the full `|U_ij|²` matrix and
      verify symmetry numerically to machine precision. This is the
      control: if it fails, stop and debug the propagator.
- [ ] Reproduce the observed set-level asymmetry, then recompute it with
      **matched normalisation** (divide both directions by the same
      quantity, or compare per-pair means rather than per-seed sums).
- [ ] Report which hypothesis holds.

## Note

If hypothesis 1 holds — as the mathematics says it must — then genuine
directionality requires **breaking time-reversal symmetry**, i.e.
**complex hopping amplitudes** (a chiral quantum walk / synthetic gauge
phase). That is not a re-analysis of what we have; it is a different
Hamiltonian, and it connects directly to [[TASK-0310]]'s lead candidate.
