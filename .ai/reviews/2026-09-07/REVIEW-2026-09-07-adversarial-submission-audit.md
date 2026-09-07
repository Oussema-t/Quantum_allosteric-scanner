# REVIEW 2026-09-07 — Adversarial audit: submission readiness, v2 ingredients, archive growth

- **Reviewer**: external adversarial pass, working from the working-tree snapshot
  `Quantum_allosteric-scanner-bartosz__15_.zip` (45.4 MB, 1566 entries)
- **Scope**: submission-facing MD/HTML, TASK-0332's named v2 ingredients, archive
  size forensics
- **Deadline context**: 8 days to 2026-09-15
- **Note on method**: the archive contains **no `.git` directory**. The "what the
  commits say" question is answered below from artifacts, `.gitignore` semantics
  and file provenance, not from history. Two findings in Part 3 are stated as
  *high-probability, must-verify-with-one-command* rather than confirmed, and are
  marked as such.

---

## 0. Verdict in one paragraph

The scientific register is in better shape than the submission is. The last
week's work ([[TASK-0327]] through [[TASK-0336]]) is the strongest sequence in the
repo — it found the reference arm that was designed and never run, caught a
non-reproducible null seed, and turned a below-chance result into a measured
mechanism. TASK-0332 is the sharpest planning document here and its diagnosis is
correct on every item I checked. But **v2 does not exist**, three of the four
positives it wants to lead §2 with have defects that must be fixed *before* they
are written down rather than after, and one claimed criterion-2 asset (the
reproducibility container) will most likely fail on a cold clone. None of that is
fatal at 8 days. All of it is cheaper to fix now than to have a referee find.

**Scores as a Phase-1 panel would apply them, on the v1 text as it stands:**

| Criterion | Wt | Score | Why |
|---|---|---|---|
| Problem Relevance & Impact | 25% | **4** | The benchmark-audit framing is genuinely differentiated. Loses a point for the MYR inversion, which a structural biologist reads as not knowing the target. |
| Technical Approach & Innovation | 25% | **2.5** | §2 is 468 words and proposes four things without committing to one. The strongest positive ([[TASK-0318]]) is not in it. |
| Feasibility | 20% | **3** | §3 is 107 words for a 20%-weighted criterion. Correct content, no depth. |
| Validation Plan | 15% | **5** | Best section in the document by a distance. Nothing to add. |
| Hybrid / Cross-Domain | 5% | **1.5** | Section openly says the diagram is unbuilt and the demo contradicts the paper. |
| Team Capability | 10% | **3** | 709 words — the *largest* section for the *smallest* weight — and two of three bios are placeholders. |

---

## Part 1 — Why the archive went from ~15 MB to ~45 MB

### 1.1 The arithmetic

Compressed contribution, measured from the zip's central directory:

| Path | Compressed | Files | Note |
|---|---|---|---|
| `results/tasks/0336_matched_multiplicity_classical_comparison/` | **14.63 MB** | 14 | 94% of it is two files |
| `results/tasks/0318_input_space_ceiling/` | **10.88 MB** | 109 | 105 × `.npz` feature cache |
| `results/CARDIAC_MYOSIN/quantum_connectivity_matrix.npz` | 3.56 MB | 1 | pre-existing |
| `documentation/Cleveland-Clinic-Challenge-Statement-vF-1.pdf` | 4.10 MB | 1 | pre-existing |
| `results/BCR_ABL1/quantum_connectivity_matrix.npz` | 1.45 MB | 1 | pre-existing |
| everything else | ~8 MB | ~1440 | |
| **total** | **42.8 MB** | 1566 | uncompressed 63.7 MB |

**The delta is 25.5 MB, and it is two directories.** Both were created in the
2026-09-01 → 2026-09-06 window, which matches the [[TASK-0318]] and [[TASK-0336]]
filing dates exactly.

### 1.2 The two culprits, individually

**`0336/upstream_artifacts/` — 14.63 MB.** `r1_minhop2.json.gz` (10.7 MB) and
`r2_minhop2.json.gz` (3.9 MB), vendored verbatim from the collaborator's
`allosteric` branch at commit `8dcc6fa`. These are the round-1 and round-2 CTQW
cell matrices for all 1022 proteins — per protein, 221 Hamiltonian×score cells
with full per-seed rank vectors. They are *already gzipped*, so the zip cannot
compress them further; 14.6 MB in is 14.6 MB out.

**`0318/feature_cache/` — 10.88 MB.** 105 per-structure `.npz` files, the Phase-A
output of the 118-minute feature build. Deliberately committed (or at least
retained) so Phase B is re-runnable in ~118 s without re-paying Phase A.

### 1.3 The part that actually matters

Both directories sit under `__WORK_IN_PROGRESS__/results/`, which `.gitignore`
excludes:

```
__WORK_IN_PROGRESS__/results/
```

with **no negation pattern anywhere in the file** (verified: `grep '^!' .gitignore`
returns nothing). `documentation/*.pdf` and `documentation/*.md` are likewise
ignored, yet the Cleveland PDF is in the archive.

**Conclusion: this zip is a working-tree snapshot, not `git archive`.** The
growth is in *untracked or force-added* material, and roughly 25 MB of the 45 MB
may not exist in the public repository at all. That is not a size problem — it is
the reproducibility problem in Part 3.1, wearing a different hat.

### 1.4 Recommendation

Do not prune for size. 45 MB is irrelevant to a submission whose PDF limit is
20 MB and whose repo link is a URL. **Do** resolve the tracked/untracked question,
because the answer changes what a judge can run. If you want the size down anyway,
`0336/upstream_artifacts/r1_minhop2.json.gz` is 10.7 MB of collaborator data that
[[TASK-0336]] has already reduced to a 4 KB result JSON — a `PROVENANCE.md` naming
`8dcc6fa` and the fetch command would preserve auditability at 1/2500th the size.

