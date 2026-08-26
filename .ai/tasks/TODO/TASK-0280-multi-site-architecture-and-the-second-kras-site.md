# TASK-0280 — Two proteins, two multi-site architectures: verify the second KRAS site and close H6.2

- Status: TODO
- Assignee: unassigned (suggest Explorer — this is verification + write-up support, not a run)
- Priority: **High — small, feeds [[TASK-0184]] directly, and it closes a register hypothesis that has been open since the reference audit**
- Filed: 2026-08-27 by Reviewer
- Related: [[TASK-0276]], [[TASK-0270]], [[TASK-0229.003]], [[TASK-0248]], [[TASK-0265]], [[TASK-0184]]

## The measurement, already made

Computed directly from [[TASK-0276]]'s stored footprints
(`holo_only_structural_signature.json`, `allosteric_keys`), clustering the ten
verified KRAS holo structures by pairwise pocket Jaccard:

| | result |
|---|---|
| **9 of 10 drugs** | one site — Switch-II pocket, consensus residues 9, 58–72, 95–103; pairwise Jaccard **0.43–0.90** among them |
| **`7A1X` (QWB)** | **Jaccard 0.00** against eight of the nine, 0.04 against the ninth. Footprint **37, 39, 54, 55, 56, 71, 74, 75** — the **Switch-I/II groove**, a different site |

So KRAS is a **9:1 two-site** protein. [[TASK-0276]] found HCV_NS5B is **2:2
fully disjoint** (within-apo-pair Jaccard 0.941, across-pair **0.000**).

**Two families, two different multi-site architectures.** That is a real,
measured result and it is currently sitting only in a JSON file.

## Why it matters beyond a nice observation

**It is direct evidence for H6.2**, which this register has carried as
**UNTESTED** since the reference audit — *"the allosteric site is
effector-specific; one protein has different allosteric sites for different
effectors"* (Tsai & Nussinov 2014). [[TASK-0229.003]] tested it via an ASD
lookup and found one genuine second site (BCR-ABL1); this is structural
evidence from two more proteins, obtained as a by-product.

It also compounds [[TASK-0265]]'s conclusion. If one protein has several
allosteric sites used by different chemotypes, then "the allosteric pocket of
protein X" is not a well-defined single object — and our benchmark assigns
exactly one per target.

## Scope

- [ ] **Verify the Switch-I/II site live.** The residue-number reading
      (37/39/54/55/56/71/74/75 against KRAS landmarks: Switch-I 30–38,
      Switch-II 59–76) is the Reviewer's own inference from coordinates, **not
      a verified citation**. Establish whether this is a recognised,
      published second druggable site on KRAS, and identify `QWB`/Cpd1's own
      primary reference. This is the difference between *"we observed two
      clusters"* and *"we recovered the two known druggable sites"* — which
      read very differently to a reviewer.
- [ ] Confirm `7A1X` is genuinely KRAS G12C and that its chain/numbering match
      the other nine, so the 0.00 Jaccard is a real site difference and not a
      numbering artefact. [[TASK-0273]] found GAC's chain-exact vs resnum-only
      Jaccard differed by an order of magnitude — the same trap applies here
      and must be ruled out explicitly.
- [ ] Repeat the clustering for **every** frozen-set protein with ≥2 holo
      structures, not just KRAS and HCV_NS5B. Report the architecture per
      protein: single-site, N:M split, or fully disjoint.
- [ ] Update the register's H6.2 entry in
      `.claude/hypotheses/reference_register.md` with the outcome and cite
      this task, per [[TASK-0248]]'s sync rule.
- [ ] Draft the paragraph for [[TASK-0184]]. One sentence carries it: *two
      independent families, two different multi-site architectures, and our
      benchmark assigns one pocket per target.*

## Acceptance

- [ ] Live-verified answer on whether the Switch-I/II site is documented, with
      citation or an explicit "not established".
- [ ] Numbering/chain artefact ruled out for `7A1X`.
- [ ] Per-protein architecture table across the frozen set.
- [ ] H6.2's register entry updated.
- [ ] Submission paragraph drafted.

## Constraint

If the Switch-I/II site turns out **not** to be a recognised allosteric site —
if `7A1X` is a fragment hit, a crystallisation artefact, or a surface binder
with no published function — say so. The 9:1 split would then be a finding
about *deposition practice*, not about allostery, and the H6.2 claim would not
follow. Verify before the claim reaches the submission, not after.
