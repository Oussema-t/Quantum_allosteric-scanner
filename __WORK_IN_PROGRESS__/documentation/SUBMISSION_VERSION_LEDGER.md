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

## V3 revisions — the instrument spine ([[TASK-0362]], 2026-09-09)

| change | why | must not regress |
|---|---|---|
| Apo-vs-stripped-holo promoted from **Phase-2 proposal to delivered result** | [[TASK-0345]] ran it on 2026-09-07/08 and the document still said "we expect to report it": 63 pairs / 59 distinct proteins, **+0.199** mean, median +0.184, Wilcoxon p=2.6e-4, sign-flip permutation p<1e-4, bootstrap 95% CI **[+0.102, +0.296]**, same sign in both source cohorts | **Never demote it back to a proposal.** And **keep the n=63 caveat** — the ≥100 stays a Phase-2 target rather than being quietly dropped to make the result look finished |
| §1 count "Four measurements" → **"Five"** | the delta is an instrument finding, not a method result, and belongs beside the contamination audit | Keep it in §1, not in the Phase-2 table |
| §4 impact-table baseline cell now reads **"Done at n = 63"** | the row previously advertised a gap we had already closed | Do not restore "Not reported in the literature we surveyed" as *our* status — it remains true of the literature, not of us |
| §5: **protein-identity floor** added as a second floor | [[TASK-0359]]/[[HYP-P28]] — a constant-per-protein score with zero site information reaches **AUC 0.65**, p<5e-5, reproduced on 54 proteins added afterwards | **Keep the immunity sentence.** The floor bites on *pooled* AUC; per-structure metrics — including every number in this document — are immune by construction. Overstating its reach would be the exact error we criticise elsewhere |
| §4: detector cascade added beside the 84% decomposition | [[TASK-0360]] — 94.8% flagged by ≥1 of four detectors, **24.0%** by all four | Keep the *mechanism*, not just the ratio: PocketMiner answers a different question (pockets that open) from the other three's static-cavity geometry. Without that, it reads as noise |
| Phase-2 table row (b) removed; §2 sentence rewritten | (b) is delivered, so listing it as a component to build was stale — and removing it paid the page budget for the §1 promotion | Components (a) and (c) are what remain |
| "§1" cross-reference removed from §2 | house style: no section-symbol cross-references in the shipped document | No § cross-references |
| §5: the aggregation convention stated as **audited**, not argued | [[TASK-0361]] classified every number in the document with `file:line` citations and found **no pooled AUC among our own claims** | Keep the word "audited". The earlier wording was an argument from construction; this is a checked fact, and that difference is the point of the paragraph it sits in |
| §2: **inherited family labels** caveated where 276 appears | the external branch found its 399 "families" are labels from five source datasets, not one clustering — and [[TASK-0336]]'s 276 derives from that same artifact | **Keep both halves**: the absolute count depends on the convention, the McNemar comparison does not, because it is paired over the same families. Do not drop the second half — without it the caveat reads as a retraction |

## V3 human review pass (2026-09-10)

Nine edits from a line-by-line read of the built PDF. Every one traceable to a reader question the text failed to answer.

| change | why | must not regress |
|---|---|---|
| The "2 of 7" targets **named**: three from Table 1 (KRAS G12C, BCR-ABL1, cardiac myosin), four drawn by us from the Allosteric Database | a reader could not tell what the seven were, and guessed "4 apo + 3 holo" — a reasonable guess the text invited | Name the two sets. The number alone reads as arbitrary |
| **Correction:** "we did not choose them; Table 1 and the source database did" → we chose the four database entries, not the three mandated | the old sentence overclaimed. The challenge names the database ([[TASK-0209]], §6); it did not pick the entries | **Never restore the stronger wording.** The point survives without it: the failure spans both sources |
| 49% failure modes added: of the 32 failures, **19 both-miss, 10 apo-already-open, 3 inverted** | a reader can otherwise suspect the rule trivially passes apo and fails holo. It does not — the dominant failure is no pocket in either half ([[TASK-0346]]) | Keep the breakdown. It is what makes 49% a finding rather than an artifact |
| c-Myc reframed as a **prospective, unverified prediction** | "we report it together with its lack of validation" read as apology; the challenge asks for a prediction on a target with no holo, which is exactly what we give | Keep "unverified" as a label, not a hedge |
| "we measured the gap nobody reports" → **"a gap we have found no report of"** | we have not read all of the literature and must not imply we have | Never claim exhaustive literature coverage |
| Organiser-clarification paragraph trimmed | it explained our reasoning about a reader rather than stating the facts | Facts about the deviations, not narration about the reader |
| "generalise across the ensemble" **bolded** | it is the verdict of the whole section and was set in body weight | Keep the emphasis |
| *Family* defined in-place: groups structures of the same protein, so a protein deposited many times counts once | the count is load-bearing and the term was never defined | Define it where the count first carries weight |
| (a) and (c) named inline; **LOPO expanded** on first use | both were referenced before being introduced | Expand an acronym at first use, name components where invoked |

## V3 → V4 (current)

| change | why | must not regress |
|---|---|---|
| **§6: an AI stage, with both models** — topology→MIN_HOP (near/distal AUC **0.793**; **0.924 vs 0.901** running at the predicted distance) used; topology→operator (**0.625 vs 0.630**, 13 vs 15 families) reported as a negative | "AI workflows" is Submission Guidelines item 6 and asks how the *method* integrates AI — scored 5%. Our §6 architecture had no AI stage; the existing AI paragraph is about *authoring* | **Keep both models.** Reporting only the negative understates the work; reporting only the positive would be the failure this whole document argues against. Keep the cohort (597/380 — not the 630/399 used elsewhere) |
| **§6: the funnel ablation**, including that AUC *rises* (0.576→0.626) while the strict hit count falls 48→6 | the base rate drops 0.33→0.070; AUC is prevalence-insensitive and P@5 is not, so **AUC conceals the collapse** | Keep the AUC half. The hit-count drop alone is the weaker version of the finding |
| **§7: "not as a credential" defence removed** | it argued with an imagined objector; the facts carry it | Do not re-add a defensive clause. State what the register caught and stop |
| V3 kept on disk; V4 is a new file | version-history convention — see the improvement, don't lose what was being fixed | Never edit a shipped version in place |
| Phase-2 components **relabelled (a)/(b)**, and the removed one described in prose | [[TASK-0362]] deleted the (b) row but left (a) and (c), so a reader asks "what was (b)?" — and the trailing sentence called the delta the *third* component when it was the second | **Keep the letters contiguous.** If a component is ever delivered and removed again, renumber and say in prose what left |
| `fpocket` described as **interchangeable**, pointing at the detector-agreement measurement | naming one detector in the dependency list reads as a commitment we have not made — and we measured detector disagreement two sections earlier ([[TASK-0360]]) | Keep the pointer. The cascade is the reason the choice is open, not a hedge |

**Numbers borrowed from `origin/allosteric` were read from its own committed files, not from the summary we were given** — which understated their own results in three places ([[TASK-0365]]).

---

## Open, not yet in any version

| item | source |
|---|---|
| Structure rationale, and citing the 2026-08-26 clarification | [[TASK-0351]] — organisers asked for it explicitly |
| Merge contributions from the `allosteric` branch: stage ablation, centrality ablation, recommender-as-negative | collaborator reply, 2026-09-09 |
| `+0.031` matched-twin result | **held** pending a spectrally-matched control — `p_avg` is phase-free by [[TASK-0130]], so `p_avg` vs heat kernel differs in spectral weighting, not interference |
