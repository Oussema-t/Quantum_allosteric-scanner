# TASK-0224 `WORKFLOW.md` — the canonical pipeline, with the assertion at every step

## Context

- ID: TASK-0224
- Title: write the step-by-step account of how this project actually attempts
  the challenge, with each step's **assertion**, its **failure mode**, and the
  task that discovered it.
- Status: Done
- **Thread: Architect/Planner.** Synthesis, no compute.
- Owner: Architect/Planner
- Claimed By: —
- Claimed At: —
- Source: Bartosz, 2026-08-19 — "we are not really storing a step-by-step
  intent/algorithm/workflow of how we are right now attempting to solve the
  challenge," with two worked examples (apo/holo chain correspondence;
  pre-opened apo structures).
- Priority: **P0.** It is a required submission component, not only an
  internal artifact — Submission Guidelines §4.3 item 2 asks for *"a clear
  description of the proposed method, algorithm, or workflow."*

## The gap

The repository holds ~220 task files and a ~6,000-line result register, and
**no document states the pipeline end to end.** A reader cannot currently
answer "what does this project actually do, in order?" without reading the
register.

That is a gap in two places simultaneously:

1. **Process.** Every step below was discovered *reactively*, mid-task, rather
   than existing as a named step with an assertion attached. Each cost a
   correction cycle, and several silently produced published numbers first.
2. **Submission.** §4.3 item 2 requires exactly this description, and §8's
   tips reinforce it: *"Show your working: explain the technical approach
   clearly enough that a non-specialist reviewer can follow the logic."*

## What makes this document worth writing rather than a flowchart

The valuable artifact is **not** a diagram of boxes. It is the pipeline
**with each step's assertion and what happens when the assertion fails** —
because that table is where this project's actual contribution lives. Every
significant finding of the 2026-08 window is a failed assertion at a named
step:

| # | Step | Assertion | Failure actually found |
|---|---|---|---|
| 1 | Resolve the apo/holo pair | Both entries are the same protein; chain letters correspond | GLUCOKINASE `chain="X"` vs apo chain A ([[TASK-0219]]); GLUR2 holo chain B vs apo chain A ([[TASK-0216]]); PTP1B recorded as 8QYP/8QYR in a pre-registration when it is 1SUG/1T49 |
| 2 | Assert the apo is genuinely unliganded **at the site** | No non-buffer HETATM within the pocket cutoff | BCR-ABL1 `MYR` at 3.47 Å; GLUCOKINASE `MRK` at 2.45 Å ([[TASK-0209]]) — both hold the "apo" pocket open |
| 3 | Assert the pair expresses the contrast | apo scores closed **and** holo scores open | 5 of 7 fail; 2 of 3 mandated ([[TASK-0209]]) |
| 4 | Assert index spaces correspond | apo/holo residue arrays align before indices cross between them | Holo heavy-atom indices written into an apo-sized mask ([[TASK-0216]]) |
| 5 | Derive the active site | `func_ligand` is a chem-comp code, not prose; provenance is real, not a fallback | 9 of 13 targets silently seeded at the top-5 highest-degree residues ([[TASK-0216]]) |
| 6 | Build the contact graph | cutoff stated; disconnected components handled | cutoff sensitivity swept ([[TASK-0067]]/[[TASK-0113]]) |
| 7 | Propagate | converged limit, not a truncated clock | shipped `t_max=15` was 10⁴–10⁵× short ([[TASK-0159]]) |
| 8 | Score | must beat the **proximity floor**, not chance | KRAS's headline failed the floor once it existed ([[TASK-0094]]) |
| 9 | Test significance | null must match the label's own geometry | three null generations, each fixing the last ([[TASK-0158]] → [[TASK-0190]] → [[TASK-0201]]) |
| 10 | Interpret | criterion must be able to return each verdict; a positive control must exist | [[TASK-0204]] D1/D2, [[TASK-0208]] V1, [[TASK-0189]] |

**That table is the methodological contribution.** It is currently scattered
across a dozen task files and reconstructible only by someone who has read all
of them.

## Intent Contract

- Outcome: `__WORK_IN_PROGRESS__/documentation/WORKFLOW.md` — the canonical
  end-to-end pipeline: what each step does, what it asserts, what happens when
  the assertion fails, and which task established that failure mode. Written
  so it can be compressed into §4.3 item 2 without rewriting.
- Why required, not assumed: it is a scored submission component; and every
  step above was learned the expensive way, so recording them is what prevents
  step 11 being learned the same way.
- In Scope:
  - The pipeline as it **actually is today**, not as originally designed.
    Where the shipped path differs from the intended one, say so.
  - Per step: inputs, outputs, the assertion, the failure mode, the guard (if
    one exists), and the task reference.
  - **Mark which assertions are currently enforced in code vs. only
    documented.** [[TASK-0217.001]] is auditing exactly this; several are
    documentation-only today, and the document must not imply otherwise.
  - A short "what this pipeline cannot do" section — the apo-only input, the
    Cα/8 Å resolution bound, the single-conformer assumption.
- Out Of Scope:
  - Building new guards ([[TASK-0217.001]] owns that).
  - Re-running anything.
  - The Phase-2 forward method ([[TASK-0183]]).
- Constraints And Invariants:
  - Every claim traceable to a task or a file path. No idealised steps that
    the code does not perform.
  - Where a step's assertion is unenforced, that is stated in the same
    sentence — a workflow document that reads as more rigorous than the code
    is worse than none.
