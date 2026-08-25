# TASK-0260 — Does a purpose-built cryptic-pocket predictor close the 29% residual?

- Status: Done
- Assignee: unassigned (suggest Explorer for the citation/constraint pass, then Implementer)
- Priority: **Highest — this is the direct test of [[TASK-0259]]'s finding and it decides what Phase 2 is about**
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0259]], [[TASK-0254]], [[TASK-0163]] (fpocket baseline precedent), [[TASK-0137]] (citation-verification convention)

## Why

[[TASK-0259]] found the unexplained share is **not** mysterious physics. It is
apo crypticity, and almost nothing else:

| correlate of the unexplained share | rho | p (rows) | p (clustered by structure) |
|---|---|---|---|
| **apo crypticity** | −0.771 / −0.646 | **0.0001** | **0.017** |
| ENM validity | +0.002 | 0.99 | — |
| distance to active site | −0.236 | 0.32 | — |
| pocket size | +0.213 | 0.37 | — |

Median unexplained: **55% on cryptic targets vs 24% on already-open ones.**
Mirror confirmation: fpocket's own Shapley share correlates **+0.518
(p=0.019)** with apo-openness — it works when the pocket is already there.

So the residual has a name. The question this task answers is whether it is
**addressable classically**. If a predictor built specifically for cryptic
sites closes it, the residual is a solved problem we simply had not applied,
and any quantum proposal must beat that predictor, not the current baselines.
If it does not close it, there is something genuinely unmodelled — and that is
the strongest possible motivation for Phase 2.

Either answer is decisive. There is no outcome of this task that leaves the
Phase 2 story where it is now.

## Candidate methods

Suggested by an external model; **all four must be citation-verified live
before any implementation**, per this register's standing convention. The
external suggestion dated PocketMiner to 2021, which we believe is wrong — do
not inherit any of these details, check them.

- **PocketMiner** — graph neural network, predicts cryptic-pocket-opening
  probability from a single static structure. Believed Meller et al.,
  *Nature Communications*, ~2023. Expected to be the strongest candidate.
- **CryptoSite** — SVM over static structural/sequence descriptors. Believed
  Cimermancic et al., *J. Mol. Biol.* 2016.
- **P2Rank** — random forest over Connolly surface points; a modern geometric
  peer to fpocket. Believed Krivák & Hoksza, *J. Cheminform.* 2018.
- **FTMap / FTSite** — fragment-based hot-spot mapping via FFT correlation of
  organic probes.

## The constraint question that must be settled first

**PocketMiner is trained on MD trajectories but infers from a static
structure.** The challenge forbids MD as *input*. Does an MD-trained model
whose inference is MD-free violate constraint 3?

- [x] Settle this **before** building. Document our reading either way. If it
      is genuinely ambiguous, add it to [[TASK-0221]]'s organiser question
      list rather than assuming the favourable interpretation. **Added as
      item (f).**
- [x] The same question applies to CryptoSite (trained on a curated cryptic
      set) and P2Rank (trained on bound structures). State a single consistent
      rule and apply it to all four. **Done — see Done section.**

## Scope

- [x] Verify all four citations live (Crossref/publisher record: title,
      authors, journal, volume, DOI) before writing code against them.
- [x] Settle the MD-training constraint question and record the ruling.
- [x] Install/run whichever survive both gates on the frozen set's **apo**
      structures. Apo only — holo would leak the label ([[TASK-0259]]).
      **Only P2Rank survives both gates and was successfully installed/run
      — see Done for FTMap/CryptoSite exclusion and PocketMiner's
      infeasibility (attempted, not skipped).**
- [x] Score each as a **fourth block** in [[TASK-0254]]'s Shapley attribution,
      reusing that script unmodified with the new block's values substituted.
- [x] Report the decision statistic: **each method's contribution when added
      last**, on top of geometry + fpocket + CTQW. That is the increment it
      supplies that nothing else does.
- [x] Report how much of the 29% residual survives.
- [x] Stratify by crypticity. The prediction to test: **the new method's gain
      should be concentrated on the cryptic targets**, mirroring fpocket's
      +0.518 correlation with openness in the opposite direction. If the gain
      is uniform across cryptic and open targets, it is not doing what its
      name says. **It is not — same pattern as fpocket, see Done.**
