# Organiser clarifications — Cleveland Clinic team, received 2026-08-26

**Status: OFFICIAL. Private response to Team AuraQu.**

**This is a direct reply to questions we sent; it is NOT a public update to
the Challenge Statement.** Checked 2026-08-26: no corresponding revision to
the Challenge Statement available to all teams. Other teams may therefore be
working to Table 1 as originally published. Any submission claim that depends
on a substitution below **must cite this clarification explicitly**, because a
reader holding only the public Challenge Statement will otherwise see an
unexplained deviation from a mandated structure pair.

Recorded here verbatim and unedited. Our reading and its consequences are in
the separate section below and must not be confused with the organisers' own
words.

> **Filing note.** This belongs conceptually beside
> `documentation/Cleveland-Clinic-Challenge-Statement-vF-1.md` at the repo
> root, but `.gitignore:39` ignores `documentation/*.md` (the Challenge
> Statement itself is tracked only because it was force-added). Rather than
> override that rule silently, this primary-source document is filed here
> where tracking is normal. **If the root `documentation/` folder is the
> intended home for official challenge material, this should be moved and
> force-added — a decision for the repo owner, not one to take silently.**

---

## Verbatim response

> Kindly find as follows the responses to your questions.
>
> 2.  A nice structure for KRAS G12C would be 8S8C.
> 3.  Cardiac Myosin - Your 8QYP – 8QYR substitution is accepted as primary.
> 4.  BCR-ABL1 — you may substitute 1OPL with an alternative apo structure that fits your pipeline. Please document the rationale in your submission.
> 5. No specific formats are prescribed. Please use formats accessible with conventional software.
>
> Hope this helps and good luck with your submission!

---

## Mapping onto our own question list ([[TASK-0221]] §3)

Our questions were lettered (a)–(f); the reply is numbered 2–5. Mapping, with
what remains open:

| their no. | our question | status |
|---|---|---|
| 3 | **(a)** Cardiac Myosin's mandated structures — is 8QYP→8QYR acceptable? | **ANSWERED — accepted as primary** |
| 5 | **(c)** Deliverable format | **ANSWERED — no prescribed formats** |
| 2, 4 | **(b)** the benchmark-validity finding | **Substantively responsive, not directly answered** — see below |
| — | **(g)** may a submitted document be revised / re-uploaded? | **ANSWERED 2026-09-07 — yes, unlimited** |
| — | **(d)** which reference governs when the bibliography contradicts itself | **UNANSWERED** |
| — | **(e)** does Constraint 3 exclude minimisation / Monte-Carlo sampling? | **UNANSWERED** |
| — | **(f)** does Constraint 3 exclude an MD-*trained* tool with MD-free inference? | **UNANSWERED — gates [[TASK-0269]]** |

**On (b).** The organisers did not address the benchmark-validity audit in
words, but answers 2 and 4 respond to it in substance: they offered an
alternative KRAS G12C structure unprompted and granted latitude on BCR-ABL1's
apo. That is a tacit acknowledgement that the mandated structures are not
beyond question. **It is not an endorsement of our finding and must not be
reported as one.**

**On (e) and (f).** Both remain open and both gate real work. (f) in
particular gates [[TASK-0269]]'s PocketMiner run, which currently proceeds
under our own permissive literal reading. Worth a follow-up ask — the channel
is evidently live and responsive.

---

## Consequences (our reading, not the organisers')

### 1. KRAS G12C — `8S8C` offered as an alternative apo

Our current apo is **`4OBE`**. Every KRAS G12C number in this register —
floor, AUC, ENM validity (`r = 0.646`, PASS), attribution shares, the pocket
distance category (contact-adjacent, min heavy-atom **1.32 Å**) — is computed
on 4OBE. Substituting changes all of them.

> **2026-08-26 update ([[TASK-0270]]):** decided. `8S8C` turned out to be
> HOLO, not apo (checked live — MK-1084-bound, not usable as an apo
> replacement). `4LDJ` adopted instead, on structural grounds (best
> resolution of the genuinely-apo true-G12C candidates a live RCSB sweep
> found). This section is kept as the decision record at the time it was
> written, not rewritten — see [[TASK-0270]]'s own Done section for the
> full analysis and re-run numbers.

Note carefully: the organisers say "a nice structure ... would be 8S8C". That
is a **suggestion, not a mandate**, and it does not say whether 8S8C is
intended as apo, holo, or simply a better-resolved reference. **Establish what
8S8C actually is before acting on it** ([[TASK-0270]]).

### 2. Cardiac Myosin — substitution accepted as primary

Resolves [[TASK-0222]] and removes the [[TASK-0169]] compliance risk for the
primary pair. **8QYP → 8QYR is now the sanctioned pair, on the record.**

What this does *not* erase: the underlying finding that Table 1's own 6C1H
does not contain mavacamten (re-confirmed live:
`nonpolymer_bound_components = ['ADP','MG']`) stands as a benchmark
observation and remains reportable. It is now *documented and permitted*
rather than a deviation we had to defend.

Also unaffected: [[TASK-0251]]'s separate finding that CARDIAC_MYOSIN's real
mechanism is inter-subunit and the challenge's catalytic-domain scope
truncates the coupling by construction. That is a scope problem, not a
structure-choice problem, and the substitution does not address it.

### 3. BCR-ABL1 — apo substitution permitted, rationale required

**"Please document the rationale in your submission"** is an explicit
instruction, not a courtesy. Whatever we choose, the submission must carry the
reasoning.

Live reasons to consider substituting `1OPL`:
- ENM validity is only **MARGINAL** (`r = 0.493`, [[TASK-0250]]) — one of five
  marginal targets, and it sits directly under [[TASK-0257]]'s finding that
  ENM-derived results are weakly interpretable there.
- 1OPL is the autoinhibited near-full-length structure. This intersects
  [[TASK-0265]]'s open question about whether the myristoyl pocket's
  allosteric action depends on the covalent N-cap tether — the apo choice
  determines whether that mechanism is even present in the model.

Reasons for caution: BCR-ABL1's published numbers all rest on 1OPL, including
the pocket taxonomy (proximal, min heavy-atom 7.96 Å) and the
[[TASK-0235]]/[[TASK-0241]] ceiling dispute. A substitution invalidates that
comparison set.

### 4. Formats — closed

No prescribed formats; conventional software. No action. [[TASK-0184]] may
treat format as a free choice.

---

## Provenance

- Received: 2026-08-26, direct reply to Team AuraQu's questions.
- Recorded by: Reviewer thread, same day, verbatim from the text supplied by
  Bartosz.
- Public Challenge Statement checked the same day: **no corresponding public
  revision found.**

## (g) Revisions and re-upload — answered 2026-09-07

**Question**: is it allowed to make revisions of a submitted document? Are these
versioned? Can we upload / delete / re-upload newer ones?

**Organiser answer, verbatim**:

> You can cancel and reupload as many times as you want until the Sep 15th
> deadline is reached. After that, everything you've uploaded by that time will
> be counted as submitted.

**Consequence**: there is no cliff and no penalty for iterating. A
submitted-but-imperfect document strictly dominates an unsubmitted perfect one,
so the operating rule from here is **upload early and re-upload often** — the
last artifact standing at the deadline is the submission. This also settles the
earlier open question about whether the "multiple entries" FAQ clause could be
stretched to cover revisions: it does not need to be. Revisions are explicitly
allowed in their own right. See [[TASK-0341]], which is built around this.
