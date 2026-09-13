# TASK-0382 — BLOCKER: publishing the repo publishes the organisers' private reply verbatim

- Status: IN PROGRESS — **BLOCKER. Must be resolved before the repo is made public.**
  Team Lead decision (2026-09-13, Bartosz): pursuing **Option 2**. Asked the
  Cleveland Clinic organisers directly whether we may publish their prior
  replies verbatim in the repo, or whether we are required to remove/redact
  them. Awaiting their answer. Do not publish the repo, and do not action
  Option 1 or 3 pre-emptively, until that answer is recorded here.
- Owner: **Team Lead only.** This is a disclosure decision, not an edit. Do not action without Bartosz.
- Priority: **Highest open item in the submission. Ahead of every content fix.**
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §A1
- Related: [[TASK-0383]], [[TASK-0221]]

## The exposure, verified

`__WORK_IN_PROGRESS__/documentation/2026-08-26-organiser-clarifications.md` is
**tracked** and carries its own header, quoted from the file:

> **Status: OFFICIAL. Private response to Team AuraQu.**
> **This is a direct reply to questions we sent; it is NOT a public update to
> the Challenge Statement.** … Other teams may therefore be working to Table 1
> as originally published.
> Recorded here verbatim and unedited.

Checked directly: **18 tracked files reference it.** Concept Proposal §7 and the
Team Profile both direct reviewers to
`github.com/Oussema-t/Quantum_allosteric-scanner` (branch `bartosz`).

On the publication date, every competing team gains the Cleveland Clinic team's
structure suggestions and format latitude, unedited, **because we published
them**. The file itself states the organisers did not issue a public revision.

## Why this outranks everything else

T&C §10 covers conduct "harmful to other Participants… or the integrity of the
Challenge". The team whose entire pitch is procedural rigour would be the team
that leaked the organisers' private guidance to the field. The reputational cost
is the exact currency this submission is trying to buy.

Do **not** resolve it on the theory that T&C §7 only binds finalists. That
reading protects us legally and costs us the thing we are competing on.

## Three options, in the reviewer's order of preference

1. **Redact the verbatim block** before publication; keep our own consequences
   section; cite the clarification by date rather than content.
2. **Ask the organisers for permission to publish it.** The channel is live and
   has answered four times. If they say yes it is on the record for everyone and
   the exposure inverts into an asset. **Costs a round-trip we may not have.**
3. **Publish the repo minus that file**, and state in the Concept Proposal that
   one primary-source document is withheld at the organisers' discretion.

Reviewer's read: **2 if there is time to ask today, 1 as the fallback.** 1 is
~10 minutes of work; 2 is free but has latency; 3 is cheapest but weakens the
"checkable rather than believed" argument slightly, since the one document a
sceptic most wants is the one missing.

## Status log

- 2026-09-13, Bartosz (Team Lead): Chose Option 2. Sent the question to the
  Cleveland Clinic organisers via the live channel — asking permission to
  publish their prior clarification replies verbatim, vs. being required to
  remove them from the public repo. Waiting on their reply. Publication stays
  blocked until an answer is recorded here (or the Team Lead decides to fall
  back to Option 1/3 without waiting further).

## Done when

- A decision is recorded here by the Team Lead, with date.
- If 1 or 3: the change is made **and** the 18 referencing files are checked for
  quoted fragments that would reconstitute the content (`grep -rn` for
  distinctive phrases, not just the filename).
- If 2: the organisers' answer is recorded in the repo before publication.
