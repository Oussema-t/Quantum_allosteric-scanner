# Submission version ledger

**Internal artifact — not shipped to the organisers.** Companion to
`REVIEW_TARGETS.md`.

Records, per version: **what changed · why · what must not regress.** Deliberately
not a diff. A diff shows *what*; the reason this file exists is that the *why* was
scattered across a dozen task files and two adversarial reviews, and a later editor
undid a correction without knowing it was one.

**The incident that prompted it**: V2 was a ground-up rewrite and it silently
dropped **c-Myc**, a mandated minimum-set target that V1 had deliberately added
four days earlier ([[TASK-0339]]). Caught by the repo owner, not by us.

**How to use it.** Before shipping any version, read the *Must not regress* column
end to end against the current draft. That check is the whole mechanism.

## Files on disk, oldest first

| file | status |
|---|---|
| `ARCHIVE-PHASE1_SUBMISSION_DRAFT-v0.md` | superseded; still carries the MYR error — do not quote |
| `PHASE1_SUBMISSION_V1.{md,html}` | superseded |
| `PHASE1_SUBMISSION_V2.{md,html}` | superseded |
| `PHASE1_SUBMISSION_V3.md` | **current**, LaTeX route |

Prior versions stay on disk deliberately: deleting them destroys the comparison
this ledger exists to make.

---

## v0 → V1

| change | why | must not regress |
|---|---|---|
| Restructured onto the mandated seven-item ToC | Guidelines §4.3 mandates seven items; the previous draft followed the six assessment criteria, so a reviewer looking for item 4 would not have found it | **ToC stays exactly 7 items** |
| §8 "Attack these first" moved to `REVIEW_TARGETS.md`; reviewer front-matter removed | ~758 words addressed to an internal reviewer, in a document going to a panel; §8 also sat *after* the appendices | No internal review-solicitation, no draft/deadline banners |
| c-Myc subsection added | challenge §6: c-Myc is in the **mandated minimum set** | **Never drop c-Myc** |
| `PHASE1_SUBMISSION_DRAFT.md` archived | two files named like the submission, one carrying the MYR error | Only one file is "the submission" |
| §7 repo statistics regenerated | claimed 338/310/549, actual 355/326/579 | Regenerate at freeze; pin a SHA |
| §6 diagram drawn, "OPEN" box deleted | a 5%-weighted section consisting of an admission that its deliverable was unbuilt | §6 never ships as a disclosure of its own absence |

## V1 → V2 (ground-up rewrite)

| change | why | must not regress |
|---|---|---|
| **c-Myc dropped** | regression — unintended | **Restored. This is the case this ledger exists for.** |
| MYR reframed as the physiological autoinhibitor | `1OPL` carries myristate, the autoinhibitory ligand of that exact pocket and the reason the structure was solved — the draft had called it "an unexplained ligand", inverting our own best example | **Never "unexplained"** |
| cryptic/allosteric taxonomy corrected | orthogonal axes, conflated throughout; mavacamten's site is allosteric, not cryptic, and not a single-molecule property | Keep the axes separate |
| Every finding given its consequence in-sentence | findings were stated without answering "so what?" | Each finding states its consequence |
| Prior art cited; delta stated | a JACS paper (Mohtashim, Sajjan & Kais, July 2026) published essentially our construction, reporting ρ≈0.95 vs eigenvector centrality | **Always cite it and state our delta** |
| "No quantum work exists here" never claimed | the sponsor's own group published one (Zhang et al., Cheng senior author) | **Never claim the domain is untouched** |
| Five ranked residues per target added, with our own verdict | the mandated hit list is five per protein and the draft gave none | Keep all four targets' five |
| `NO_SIGNAL_IN_APO` glossed | undefined jargon in a shipped document | Define it where first used |
| Generalisation paragraph added | explains why near-chance numbers are reported and nothing beats them: 221 chances per target, and we took the best of them once and retracted it | Keep the "fits one protein / does not generalise" framing |
| 15 verified citations | the draft cited nothing, in a document arguing about what the field has measured | Citations stay |
| QA-credential paragraph cut | "fourteen years of QA" is not evidence; what the method *caught* is | No credentials as argument |

## V2 → V3 (current)

| change | why | must not regress |
|---|---|---|
| §1: "1 of 3 / 1 of 4" → **"2 of 7, and 49% across 63 pairs"** | [[TASK-0346]] — the strong claim did not survive scale | **Do not restore the stronger wording.** The supported claim is that the *mandated targets* are unrepresentatively bad |
| §2: coherent-vs-decoherent result added | [[TASK-0350]] — +0.0023 AUC, p=0.92, cluster-p=0.83, 108 structures / 76 clusters | Report it as a **well-powered** null, not merely a null |
| §2: the phase-free chain stated | [[TASK-0130]] proved the converged limit is phase-free; [[TASK-0140]]/[[TASK-0146]]/[[TASK-0157]] were built to reach past it | Keep the chain — it is what turns an external criticism into our own prior finding |
| §2: ρ-to-proximity ordering added (0.953 / 0.735 / 0.692) | the walk is measurably less of a distance proxy than classical diffusion; what it adds is not coherence | Keep both halves — the effect *and* that it is not coherence |
| §5: finite-T convergence check added | [[TASK-0350]] — 50/108 verdicts flip between T=15 and the converged limit | Keep; no published lineage reports this check |
| References moved to the appendix | [[TASK-0349]] fixed the appendix split; §4.4 names references as appendix-eligible | References stay out of the 6-page body |

---

## Open, not yet in any version

| item | source |
|---|---|
| Structure rationale, and citing the 2026-08-26 clarification | [[TASK-0351]] — organisers asked for it explicitly |
| Merge contributions from the `allosteric` branch: stage ablation, centrality ablation, recommender-as-negative | collaborator reply, 2026-09-09 |
| `+0.031` matched-twin result | **held** pending a spectrally-matched control — `p_avg` is phase-free by [[TASK-0130]], so `p_avg` vs heat kernel differs in spectral weighting, not interference |
