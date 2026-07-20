# TASK-0124 Re-anchor or retire CARDIAC_MYOSIN: 5TBY cannot support a Cα contact graph

## Context

- ID: TASK-0124
- Title: CARDIAC_MYOSIN's apo structure (5TBY) is a **20 Å cryo-EM IHM
  assembly / docked homology model** — not a real crystallographic
  structure, its "B-factors" are not crystallographic, and its chain
  assignment is unverified against a 6-chain complex. This is currently
  the pipeline's one surviving positive result (0.786, floor-cleared)
  and it rests on the worst structure in the mandatory-target set. Find
  a real apo β-cardiac myosin motor-domain crystal structure, or
  explicitly report CARDIAC_MYOSIN as data-limited.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §1.2, §3
  (Weaknesses #4), §5 P1-8.
- Priority: **P1 — weeks 2-4.** Per the panel: "do not build the only
  positive on a 20 Å docked homology model."
- **New lead, 2026-07-20 (relayed via `.ai/reviews/2026-07-20/
  Mavacamten-fix.txt`, not yet independently verified by this
  Architect/Planner thread — no internet access confirmed available in
  this session):** this project's own prior finding that **6C1H (the
  challenge's own designated CARDIAC_MYOSIN holo structure) contains no
  mavacamten** is corroborated — the note states 6C1H has only ADP
  bound (the post-hydrolysis product), the inhibited conformation but
  not the drug-bound one. **A genuinely new candidate is proposed**:
  **PDB 9GZ1** (cryo-EM, reportedly April 2026, *Science Advances*,
  https://www.science.org/doi/10.1126/sciadv.aea9335) — claimed to
  contain mavacamten directly (ligand code `XB2`), compared against an
  apo structure to show the drug-induced conformational change. If
  this holds up under this task's own independent-verification
  discipline, it would be a real, concrete fix for CARDIAC_MYOSIN's
  holo side — not just the apo side this task was originally scoped
  around — and directly strengthens the existing "6C1H correction"
  finding the panel called "still under-sold."

## Intent Contract

- Outcome: either (a) a real, higher-resolution apo β-cardiac myosin
  motor-domain crystal structure is identified on RCSB, verified
  (resolution, chain assignment, B-factor provenance — same
  independent-verification discipline as [[TASK-0081]]'s ASD candidates),
  and substituted for 5TBY in `config/targets.yaml`, with the full
  pipeline re-run against it; or (b) CARDIAC_MYOSIN is explicitly
  reported in `RESULTS.md`/`COMPETENCE_MAP.md` as data-limited — its
  0.786 floor-clearing result caveated as resting on a structure whose
  B-factors are not crystallographic and whose chain assignment is
  unverified, not presented as a clean positive.
- Why this matters beyond one target: this is currently **the only
  target in the mandatory set with any positive headroom at all**
  (per TASK-0082's competence map) — if it does not survive scrutiny of
  its underlying structure, the submission currently has zero clean
  positives across all 3 mandatory targets. This needs to be known
  before Phase 1 submission, not discovered by a referee.
- In Scope:
  - RCSB search for alternative apo β-cardiac myosin (MYH7) motor-domain
    structures — crystallographic, verified chain ID and ligand records,
    same independent-verification discipline TASK-0081 already
    established for ASD candidates (don't trust `targets.yaml`'s
    existing entry uncritically).
  - **Independently verify PDB 9GZ1** (the 2026-07-20 lead above) with
    the same discipline: fetch directly, confirm it is a real deposited
    structure, confirm ligand `XB2` is present and matches mavacamten's
    real chemical identity (not assumed from the relayed note alone),
    confirm what apo structure it should be compared/aligned against
    (the note implies a companion apo structure was used in the citing
    paper — identify and verify it too, do not assume 5TBY is the right
    pairing for a 9GZ1-based holo). If verified, this becomes this
    task's own preferred holo replacement for 6C1H, addressed alongside
    (not instead of) the apo-side search above.
  - If a real apo replacement (and/or 9GZ1 as holo) is found: re-run the
    full pipeline (floor/ceiling/actual, per whatever seed/clock
    convention has landed by then — TASK-0118/0119/0130 are all Done)
    against the new structure(s).
  - If not found (either side): write the data-limited caveat into
    `RESULTS.md`/`COMPETENCE_MAP.md`, additive per the no-silent-
    overwrite convention, citing this task and the specific structural
    defects (20 Å resolution, non-crystallographic B-factors, unverified
    chain assignment against a 6-chain complex; 6C1H's own confirmed
    lack of mavacamten).
- Out Of Scope:
  - Re-deriving the `LARGE_N_THRESHOLD` correction (TASK-0101's
    2026-07-15 fix) — the panel confirms that correction was itself
    correct; it "removed two wrong reasons for caution and left the
    right one load-bearing" (structural quality, not size). Do not
    re-litigate the threshold value.
- Constraints And Invariants: any replacement structure must go through
  the same independent RCSB verification TASK-0081 applied (don't trust
  a single source's chain-ID/ligand guess).
- Planned Validation: if a replacement is found, the full re-run against
  it, checked against the proximity floor same as every other target;
  if not, the caveat text itself, checked for accuracy against the
  panel's specific structural claims (20 Å, IHM assembly, unverified
  6-chain assignment).

## In Progress

None

## TODO

- [ ] Search RCSB for alternative apo β-cardiac myosin (MYH7)
      motor-domain crystal structures.
- [ ] Independently verify PDB 9GZ1 (ligand `XB2`=mavacamten, its
      companion apo structure, resolution, chain composition) — the
      2026-07-20 lead, not yet checked by this thread.
- [ ] Independently verify any apo candidate (resolution, chain ID,
      B-factor provenance) before adopting it.
- [ ] If found (either side): substitute in `config/targets.yaml`,
      re-run full pipeline.
- [ ] If not found: write the data-limited caveat into `RESULTS.md`/
      `COMPETENCE_MAP.md`, citing this task.

## Dependency

- Soft: should ideally re-run under whatever seed/clock conventions
  [[TASK-0118]]/[[TASK-0119]] land, if this task starts after them.
- None hard — the RCSB search itself can start immediately.

## Open Questions

- Whether any real apo β-cardiac myosin motor-domain structure at
  usable resolution actually exists on RCSB at all — genuinely unknown
  until searched; if none exists, (b) (data-limited reporting) is the
  only honest option, stated as such.

## Done

(not yet)
