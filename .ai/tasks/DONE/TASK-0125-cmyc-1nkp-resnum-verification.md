# TASK-0125 Verify c-Myc/1NKP resnums: does `keep_nucleic: true` leak DNA into the hit list?

## Context

- ID: TASK-0125
- Title: c-Myc's target config carries `keep_nucleic: true` (1NKP is a
  protein-DNA complex) — verify the hit list's residue numbers are
  actually protein residues, not DNA nucleotide indices leaking through
  under a shared numbering scheme.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-18
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

- [x] Trace every c-Myc hit-list index back to 1NKP's real PDB
      residue/chain records.
- [x] Confirm each is a protein Cα with correct 1NKP-native numbering.
- [x] If any is wrong: find root cause in index bookkeeping, fix, re-run.
      (N/A — none wrong.)
- [x] Report result (verified-correct or fixed-and-rerun) in Done.

## Dependency

- [[TASK-0080]] (Done) — provides the real hit list this task traces.

## Open Questions

- None — the check itself is fully specified; whether a fix is needed
  depends entirely on what the trace finds.

## Done

**2026-07-18, Implementer B.** Verified — no bug. All 5 hits in
`results/tasks/0080/MYC_MAX/hit_list.json` are real protein residues with
correct 1NKP-native numbering. No DNA nucleotide leakage. No fix needed;
this is a real negative result.

### Method (two independent checks, per Planned Validation)

1. **Production pipeline trace**: for each hit-list array index, read
   `clean_from_config('MYC_MAX', role='apo').resnums/chain_ids/resnames`
   at that index — the exact array the consensus-ranking code actually
   indexes into.
2. **Raw PDB cross-check**: independently `prody.parsePDB('1NKP')` and
   select `chain <X> and resnum <Y>` for the resulting (chain, resnum)
   pair — confirm resname matches and the atom set is a genuine amino
   acid (has N/CA/C/O backbone atoms; not one of the DNA resnames
   DA/DC/DG/DT).

Script: `scripts/verify_cmyc_resnums.py` (new, reusable — re-run any time
`hit_list.json` is regenerated).

### Trace table (every hit-list entry, explicit per Planned Validation)

| idx | pipeline resnum | pipeline chain | pipeline resname | raw-PDB resname | raw-PDB atoms | verdict |
|-----|------------------|-----------------|--------------------|-------------------|----------------|---------|
| 46  | 943 | A | LEU | LEU | C,CA,CB,CD1,CD2,CG,N,O | OK — real protein residue |
| 132 | 246 | B | ALA | ALA | C,CA,CB,N,O | OK — real protein residue |
| 28  | 925 | A | ARG | ARG | C,CA,CB,CD,CG,CZ,N,NE,NH1,NH2,O | OK — real protein residue |
| 129 | 243 | B | LEU | LEU | C,CA,CB,CD1,CD2,CG,N,O | OK — real protein residue |
| 112 | 226 | B | ARG | ARG | C,CA,CB,CD,CG,CZ,N,NE,NH1,NH2,O | OK — real protein residue |

All 5/5 confirmed: real amino acids, correct native 1NKP chain/resnum,
zero DNA-resname or atom-set anomalies. `hit_list["resnums"]` values
match the pipeline's own `resnums` at those indices exactly (no re-
indexing drift between the two).

### Secondary observation (not a bug, not pursued — Out Of Scope)

`keep_nucleic: true` has **zero actual effect** for MYC_MAX: `clean()`'s
selection is `(protein or nucleic) and (chain A or chain B)` — since
`chains: ["A", "B"]` never includes the DNA chains (F, G, H, J), the
`chains` filter excludes all DNA regardless of `keep_nucleic`. Confirmed
directly: `clean_from_config('MYC_MAX', role='apo')` returns the
identical 171-residue set whether `keep_nucleic` is `true` or `false`.
This means the actual risk this task was created to check
(protein/nucleic index conflation) can never have occurred for this
target's specific `chains` config — the flag is a documented-but-inert
setting here, not the load-bearing mechanism it reads as. Flagged for
awareness; not changed, per this task's declared Out Of Scope
("re-deriving `keep_nucleic`'s own necessity").

### Root cause of the "risk" not materializing

The hit-list indices come from `functional_indices`/`consensus_ranking`
operating over `clean_from_config`'s output array, which — per the above
— never contained DNA atoms for MYC_MAX in the first place (chain filter
excludes them upstream of any protein/nucleic type distinction). There
was no index-bookkeeping path where conflation could happen for this
target; the risk described in the task's Intent Contract requires DNA
chains to actually be present in the cleaned structure, and for MYC_MAX
they are not.
