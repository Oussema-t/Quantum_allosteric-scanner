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

- [x] Score `V_C`, `V_B`, `degree`, SASA at **both** site definitions across
      all ten KRAS holo structures **plus `4LDJ`**, ligand physically stripped
      throughout ([[TASK-0276]]'s own stripping, reused).
- [x] **Match node sets** via `allostery.superpose.align_apo_holo`. Done via
      a single fixed reference (`4LDJ`) each of the ten holo structures is
      aligned against independently — not an all-pairs alignment, a simpler
      design that still satisfies the requirement (every comparison in this
      task is anchored to one reference frame). n_common ranged 166–170 of
      170 (`4LDJ`'s own resolved residue count), disclosed per structure.
- [x] Run fpocket per structure at the Switch-I/II residues for **P3**.
- [x] Report effect sizes with the sample structure stated plainly — done
      throughout; no cross-structure significance test computed.
- [ ] Extend to any other frozen-set protein [[TASK-0280]] finds multi-site.
      **Not attempted** — [[TASK-0280]] was still in progress when this task
      ran (its own clustering headline was already quoted in this task's own
      filing and reused directly; its Scope item extending the search to
      other proteins had not yet landed). Flagged as the natural next step
      for whoever next touches either task, not silently dropped.

## Acceptance

- [x] P1, P2, P3 each answered explicitly against the table above.
- [x] A verdict on the capacity hypothesis: **dies** — not untestable, not a
      partial success. See Done.
- [x] `RESULTS.md`, and an update to [[TASK-0279]]'s record recording what
      became of the reading it prompted (dated addendum, same convention
      every prior cross-task update in this register has used).

## Constraint

**The hypothesis is post-hoc and the Reviewer proposed it.** Both facts make a
favourable outcome less trustworthy. Predictions P1–P3 are fixed above
precisely so they cannot be adjusted afterwards; if the result is ambiguous,
report ambiguity rather than selecting whichever of the three arms cooperated.

And if it dies: that is the correct outcome for a post-hoc rescue of a failed
test, and it belongs in the Phase 2 section as an example of the register
testing its own explanations rather than accumulating them.

## Done

**2026-08-27, Implementer B.** Full numbers in `RESULTS.md`'s own section
and `results/tasks/0281_docked_undocked_capacity/docked_undocked_capacity.json`
(not duplicated verbatim here) — summary:

**Data reused, not re-derived**: [[TASK-0280]]'s own clustering result
(quoted directly from that task's own file, itself computed from
[[TASK-0276]]'s stored KRAS footprints) — Switch-I/II footprint
(residues 37, 39, 54, 55, 56, 71, 74, 75) docked in exactly `7A1X`;
Switch-II consensus (residues 9, 58–72, 95–103) docked in the other
nine. This task's own job was the new measurement, not re-clustering.

**Method**: every one of the ten verified KRAS holo structures
([[TASK-0270]]'s own live-verified ensemble) aligned independently
against `4LDJ` (the register's own verified genuine apo, [[TASK-0270]])
via `align_apo_holo` — `V_C`/`degree` computed on the common-set-restricted
coordinates (matched node set, this task's own Scope item 2, non-negotiable
per [[TASK-0275]]/[[TASK-0279]]); `V_B`/SASA computed on each structure's
full resnums and indexed at the common set afterward, [[TASK-0279]]'s own
established split. Ligand stripped throughout ([[TASK-0276]]'s own
`write_ligand_stripped_pdb`). n_common ranged 166–170 residues per
structure (of `4LDJ`'s own 170) — no target residue (Switch-I/II or
Switch-II) was missing from the common set for any structure except
`8S8C`, which resolved 21/25 Switch-II residues (4 missing, disclosed,
not silently dropped).

**P1 (Switch-I/II): weak, direction-consistent, not clean.** 9 of the 10
undocked observations (9 holo + `4LDJ` apo) score higher `V_C` than the
one docked structure (`7A1X`, 12.684) — median undocked 12.967 vs docked
12.684, the predicted direction. But separation is not clean: `6OIM`
(undocked) scores 12.604, *below* the docked value, and two more
(`4LDJ`=12.715, `7YCE`=12.730) sit within 0.05 of it. The docked value is
not uniquely separated from the undocked distribution's own low end.

**P2 (Switch-II): fails outright, wrong direction.** The prediction is
undocked (`7A1X`=14.966) higher than docked (the other nine). Measured:
the **docked group's own median (15.097) is HIGHER than the undocked
value**, and 6 of 9 individual docked structures exceed it (only `8S8C`,
`6OIM`, and `7MDP` fall below `7A1X`). This is not merely "no
difference" — it points in the direction the hypothesis explicitly
predicts *against*, the same direction as the original BCR-ABL1 anomaly
([[TASK-0279]]) that the capacity reading was invented to explain away.

**Per this task's own pre-registered logic** ("a result that holds at one
and not the other is a null, not a partial success") — **P1's weak,
non-clean trend and P2's outright reversal do not together support the
hypothesis. Verdict: the capacity hypothesis DIES.** Not untestable (both
P1 and P2 produced clear, computable answers at the pre-specified sites);
not a partial success (the task's own Constraint forbids reading P1 alone
as a win when P2 was pre-registered as an equally decisive arm).

**P3, answered independently of P1/P2's outcome**: fpocket detects a real
cavity overlapping the Switch-I/II window in effectively every undocked
structure (best overlap_frac 0.125–1.00, ≥0.5 in 7 of 10; `4LDJ` apo
itself: 0.875). Per this task's own pre-registered reading rule ("if it
detects one in most, the site is an unused open groove and 'cryptic' is
the wrong word for it"): **Switch-I/II reads as an unoccupied open
groove, not a genuinely cryptic pocket**, in most of these structures —
independently informative for how [[TASK-0259]]'s own crypticity
correlation should be read on a multi-site protein, and worth carrying
into whichever task next touches KRAS's own crypticity classification.

**[[TASK-0279]]'s own record updated** with a dated addendum recording
this outcome, per this task's own Acceptance.

**Artifacts**: `scripts/task0281_docked_undocked_capacity.py`; `results/
tasks/0281_docked_undocked_capacity/docked_undocked_capacity.json`
(every structure's per-residue `V_C`/`degree`/`V_B`/SASA at both site
definitions, plus the full P3 fpocket detail); `RESULTS.md`; this file;
`.ai/tasks/DONE/TASK-0279-ligand-selectivity-gate-occupancy-vs-efficacy.md`
(addendum).

**Not attempted, explicitly out of scope**: extending to a second
multi-site protein ([[TASK-0280]] was still in progress, had not yet
surfaced a second candidate when this task ran — flagged as the natural
next step, not silently dropped, per this task's own Scope note above);
re-clustering or re-verifying [[TASK-0280]]'s own Switch-I/II citation
claim (that task's own Scope, not this one's).
