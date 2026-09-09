# TASK-0353 — A submission version ledger: what each version fixed, and what must not regress

- Status: TODO
- Owner: **Reviewer thread**, maintained by whoever makes each drafting pass
- Priority: High — cheap, and it is the only thing preventing a silent regression
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0332]], [[TASK-0339]], [[TASK-0351]], [[TASK-0307]]

## Why

Three submission versions now exist and a fourth is likely before 2026-09-15.
Each was a substantial rewrite, and **the reasons for individual sentences are
scattered across a dozen task files and two adversarial reviews.** Two failure
modes follow, and both have already happened once:

- **Silent regression.** V2 was a ground-up rewrite of V1 and it *dropped c-Myc*
  — a mandated minimum-set target that [[TASK-0339]] had deliberately added to V1
  four days earlier. Caught by the repo owner, not by us.
- **Losing the argument for a fix.** Several V2 sentences are worded the way they
  are because a specific measurement forced it. Nothing in the document records
  which, so the next editor can undo a correction without knowing it was one.

## Intent Contract

- Outcome: `documentation/SUBMISSION_VERSION_LEDGER.md` — one section per version,
  each row: **what changed · why (task or review id) · what must not regress.**
  Not a diff; a diff shows *what*, and the whole point is *why*.
- **Populate it retroactively for V1 → V2 → V3 first**, from the existing task
  record, before it is used going forward. That is the expensive half and it is
  also the half that captures reasoning still fresh enough to recover.
- Known entries to seed it with (not exhaustive):

  | version | change | why | must not regress |
  |---|---|---|---|
  | V1 | seven-item ToC, §8 moved out | Guidelines §4.3 mandates seven items | ToC stays exactly 7 |
  | V1 | c-Myc subsection added | mandated minimum set | **dropped by V2; restored — do not drop again** |
  | V2 | MYR reframed as physiological autoinhibitor | it is myristate, not an unexplained ligand | never call it "unexplained" |
  | V2 | "no quantum work exists" never claimed | the sponsor's own group published one | never claim the domain is untouched |
  | V2 | prior art cited, delta stated | a JACS paper published our construction | always cite it and state the delta |
  | V3 | "1 of 3 / 1 of 4" → "2 of 7, and 49% at scale" | [[TASK-0346]] — the strong claim did not hold | do not restore the stronger wording |
  | V3 | coherent-vs-decoherent result added | [[TASK-0350]] — well-powered null, p=0.92 | report it as *well-powered*, not merely null |
  | V3 | finite-T convergence check added to §5 | [[TASK-0350]] — 50/108 verdicts flip | keep; no published lineage reports this |

- **Each row cites its evidence.** A row without a task id is an opinion, and
  opinions are what the next editor is entitled to overrule.
- Constraints:
  - Keep every prior version file on disk. The point is visible improvement;
    deleting V1/V2 destroys the comparison.
  - The ledger is **not** shipped to the organisers. It is an internal artifact,
    like `REVIEW_TARGETS.md`.
  - Keep it short. A ledger nobody reads is [[TASK-0321]]'s failure again, and
    this one is small enough to stay readable if it stays terse.
- Planned Validation: for each shipped version, the ledger's "must not regress"
  column must be checkable against the current draft in one pass. Do that check
  as part of every future drafting pass — it is the mechanism that would have
  caught c-Myc.

## Note

This pairs with [[TASK-0352]]'s Part B rather than duplicating it: that check
reconciles *task state*, this ledger records *document decisions*. Neither
substitutes for the other, and both exist because the same thing keeps happening
— the reasoning is recorded somewhere, and not where the next person looks.
