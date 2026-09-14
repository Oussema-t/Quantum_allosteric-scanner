# TASK-0382 — BLOCKER: publishing the repo publishes the organisers' private reply verbatim

- Status: Done
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

---

## Resolved — 2026-09-14. Organisers answered; Option 2 succeeded.

**Their reply, relayed by the Team Lead:**

> Within your submissions, please just add a note documenting how some of your
> answers were submitted based on the following responses received by the
> Cleveland Clinic team "…". This will ensure you are neither put at advantage
> nor at disadvantage vs other teams in regards of your submission evaluation.

**What they granted, and what they did not.** They named a remedy — disclosure
inside our submission — and framed the whole matter as **evaluation fairness**.
They did *not* say "you may republish our private correspondence publicly", and
the distinction matters: our submission is read by evaluators, the repository is
read by everyone including competing teams. **The note satisfies their
instruction. It does not by itself settle the repo question.**

### Done: the note is in the submission

Added to `03_Problem_Statement_Selection.md` as **"Note on organiser
correspondence"**, opening with the organisers' own stated purpose (neither
advantaged nor disadvantaged). It documents each reply and what it changed:

| reply | changed |
|---|---|
| 2026-08-26 — cardiac `8QYP`–`8QYR` accepted as primary | the scored cardiac structures |
| 2026-08-26 — `8S8C` suggested for KRAS G12C | we checked it, found it **holo**, substituted `4LDJ` |
| 2026-08-26 — BCR-ABL1 may be substituted, *"please document the rationale"* | we **declined**; rationale given, as they asked |
| 2026-08-26 — no prescribed formats | the five-file package, CSV rather than an archive |
| 2026-09-07 — documents may be re-uploaded | nothing in the science |
| 2026-09-08 — ENM allowed; MD-trained/MD-free inference permitted | PocketMiner kept as the veto |

Closing line, deliberate: *"These replies granted latitude on structure choice
and deliverable format. They did not endorse any finding in this submission, and
no finding here is presented as endorsed."* That matches the caution the
clarification file itself records — answers 2 and 4 are substantively responsive
to our benchmark-validity finding but are **not** an endorsement of it.

`03_Problem_Statement_Selection.pdf` rebuilt: 2 pages, `RESULT: PASS`,
text-extraction verified.

### Still the Team Lead's call: the file in the public repo

Reviewer's read, for the record. Publishing the verbatim file is now **low risk
and defensible** — the content is disclosed in our own submission, the
organisers treated it as a fairness matter rather than a confidence, and Phase 1
closes 2026-09-15 so any competitor window is hours. But it is still not
something they explicitly authorised.

**Recommendation: keep the file, and add one line to its header** — *"Disclosed
in our Phase-1 submission at the organisers' instruction, 2026-09-13"* — so the
repo and the submission tell the same story. Redacting now would be inconsistent
with having just documented the content ourselves.
