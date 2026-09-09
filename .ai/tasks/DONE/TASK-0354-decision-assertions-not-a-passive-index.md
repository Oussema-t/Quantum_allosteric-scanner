# TASK-0354 — Decision assertions at build time, not a passive decision index

- Status: Done
- Owner: **Toolsmith**
- Priority: Low — tooling, not submission work; no deadline pressure
- Filed: 2026-09-09 by Toolsmith thread, as [[TASK-0352]] Part A's own scoping decision
- Related: [[TASK-0352]] (Part A, gated on this), [[TASK-0322]], [[TASK-0321]]

## Why Part A was not built as specified

[[TASK-0352]] Part A asked for "a generated index, one line per recorded
decision: what was decided, when, and where the reason lives." Investigated,
not built, for a reason [[TASK-0352]] itself surfaces but doesn't quite
follow through on: **an incomplete decision index risks the exact "confident
negative" failure [[TASK-0352]]'s own "why this is an index and not a search
tool" section warns about.**

The precedent it names ([[TASK-0322]]'s hypothesis index,
`.claude/hypotheses/INDEX.md`) works because hypotheses are already
**structurally tagged** — every `HYP-Pxx`/`HYP-Sxx` id lives in a canonical
register with a claim/status/citation field, and the index is *generated*
from that structure by `hyp_register_check.py --build-index`. "Decisions and
their reasons," by contrast, are not structurally tagged anywhere in this
repo — they're prose, scattered across config comments
(`config/targets.yaml`), organiser-clarification docs, DONE task Done
sections, and `.claude/hypotheses/*`. Building a real index would mean
either:

