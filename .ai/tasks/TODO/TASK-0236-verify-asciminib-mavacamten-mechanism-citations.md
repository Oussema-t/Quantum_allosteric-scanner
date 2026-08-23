# TASK-0236 Verify the asciminib/myristoyl and mavacamten/SRX mechanism citations

## Context

- ID: TASK-0236
- Title: DOI-verify the two per-target mechanism claims [[TASK-0233]] used
  as field-standard background without checking them, per
  `.ai/reference/PAPER_CITATION_PROTOCOL.md`.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: [[TASK-0233]]'s own Open Questions and Done section, both
  explicit: "Do the asciminib/myristoyl-autoinhibition and mavacamten/
  SRX-state mechanism claims actually verify against live DOIs...? Not
  checked when this task was filed." Filed on user instruction to check
  TASK-0230/0234 (and adjacent tasks) for unbuilt items worth verifying.
- Priority: P2 — small, bounded, cheap; not blocking any open
  computation, but a real citation-protocol gap left standing since
  2026-08-22.

## Why this matters

[[TASK-0233]]'s own per-target grounding (BCR_ABL1: asciminib mimics the
kinase's own natural myristoylation-based autoinhibition; CARDIAC_MYOSIN:
mavacamten stabilizes the naturally-occurring "super-relaxed" (SRX)
state) is field-standard structural-biology knowledge, but was used
without a checked DOI — exactly the "citation you remember is not a
citation you've checked" failure mode
`.ai/reference/PAPER_CITATION_PROTOCOL.md` exists to prevent. The KRAS
one (Ostrem 2013) is already verified and in `REFERENCES.md` [18]; these
two are not.

## Intent Contract

- Outcome: both claims either verified against a real, resolving DOI and
  added to `REFERENCES.md` (method/tool papers or challenge-bibliography
  table, whichever fits), or found unverifiable/wrong and the claim in
  [[TASK-0233]] corrected accordingly — either outcome closes this task,
  per this project's own "report negatives clearly" discipline.
- In Scope:
  - Find and verify a real paper establishing asciminib's mechanism as
    myristoyl-pocket binding / mimicry of the kinase's own natural
    autoinhibited (myristoylated) conformation.
  - Find and verify a real paper establishing mavacamten's mechanism as
    stabilizing the myosin super-relaxed (SRX) state.
  - Add both to `documentation/REFERENCES.md`'s method/tool papers table
    (or challenge bibliography table if either turns out to already be
    one of the challenge's own [1]-[25] references — check before
    assuming it's a new entry), following this project's own established
    row format (citation, DOI, status tag, one-line takeaway in this
    project's own words, task link back to this task and [[TASK-0233]]).
  - If either claim does not verify as stated, correct [[TASK-0233]]'s
    own text with an explicit, dated correction note (matching that
    task's own established pattern for corrections, e.g. its own
    [[TASK-0234]]-driven correction already in its Done section) — do
    not silently leave a wrong claim standing.
- Out Of Scope:
  - Re-verifying Ostrem 2013 (KRAS) — already done, [[TASK-0227]]'s
    Source line, `REFERENCES.md` [18].
  - Any new scientific claim beyond confirming/correcting what
    [[TASK-0233]] already stated — this is a verification task, not a
    literature-review expansion.
- Constraints And Invariants: follow
  `.ai/reference/PAPER_CITATION_PROTOCOL.md` exactly — verify the DOI
  resolves to the claimed paper (title/authors/journal/year/claim) before
  adding any row, same bar [[TASK-0229.004]]/[[TASK-0156]] already met.
- Planned Validation: each DOI added must actually resolve (checked live,
  not assumed) and the linked paper's own abstract/summary must support
  the specific mechanism claim being cited, not just the drug name.

## Done

(not yet)
