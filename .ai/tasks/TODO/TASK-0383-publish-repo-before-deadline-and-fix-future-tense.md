# TASK-0383 — Publish the repo on 2026-09-14 and change the proposal's wording to present tense

- Status: **BLOCKED on [[TASK-0382]].** The Team Lead asked the organisers
  (2026-09-13) whether their replies may be published verbatim. **Do not publish
  the repo until that answer lands** — publishing is the harm 0382 describes, and
  it is irreversible once other teams have the file.
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