---

## Part 2 — What is genuinely strong

Stated first and without hedging, because the rest of this document is criticism
and the balance would otherwise be misleading.

1. **`doc_parity.py` works and parity currently holds.** I ran it against the
   `.md`/`.html` twins: exit 0, no drift. Building a purpose-made content-parity
   checker (numbers, headings, identifiers, compared as sets, with unicode and
   superscript folding) instead of eyeballing two files is exactly the right
   engineering response to [[TASK-0307]]. It also has its own test file.

2. **[[TASK-0318]]'s robustness check is textbook.** The top feature by permutation
   importance was `euclid_prox` itself, at nearly 3× the next feature. The obvious
   objection — a high-capacity model reconstructing a nonlinear function of
   proximity that linear residualisation cannot strip — was *tested by refitting
   with both proximity columns deleted*, not argued away. The ceiling went **up**
   (0.5949 → 0.6017). The positive control lands at 0.5000 exactly, 105/105.
   That is as clean as this register gets and the phrasing "a lead, not a result"
   was honoured even after the check passed.

3. **[[TASK-0318]]'s pre-registration correction is rarer still.** The Reviewer
   thread went back and marked its own outcome table *wrong* — not the execution,
   the licensing it had written in advance — and reversed the build/don't-build
   recommendation on the strength of the task's own permutation importances. Very
   few registers contain a correction of that shape.

4. **[[TASK-0333]] found a real defect by building the container rather than
   reading it.** `FileNotFoundError` on `asbench_detection.json` — a second
   top-level `open()` invisible to inspection. It also cross-checked the headline
   in a second, non-container path before the Dockerfile existed. The
   `SEEDING_CONVENTION.md` write-up of the `random_state`-doesn't-advance pitfall
   is the kind of thing that saves a future session a day.

5. **[[TASK-0327]] is the single most valuable task in the last month.** The
   PASSer-only arm was specified in `PIPELINE_DESIGN.md` §S5 and never run. Finding
   the arm your own design mandates and your collaborator skipped — and running it
   — is the behaviour the Validation section claims, demonstrated rather than
   asserted.