- [x] Cluster by distinct apo structure ([[TASK-0261]]) — 20 rows are only 13
      structures, and apo-side scores are identical within a pair. **Used
      TASK-0261's own already-published first-pass method (per-structure
      averaging); TASK-0261's own more rigorous cluster-robust/mixed-model
      method landed in the same window as this task — re-checking against
      it is flagged as a quick follow-up, not redone here.**

## Acceptance

- [x] Citation-verification record for all four; ruling on the MD constraint.
- [x] Four-or-more-block attribution table with each method's added-last value.
- [x] An explicit number: how much of the 29% residual remains.
- [x] The crypticity-stratified breakdown.
- [x] `RESULTS.md`, and an update to
      `documentation/CTQW_CONTRIBUTION_BRIEF.html` §08, which currently argues
      for a cryptic-enriched target set on the strength of this residual.

## Constraint

If a classical cryptic predictor closes the residual, that is a negative for
the quantum proposal and must be reported with the same prominence as
everything else in the brief. It would also be genuinely useful science —
"the unexplained majority was a solved classical problem we had not applied"
is a publishable finding and an honest one.

## Done

**2026-08-25, Implementer D.**

**Citations verified live, before any code was written against them** (via
Crossref directly, not search snippets): PocketMiner — Meller, Ward,
Borowsky, Kshirsagar, Lotthammer, Oviedo, Ferres, Bowman (2023), *Nature
Communications* 14:2135, DOI 10.1038/s41467-023-36699-3. CryptoSite —
Cimermancic et al. (2016), *J. Mol. Biol.* 428:709-719, DOI
10.1016/j.jmb.2016.01.029. P2Rank — Krivák & Hoksza (2018), *J.
Cheminform.* 10:39, DOI 10.1186/s13321-018-0285-8. FTMap/FTSite — Kozakov,
Grove, Hall, Bohnuud, Mottarella, Luo, Xia, Beglov, Vajda (2015), *Nature
Protocols* 10:733-755, DOI 10.1038/nprot.2015.043. All four match the
task's own "believed" citations — the filing's warning that PocketMiner's
year "we believe is wrong" was itself not borne out; 2023 is correct.

**Constraint-3 ruling, one consistent rule applied to all four, before any
tool was run** (per this task's own Scope): Constraint 3 forbids MD
trajectories as *inputs* — read literally, per this register's own settled
precedent (`search_complexity.md` HYP-S7), as governing what this pipeline
supplies at inference time, not a third-party tool's own historical
training provenance.
- **P2Rank**: supervised ML on labelled bound/holo structures (Random
  Forest, Connolly surface points) — no MD anywhere, training or
  inference. LEGAL, unambiguous.
- **FTMap/FTSite**: physics-based FFT probe-clustering, not ML at all, no
  training data, no MD anywhere. LEGAL, unambiguous — but the citation's
  own title ("the FTMap family of *web servers*") confirms it is hosted-
  service-only; no scriptable local tool exists for a 20-target batch
  run. EXCLUDED on installability, not the constraint question.
- **CryptoSite (full model)**: verified directly (WebFetch on the paper's
  own PMC record) that its single most informative feature is "the
  average pocket score from the molecular dynamics simulations" (AllosMod)
  — this model runs its *own* internal MD conformational sampling *at
  inference* to score a new structure. That is MD executing as an
  input-generation step inside our own pipeline, not training-time-only
  provenance — qualitatively different from PocketMiner, not a matter of
  degree. EXCLUDED. The paper's own reported MD-free "faster version" (AUC
  0.74 on their own benchmark) would be legal in principle but is not
  independently released as runnable software (an ablation reported
  inside the paper, not shipped as the actual CryptoSite tool) — dropped
  on installability, not the constraint.