- Planned Validation:
  - Walk one real target (KRAS_G12C) end to end through the written document
    and confirm each step matches what the code does, in order.
  - Confirm each of the 10 failure modes above is traceable to its cited task.

## TODO

- [x] Enumerate the pipeline as shipped, in order, from `run_challenge.py`.
- [x] Per step: inputs/outputs/assertion/failure/guard/task.
- [x] Mark enforced-in-code vs. documented-only. Used a 3-way
      distinction (Enforced / Enforced downstream / Documented-audited,
      not gated) since a plain binary flattened real cases (e.g. Step 6's
      connectivity check: `clean.py` only warns, the real hard gate is
      `superpose.py`'s ANM nullspace check, a different module entirely).
- [x] "What this pipeline cannot do" section.
- [x] Walk KRAS_G12C through it as validation — `--dry-run` confirmed
      config resolution; each of the 10 steps traced to its real call in
      `run_target` for this target specifically.
- [x] Hand the compressed form to [[TASK-0184]] §4.3 item 2 — a
      ready-to-paste paragraph is in `WORKFLOW.md`'s own closing section;
      not copied into TASK-0184's file itself (that document's own
      narrative-freeze content is another thread's active concern, per
      the Merge Conflict Protocol — a pointer was added instead, see Done).

## Dependency

- [[TASK-0217.001]] — supplies the enforced-vs-documented status.
- Feeds [[TASK-0184]] (§4.3 item 2) and [[TASK-0183]].

## Done

**2026-08-19, Architect.** `__WORK_IN_PROGRESS__/documentation/WORKFLOW.md`
(new, ~260 lines). Picked up after overriding a 5h20m-stale claim by
Reviewer-thread (Opus) — no `WORKFLOW.md` existed on disk yet, no work to
lose, override authorized directly by the orchestrating user in-session.

Transcribed the shipped pipeline from `scripts/run_challenge.py::run_target`
itself (read end to end, not from design notes), against the 10-step table
this task's own pre-registration named. Per step: what the code does (file:
line), the assertion, a 3-way enforcement classification (**Enforced** — code
raises; **Enforced downstream** — a later, different gate catches it as a
side effect, named explicitly; **Documented/audited, not gated** — a separate
script checks it, `run_challenge.py` does not), and the failure actually
found with its task citation.

**Enforcement findings worth flagging on their own** (not just a transcript
of already-known task summaries):
- Step 1 (apo/holo chain correspondence): the per-target
  `apo_chains`/`holo_chains` override is opt-in — a target without it gets
  **no** correspondence check beyond coincidence, only `align_apo_holo`'s
  coarse `<3-common-pairs` raise.
- Step 6 (disconnected contact graph): `clean.py` only warns, deliberately
  (TASK-0038, resolved 2026-08-14, checked against the module's own current
  docstring) — the real hard gate is `superpose.py`'s ANM nullspace check, a
  different module a reader would not necessarily think to check.
- Steps 2, 3, and the corrected-null half of Step 9: **not gated by
  `run_challenge.py` at all** — genuinely separate, human-invoked audit
  layers ([[TASK-0209]] for 2/3; per-claim significance scripts for 9). A
  target with an invalid closed→open contrast, or a positive whose
  significance was never re-tested under a corrected null, will still run
  and report a diagnosis with nothing in the code path objecting.

**One real error caught by this task's own verification step and fixed
before publishing**: the first draft of Step 7's failure-mode paragraph
cited fabricated truncation-magnitude numbers and misattributed the finding
to [[TASK-0110]]/[[TASK-0146]] (neither actually about this). Re-grepped
[[TASK-0159]]'s own COMMON.md row directly and replaced with the real,
sourced numbers (83,834×–420,682× short, closed-form independently validated
by brute-force integration to 1e-6/1e-7 agreement, PTP1B's verdict flip
0.4859 vs. 0.2050) and the correct single citation. Recorded here per this
project's own convention of not silently patching a caught error — this is
exactly the failure mode ("a workflow document that reads as more rigorous
than the code is worse than none") the task's own Constraints warned against,
now also true of unverified citations, not just unverified code claims.

**"What this pipeline cannot do" section** includes a finding not in the
original pre-registered table: KRAS_G12C's own apo structure is wild-type,
not G12C, and the register's own apo-structure sensitivity sweep
([[TASK-0155]]/[[TASK-0192]]) found the target is a lucky-draw outlier among
10 verified true-G12C structures (median AUC 0.482, P@5=0.000 on all ten) —
included because a submission-facing pipeline document that omits this about
its own flagship target would itself be the kind of gap this task exists to
close.

**Walkthrough**: KRAS_G12C's config confirmed resolvable
(`run_challenge.py --dry-run`); each of the 10 steps traced to its real call
site for this specific target, including which steps (2, 3) are known to
*not* run for it (validated separately as VALID by [[TASK-0209]]'s own
audit, not by anything in `run_challenge.py` itself).

**Not done**: did not edit [[TASK-0184]]'s own file — that document is mid
active narrative-freeze work by another thread; added a one-line pointer to
its registry row instead (see `COMMON.md`), per the Merge Conflict Protocol's
own convention (don't touch a file mid-claim by a concurrent thread; a
pointer costs nothing and loses no information). Did not build any new
guard — [[TASK-0217.001]] class work owns that, explicitly out of scope here.
Did not re-run anything beyond the `--dry-run` config check.
