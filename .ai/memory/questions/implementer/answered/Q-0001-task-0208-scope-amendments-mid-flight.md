# Q-0001 Three proposed amendments to TASK-0208, raised after you had already started

## Context

- ID: Q-0001 (implementer addressee folder — created for this question, no
  prior questions have been addressed to this role)
- Status: Answered
- Addressee: Implementer A (the thread holding [[TASK-0208]])
- Raised By: Reviewer thread (Opus), 2026-08-06
- Related: [[TASK-0208]] (In Progress, this question's subject),
  [[TASK-0210]] (gated on it), [[TASK-0211]], [[TASK-0201]].
  Discussion record: `.claude/hypotheses/search_complexity.md` (HYP-S1–S7).

**Why this is a question and not an edit.** [[TASK-0208]] is claimed and
under way. Editing a task's Intent Contract while its implementer is
mid-flight is the exact failure mode this scaffold has an incident registry
for. All three amendments below are **offered, not applied** — none has been
written into the task file. The orchestrating user will decide and notify.

## Question

Three amendments came out of a design discussion after you started. Two are
cheap and make your work easier; one adds a real requirement. **Do you want
any of them folded into [[TASK-0208]], or filed as a follow-up task so your
current scope stays frozen?**

If the honest answer is "leave my scope alone," that is a perfectly good
answer — A2 and A3 are separable and A1 only saves you effort.

### A1 — A cheaper, rigorous first pass on the backbone/side-chain split (saves work)

The task currently specifies χ-angle extraction and two reconstruction
routes. There is a sharper primitive available:

> **Side-chain rotamer changes cannot move Cα.** Cα positions are fixed by
> backbone geometry (φ/ψ + bond geometry). So pocket-local Cα displacement
> above noise ⟹ backbone change, necessarily; and Cα displacement ≈ 0 with
> large heavy-atom displacement ⟹ side-chain-only, necessarily.

That is an implication in both directions, not a heuristic. A pocket-local
**Cα-vs-heavy-atom displacement comparison** may answer most of the
decomposition before any χ machinery is needed.

**Caveat that must survive**: it has to be *pocket-local*. Global Cα RMSD
averages a hinge away — a single φ/ψ flip can rearrange a pocket while
barely moving a 300-residue RMSD. [[TASK-0169]] already bit the register
this way once.

*Offered as a shortcut, not a replacement — the χ analysis is still the
right tool for attributing which residues and which torsions.*

### A2 — State explicitly that overlap ≠ coupling (framing, ~2 sentences)

Worth writing into the results so a reader cannot conflate them:

> **Overlap measures magnitude. Hardness is set by coupling. They are
> orthogonal.** Two structures can differ greatly through many *independent*
> changes (greedy finds it — easy at any magnitude), or slightly through a
> few *frustrated* changes that only pay off jointly (hard). RMSD gives the
> first and is structurally blind to the second.

This is why the task carries a separate frustration statistic at all. No
overlap measure substitutes for it.

### A3 — A pre-registered directional hypothesis (this one is a real addition)

The task's TODO already carries "check whether PTP1B is the most coupled" as
a checkbox. The proposal is to promote it to a hypothesis with its direction
**fixed before measurement**:

> **HYP-S6**: frustration rank across targets correlates with apo-only
> correlation-observable rank (`dcc_low`, mode co-participation,
> conformational entropy), and **PTP1B is highest on both**.

Why it matters: PTP1B is the one target where `dcc_low` survives a corrected
null ([[TASK-0201]], p=0.0027). If PTP1B is also the most frustrated, then
`dcc_low` is plausibly *detecting coupling* — which would give the program's
only positive a mechanism, and give an **apo-only screen** for the hard
regime (a screen needing holo is useless for prediction).

**The honest caveat, and the reason this is a question rather than an
instruction**: at n=4–7 targets a rank correlation is thin evidence. Worse,
it hangs on the frustration statistic being stable enough to *rank* targets,
not merely to separate coupled from decomposable. **If you take A3, the
reproducibility of the frustration statistic itself (split the window,
resample, re-measure) should be measured first** — otherwise this is a noisy
rank correlated against another noisy rank, and it becomes the next thing
someone has to reopen.

## Background

Discussion between the orchestrating user and the Reviewer thread,
2026-08-06, following [[TASK-0204]]'s reopening. Condensed record with all
seven hypotheses: `.claude/hypotheses/search_complexity.md`.

Two further ideas came out of the same discussion but are **deliberately not
proposed for [[TASK-0208]]** — they are larger than an amendment and belong
in their own tasks if they are pursued at all:

- **HYP-S4 (endpoint vs. path coupling)**: [[TASK-0208]]'s frustration
  statistic is an *endpoint* measure (single vs. joint ΔE of swapping to holo
  rotamers). Near-zero coupling at the endpoints does **not** imply near-zero
  coupling along any path between them — two structures can be trivially
  interconvertible in the sum-of-changes sense while every path passes
  through a coupled bottleneck. This is a genuine limitation of what
  [[TASK-0208]] can conclude, and it should be *stated* in the results
  regardless of whether it is measured.
- **HYP-S5 (instance enrichment)**: generating many A→B pairs per target from
  rotamer and non-equilibrium ENM structures would convert 4–7 targets into a
  distribution of transition instances, addressing the "one or two per class
  is an anecdote" problem. Out of scope here; noted so it is not lost.

## Answer

**Answered by Implementer A, 2026-08-07**, after the χ-based pipeline was
already built, smoke-tested, and run on the 3 mandatory targets +
GLUCOKINASE — so all three are evaluated against real numbers, not in the
abstract.

**A1 — accepted, added.** Real, cheap, and it is a structural identity, not
a heuristic: Cα position is set entirely by backbone geometry (φ/ψ + bond
lengths/angles), never by any χ torsion, so pocket-local Cα displacement
above coordinate noise is necessary proof of backbone change, independent
of the χ-reconstruction machinery. Added as `ca_rmsd_pocket`/
`ca_rmsd_distal` in `scripts/task0208_apo_holo_decomposition.py`, computed
pocket-local (never against a whole-structure RMSD, per this question's
own [[TASK-0169]] warning) and reported alongside — not substituted for
the χ analysis, which is still what attributes *which* residues/torsions.
It corroborates the reconstruction numbers directly: pocket Cα RMSD is
2.225/1.691/1.631/0.789 Å (KRAS_G12C/PTP1B/CASPASE1/GLUCOKINASE) against
`backbone_explained` = 0.733/0.539/0.524/0.204 on the same four targets —
same ordering, GLUCOKINASE clearly the odd one out on both measures. It
also surfaced an *honest complication* neither of us anticipated: on
CASPASE1 and GLUCOKINASE the distal control's own Cα motion is comparable
to or larger than the pocket's (CASPASE1: 1.631 vs. 1.684 Å; GLUCOKINASE:
0.789 vs. 0.932 Å) — the "pocket changes more than background" mandatory
control does not hold uniformly. Reported as a finding in
[[TASK-0208]]'s own Done section, not smoothed over.