6. **[[TASK-0334]]'s specificity control.** PASSer showing no distance correlation
   (all p > 0.17 across 8 combinations) rules out "distal pockets are just harder
   for everyone." The random arm correlating *positively* with distance while the
   pipeline correlates negatively is a genuinely persuasive piece of evidence.
   The scope statement ("this is within-distal dose-response, not a
   distal-vs-proximal contrast — there is no proximal half in this cohort") was
   volunteered as a finding from the validation step. That is the right instinct.

7. **[[TASK-0332]] itself.** The MYR diagnosis, the cryptic/allosteric orthogonality
   table, the mavacamten single-molecule point, the observation that the "ceiling"
   title overclaims in the direction that discredits the surrounding negatives —
   all correct, all things a referee would have found.

8. **The 2026-08-31 evidence pack.** A verify-only audit that edits nothing,
   labels `STALE` vs `MISSING` vs `CURRENT` vs `UNVERIFIED` separately, and traces
   to task files with commit SHAs rather than to `RESULTS.md`. Reusable as-is for
   the v2 numbers audit.

---

## Part 3 — Findings, severity-ranked

Verdict key: **BLOCKER** (do not submit with this) · **HIGH** (a referee will find
it and it costs points) · **MEDIUM** (fix if time) · **LOW** (hygiene)

---

### 3.1 — BLOCKER — the reproducibility container will most likely fail on a cold clone

`Dockerfile.pipeline` lines 75–80 COPY three paths:

```
__WORK_IN_PROGRESS__/results/tasks/0318_input_space_ceiling/feature_cache/
__WORK_IN_PROGRESS__/results/tasks/0304_asbench_casbench/asbench_annotations.json
__WORK_IN_PROGRESS__/results/tasks/0305_asbench_detection/asbench_detection.json
```

All three are under the `__WORK_IN_PROGRESS__/results/` ignore rule. There is no
negation pattern. The `.gitignore` comment itself explains the grandfathering
rule — *"Files already tracked before this fix stay tracked — gitignore does not
retroactively untrack anything"* — but `feature_cache/` was **created 2026-09-01
by [[TASK-0318]], ten days after the 2026-08-21 gitignore fix.** It cannot have been
grandfathered. It is tracked only if someone ran `git add -f`.

If it is not tracked, then on a fresh clone:

```
docker build -f Dockerfile.pipeline .
# => ERROR: failed to compute cache key: ".../feature_cache": not found
```

The build dies at COPY. Not a wrong number — a hard failure, in the first thing a
diligent judge tries.

TASK-0332's brief update says: *"[[TASK-0333]]'s container reproduces the §2
headline number byte-for-byte from a cold clone — state that in the reproducibility
section, it is a direct criterion-2 asset."* **Writing that claim into the
submission while the build is broken converts an asset into a liability.**
[[TASK-0333]]'s own validation ran on the authoring machine, where the untracked
files are present — which is precisely why it passed and why it does not settle
this.

Also note [[TASK-0318]]'s own Done section says the result JSONs are *"gitignored,
not committed"* — the task itself records the files as absent from git, and
[[TASK-0333]] later builds a container that COPYs from that directory. Nobody
reconciled the two.

**Verify in 30 seconds, from a clean clone of the public repo:**

```bash
git clone --depth 1 <repo-url> /tmp/coldclone && cd /tmp/coldclone
git checkout bartosz
ls __WORK_IN_PROGRESS__/results/tasks/0318_input_space_ceiling/feature_cache/ | wc -l
# expect 105. If 0 or "No such file", the container is broken for everyone but you.
```

**Fix**: add a negation block to `.gitignore` and force-add the three paths.

```gitignore
__WORK_IN_PROGRESS__/results/
# Exception (TASK-0333): the three inputs Dockerfile.pipeline COPYs. Without
# these a cold clone cannot build the container, which is the artifact the
# challenge's reproducibility requirement is scored on. ~11 MB, deliberate.
!__WORK_IN_PROGRESS__/results/tasks/0318_input_space_ceiling/
!__WORK_IN_PROGRESS__/results/tasks/0318_input_space_ceiling/feature_cache/
!__WORK_IN_PROGRESS__/results/tasks/0318_input_space_ceiling/feature_cache/*.npz
!__WORK_IN_PROGRESS__/results/tasks/0304_asbench_casbench/
!__WORK_IN_PROGRESS__/results/tasks/0304_asbench_casbench/asbench_annotations.json
!__WORK_IN_PROGRESS__/results/tasks/0305_asbench_detection/
!__WORK_IN_PROGRESS__/results/tasks/0305_asbench_detection/asbench_detection.json
```

(Directory-level negations are required — git will not descend into an excluded
directory to find an un-excluded file.)

Then re-run [[TASK-0333]]'s validation **from `/tmp/coldclone`, not from the
working tree**. That is the only run that tests what the claim asserts.

---

### 3.2 — BLOCKER — [[TASK-0334]] is the one recent result that breaks the register's own cluster discipline

This is the result TASK-0332 wants as §2's second positive and calls "a measured
mechanism, not a null." The mechanism is probably real. The statistics as reported
are not defensible under this register's own standing rules.

`distance_anticorrelation.py` computes Spearman ρ over **structures**. The
`cluster` column is present in the very CSV it reads
(`pocket_distance.csv`, columns: `name, source, truth_type, cluster, pdb, …`) and
the script never references it — `grep -n "cluster\|family\|fam"` returns nothing
outside the docstring. The result JSON has no cluster field either.

What that cohort looks like when you do count clusters:

| | rows | distinct clusters |
|---|---|---|
| full CSV | 1020 | 688 |
| `is_distal` subset (0334's universe) | **138** | **86** |
| asbench + curated_allosteric + distal | 49 | 37 |

And the concentration is severe: within the 138 distal rows, **`CAS0002` alone
contributes 28 — 20% of the cohort in one protein family.** `CAS0001` adds 8,
`CAS0040` 6.

So the reported ρ = −0.614, p = 9.3×10⁻⁶ at "n = 44" is over 44 correlated
structures, not 44 independent proteins. The effective n is smaller, plausibly
by a third or more, and the p-value is inflated accordingly.

**Why this is a blocker rather than a nitpick:**

- The register's identity is cluster-robust inference. Appendix A says *"Cluster-
  robust inference by structure — exact cluster-level permutation, after four
  selection procedures in our own register died of pseudo-replication."*
- [[TASK-0336]], **run the same day by the same owner**, states in its own README:
  *"Family-level counting is mandatory: e.g. CAS0061 = 33 structures,
  CAS0002 = 28 — one protein each."* Same cohort. Same trap. Named explicitly in
  one task and stepped into in the other.
- A referee who reads the repo — which you are inviting them to do — finds a
  §2 headline that violates the discipline §5 is built on. That is worse for the
  Validation score than not making the claim.

**Fix**: collapse to cluster medians before the Spearman, or run a
cluster-bootstrap / cluster-permutation p-value. The mechanism is strong enough
that it will very likely survive (ρ = −0.6 over ~30 clusters is still p ≈ 10⁻³).
Then report the **cluster-collapsed** number as the headline and the row-level one
as a footnote, not the reverse. This is a ~1-hour job on data already in the repo.

---

### 3.3 — HIGH — [[TASK-0336]]'s "classical beats CTQW on ALL" is a one-family difference with no error bar

TASK-0332's brief update presents this as decisive and uses it to exclude the
entire v2 pipeline result from the draft. The underlying numbers, from
`matched_comparison_result.json`:

| arm | ALL: observed | chance | `real_excess` |
|---|---|---|---|
| CTQW `hnew\|full\|p_avg` | 4 / 276 fam | 1.25 | +2.75 |
| CTQW `binary\|adj\|p_avg` | 4 / 276 | 1.25 | +2.75 |
| fpocket_drug | 5 / 276 | 1.25 | +3.75 |
| passer_rank | 5 / 276 | 1.25 | +3.75 |
| pocket_size | 5 / 276 | 1.25 | +3.75 |

**The entire claim is 5 versus 4.** One family.

`real_excess` is computed in `family_counts()` as `obs - chance` — a bare
subtraction. No variance, no CI, no p-value, anywhere in the script or the output.
On counts this small the Poisson sd on the observed term alone is ~2. `+2.75 ± 2`
and `+3.75 ± 2.2` are indistinguishable by any test you would run.

The honest reading is not "three classical descriptors beat the CTQW." It is:
**under matched multiplicity, a matched candidate set and a matched null, no arm —
quantum or classical — clears more than 5 of 276 families, and the arms are
statistically indistinguishable from each other and barely distinguishable from
chance.** That is a *stronger* and more defensible submission sentence than either
the upstream over-claim (19 vs 1) or its mirror-image in the brief.

The task deserves real credit for the design — one candidate set, one truth
definition, two pre-registered cells, one imported null. That work is what makes
the collapse from 69 families to 4 interpretable. The error is only in the last
step, reading a difference of one as a direction.

**Secondary defect in the same artifact — a mislabel in machine-readable output.**
`degree` and `proximity(-hop)` report:

```json
"degree":          {"ALL": {"n_families": 48, ...}, "near": {"n_families": 0, ...}}
"proximity(-hop)": {"ALL": {"n_families": 48, ...}, "near": {"n_families": 0, ...}}
```

`ALL` = 48 = the distal count; `near` = 0. Those two arms were run on the distal
subset only. The scope reduction **is** disclosed, clearly, in the script's
docstring (*"SCOPED TO THE DISTAL SUBSET ONLY (80 structures) … Stated as a scope
reduction, not hidden"*) — so this is a labelling bug, not concealment. But the
JSON is what anyone else reads, and it currently says `ALL` for two arms where it
means `distal`. Rename the key to `distal_only` for those arms, or emit `null`.

Note also that **proximity — the baseline this whole register is organised
around** — is the arm missing from the ALL comparison. If the submission cites the
ALL row at all, that absence has to be stated in the same sentence.

---

### 3.4 — HIGH — the §2 headline number has no artifact in the repo

TASK-0332 item 4 wants §2 to lead with: *"Residual AUC 0.5949 mean / 0.6203 median,
p = 3.3×10⁻⁶, LOPO over 74 protein clusters, **holding at 0.6017 with proximity
features deleted outright**."*

- `ceiling_result.json` exists and confirms 0.5949 / 0.6203 / 3.32×10⁻⁶ / 74
  clusters / self-check 0.5000. Good.
- **`no_proximity_feature_check.json` does not exist.** `find . -name "no_prox*"`
  returns nothing.
- There is **no script** that produces it. `task0318_input_space_ceiling.py` has
  exactly two flags (`--phase-b-only`) and no proximity-exclusion path. The Done
  section describes the refit as *"run as a standalone follow-up against the same
  cache"* — the follow-up was never committed.

So 0.6017 is traceable to two prose sources ([[TASK-0318]]'s Done section and
`RESULTS.md:11591`) and to nothing executable. It is the number doing the most
argumentative work in the whole plan — it is what converts "high-capacity model
reconstructs proximity" from an open objection into a closed one — and it is the
one number in that sentence that cannot be re-run.

**Fix**: it is a ~10-line variant of the existing Phase B. Write
`task0318_no_proximity_check.py` (or add `--exclude-proximity`), run it against the
committed cache, commit the JSON. ~2 minutes of compute. Without it, drop 0.6017
from the draft and the objection in §8 item 02 reopens.

---

### 3.5 — HIGH — §8 "Attack these first" must be deleted, and it currently breaks the mandated ToC

§4.3 mandates seven numbered items. The document has eight numbered sections, and
the eighth is an internal review-solicitation:

> **"An adversarial review is more useful aimed than unaimed"** … *"What we
> specifically want from this round: a ruling on 01 and 06 … Whether Appendix C
> should ship."*

Together with the front-matter (`Draft | v1 — for adversarial review`,
`Deadline | 2026-09-15 · 13 days`, `## What this document is`, *"It is circulated
for adversarial review"*), that is **758 words of material addressed to an internal
reviewer, in a document about to be sent to a judging panel.**

It is also mis-ordered: §8 sits *after* Appendices A–C, so the reading order is
1–7, Appendix A, B, C, then section 8.

TASK-0332 does not mention removing any of this. If v2 is the submission candidate
rather than another review round, this is the first edit, not the last.

Suggested handling: move §8's content into a separate, untracked-for-submission
`REVIEW_TARGETS.md`. It is useful — it just is not part of the deliverable. Several
items in it (01 "what is actually quantum about this", 06 "benchmark or paper")
should be *answered inside §1 and §2* rather than posed as open questions.

---

### 3.6 — HIGH — the Submission Guidelines document is not in the repo

`TASK-0184:33` cites `documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md`
as obtained 2026-08-19 and converted. `TASK-0184` also cites
`2026-04-06-Assessment-Criteria-VF.md` §4 for the Phase-2 weights.

**Neither file exists in the archive.** `find . -iname "*uideline*"` returns
nothing; `documentation/` contains only the Challenge Statement (`.md` + `.pdf`).

The `.gitignore` explains why — `documentation/*.md` and `documentation/*.pdf` are
both ignored, and the Challenge Statement is only here because this is a working-
tree snapshot.

Consequences, in order of seriousness:

1. **Every structural claim in the submission is unverifiable against its source.**
   §1's *"Guidelines §4.1 — advantage or novel insight"*, §5's *"Guidelines §8 calls
   this one of the strongest differentiators"*, the seven-item ToC, the 6pp + 3pp
   + repo-link allowance — all cited, none checkable by anyone but the person who
   read the PDF three weeks ago.
2. **No page-limit check is possible** without the formatting rules (§3.7).
3. If the Guidelines were revised after 2026-08-19, nothing in this repo would
   detect it. Worth a re-download regardless.

**Fix**: commit both converted `.md` files with a `!documentation/2026-04-06-*.md`
negation, or move them under `__WORK_IN_PROGRESS__/documentation/` where the ignore
rule does not apply. Then re-verify the §4.3 item list against the source before
the ToC is frozen.

---

### 3.7 — HIGH — nobody has checked the page budget, and v2 only adds

Measured word counts for `PHASE1_SUBMISSION_V1.md`:

| Block | Words | Share of body |
|---|---|---|
| §1 Problem Framing (25%) | 455 | 20% |
| §2 Technical Approach (25%) | 468 | 21% |
| §3 Feasibility (20%) | **107** | 5% |
| §4 Expected Impact | 181 | 8% |
| §5 Validation (15%) | 210 | 9% |
| §6 Hybrid (5%) | 103 | 5% |
| §7 Team Capability (10%) | **709** | **32%** |
| **Body total (§1–7)** | **2233** | |
| Appendix A–C | 1053 | (3pp allowance) |
| Front-matter + §8 (review-only) | 758 | (must be cut) |

Two things fall out.

**(a) The body fits, but only just, and every planned edit is additive.** 2233
words plus ten tables plus an unbuilt architecture figure is a realistic 5–6 pages
at 10pt. TASK-0332 then wants to add: four positives to §2, the clinical paragraph
to §4, two full bios to §7, and Berke's "why classical detection fails" paragraph
lifted into §1. That is plausibly +700–900 words with no cuts named anywhere in the
brief. **v2 as specified goes over 6 pages.**

**(b) The word budget is inversely correlated with the rubric weights.** §7 is the
largest section in the document and carries 10%. §3 is the second-smallest and
carries 20%. §2 — the section TASK-0332 correctly identifies as where the
submission wins or loses — is 468 words.

**Recommendation, and it is the single highest-leverage editorial move available:**
cut §7 by roughly half and move the space to §2 and §3. Specifically, the
709 words contain three passages that argue *why* the team is disclosing its AI
usage. The decision is defensible and was made deliberately ([[TASK-0184]], §8 item
07), but three paragraphs of justification reads as anxiety about it. State it in
four sentences, keep the QA-provenance argument (which is genuinely
differentiating), keep the cross-model adversarial-split table (which is evidence),
and cut the rest. That buys ~350 words for §2's four positives at no cost to any
scored criterion.

---

### 3.8 — MEDIUM — the MYR error has a third copy, unlisted in TASK-0332

TASK-0332 item 1 targets `PHASE1_SUBMISSION_V1.{md,html}` and says to check
`REVERSE_CTQW_BRIEF.html`. Measured:

| file | "unexplained ligand" |
|---|---|
| `PHASE1_SUBMISSION_V1.md` | 1 |
| `PHASE1_SUBMISSION_V1.html` | 1 |
| `PHASE1_SUBMISSION_DRAFT.md` | **1 — not in TASK-0332's target list** |
| `REVERSE_CTQW_BRIEF.html` | 0 (clean) |

`PHASE1_SUBMISSION_DRAFT.md` (47.5 KB, 6867 words — larger than V1) is the
superseded draft and still carries the inverted claim. Related: it is also the file
the 2026-08-31 evidence pack audited, so anyone following that pack's line
references lands in the stale document.

**Fix**: either delete `PHASE1_SUBMISSION_DRAFT.md`, or rename it
`ARCHIVE-PHASE1_SUBMISSION_DRAFT-v0.md` with a one-line superseded-by banner at the
top. Two files both named like the submission, one of them wrong, eight days out,
is exactly the [[TASK-0307]] failure mode the parity checker was built to prevent —
except parity only covers the `.md`/`.html` pair, not the draft/V1 pair.

Worth noting on the science: TASK-0332's correction is right and the framing it
proposes is right. The measurement survives — `1OPL` genuinely *is* held open at
that site, which is why the score is confounded ([[TASK-0278]]). Only the
interpretation inverts. Keeping the confound and fixing the cause is the strongest
version of both.

---

### 3.9 — MEDIUM — c-Myc is entirely absent from V1

Challenge Statement §6: *"c-Myc and the targets listed in Table 1 constitute the
**minimum set** required for submission."*

| term | V1.md | DRAFT.md |
|---|---|---|
| `c-Myc` | **0** | 3 |
| `MYC` | **0** | 3 |
| `1NKP` | 0 | 0 |

The restructure from DRAFT to V1 **dropped** c-Myc. `results/MYC_MAX/` exists in
the repo (a 0.20 MB connectivity matrix), so the work was done — it just is not in
the document. [[TASK-0184]]'s own Open Questions flagged this: *"Does c-Myc get its
own section? … Recommend a short dedicated subsection so it is visibly not
forgotten."* It was then forgotten.

A panel checking the minimum-set requirement will look for it. Two or three
sentences plus the artifact reference closes it.

Same check, other mandated §5 deliverables:

| element | V1 mentions |
|---|---|
| Connectivity Matrix (§5.1) | 1 |
| Hit List (§5.2) | 1 |
| Methodological Report (§5.3) | implicit |
| noise resilience (§4.2) | 2 |
| coarse-graining (§4.2) | 1 |
| AWS Braket / Classiq (§6 constraint 4) | **0 / 0** |
| Qiskit (§6) | **0** |

The Braket/Classiq omission is defensible given the `FAULT_TOLERANT_ONLY` verdict —
but *saying* "we evaluated the provided Braket and Classiq infrastructure and here
is why neither changes the verdict" scores better under Feasibility than silence,
and costs one sentence.

---

### 3.10 — MEDIUM — `doc_parity.py` still is not wired to anything

TASK-0332 Constraints: *"a pre-commit hook on these two paths was offered and
never wired ([[TASK-0307]] follow-up) — **wire it here**."*

Status: not wired. `grep -rn doc_parity` outside `.ai/tools/` returns nothing.
`.github/workflows/` contains one file, `keepalive.yml`, which pings a Render
health endpoint every 10 minutes. **There is no CI running tests, parity, or
reference checks on this repository.**

Parity happens to hold today (I checked). It will not survive the v2 edit, which
touches both twins in several places, unless something enforces it.

Cheapest sufficient fix — a workflow that runs on any push touching those paths:

```yaml
name: submission-parity
on:
  push:
    paths:
      - '__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V*.md'
      - '__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V*.html'
jobs:
  parity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: python3 .ai/tools/doc_parity.py
              __WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V1.md
              __WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V1.html
```

A local pre-commit hook is fine too, but CI is the version that also protects
against a commit made from another machine.

---

### 3.11 — MEDIUM — §6 declares a live contradiction and §6 is 5% of the score

The section currently ships this text:

> **OPEN — diagram not yet drawn.** … *the shipped demo reports P@5 with no floor,
> on an operator this register has since falsified. A judge who clicks the demo and
> then reads this document would find them in contradiction. This must be fixed
> before submission, not explained.*

Two problems, one of them not the one the paragraph is about.

**First**: the `bartosz` branch's `backend/` and `frontend/` in this snapshot
contain no P@5 reporting at all (`grep -rn "p_at_5\|P@5\|precision_at"` on both
directories: no hits). So the contradiction lives on `main`, which is not in this
archive, and cannot be verified from here. [[TASK-0184]]'s TODO `- [ ] Reconcile
main branch outputs` is still unchecked. **The keepalive workflow proves the demo
is live and being kept warm** — so a judge clicking through is not hypothetical.

**Second, and worse**: even after the demo is fixed, *this paragraph* is still in
the document. Right now §6 — the only section for a 5%-weighted criterion —
consists of three sentences of content and a boxed admission that the deliverable
is unbuilt and self-contradicting. Disclosing known defects in Appendix C is a
strength. Disclosing them *in place of* the section's content is not the same move,
and a panel will not read it as one.

**Fix**: resolve `main`, delete the box, draw the diagram. If the diagram genuinely
cannot be drawn in eight days, three boxes and two arrows in `mermaid` or plain SVG
beats a paragraph saying it does not exist.

---

### 3.12 — LOW — §7's repo statistics are stale and independently checkable

§7 states: **"338 task files (310 done), 549 commits"**, twice (prose and table).

Measured in this snapshot:

| | claimed | actual |
|---|---|---|
| task files | 338 | **355** |
| done | 310 | **326** |
| commits | 549 | unverifiable (no `.git`) |

Off by 17 and 16. Small — but this is the one number in the document a referee can
check with `ls | wc -l` after following the repo link you are prominently
advertising, and it sits inside the paragraph arguing that this team's distinguishing
property is that it audits its own numbers. Getting it wrong there costs more than
the 17 files are worth.

**Fix**: regenerate at freeze time and pin the commit SHA rather than a count —
*"as of `<sha>`, 2026-09-14"* — so the claim stays true as the register keeps
moving after submission.

---

### 3.13 — LOW — working-file hygiene

- `RESULTS.md` is **886 KB** in a single file. It is the register's narrative spine
  and [[TASK-0195]] built concurrent-write protection for it, so this is a known and
  managed situation — but at this size it is past the point where any reviewer,
  human or model, reads it end to end. Not a submission blocker. Worth an index or
  a per-quarter split after 2026-09-15.
- `.ai/COMMON.md` at 274 KB has the same shape.
- `EXECUTION_PLAN.md` at 154 KB likewise.

Flagged only because §7 explicitly invites a referee to read the register, and
three files totalling 1.3 MB of prose are the first thing they meet.

---

## Part 4 — How v2 is going, by section

You are right that v2 does not exist. What exists is a good plan and a set of
ingredients in mixed condition. Readiness per §4.3 item:

| §4.3 item | v1 state | TASK-0332's plan | Ingredient risk | Ready? |
|---|---|---|---|---|
| **1. Problem Framing** | Strong, one factual inversion | Fix MYR, fix cryptic/allosteric taxonomy, lift Berke's paragraph | Low — all editorial | **Yes, ~2h** |
| **2. Technical Approach** | Weakest scored section | Four positives, in order | **High** — #1 missing artifact (3.4), #2 breaks cluster discipline (3.2) | **No — 2 fixes first** |
| **3. Feasibility** | 107 words, 20% weight | not addressed by 0332 | Low | Needs expansion nobody has planned |
| **4. Expected Impact** | Adequate | + clinical paragraph | Low — strongest single paragraph in the plan | **Yes** |
| **5. Validation Plan** | Excellent | unchanged | — | **Yes** |
| **6. Hybrid** | Declares itself unbuilt | not addressed by 0332 | Medium — depends on `main` reconcile | **No** |
| **7. Team** | 2 of 3 bios placeholder, oversized | Both bios supplied, Berke relabelled | Low, but adds words to the wrong section | **Yes, with cuts (3.7)** |
| Appendix C | 5 defects | + 0329, 0327, 0328 | Low — all three verified accurate | **Yes** |

**On the four §2 positives specifically:**

1. **[[TASK-0318]]** — the right choice for the lead. Retitle as the brief says
   (*"ceiling"* → something like *"the reachable limit of 19 hand-built functionals
   of the contact graph"*). Blocked on 3.4 until the 0.6017 artifact exists.
2. **[[TASK-0334]]** — genuinely the best *narrative* asset you have, because it
   answers "why does the quantum method fail" with a mechanism instead of a null.
   Blocked on 3.2. Fix the clustering and it becomes the strongest thing in §2.
3. **[[TASK-0331]]/[[HYP-P21]]** — the cleanest of the four. Three independent
   measurements, no defect found. The *"cryptic ≠ distal, now measured"* line is a
   real contribution and reframes the whole field's benchmark problem. Ship as-is.
4. **[[TASK-0328]]** — verified: 45/110 → **0/110** under a pocket-block null is
   confirmed in the task's own Done section (`TASK-0328:185-186`). The brief's
   citation is accurate. Note the *other* table in that task (24/55 → 11/55) is the
   external motivating re-run, explicitly marked *"Not independently reproduced
   here"* — make sure v2 quotes the 45/110 figures, which are yours, not the 24/55
   ones, which are not.

**On the decision to exclude the v2 pipeline results** — right call, wrong stated
reason. Exclude them because best-of-221-cells selection does not survive
multiplicity matching (69 families → 4), which is a clean methodological argument
you own. Do not exclude them because "three classical descriptors beat the CTQW,"
which is a one-family difference with no error bar (3.3) and which a referee could
turn around on you.

---

## Part 5 — Suggested plan for the remaining 8 days

Ordered by (blocks-submission × cheapness). Items 1–4 are ~4 hours total and remove
both blockers.

**Day 1 — verification, ~2h**
1. Cold-clone check of `feature_cache/` tracking (3.1). One command. If it fails,
   apply the `.gitignore` negation and force-add, then re-run [[TASK-0333]]'s
   validation *from the cold clone*.
2. Recover or re-download the Guidelines + Assessment Criteria `.md` files and
   commit them under a path the ignore rules do not eat (3.6). Re-verify the §4.3
   item list before freezing the ToC.
3. Wire `doc_parity.py` into CI (3.10). ~15 lines.

**Day 1–2 — the two statistical fixes, ~3h**
4. Cluster-collapse [[TASK-0334]] (3.2). Add cluster-bootstrap or cluster-permutation
   p-values; report those as headline. Append to the task file under a dated
   `## Correction` heading, per the register's own no-silent-overwrite convention.
5. Write and run the [[TASK-0318]] proximity-exclusion script; commit
   `no_proximity_feature_check.json` (3.4). ~2 min compute.
6. Add a CI or CI-note to [[TASK-0336]]: either bootstrap the family counts, or state
   in the task and the draft that the ALL-row differences are within noise. Rename
   the mislabelled `ALL` keys for `degree`/`proximity(-hop)` to `distal_only`.

**Day 2–4 — write v2**
7. Delete §8 and the review front-matter; move to `REVIEW_TARGETS.md` (3.5).
8. Apply TASK-0332 items 1, 2, 3, 5 (MYR, taxonomy, clinical paragraph, team).
9. Cut §7 to ~350 words; reallocate to §2 and §3 (3.7).
10. Add the c-Myc subsection and one Braket/Classiq sentence (3.9).
11. Archive or delete `PHASE1_SUBMISSION_DRAFT.md` (3.8).
12. Draw the §6 diagram; delete the OPEN box (3.11).

**Day 5 — reconcile and re-audit**
13. `main` branch demo reconcile ([[TASK-0184]] TODO, still unchecked).
14. Numbers audit v2 against `RESULTS.md`, reusing the 2026-08-31 evidence pack's
    STALE/MISSING/CURRENT/UNVERIFIED format. Regenerate the §7 repo counts and pin
    a SHA (3.12).
15. Run `doc_parity.py` and confirm CI green.

**Day 6 — page-count check**
16. Render to PDF at the mandated 10pt minimum and **count pages**. This has never
    been done. If over 6, the cut list is §7 first, then Appendix A's QUALIFIED
    rows (they are the ones §8 itself says you are least confident calibrating).

**Day 7 — buffer.** Do not plan work here.

**Explicitly out of scope before 2026-09-15**: any new experiment, any re-run of
[[TASK-0318]] Phase A, any attempt to rescue the v2 pipeline numbers.

---

## Appendix — commands used, so every claim above is re-checkable

```bash
# archive composition by directory (compressed bytes)
python3 -c "
import zipfile,collections
z=zipfile.ZipFile('Quantum_allosteric-scanner-bartosz__15_.zip')
g=collections.Counter()
for i in z.infolist():
    p=i.filename.split('/'); g['/'.join(p[1:3])]+=i.compress_size
for k,v in g.most_common(12): print(f'{v/1048576:8.2f} MB  {k}')"

# parity — currently exit 0
python3 .ai/tools/doc_parity.py \
  __WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V1.{md,html}

# 3.1 gitignore has no negations
grep -c '^!' .gitignore                      # => 0
grep -n 'COPY.*results/' Dockerfile.pipeline # => lines 75-80

# 3.2 cluster column present, unused
grep -c 'cluster' \
  __WORK_IN_PROGRESS__/results/tasks/0334_*/distance_anticorrelation.py   # => 0
python3 -c "
import csv
r=[x for x in csv.DictReader(open('__WORK_IN_PROGRESS__/results/tasks/0334_ctqw_proximity_anticorrelation/pocket_distance.csv')) if x['is_distal']=='True']
print(len(r),'rows /',len({x['cluster'] for x in r}),'clusters')"        # => 138 / 86

# 3.3 no variance on real_excess
grep -n 'real_excess' __WORK_IN_PROGRESS__/results/tasks/0336_*/matched_comparison.py

# 3.4 artifact absent
find . -name 'no_prox*'                      # => nothing

# 3.6 guidelines absent
find . -iname '*uideline*'                   # => nothing

# 3.8 third copy of the MYR error
grep -c 'unexplained ligand' __WORK_IN_PROGRESS__/documentation/*.md

# 3.9 c-Myc absent from V1
grep -ci 'c-myc\|1NKP' __WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V1.md

# 3.10 nothing wired
grep -rn 'doc_parity' --include='*.yml' --include='*.json' . | grep -v '.ai/tools/'

# 3.12 counts
ls .ai/tasks/DONE/TASK-*.md | wc -l          # => 326  (doc says 310)
find .ai/tasks -name 'TASK-*.md' | wc -l     # => 355  (doc says 338)
```

---

*Filed 2026-09-07. Every finding above is stated against a file path and a
reproducible command; where I could not verify something from this snapshot —
`main`-branch demo state, git tracking of `feature_cache/`, commit counts — it is
marked as such rather than asserted.*

---

# Response — Reviewer thread, 2026-09-07

Every finding was re-checked against the live repository before anything was
filed. That mattered: the audit worked from a zip snapshot with **no `.git`**,
correctly flagged several findings as inference rather than fact, and **three of
them do not hold.** Recorded here so the next reader of this document does not
chase them again.

## Findings that did not survive verification

| § | Claim | Verified state |
|---|---|---|
| **3.1** | *BLOCKER — container fails on a cold clone; the three COPY paths are untracked* | **Does not hold.** `git ls-files` returns **107 files** under `0318_input_space_ceiling/`, and both JSONs are tracked. Force-added by [[TASK-0333]] in `ff0979d`. The proposed `.gitignore` negation block is unnecessary — git tracks what it was told to track regardless of ignore rules. |
| **3.6** | *HIGH — the Submission Guidelines are not in the repo* | **Does not hold.** `documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md` **and** `.pdf` are both present. The snapshot was a working tree that did not carry them. |
| **3.4** | *HIGH — `no_proximity_feature_check.json` does not exist* | **Artifact exists** and is committed. The narrower defect the audit identified underneath it — *no script regenerates it* — was real, and was filed. |

The reasoning behind all three was sound; only the premise was stale. §3.1 in
particular was the right thing to worry about, and the *verification* it asked
for was still owed even though the defect was not — see [[TASK-0340]].

## Filed, and now closed

| § | Task | Outcome |
|---|---|---|
| 3.2 | **[[TASK-0337]]** — cluster-robust correction to [[TASK-0334]] | **Confirmed, and mostly survived.** `distance_anticorrelation.py` had zero references to `cluster`; cohort is 138 rows / 86 clusters with `CAS0002` alone at 28. Cluster-collapsed: **7 of 8 pre-registered combinations clear** (ρ −0.34 to −0.50, permutation p 0.004–0.038, CIs excluding zero). One borderline (round 2, held-out, `median_euclid`, n=22, p=0.0577); its `median_hop` sibling clears. PASSer control unweakened; **random-arm control weakens** to non-significant. `HYP-P25` updated. §2 must say "7 of 8", not "everywhere". |
| 3.3 | **[[TASK-0338]]** Part A | **Confirmed exactly.** McNemar exact **p = 1.0**; Poisson 95% CIs `[1.09, 10.24]` vs `[1.62, 11.67]`, heavily overlapping. 4-vs-5 of 276 is noise. [[TASK-0332]]'s exclusion argument rewritten to the multiplicity methodology; `HYP-P13` status corrected. Mislabelled `"ALL"` keys on `degree`/`proximity(-hop)` renamed `"distal_only"`. |
| 3.4 | **[[TASK-0338]]** Part B | `--exclude-proximity` added to Phase B; re-run against the committed cache reproduces `no_proximity_feature_check.json` **byte-identical**. 0.6017 is now regenerable. |
| 3.5, 3.7–3.9, 3.11–3.12 | **[[TASK-0339]]** | §8 moved to `REVIEW_TARGETS.md`, **ToC now exactly 7 items**; items 01 and 06 answered inside §1/§2 (06's answer flagged for human sign-off — it is a positioning decision, not an edit); c-Myc and a Braket/Classiq sentence added; `PHASE1_SUBMISSION_DRAFT.md` archived; §6 diagram drawn and the OPEN box deleted; §7 statistics regenerated. |
| 3.1, 3.10 | **[[TASK-0340]]** | Cold-clone build verified **byte-identical**; `doc_parity.py` wired into CI. |
| 3.7 | **[[TASK-0341]]** | The page count remains **uncertified** — no renderer in the environment. Filed as a Toolsmith task, then revised into a *build* tool (one command → numbered PDF + change report) after the repo owner clarified the underlying need. |

## Filed, but not as the audit framed it

**§3.7, the page budget.** [[TASK-0339]] cut §7 by 187 words but spent 234 on
§1/§2/§3 — a **net +47**, not the saving the audit's recommendation implies. The
recommendation to cut §7 roughly in half was only partly taken (709 → 522, 26%),
with a stated reason. The page count itself has still never been measured; every
figure in this register remains words × a constant. [[TASK-0341]] closes that.

**§3.3, the framing.** The audit's own alternative sentence — *no arm, quantum or
classical, clears more than 5 of 276, and the arms are indistinguishable* — was
adopted verbatim as the correct reading, and is the version now in the draft plan.
Credit where it is due: that is a better sentence than either the upstream
over-claim or this thread's mirror-image of it.

## Not filed, deliberately

| § | Item | Why not |
|---|---|---|
| 1.1–1.4 | Archive size, 45 MB | The audit's own recommendation was *"do not prune for size"* — 45 MB is irrelevant against a 20 MB PDF limit and a repo **link**. The part that mattered (tracked vs untracked) was the §3.1 question, resolved above. The `PROVENANCE.md`-instead-of-10.7 MB suggestion is sound but is post-deadline hygiene. |
| 3.13 | `RESULTS.md` 886 KB, `COMMON.md` 274 KB, `EXECUTION_PLAN.md` 154 KB | Real, and correctly flagged as not a blocker. Splitting the register's narrative spine eight days out risks more than it saves — [[TASK-0195]] already built concurrent-write protection for it. **Deferred to after 2026-09-15**, not dismissed. |
| Part 5, item 13 | `main`-branch demo reconcile | [[TASK-0339]] §5 drew the diagram and demoted the disclosure box to a scoped, confirmed note, which removes the *document's* self-contradiction. The `main` branch itself is still unreconciled and remains open on [[TASK-0184]]. |

## One thing the audit got right that is worth repeating

The scoring table's structural observation — **§7 carries 32% of the body's words
for 10% of the score, while §3 carries 5% for 20%** — is the highest-leverage
editorial point anyone has made about this document, and it cost nothing to act
on. It is the reason [[TASK-0339]] exists as a task at all rather than as a list of
nits appended to [[TASK-0332]].

## Status

All findings are dispositioned. [[TASK-0332]] (the v2 writeup) is unblocked; the
only outstanding audit item is the page count, which [[TASK-0341]] owns and which
does not block drafting — it constrains the cut list afterwards.