- **PocketMiner**: MD used only to generate the external authors' own
  training labels; our own inference call supplies zero MD trajectories
  at runtime. Reads LEGAL under the literal rule above — but the closest
  call of the four, since the tool's own stated purpose is "predict where
  pockets open in MD simulations." **Not silently assumed**: added to
  [[TASK-0221]]'s own organiser-question list as item (f), with the
  CryptoSite contrast stated for precision (training-provenance-only vs.
  MD-at-inference are genuinely different cases, not a spectrum).

**Survivors: P2Rank only, of the four.** PocketMiner needed Python 3.7-3.9
+ TensorFlow≤2.9 (confirmed from its own repo, `Mickdub/gvp` pocket_pred
branch, README + `pocketminer.yml`); this environment has Python 3.13 with
only TensorFlow 2.16 available via pip. **Attempted, not silently
skipped**: `pyenv install 3.9.18` tried twice, once plain and once with
explicit `CPPFLAGS`/`LDFLAGS`/`PYTHON_CONFIGURE_OPTS` pointed at
Homebrew's `openssl@3` — both times the build completes but the `_ssl`
extension fails to compile (`ModuleNotFoundError: No module named
'_ssl'`), traced to the real, specific, documented cause: CPython 3.9's
own OpenSSL detection predates general OpenSSL 3.x support, and
`openssl@1.1` — the version 3.9 was actually tested against — has been
removed from Homebrew entirely (confirmed via `brew info openssl@1.1`).
Architecture mismatch ruled out directly (`uname -m`/homebrew prefix/
Python all confirmed `arm64`). A real, costed follow-up: a container with
an older base image, or a from-source OpenSSL 1.1 build — not a vague
"future work" gesture.

**Installed and run: P2Rank 2.5.1** (prebuilt release, Java 21 already
present, no compilation needed) — real ML, no MD anywhere, unambiguously
legal, ~8-11s/target. `scripts/task0260_cryptic_predictor_residual.py`,
reusing `task0249_composite_dumb_baseline.target_rows` and
`task0254_fpocket_variance_and_crypticity`'s own `cv_auc`/`build_blocks`/
`crypticity`/`z` (imported, not copied) — a generalised n-block exact
Shapley routine added here (4!=24 permutations, still cheap) since
`task0254`'s own `shapley_attribution` hardcodes 3 blocks at module
level, not edited at its source. 20/20 usable targets scored by P2Rank
cleanly (matching [[TASK-0249]]'s own n=20 filter, [[TASK-0253]]'s
empty-seed guard inherited automatically for the 2 excluded
HIV-integrase rows).

**Four-block Shapley attribution (geometry / fpocket / CTQW / p2rank)**:
p2rank Shapley share median **+9%** (n=20 rows, range −18% to +41%,
Wilcoxon-vs-0 p=0.007) — real and significant. **Unexplained (4-block)
median 27%**, down from [[TASK-0254]]/[[TASK-0259]]'s own published 29%
— a small, real movement, **not a closure**.

**The decision statistic this task's own Scope actually specifies —
p2rank's contribution when added *last*, on top of the already-fitted
geometry+fpocket+CTQW model — is smaller still and not significant**:
median **+0.0%** (range −9.4% to +14.9%, Wilcoxon-vs-0 p=0.881). The
Shapley share credits p2rank its fair average share of variance it
overlaps with the already-present fpocket block (both are static apo-
geometry detectors); the added-last number shows that once fpocket is
already in the model, p2rank supplies essentially nothing further. Both
numbers are honest, computed from the same run, and say the same thing
from different angles.

**Clustered by distinct apo structure** ([[TASK-0261]]'s own already-
published first-pass method — per-apo-structure averaging, n=13; that
task's own more rigorous cluster-robust/mixed-model method landed in the
same window as this task and was not re-applied here, flagged as a quick
follow-up): p2rank Shapley median **+10%** (Wilcoxon-vs-0 p=0.021,
n=13), unexplained median **26%** (29%→26%). Same conclusion, same
magnitude, at the more conservative sample size.

