# TASK-0340 — Verify the container from a cold clone, and wire doc_parity into CI

- Status: TODO
- Owner: **Implementer D** / Toolsmith
- Priority: High — cheap, and one item protects a criterion-2 claim
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-07/...adversarial-submission-audit.md` §3.1, §3.10
- Related: [[TASK-0333]], [[TASK-0332]], [[TASK-0307]]

## 1. The container blocker does NOT hold — but verify it the right way

The review called this a BLOCKER: `Dockerfile.pipeline` COPYs three paths under
the `__WORK_IN_PROGRESS__/results/` ignore rule with no negation in `.gitignore`,
so a cold clone would die at COPY. **It could not check, having no `.git` in its
snapshot. Checked here:**

```
git ls-files __WORK_IN_PROGRESS__/results/tasks/0318_input_space_ceiling/  -> 107 files
git ls-files .../0304_.../asbench_annotations.json                         -> tracked
git ls-files .../0305_.../asbench_detection.json                           -> tracked
```

All three are **tracked** — force-added by [[TASK-0333]] in `ff0979d`. The
`.gitignore` negation the review proposes is unnecessary; git tracks what it was
told to track regardless of ignore rules.

**What still needs doing**, because [[TASK-0333]]'s validation ran on the authoring
machine where untracked files are also present:

- Clone the public repo to a scratch path, check out `bartosz`, and run
  [[TASK-0333]]'s validation **from there**. That is the only run that tests what
  [[TASK-0332]]'s brief asserts ("reproduces the §2 headline byte-for-byte from a
  cold clone").
- Confirm 105 `.npz` files land in `feature_cache/` from the clone alone.
- If it passes, the claim is safe to write. If anything is missing, apply the
  review's negation block and force-add before v2 quotes the claim.

**Do not write the reproducibility sentence into the draft until this run exists.**
A broken build is the first thing a diligent judge hits, and it converts the asset
into a liability.

## 2. Nothing enforces doc parity — verified

`grep -rn doc_parity` outside `.ai/tools/` returns nothing. `.github/workflows/`
holds one file, `keepalive.yml`, pinging a Render health endpoint every 10
minutes. **There is no CI running tests, parity, or reference checks.**

Parity holds today (the reviewer ran it: exit 0). It will not survive v2, which
touches both twins in several places, unless something enforces it. [[TASK-0332]]'s
Constraints already say "wire it here" and it was not wired.

Add a workflow triggered on pushes touching the two submission paths, running
`doc_parity.py` on the pair. ~15 lines; the review's §3.10 has a working draft.
CI rather than a local pre-commit hook, because the repo owner sometimes edits on
GitHub directly (`CLAUDE.md` convention 6) and a local hook would not fire.

## 3. Two more review findings that do not hold — recorded so they are not re-filed

- **§3.6 "the Submission Guidelines are not in the repo"** — they are:
  `documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.{md,pdf}` both
  present. The snapshot was a working tree without them staged.
- **§3.4 "`no_proximity_feature_check.json` does not exist"** — it does. The real
  defect there is narrower (no script regenerates it) and is [[TASK-0338]] Part B.

Both were correctly marked by the reviewer as inference from an incomplete
snapshot rather than asserted as fact. Recording the resolution here so the next
reader of that review does not chase them again.
