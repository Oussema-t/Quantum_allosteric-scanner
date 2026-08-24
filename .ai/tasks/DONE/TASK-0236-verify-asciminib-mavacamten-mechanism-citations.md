# TASK-0236 Verify the asciminib/myristoyl and mavacamten/SRX mechanism citations

## Context

- ID: TASK-0236
- Title: DOI-verify the two per-target mechanism claims [[TASK-0233]] used
  as field-standard background without checking them, per
  `.ai/reference/PAPER_CITATION_PROTOCOL.md`.
- Status: Done
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

**2026-08-24.** Both claims verified, both stand as stated — no
correction needed.

**Picked up as a stale claim**: claimed by a prior session
(`Implementer B`, 2026-08-23 06:40) with zero recorded progress after
>1 day, no matching active peer session (checked via the agent
directory), and no `COMMON.md` trace of work started — force-claimed
per `.ai/tools/claim.py`'s own override protocol, reason logged in the
claim history.

**Asciminib / myristoyl-pocket autoinhibition (BCR_ABL1)**: Wylie AA,
Schoepfer J, Jahnke W, et al. "The allosteric inhibitor ABL001 enables
dual targeting of BCR-ABL1." *Nature*. 2017;543:733-737,
doi:10.1038/nature21702. Verified via Crossref (title/authors/journal/
volume/pages all match exactly, independent of any search-snippet
paraphrase) and the abstract/summary directly supports the specific
claim [[TASK-0233]] cited: ABL001 (asciminib) binds the kinase's own
myristoyl pocket (found via fragment-based NMR + a conformational-NMR
assay), engaging the kinase's natural autoinhibitory mechanism rather
than competing at the ATP site — not just "asciminib is a real drug,"
the mechanism claim itself.

**Mavacamten / super-relaxed (SRX) state (CARDIAC_MYOSIN)**: Rohde JA,
Roopnarine O, Thomas DD, Muretta JM. "Mavacamten stabilizes an
autoinhibited state of two-headed cardiac myosin." *PNAS*.
2018;115:E7486-E7494, doi:10.1073/pnas.1720342115. Verified via Crossref
(same fields, exact match) and the abstract's own claim is the mechanism
directly, not merely adjacent: the drug enhances an autoinhibited myosin
state whose kinetics/energetics match the SRX state previously observed
only in intact sarcomeres.

**Neither claim required correction** — both `REFERENCES.md`'s
per-target grounding lines in [[TASK-0233]]'s own filing turn out to be
accurate field-standard claims, not remembered-but-unchecked ones that
happened to be wrong. Added both to `REFERENCES.md`'s method/tool papers
table (neither is one of the challenge's own [1]-[25] references —
checked against the challenge bibliography table first, not assumed).
[[TASK-0233]]'s own Open Questions entry marked resolved with a dated
note, matching that task's own established correction-note pattern (no
retraction needed here, unlike its [[TASK-0234]] entry — this one closes
clean).

**Not done, per this task's own Out Of Scope**: no new scientific claim
beyond confirming what [[TASK-0233]] already stated; Ostrem 2013 (KRAS)
was not re-verified (already done, [[TASK-0227]]).

**Validated**: both DOIs resolve live (checked 2026-08-24, not assumed
from memory or a prior session's claim); both confirmed via Crossref's
structured metadata (authoritative bibliographic registry), not only
search-engine snippets — the stronger of the two verification tiers this
project's own citation protocol distinguishes. `check_references.py`
clean on both edited task files.
