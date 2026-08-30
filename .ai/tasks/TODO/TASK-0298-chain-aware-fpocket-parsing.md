# TASK-0298 — Chain-aware fpocket parsing, and re-quantify the ceiling

- Status: TODO
- Priority: **High — the published ceiling 0.1649 rests on candidate residue sets that are wrong for 9 of the frozen 20**
- Filed: 2026-08-30 by Reviewer thread (D1 from [[TASK-0297]]; defect originally found by the external distal-pockets session)
- Related: [[TASK-0297]], [[TASK-0282]], [[TASK-0287]], [[TASK-0292]], [[TASK-0293]]

## The defect

`task0242_two_stage_dryrun.fpocket_candidates` parses pocket residues as
`int(line[22:26])`, discarding the chain. Every consumer then builds
`idx_of = {int(r): i for i, r in enumerate(resn)}`, which on a
multi-chain selection **keeps only the last chain's index** per residue
number. A pocket lining chain A silently maps onto chain B's coordinates.

## Exposure

Nine targets carry cross-chain residue-number collisions, **all of them in
[[TASK-0282]]'s frozen 20**: `GAC_BPTES` (406), `GAC_CPD12` (405),
`PKR_MITAPIVAT`/`PKR_AG946` (422), `PF_ATCASE` (328), `FBPASE_95S` (310),
`SUMO_E1_FHJ` (280), `TRP_SYNTHASE_F6F`/`F19` (253).

Unlike the seed defect ([[TASK-0297]] D2), **this one has no
homo-oligomer exemption**: even when both chains are the same protein, a
specific fpocket cavity lines *one* of them, and mapping it to the other
is wrong regardless.

## Scope

- [ ] Key fpocket residues on `(chain, resnum)`; parse `line[21]`
      alongside `line[22:26]`. Build `idx_of` on the same compound key.
- [ ] Audit every other `int(line[22:26])` / resnum-only `idx_of` in the
      scripts tree — this pattern is likely copied.
- [ ] **Re-run [[TASK-0282]]'s ceiling** and report the corrected mean EH
      against the published **0.1649**, per-target.
- [ ] Re-run [[TASK-0287]] Part C, [[TASK-0292]] Parts A–C, and
      [[TASK-0293]]'s LOTO on corrected candidates.
- [ ] Fix `DHPS_GC7`'s config: chains `[A, B]` but 1RLZ deposits only A.

## Constraint

Report the corrected ceiling **whichever way it moves**. If it rises,
that is not a licence to re-open the CTQW comparison without re-running
the CTQW arm on the same corrected candidates.

## Note

[[TASK-0297]] found the analogous seed defect moved exactly one target.
The likeliest outcome here is similarly small — but "likeliest" is not
"measured", and the ceiling is quoted in the collaborator brief.