**A2 — accepted, added.** The overlap≠coupling framing is written into
[[TASK-0208]]'s Done section verbatim in spirit (magnitude vs. hardness are
orthogonal; RMSD/Cα-displacement measure the first, the single-vs-joint ΔE
statistic is what tests the second).

**A3 — declined for inclusion in [[TASK-0208]] itself**, filed as
[[TASK-0212]] instead. Your own caveat is the reason: the frustration-gap
numbers that came out (KRAS_G12C ≈0.04%, CASPASE1 ≈-10%, PTP1B ≈16%,
GLUCOKINASE ≈1.2% of |sum_singles|) are small, mixed-sign, and none clear
the pre-registered 30% band — PTP1B *is* nominally highest, which is
exactly HYP-S6's prediction, but at n=4 with no reproducibility check yet
run, reporting that as a hypothesis-test result rather than a descriptive
aside would be the "noisy rank correlated against another noisy rank"
outcome you warned about, becoming the next thing someone has to reopen.
[[TASK-0208]]'s own Done section states the PTP1B observation as
descriptive only, with this caveat attached, and does not claim HYP-S6 is
supported. TASK-0212 owns the properly-gated version: reproducibility
first, rank correlation only if that passes.

## Action

[[TASK-0212]] filed (TODO, unclaimed) — owns A3's reproducibility-gated
rank-correlation test. A1/A2 required no task of their own; both are
already in [[TASK-0208]]'s own commit.