1. Retroactively tagging every decision across the whole repo — large,
   judgement-heavy, and not exhaustively verifiable as complete (the person
   doing the tagging is exactly the kind of single unreviewed pass this
   scaffold's own conventions distrust), or
2. Indexing only what's already easy to find mechanically — which
   reproduces the same **incomplete, confidently-presented index** problem
   [[TASK-0352]] itself argues a search tool has, just one layer removed.

Either way, a *passive* artifact that requires someone to remember to
consult it is also directly contradicted by [[TASK-0322]]'s own filed
citation-rate measurement: **9%**. Building a more complete list does not
fix a 9% consultation rate.

## What to build instead — the Reviewer's own reframing, taken seriously

[[TASK-0352]]'s "Hold released" addendum names the actual working precedent
already in this repo: `submission_build.py`/`submission_build_latex.py`
assert compliance (page count, font floor, clipping) **at the moment of
building**, not as a document someone has to go read. That pattern already
caught real defects within seconds of existing (a tofu-rendered glyph, an
uncited reference) that three careful human readings of the same PDF missed.

**Outcome for this task**: pick 1-2 of the four concrete incidents
[[TASK-0352]] Part A named, and turn each into a standing assertion that
fires automatically at the point something could get it wrong again — not
an index entry someone has to think to check. Candidates, in likely order of
tractability:

1. **`config/targets.yaml`'s genotype/apo-vs-holo comments.** The reason a
   wrong target (`8S8C`, wrong KRAS genotype) got proposed twice is not that
   the correct answer was hard to find — it was already an inline comment in
   the file being read. A pre-flight assertion (fires wherever target
   selection reads this file, or as a standalone check runnable before
   proposing a structure substitution) that fails loudly if a proposed PDB
   id contradicts the file's own recorded genotype/apo verdict would catch
   this at the moment of proposal, not on review.
2. Audit whether [[TASK-0130]] (the chiral-walk interference-test precedent,
   cited by four tasks per [[TASK-0352]]'s own table) has a natural
   "did you check this" hook — e.g. a lint rule or docstring pointer in
   whatever module a new interference-test variant would be added to.
3. The fourth incident ("consistent with the JACS ρ≈0.95") was genuinely
   unmeasured, not misfiled — no assertion applies; leaving it as a plain,
   named open question is correct and requires no tooling.

## Constraints And Invariants

- Same as [[TASK-0352]]: read-only where it's a check, no auto-repair.
- **Record the pointer, never restate the reason** — an assertion should
  fail with a pointer to `targets.yaml`'s own comment (or wherever the
  reasoning lives), not a restated summary of it that can drift from the
  source.
- Ships with a test proving the assertion fires on the seeded original
  mistake (propose the wrong genotype/PDB id, the check must fail) —
  [[TASK-0319]]'s standing rule, same as [[TASK-0352]] Part B.
- Do not build a general "decision index" alongside this without first
  checking whether the assertion-based approach alone already closes the
  gap the index was meant to close — per this task's own argument, prefer
  fewer, load-bearing checks over a more complete but still-passive list.

## Not required before this can be picked up

No timing hold — [[TASK-0352]]'s own hold was already released before this
was filed, and this task carries no new one.

## Done — 2026-09-09, Toolsmith

Built candidate 1 (targets.yaml genotype assertion) as a real, wired-in,
tested guard. Audited candidates 2 and 3, per their own lighter "audit
whether" framing — both audits found the candidate itself had drifted
stale in exactly the way this task exists to prevent, which is directly
relevant evidence for this task's own thesis, not a detour from it.

### Candidate 1 — built, wired, tested

New `assert_genotype_identity(target_name, cfg, role, result)` in
`allostery/clean.py`, wired into `clean_from_config` itself -- same
build-time precedent TASK-0231 set for `assert_functional_provenance_
allowed` in `labels.py`/`build_labels`. Every real caller (`run_challenge.
py`, every test/script using `clean_from_config`) is protected the moment
a wrong-genotype structure is actually loaded, not only whichever test
happens to check the field directly.

New optional `genotype_check` field on `targets.yaml`'s KRAS_G12C entry
(`role`, `chain`, `residue`, `expect_resname`, `reason_ref`) -- ONE
residue identity, not a pocket-residue list, so it does not fall under
this file's own HARD RULE against hand-transcribed pocket residues
(documented explicitly, both in the field-meanings block and inline).
Absent on every other target (14/15) -- confirmed a true no-op there via
a real ASD target's actual config, not a fabricated stub.

**Constraint honored**: the error message names the mismatch (residue,
actual, expected) and points at `reason_ref` -- it does not restate the
wild-type/8S8C/organiser-clarification story from the target's own
`apo_pdb` comment. Regression test (`test_error_points_at_the_comment_
not_a_restated_reason`) asserts the restated words are literally absent
from the raised message, not just "seems short."

**Planned Validation, per this task's own Constraint** (fires on the
seeded original mistake): `test_seeded_wild_type_mistake_is_caught`
fetches the real, RCSB-deposited 4OBE (TASK-0270's own wrong apo
proposal) and confirms the guard raises `... is GLY, expected CYS`.
Control (`test_real_current_kras_apo_passes`) confirms the real, current
4LDJ does not raise, so the guard is proven to distinguish the two, not
just proven to raise unconditionally. 6 more synthetic/no-network tests
cover the comparison logic, the no-op case, the role gate, and the
missing-residue case directly (`CleanResult` built by hand, no fetch) --
8 new tests total, all in `test_config_integrity.py::
TestGenotypeIdentityGuard`, same file/module TASK-0231's own guard tests
live in.

**Found and fixed a live, real regression while validating, of the exact
class this task exists to prevent**: `test_targets_config.py::
test_kras_g12c_anchors` had been asserting `apo_pdb == "4OBE"` -- the
wrong-genotype value TASK-0270 replaced on 2026-08-26 -- and had been red
for 2+ weeks, unnoticed (confirmed by running it before touching
anything: `AssertionError: assert '4LDJ' == '4OBE'`). This is not a
hypothetical the assertion guards against; it is the same mistake sitting
live in the suite as a passive, silently-ignored-because-nobody-reads-CI
pin, corroborating this task's own argument (a passive artifact does not
get consulted) with a second, independent real incident beyond the two
[[TASK-0352]] already named. Fixed the assertion (4OBE -> 4LDJ), with a
comment citing both TASK-0270 and this task.

