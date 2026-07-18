# TASK-0137 Citation verification audit: fetch, transcribe, and pin every load-bearing external reference to a precise location

## Context

- ID: TASK-0137
- Title: this project's reviews, hypotheses, and task files cite a
  growing list of external academic references (quantum-walk mixing-time
  bounds, protein-network spectral-dimension results, linear-response/
  perturbation-scanning methods, GNM transfer-entropy baselines, the
  challenge statement's own 25-reference bibliography) as scientific
  grounding — **none of them have been independently verified to exist
  or to say what's claimed**, by this thread or, as far as can be
  determined, by anyone upstream in this session's chain of reviews.
  Fetch each (preferring arXiv/open-access), transcribe to a cheap-to-
  read format (reusing `tools/pdf_to_md_exporter.py`'s already-
  established pattern), and replace every bare `Author, Journal, Year`
  citation currently in this project's own docs with a precise pointer
  (page/section/equation) into the transcribed text.
- Status: TODO
- Owner: Implementer (needs `WebFetch`/`WebSearch` tool access — flag if
  unavailable in whatever environment picks this up, per this task's own
  Open Questions)
- Claimed By: —
- Claimed At: —
- Source: raised directly by the orchestrating user, 2026-07-18, in a
  reflective discussion about how much of this project's own confidently-
  stated content ("bullshit believed to be true by the writer") has
  actually been checked versus merely sounded right and gotten repeated.
  This Architect/Planner thread's own honest accounting in that
  discussion: "I have not independently confirmed a single one of these
  actually exists and says what's claimed... a citation gets stated
  confidently once, sounds right, fits the narrative, and then gets
  repeated by the next thread as established grounding."
- Priority: **P1.** Does not block any currently in-flight compute task,
  but directly bears on whether several of this week's task
  specifications (most acutely [[TASK-0132]] and [[TASK-0015]]/
  `HOLO_DIRECTION_MODULE.md`) are built on real method descriptions or on
  a plausible-sounding paraphrase of one.

## Intent Contract

- Outcome: for each citation in the list below (not exhaustive — this
  task's own first step is compiling the complete list, see TODO), (1)
  locate a real, legitimately-obtainable copy — **arXiv preprint
  preferred** (openly available, matches this project's own existing
  `tools/pdf_to_md_exporter.py` pattern); where no arXiv version exists,
  use a legitimate open-access copy (PubMed Central, the journal's own
  OA policy — several of these are published in PLoS Comput Biol,
  fully OA by the journal's own policy) — **do not use a paywall-bypass
  or unauthorized copy of anything that isn't legitimately open**; (2)
  transcribe to Markdown via the existing exporter pattern; (3) confirm
  the paper exists, is correctly attributed (right authors/venue/year),
  and actually states what this project's citing document claims it
  states; (4) update the citing document (task file, hypothesis file,
  review) with a precise pointer — page number, section, equation, or
  quoted sentence — into the transcribed text, additively, per this
  project's no-silent-overwrite convention; (5) where a citation cannot
  be verified (no legitimate copy locatable, or the paper doesn't say
  what's claimed), report that explicitly and flag every place that
  citation is currently used as unverified, rather than silently leaving
  it looking authoritative.
- **Load-bearing citations to check first (compiled from this session,
  not exhaustive — Part 1 of this task's own TODO is completing this
  list)**:
  - Aharonov, Ambainis, Kempe, Vazirani — quant-ph/0012090 (arXiv ID
    already given in [[TASK-0109]]'s own text; the AAKV mixing-time
    bound this project actually implemented in
    `propagators.check_convergence(kind="time_averaged_ctqw")` —
    **highest priority, already load-bearing in shipped code**, not
    just cited in prose).
  - Godsil, "average mixing matrix" (§2.3, `REVIEW-panel-2026-07-17.md`)
    — the mathematical basis [[TASK-0130]]'s closed-form implementation
    rests on (spectral-idempotent grouping for degenerate spectra).
  - Reuveni, Granek & Klafter, PNAS 107:13696 — spectral dimension of
    protein contact networks, cited to justify why near-degenerate
    spectra are "the generic case, not a quirk" (§2.2 of the same
    review) — a claim this project has been treating as settled without
    checking.
  - Chennubhotla & Bahar, PLoS Comput Biol 2007;3:1716-1726,
    doi:10.1371/journal.pcbi.0030172 — cited **in the challenge statement
    itself** (ref [8]) and independently by [[TASK-0136]]'s own
    bottleneck-vs-distributed framing — DOI already known, PLoS Comput
    Biol is fully open-access.
  - Nussinov & Tsai, Cell 2013;153:293-305,
    doi:10.1016/j.cell.2013.03.034 — cited in the challenge statement
    (ref [3]) and [[TASK-0136]] — Cell may not be OA; check licensing
    before attempting transcription, flag if paywalled rather than
    circumventing it.
  - Zheng, Brooks, Thirumalai, PNAS 103:7664 — soft-mode/allosteric-
    signaling result cited by [[TASK-0122]]'s own `CP_low` specification
    as the expected signature of real structure.
  - Ikeguchi, Ueno, Ota, Kidera, PRL 2005 (Linear Response Theory) and
    Atilgan & Atilgan, PLoS Comput Biol 2009 (Perturbation Response
    Scanning), and Das, Gur, Cheng, Jo, Bahar, Roux, PLoS Comput Biol
    2014 (two-state ANM) — the entire method basis
    `HOLO_DIRECTION_MODULE.md`/[[TASK-0015]] rests on, currently shelved
    but worth verifying before it's ever picked back up.
  - Hacisuleyman & Erman, PMID 28241380, and Kaynak & Bahar, J Mol Biol
    2022, PMID 35644497 — [[TASK-0132]]'s entire premise (GNM transfer
    entropy as a classical baseline) rests on these being real and
    correctly described; **this task's own Context already flags these
    as unverified** — resolve before or as part of TASK-0132, whichever
    lands first.
  - The Cleveland Clinic Challenge Statement's own 25-reference
    bibliography (`documentation/Cleveland-Clinic-Challenge-Statement-
    vF-1.md`) — lower priority (an official, curated document, not
    LLM-generated), but in scope for a spot-check, not exempted just
    because it's the source-of-truth document.
- In Scope:
  - Fetching, transcribing, and cross-checking the citations above and
    any others found while compiling the complete list.
  - Updating citing documents with precise pointers, additively.
  - Reporting any citation that cannot be verified or does not say what
    was claimed — a real, publishable finding in this project's own
    terms, not a failure to hide.
- Out Of Scope:
  - Re-deriving or re-implementing anything based on a verified paper's
    method beyond what's already specified in the citing task — this
    task verifies grounding, it does not do the science the grounding
    supports.
  - Papers with no legitimate open-access path — flag and stop, do not
    seek an unauthorized copy.
- Constraints And Invariants: transcribed papers are third-party
  copyrighted work, not project-authored content — store outside version
  control (extend the existing `documentation/*.pdf`/`documentation/*.md`
  `.gitignore` precedent to wherever these land, e.g.
  `documentation/references/`) and do not commit them, matching how the
  challenge-portal PDFs are already handled.
- Planned Validation: each citation's verification record (exists/
  doesn't, says-what's-claimed/doesn't, precise pointer or explicit
  unverified flag) is itself the validation artifact — report all of
  them, not only the ones that confirmed cleanly.

## In Progress

None

## TODO

- [ ] Compile the complete citation list across every review, hypothesis,
      and task file in this project (not just the ones named above).
- [ ] For each: locate a legitimate copy (arXiv preferred, OA journal
      copy otherwise), transcribe via `tools/pdf_to_md_exporter.py`'s
      pattern, store under `documentation/references/` (gitignored).
- [ ] Confirm existence, correct attribution, and that the paper says
      what's claimed.
- [ ] Update each citing document with a precise page/section/equation
      pointer, additively.
- [ ] Report any citation that fails verification (not found, wrong, or
      paywalled with no legitimate OA path) explicitly, and flag every
      place it's currently used.
- [ ] Extend `.gitignore` for the new `documentation/references/` path.

## Dependency

- None hard. Soft: coordinate with whoever picks up [[TASK-0132]] (GNM-TE
  baseline) or [[TASK-0015]] (holo-direction module) if either starts
  before this lands, since both rest directly on citations this task
  verifies.

## Open Questions

- Whether `WebFetch`/`WebSearch` (or equivalent internet access) is
  available to whichever thread picks this up — this Architect/Planner
  thread has not itself attempted a fetch in this session; if
  unavailable, this task cannot proceed as scoped and should be flagged
  back rather than silently attempted with a fabricated substitute.
- Licensing details for non-OA journals (Cell, PNAS's embargo window) —
  Implementer's own first check per citation, not pre-researched here.

## Done

(not yet)