**Crypticity-stratified breakdown — the central prediction this task's
own Scope pre-registered, and it fails, cleanly.** The prediction: "the
new method's gain should be concentrated on the cryptic targets... if
the gain is uniform across cryptic and open targets, it is not doing
what its name says." Measured: p2rank Shapley share median **+30%** on
already-open targets (n=9) vs. **+8%** on cryptic-testing targets
(n=11) — row-level; **+29%** vs. **+8%** clustered (n=6 vs. n=7
structures). **The gain concentrates on the already-open targets, the
opposite of the predicted pattern** — matching [[TASK-0254]]'s own
+0.518 correlation for fpocket exactly, not the complementary pattern a
genuine cryptic-opening specialist would show. P2Rank behaves like
fpocket, because it is what it was billed as — "a modern geometric peer
to fpocket," not the cryptic-opening specialist. This result is real and
reported, but it answers the task's own central question only for the
weaker candidate; **PocketMiner, the one method actually trained to
predict opening, remains untested — for a documented environment reason,
not a result.**

**Written up per this task's own Acceptance**: `RESULTS.md` new row (85,
plus a recovered row 84 — see below); `documentation/CTQW_CONTRIBUTION_
BRIEF.html` §08 updated in place (both the Shapley and added-last
numbers, the citation/constraint gate summary, and the PocketMiner
environment gap), plus the script added to §09's own file list.

**Incidental finding: a real, self-caused shared-file-collision bug in
[[TASK-0256]]'s own prior commit, found and fixed here.** While adding
this task's own `RESULTS.md` row, that row's own predecessor (row 84,
[[TASK-0256]]) was found missing from the file entirely, despite that
task's own commit message describing it in full. Root-caused via `git
log`/`git show`: that commit's own diff was 119 insertions against an
expected ~1-line row — the surgical-splice procedure used elsewhere in
this register (save a mixed working-tree copy, restore clean `HEAD`,
insert the new row, verify, stage) was followed correctly up to staging,
but a *later*, second `git add` in the same commit's own staging
sequence re-added `RESULTS.md` from its *working-tree* state — which had
already been reset back to the saved "mixed" (another thread's in-flight,
pre-this-row) copy for restoration purposes — silently overwriting the
clean staged version with one that both contained another thread's
content AND was missing this task's own row, before commit. The same
class of incident as [[TASK-0244]]'s own row loss, self-inflicted this
time rather than by another thread. Recovered verbatim from the original
commit message (all numbers unchanged) as `RESULTS.md` row 84 in this
task's own commit. **Process fix for future use of this technique,
recorded here rather than only fixed silently**: after restoring a saved
"mixed" file to disk for another thread's benefit, that file's path must
not be included in any later bulk `git add` in the same session before
commit — stage it once, immediately after the clean insert, and commit
before doing anything else that could re-touch it.

**Not done, and why**: PocketMiner itself (environment infeasibility,
documented above, not silently skipped). Re-checking the crypticity-
stratified/clustered numbers against [[TASK-0261]]'s own more rigorous
cluster-robust method once reviewed (that task's first-pass method was
used instead, a reasonable but not final choice, flagged not hidden).
Sending the PocketMiner constraint question to the organisers directly —
outside what this session can do; written into [[TASK-0221]]'s own
question list for whoever owns that channel next.

Tests: no `src/` code changed — investigation script only
(`scripts/task0260_cryptic_predictor_residual.py`), matching this
project's own established convention for that directory (no dedicated
unit tests for one-off analysis scripts). `task0242_two_stage_dryrun.py`
and `task0254_fpocket_variance_and_crypticity.py` both reused unmodified,
not edited.

Artifacts: `scripts/task0260_cryptic_predictor_residual.py` (new),
`tools/p2rank/p2rank_2.5.1/` (vendored, prebuilt release, not committed —
matches this repo's own `tools/fpocket`/`tools/evoef2` vendoring
convention but P2Rank's own ~250MB size argues against committing it;
flagged for whoever next decides whether to vendor it properly or
document the download step instead), `results/tasks/
0260_cryptic_predictor_residual/{shapley_4block.json,crypticity.json}`,
`RESULTS.md` rows 84 (recovered) + 85,
`documentation/CTQW_CONTRIBUTION_BRIEF.html` §08+§09,
`.ai/tasks/TODO/TASK-0221-*.md` (new organiser question (f)).