Did not build a separate standalone CLI script for "runnable before
proposing a structure substitution" -- the Outcome's own wording offers
that as an alternative ("fires wherever target selection reads this
file, **or** as a standalone check"), and the build-time wiring already
satisfies the stronger form (automatic, not opt-in) for every real
caller; a second, redundant entry point would be duplication without
new coverage.

### Candidate 2 — audited; found the citation itself was wrong

Investigated whether TASK-0130 (as named in [[TASK-0352]]'s own Part A
table, "the chiral walk was the only interference test... cited by four
tasks") has a natural documentation hook. First check, before building
anything: read TASK-0130 itself. **It has nothing to do with chirality
or interference** -- it is `time_averaged_ctqw_converged`, the closed-
form convergence fix (confirmed by grep: zero occurrences of "chiral" in
that task's file). The real chiral-walk task is **TASK-0140**
(`chiral.py`, "Chiral (broken-time-reversal) circulation observable") --
8 tasks cite it, not 4, a further sign the original count was against
the wrong id. Root cause, not just the fix: `chiral.py`'s own docstring
legitimately cites TASK-0130 as *reused math* ("reusing TASK-0130's own
closed-form convergence discipline") -- almost certainly where the
mix-up entered, not an unexplained typo.

Filed a dated correction on [[TASK-0352]]'s own Done section (not a
silent rewrite of its Part A table, per this project's convention) naming
the error and the likely mechanism.

**The actual hook, built using the corrected id**: added a short pointer
in `propagators.py`'s own module docstring (the shared home for
`coherent`/interference-related propagator logic) directing anyone
adding a new interference-test observable to read
[[TASK-0350]] first -- the pre-registered, matched-operator/seed/cohort
direct test that reached a decisive verdict, closing the exact question
four prior attempts (chiral circulation among them) each conflated with
something else. Pointer only, no restated findings -- same "record the
pointer" discipline as candidate 1. No test ships with this (it is
documentation, not an assertion with a pass/fail condition) -- consistent
with this task's own lighter "audit whether X has a hook" framing for
candidate 2, distinct from candidate 1's "turn into a standing assertion."

### Candidate 3 — re-checked; also found stale, left as directed

This task's own text calls this "genuinely unmeasured... requires no
tooling," true when [[TASK-0352]]/this task were filed. Re-checked before
leaving it alone: **it is no longer unmeasured.** [[TASK-0348]]
(2026-09-08, landed after this task was filed) ran the mandatory
centrality ablation and found median rho=0.41 vs eigenvector centrality,
**not** ~0.95 -- and corrected `PHASE1_SUBMISSION_V2.md`'s own draft
sentence that had claimed consistency with the published value. No
tooling action follows from this (matching this task's own instruction
for candidate 3) -- noted here only so a future reader of this task does
not re-flag a question [[TASK-0348]] already closed.

### Validation

- `.venv/bin/python -m pytest __WORK_IN_PROGRESS__/tests/test_targets_
  config.py __WORK_IN_PROGRESS__/tests/test_config_integrity.py
  __WORK_IN_PROGRESS__/tests/test_propagators.py` -> 112 passed, 5
  xfailed (pre-existing, unrelated).
- Full `__WORK_IN_PROGRESS__/tests/` suite: 1266 passed, 1 skipped, 8
  xfailed, 2 failed. Both failures checked directly and confirmed
  pre-existing/unrelated to this task's changes: `test_fpocket_pin.py::
  test_pinned_binary_sha256_matches_provenance_record` (this
  environment's local fpocket binary vs. a pinned sha256, no KRAS_G12C/
  clean_from_config/genotype involvement) and
  `test_ground_state_relaxation_guard.py::
  test_classical_and_heat_do_not_co_occur` (a doc-text scanner, no
  connection to this task's files). Neither references `clean.py`,
  `targets.yaml`, or `propagators.py`'s changed regions.
- YAML re-parsed after editing `targets.yaml`; `genotype_check` confirmed
  present and does not trip `_FORBIDDEN_RESIDUE_FIELDS`
  (`test_no_hand_transcribed_pocket_residues` still passes for all 15
  targets).

### Not built, correctly out of scope

- No general decision index alongside this (this task's own Constraint)
  -- checked first whether the assertion-based approach closes the gap
  for the one candidate actually built; it does, for the genotype
  concern specifically.
- The "apo-vs-holo drug-bound state" half of candidate 1's own framing
  (8S8C was wrong because it's *holo*, not because of genotype) is a
  different kind of check -- presence/absence of a ligand code in the
  raw, un-cleaned structure, which `CleanResult` does not carry (ligand
  data is stripped during cleaning; only added back for holo elsewhere,
  in `run_challenge.py`, via a separate raw parse). Named explicitly as a
  distinct, not-yet-built companion check rather than silently claimed as
  covered by the genotype guard, which cannot catch it (8S8C's own
  residue 12 is genuinely CYS -- correct genotype, wrong role).
