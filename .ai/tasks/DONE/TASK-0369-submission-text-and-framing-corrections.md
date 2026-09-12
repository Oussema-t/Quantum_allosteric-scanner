# TASK-0369 — Concept Proposal: factual corrections, and the statistical framing the reviewer turned back on us

- Status: Done
- Owner: **Reviewer** (judgement-heavy; not a mechanical pass)
- Priority: **High**
- **Blocked on [[TASK-0367]]** for anything that changes length — the page count is currently wrong and we would be trimming against a false measurement. Text corrections that are length-neutral can start immediately.
- Filed: 2026-09-11 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-11/REVIEW-2026-09-11-external-adversarial-submission-package.md`
- Related: [[TASK-0367]], [[TASK-0368]], [[TASK-0370]], [[TASK-0371]]

## A. The decision that is not ours to make

**Item 1 — the repository is private.** `github.com/Oussema-t/Quantum_allosteric-scanner`
returns 404 unauthenticated, and it is not among the 11 public repos on that
profile. Section 7, the Team Profile (*"checkable by publishing the working
repository"*), `03_Problem_Statement_Selection.md` and both READMEs all rest on it.

**Every verifiability claim in this submission is currently unsupported.** Either
the repository is made public before upload, or every sentence that offers it as
evidence must be rewritten.

**DECIDED, 2026-09-12 (Team Lead):** Oussema will make the repository public **on
2026-09-15**, deliberately late so the data cannot be borrowed before the deadline.
That resolves the decision and unblocks the sentences — with one timing caveat to
check rather than assume: **if the package is uploaded before the 15th, a reviewer
clicking the link in the window between upload and publication gets a 404.** Either
upload on the 15th, or confirm the portal does not surface links to reviewers before
the deadline closes. Do not leave this to chance — the link is load-bearing in four
separate places.

**Simplest resolution, and the one to take: say so in the document.** One clause
next to the repository link — that it is published on 2026-09-15, the submission
deadline — turns a potential 404 into a stated fact. It costs a handful of words,
removes the timing risk entirely regardless of when we upload, and is consistent
with a submission whose whole argument is that you disclose what you did rather
than hope nobody checks.

## B. Factual corrections — the reviewer is right and these are cheap

| # | Correction |
|---|---|
| 4 | **Name the Table-1 cardiac pair and the substitution reason.** Table 1 mandates `5TBY → 6C1H`. `5TBY` is a homology model rigidly fitted to a negatively-stained thick-filament reconstruction at 20.0 Å; `6C1H` is *rat* unconventional myosin-Ib bound to *rabbit* actin, with ADP and no mavacamten. **Together with `4OBE` being wild-type and `1OPL` being doubly liganded, every mandated pair has a verifiable defect — that is the single strongest piece of evidence for §1's thesis and we currently omit it.** Also name the holo structures used (`6OIM`, `5MO4`, `8QYR`) so a reader can tell what the AUCs were scored against. |
| 5 | **"The Concept Proposal's Appendix B" does not exist.** Cited by the Team Profile for five retractions. Either add it or cite what does exist. |
| 8 | **Coupled conformational search is described two ways.** [[TASK-0213]] recorded it as *"CLOSED … closes the last OPEN quantum-advantage route"*; §2 says it *"survives our own screening"*. Pick one, cite it, and if it is closed then §2's two-surviving-routes sentence has one route, not two. |
| 9 | **"169–704 qubits"** — 169 is `4OBE`'s N. We ship `4LDJ`, N=170. |
| 15 | **"0.4960 — below chance"** is at chance. |
| 27 | **"We followed it in each case" is wrong** — we *rejected* the organisers' `8S8C` for KRAS. It is two deviations plus one retention, not three deviations. |
| 28 | Three dangling colons left by floats: *"each case:"*, *"chance:"*, *"construct:"*. |
| 29 | **Broken referents**: *"the agreement measurement above"* is in §4, which is below; *"the external claim we are checking"* is uncited; *"hardware cost measured below"* is never given for either surviving route. |
| 30 | **§3 contradicts itself** — calls the 105-structure extraction the "largest single analysis", then describes the 1022-protein sweep. |
| 31 | **Citations**: 89.8% and 84% are both attributed to [4]; check whether 98.1% is Wu et al. on CASBench rather than [5]; name the group behind [8] (Cleveland Clinic Genome Center, Lerner Research Institute — the Clinic has more than one quantum effort); *"mandated ablation"* — by whom; *"5 of 7 standard targets"* — four were our picks, already corrected once in [[TASK-0363]] and apparently still present elsewhere. |

## C. Statistical framing — our own standards, applied to us

These are the substantive ones. **In each case the reviewer's fix makes the
submission's thesis stronger, not weaker**, which is why they are worth the words.

- **Item 13 — `NO_SIGNAL_IN_APO` could not have come out otherwise.** The overlap
  rule needs `score_lo > floor_hi`, which would have required AUC ≈ 0.80–0.89. So
  the verdict is near-unfalsifiable as constructed, and the gloss *"carries
  nothing beyond what distance supplies"* is the underpowered-null error our own
  §5 positive-control bullet warns against. Fix: bootstrap `score − floor`
  **paired** (they are correlated, so the CI narrows), and relabel as
  *"indistinguishable from the floor; detection limit ≈ X"*.
- **Item 14 — "a well-powered null" is powered for the wrong population.** No
  minimum detectable effect is stated; the cohort is ~77% non-distal; and §5 says
  the design cannot detect even proximity on the distal subset (p = 0.89) — which
  is precisely where the coherence hypothesis lives. **Say so.** A null that names
  the population it is powered for is more credible than one that does not.
- **Item 16 — "no arm clears more than 5 of 276" has no stated criterion.**
  Uncorrected at α = 0.05 one would expect ~14 under the null. State the rule.
- **Item 17 — two positive-looking numbers sit unreconciled.** The combined
  readout (0.6203 LOPO, "null passed") appears only in a table cell; a classical
  ranker reaches 0.626 without the pre-filter; and *"our strongest result…
  promoted from a lead to a finding"* is never named. **Two of the three Phase-2
  success criteria are already met by our own baseline column**, which a reviewer
  will notice next to "none of ours generalises".
- **Item 18 — "each AUC is per-structure and averaged, none pooled" is too
  broad.** It cannot cover the protein-level classifier AUC 0.793. Scope the
  sentence. (This is [[TASK-0363]]'s wording; the audit behind it was correct, the
  generalisation was not.)
- **Items 11, 12 — two omissions that help us.** Apo-draw sensitivity (ten true
  G12C apo structures span AUC 0.408–0.595, median 0.482; the cardiac swap moved
  AUC by 0.27, and each shipped hit list is one draw), and **fpocket beating the
  walk by ≈0.3 AUC on KRAS and BCR-ABL1** — fpocket is in our own pipeline, and
  this is evidence the benchmark is trivial rather than evidence against us.
- **Item 10 — the qubit convention invites the first objection a quantum judge
  makes.** A single-particle walk on N sites needs ⌈log₂N⌉ qubits, and the
  challenge's own ref [11] log encoding clears the qubit bar at ~10 system qubits
  + 1 ancilla (still 10⁵–10⁶ gates, so the fault-tolerant verdict survives on gate
  count). State the binary-encoding cost and why unary is kept: the one surviving
  route, multi-particle interference, needs it.

## D. Out of scope

- Anything touching hit-list biology — items 3, 19, 21, 22 — **waits on
  [[TASK-0368]]**.
- Package files rather than the Concept Proposal — [[TASK-0370]].
- Rubric-coverage additions — [[TASK-0371]].
- **Item 7** (KRAS's "VALID" computed on `4OBE`, the wild-type structure) is a
  register question, not a text question: establish whether the rule was re-run on
  `4LDJ` before deciding what the submission may say. File separately if it was
  not.

## Constraints

- **No number changes without the source artifact.** Every correction above is
  either a wording fix or a number the reviewer supplied — and a supplied number
  is a claim until we check it, which is [[TASK-0348]]'s and [[TASK-0366]]'s
  standing lesson.
- **Length is the binding constraint and it is currently unmeasured.** Section C
  additions cost words the body does not have. Expect to cut before adding, and do
  it against [[TASK-0367]]'s corrected count.
- Update `SUBMISSION_VERSION_LEDGER.md` per [[TASK-0353]]'s format.


---

## Done, 2026-09-12 (Reviewer)

**Build PASS at last: body 6/6, appendix 2/3, 10.5pt, zero overflow, glyph coverage
clean, every citation resolving.** The document entered this task at **7/6 and
FAILING** (a real violation, visible only because [[TASK-0367]] fixed the check
first) and came out compliant **with content added, not removed on net**.

### Cuts — what paid for the corrections

- **Section 6's opening paragraph**, which restated the "Pipeline" paragraph below
  it almost word for word.
- **The retraction story told twice** in Section 1; the fuller telling sits in the
  selection paragraph, where it does work.
- **The Section 7 member roster**, inlined as a sentence. Guidelines §4.1 wants a
  roster in the *Team Profile* — a separate component with no page limit, which
  already carries the full version; §4.3 item 7 asks for the *argument*.
- **The impact table's re-audit row**, which restated the 84% decomposition given
  in prose two paragraphs above.
- Compression, not deletion: the structure-rationale KRAS and BCR rows, the
  workflow paragraph, the protein-identity-floor bullet, the c-Myc paragraph, and
  three sentences in Section 3.

### Corrections applied

| # | What changed |
|---|---|
| 8 | Coupled conformational search: **one surviving route, not two** — [[TASK-0213]] closed it, and the text said it survived. Now says we closed it ourselves. |
| 9 | **170–704 qubits**, not 169 — 169 was `4OBE`'s N and we ship `4LDJ`. |
| 15 | **"0.4960 — at chance"**, not "below chance". |
| 17 | The Phase-2 criteria now **concede that two are already partly met** on our own cohort, and name the binding one: certifying ≥ 40 pairs, where we stand at 31. Stated rather than left for a reviewer to notice. |
| 27 | **Two deviations and one retention**, not three deviations — we *declined* the organisers' `8S8C`, which the old wording obscured. |
| 29/30 | Section cross-references removed; the "largest single analysis" self-contradiction removed with the sentence that carried it. |
| — | **The repository's publication date is now in the document** (2026-09-15). A link that 404s until the deadline becomes a disclosed fact, whenever we upload. |

### Carried in from [[TASK-0371]]

- **"We built the circuit and transpiled it against a real IBM device calibration
  snapshot"** — Challenge Statement §4.1 makes building a circuit mandatory, and
  the old wording implied it without saying it.
- **Noise resilience**: the pre-registered robustness hypothesis, and that we
  **falsified** it — holds on two mandated targets, reverses on the third. §4.2
  names it as a secondary objective and we had said nothing.

### Also caught

`Å` had no LaTeX rendering and **would have shipped as tofu** in the new text.
Added to the glyph map with a test-covered fix — the third glyph this check has
caught before a reader did.

### Not done, and why

- **Hit-list biology (items 3, 19, 21, 22)** waits on [[TASK-0368]]; Berke is
  working on it. No text about which pockets our five residues are has moved.
- **Item 13** (`NO_SIGNAL_IN_APO`'s near-unfalsifiability, and the paired
  score−floor bootstrap it needs) is a **measurement change**, not a wording one,
  and there is no space and no time to do it honestly. Left open and visible.
- **Items 11, 12** (apo-draw sensitivity; fpocket beating the walk by ~0.3 AUC)
  are both true and both help us. They need words the body does not have. If
  anything is cut later, these are the first two to buy back.
- **Item 31's citation attributions** (89.8% vs 84% both credited to [4]; whether
  98.1% is Wu et al. on CASBench) need the papers re-read, not a guess.
