# TASK-0281 — Docked vs undocked, same site, same protein: does the coupling signature survive an empty pocket?

- Status: TODO
- Assignee: unassigned — **Phase 2 candidate.** Well-specified and pre-registered here deliberately; a proposal carrying a designed falsification test is stronger than one carrying another result.
- Priority: High (Phase 2) — do **not** delay [[TASK-0184]] for it
- Filed: 2026-08-27 by Reviewer
- Related: [[TASK-0279]], [[TASK-0276]], [[TASK-0280]], [[TASK-0259]], [[TASK-0277]], [[HYP-P13]]

## The hypothesis this exists to test, and its provenance

[[TASK-0279]] falsified the efficacy reading of `V_C`: it is **higher on the
inert myristate pocket than the efficacious asciminib pocket, 16 of 16 matched
residues** (57.44 vs 53.63, ~7%) — a significant separation in the *wrong*
direction.

An alternative reading was proposed **after** seeing that result:

> `V_C` measures a pocket's **capacity to couple**, not whether coupling is
> being exercised. An efficacious drug clamps the site and quenches
> fluctuations; an inert occupant leaves the coupling intact. (This is the
> Cooper–Dryden mechanism arriving through our own data rather than by
> assertion.)

**It is post-hoc and currently worth nothing.** It was generated to explain a
failed pre-registered test, which is precisely the move this register has
criticised throughout. It earns credit only by surviving a test on data that
did not generate it.

## The instrument — a natural experiment already in hand

[[TASK-0280]]'s clustering found KRAS is a **9:1** two-site protein: nine
drugs in the Switch-II pocket, `7A1X` alone in the Switch-I/II groove
(residues 37, 39, 54, 55, 56, 71, 74, 75).

**Therefore the Switch-I/II site is docked in exactly one structure and
undocked in nine** — same protein, same crystallographic quality, one site
observed in both states. Plus `4LDJ`, a verified genuine apo ([[TASK-0270]]),
giving a tenth undocked observation with no drug anywhere.

This is a different site, in a different protein, from the BCR-ABL1 pair that
generated the hypothesis. That is what makes it a real test.

## Pre-registered predictions — fix these before computing anything

| # | prediction | if it fails |
|---|---|---|
| **P1** | `V_C` at the Switch-I/II residues is **higher when undocked** (9 structures + apo) than when docked (`7A1X`) | the capacity reading dies; `V_C`'s BCR-ABL1 direction was a one-off |
| **P2** | The same pattern holds at Switch-II: `V_C` higher in structures where Switch-II is *not* the drug site — i.e. `7A1X` — than in the nine where it is | as above, and more decisively, since n=9 vs 1 the other way |
| **P3** | fpocket detects **no** open cavity at Switch-I/II in most of the nine undocked structures ⇒ genuinely cryptic; if it detects one in most, the site is an unused **open** groove and "cryptic" is the wrong word for it | either answer is reportable; it decides how [[TASK-0259]]'s crypticity correlation should be read for multi-site proteins |

**P1 and P2 together are the real test**: the hypothesis predicts the *same
direction* at two different sites in the same protein. A result that holds at
one and not the other is a null, not a partial success.

## Scope

- [ ] Score `V_C`, `V_B`, `degree`, SASA at **both** site definitions across
      all ten KRAS holo structures **plus `4LDJ`**, ligand physically stripped
      throughout ([[TASK-0276]]'s own stripping, reused).
- [ ] **Match node sets** via `allostery.superpose.align_apo_holo`.
      [[TASK-0275]] found this changed `DHPS_GC7`'s `V_C` from 0.392 to 0.586;
      [[TASK-0279]] made it a Scope requirement. Non-negotiable.
- [ ] Run fpocket per structure at the Switch-I/II residues for **P3**.
- [ ] Report effect sizes with the sample structure stated plainly: **n=1
      docked vs n=10 undocked** at Switch-I/II, **n=9 vs n=1** at Switch-II.
      Do not manufacture a significance test across ten crystals of one
      protein — [[TASK-0276]]'s ten-clusters-of-one-protein framing was
      already generous and this is weaker.
- [ ] Extend to any other frozen-set protein [[TASK-0280]] finds multi-site.
      **A second protein is worth more than any amount of extra KRAS.**

## Acceptance

- [ ] P1, P2, P3 each answered explicitly against the table above.
- [ ] A verdict on the capacity hypothesis: survives, dies, or untestable at
      this sample size — **"untestable" is an acceptable and likely outcome**
      and must not be dressed as either of the other two.
- [ ] `RESULTS.md`, and an update to [[TASK-0279]]'s record recording what
      became of the reading it prompted.

## Constraint

**The hypothesis is post-hoc and the Reviewer proposed it.** Both facts make a
favourable outcome less trustworthy. Predictions P1–P3 are fixed above
precisely so they cannot be adjusted afterwards; if the result is ambiguous,
report ambiguity rather than selecting whichever of the three arms cooperated.

And if it dies: that is the correct outcome for a post-hoc rescue of a failed
test, and it belongs in the Phase 2 section as an example of the register
testing its own explanations rather than accumulating them.
