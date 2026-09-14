# TASK-0383 — Publish the repo before the deadline and flip the proposal to present tense

- Status: **UNBLOCKED 2026-09-14** — [[TASK-0382]] resolved; the organisers'
  fairness concern is answered by the note now in
  `03_Problem_Statement_Selection.pdf`. **Waiting on Oussema**, who owns the
  repo and was asked by the Team Lead to publish it today.
- **Checked 2026-09-14 15:30: still HTTP 404.**

- Owner: **Team Lead** (only Bartosz can push/publish)
- Priority: High — cheap, and it removes an asymmetric risk
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §A2
- Related: [[TASK-0382]] — **0382 must be resolved first; publishing before it is resolved is the harm.**

## Verified

`curl` against `github.com/Oussema-t/Quantum_allosteric-scanner` returns
**HTTP 404** as of 2026-09-13. The Concept Proposal states the repository is
published **2026-09-15** — which is the Phase-1 deadline itself.

## Why it matters more than it looks

§1, §5, §7 and both package READMEs rest on *"we made this checkable rather than
asking to be believed."* A reviewer who clicks on 15 Sep at 09:00 UTC and gets a
404 reads that sentence as a bluff — and it is the sentence the whole document's
credibility is staked on. The risk is asymmetric: publishing a day early costs
nothing, publishing on the deadline risks the central claim.

## Do

1. Resolve [[TASK-0382]].
2. Publish **2026-09-14**, before upload.
3. Change the Concept Proposal from a future date to a plain present-tense
   statement ("The repository is public at …"). Also update
   `SUBMISSION_PACKAGE/README.md` open item 2, which currently flags this.
4. Rebuild `01_Concept_Proposal.pdf` and re-run the page check — the body is at
   **6/6 with no slack**, so confirm the reworded sentence does not reflow to 7.

## Done when

Repo resolves 200 for a logged-out client, the proposal says so in present tense,
and the rebuilt PDF still reports body 6/6 PASS.

---

## Status note — 2026-09-14, Reviewer thread

**The wording flip is deliberately NOT done yet.** The proposal currently reads:

> Full history, retractions included: `github.com/Oussema-t/Quantum_allosteric-scanner` (branch `bartosz`), published 2026-09-15.

That is **true as written** — a future-dated statement, and 2026-09-15 is the
deadline. Changing it to present tense while the repo returns 404 would make the
document **false**, which is strictly worse than the 404 risk it was meant to
fix. Flip it only once the repo actually resolves.

**When it does resolve, the edit is 30 seconds and it *frees* page budget:**
delete `, published 2026-09-15` — five words out of a body sitting at exactly
6/6. Rebuild and re-check.

### If Oussema does not publish and we clone instead — read this first

**The URL appears in two shipped files, not one:**

| file | where |
|---|---|
| `PHASE1_SUBMISSION_V4.md` | §7, the "Full history, retractions included" sentence |
| `SUBMISSION_PACKAGE/02_Team_Profile.md` | the **Repository** row of the verification table |

A clone under a different account changes the URL in both, and **both PDFs must
be rebuilt** — `01_Concept_Proposal.pdf` *and* `02_Team_Profile.pdf`. The Team
Profile is the one most likely to be forgotten, because it has not been rebuilt
since 2026-09-13 18:42 while everything else has.

Also: a clone loses the commit history, and §7's claim is specifically *"the full
task history, including every retraction"*. If we clone, clone with history
(`git clone --mirror` then push), not a snapshot — otherwise the sentence stops
being true in a second way.

### Do TASK-0387 item 4 in the same rebuild — the budget lines up

[[TASK-0387]] shipped 5 of its 6 items and dropped **item 4** (cardiac myosin is
*Bos taurus* and the scored document never says so) purely for page budget.
Verified 2026-09-14: `bovine`/`Bos taurus` still appears **0 times** in
`PHASE1_SUBMISSION_V4.md`.

Deleting `, published 2026-09-15` frees ~22 characters. A minimal species
disclosure costs less than that. **So the repo going live is also the moment
item 4 becomes affordable** — one edit, one rebuild, one page check.

Why it is worth the words: our stated objection to Table 1's `6C1H` is partly a
*species* objection (rat myosin-Ib on rabbit actin). Scoring our own substitute
without disclosing it is bovine leaves that asymmetry visible to any reviewer who
opens the PDB entry, and the defence is strong — bovine β-cardiac myosin is a
near-identical orthologue of the human target, whereas myosin-Ib is a different
class entirely. We just have to make it.

**Residual, not worth the page:** §1 names `4LDJ` (GDP·Mg) and `8QYP`
(ADP·VO4·Mg) as our own non-ligand-free inputs but still omits `1OPL`'s second
ligand, the ATP-site inhibitor `P16`. It is disclosed in `Solution_Outputs.pdf`.
Add it only if the flip frees more than expected.
