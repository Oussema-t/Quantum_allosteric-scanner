# TASK-0125 Verify c-Myc/1NKP resnums: does `keep_nucleic: true` leak DNA into the hit list?

## Context

- ID: TASK-0125
- Title: c-Myc's target config carries `keep_nucleic: true` (1NKP is a
  protein-DNA complex) — verify the hit list's residue numbers are
  actually protein residues, not DNA nucleotide indices leaking through
  under a shared numbering scheme.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §5 P2-11: "a
  referee will spot 'residue 943' instantly."
- Priority: **P2 — weeks 4-6.** Cheap, concrete correctness check with
  real reputational risk if wrong.

## Intent Contract

- Outcome: a direct check that every index in c-Myc's consensus hit list
  ([[TASK-0080]]'s `run_target_no_ground_truth` output) maps to a real
  protein residue in 1NKP's own numbering — not a DNA nucleotide index
  that happens to fall in the same array position because
  `keep_nucleic: true` retained DNA chains in the coordinate/index space
  `functional_indices`/`consensus_ranking` operate over.
- Why this is plausible, not paranoid: `keep_nucleic: true` was set
  specifically because 1NKP's biology requires the DNA context (the
  b-HLH-LZ dimer's functional site is DNA-contact-defined) — but if
  `resnums`/index bookkeeping doesn't cleanly separate protein-chain
  indices from nucleic-chain indices downstream, a "top-5 hit" could
  silently be a nucleotide, which is nonsensical for an allosteric-pocket
  claim and immediately visible to any reviewer who checks.
- In Scope:
  - Trace every index in c-Myc's real, already-produced hit list (from
    [[TASK-0080]]'s live run) back to 1NKP's actual PDB residue/chain
    records — confirm each is a protein Cα, with the correct residue
    number in 1NKP's own numbering (not a re-indexed array position).
  - If any hit is a DNA nucleotide or mis-numbered: fix the root cause
    (index bookkeeping in whichever function conflates protein/nucleic
    indices) and re-run c-Myc's consensus ranking.
  - If all hits are confirmed correct: state this as a verified check in
    Done — a real negative result closing a real, plausible risk, not
    wasted effort.
- Out Of Scope:
  - Re-deriving `keep_nucleic`'s own necessity — already established,
    per c-Myc's biology; this task only checks the downstream indexing
    consequence.
- Constraints And Invariants: none beyond standard verification-against-
  real-data discipline already used throughout this project (e.g.
  TASK-0081's independent RCSB chain-ID verification).
- Planned Validation: the direct index-to-PDB-record trace itself is the
  validation — report the mapping for every hit-list residue explicitly,
  not just a summary "looks fine."

## In Progress

None

## TODO

- [ ] Trace every c-Myc hit-list index back to 1NKP's real PDB
      residue/chain records.
- [ ] Confirm each is a protein Cα with correct 1NKP-native numbering.
- [ ] If any is wrong: find root cause in index bookkeeping, fix, re-run.
- [ ] Report result (verified-correct or fixed-and-rerun) in Done.

## Dependency

- [[TASK-0080]] (Done) — provides the real hit list this task traces.

## Open Questions

- None — the check itself is fully specified; whether a fix is needed
  depends entirely on what the trace finds.

## Done

(not yet)
