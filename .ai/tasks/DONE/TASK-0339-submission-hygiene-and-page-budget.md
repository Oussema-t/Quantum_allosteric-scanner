# TASK-0339 — Submission hygiene and the page budget: the edits TASK-0332 does not cover

- Status: Done
- Owner: **Implementer C** — must land **before** [[TASK-0332]]'s drafting starts
- Priority: High — one item is a ToC violation, one is a minimum-set omission
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-07/...adversarial-submission-audit.md` §3.5, §3.7–3.9, §3.11–3.12
- Related: [[TASK-0332]], [[TASK-0184]], [[TASK-0307]]

## 1. §8 "Attack these first" must go — it breaks the mandated ToC

Guidelines §4.3 mandates **seven** numbered items. The document has **eight**, and
the eighth is an internal review-solicitation asking for *"a ruling on 01 and
06"*. It is also mis-ordered — §8 sits *after* Appendices A–C.

Together with the front-matter (`Draft | v1 — for adversarial review`,
`## What this document is`, *"circulated for adversarial review"*) that is
**~758 words addressed to an internal reviewer** in a document going to a panel.

Move §8's content to `REVIEW_TARGETS.md`, excluded from the submission. Two of
its open questions — 01 *"what is actually quantum about this"* and 06 *"benchmark
or paper"* — should be **answered inside §1 and §2**, not posed.

## 2. The page budget has never been checked, and every planned edit is additive

Measured word counts, body §1–7 = **2233 words** plus ten tables plus an unbuilt
figure — a realistic 5–6 pages at 10pt against a 6pp limit. [[TASK-0332]] then adds
four §2 positives, a clinical paragraph, two full bios and a lifted paragraph:
**plausibly +700–900 words with no cuts named anywhere.** v2 as specified goes over.

The budget is also inversely correlated with the rubric weights:

| section | words | weight |
|---|---|---|
| §7 Team | **709** (32% of body) | **10%** |
| §3 Feasibility | **107** | **20%** |
| §2 Technical Approach | 468 | 25% |

**The single highest-leverage editorial move available**: cut §7 to ~350 words and
move the space to §2 and §3. The 709 words contain three passages arguing *why*
the team discloses its AI usage — a defensible decision ([[TASK-0184]] §8 item 07),
but three paragraphs of justification reads as anxiety about it. Four sentences;
keep the QA-provenance argument and the cross-model adversarial-split table (both
genuinely differentiating); cut the rest.

**Render to PDF at 10pt and count pages before freeze.** This has never been done.
If over 6, cut §7 first, then Appendix A's QUALIFIED rows.

## 3. c-Myc is entirely absent from V1 — and it is in the mandated minimum set

Challenge Statement §6: *"c-Myc and the targets listed in Table 1 constitute the
**minimum set** required for submission."* V1 mentions `c-Myc` **0** times; the
superseded DRAFT mentions it 3 times. `results/MYC_MAX/` exists — **the work was
done, the restructure dropped it.** [[TASK-0184]]'s own Open Questions predicted
this ("recommend a short dedicated subsection so it is visibly not forgotten").

Two or three sentences plus the artifact reference closes it. While there: add one
sentence on AWS Braket / Classiq (currently 0 mentions each) — *"we evaluated the
provided infrastructure and here is why neither changes the `FAULT_TOLERANT_ONLY`
verdict"* scores better under Feasibility than silence.

## 4. The MYR error has a third copy [[TASK-0332]] does not list

Verified: `PHASE1_SUBMISSION_DRAFT.md` (47.5 KB, larger than V1) still carries
*"unexplained ligand"*. It is also the file the 2026-08-31 evidence pack audited,
so anyone following that pack's line references lands in the stale document.

Rename to `ARCHIVE-PHASE1_SUBMISSION_DRAFT-v0.md` with a superseded-by banner, or
delete. Two files both named like the submission, one wrong, eight days out, is
the [[TASK-0307]] failure mode the parity checker was built to prevent — and
parity only covers the `.md`/`.html` pair, not draft/V1.

## 5. §6 declares itself unbuilt, in place of the section's content

§6 currently ships a boxed admission that the diagram is undrawn and the shipped
demo contradicts the paper. Disclosing defects in Appendix C is a strength;
disclosing them *instead of* a 5%-weighted section's content is not the same move.

Reconcile the `main`-branch demo ([[TASK-0184]]'s TODO, still unchecked — and the
`keepalive.yml` workflow proves the demo is live, so a judge clicking through is
not hypothetical), draw the diagram, delete the box. If it truly cannot be drawn,
three boxes and two arrows in mermaid beats a paragraph saying it does not exist.

## 6. §7's repo statistics are stale — and independently checkable

| | claimed | actual (2026-09-07) |
|---|---|---|
| task files | 338 | **355** |
| done | 310 | **326** |
| commits | 549 | **579** |

This is the one number a referee can check with `ls \| wc -l` after following the
repo link, and it sits inside the paragraph arguing this team audits its own
numbers. **Regenerate at freeze and pin a SHA** — *"as of `<sha>`, 2026-09-14"* —
so it stays true as the register keeps moving.

## Done

**2026-09-07, Implementer C.**

### 1. §8 removed — ToC now exactly 7 items

Moved the full content (7 attack items + "what we want from this round") to a
new `documentation/REVIEW_TARGETS.md`, marked not-shipped, with a note on why
it was moved and which items got answered where. Also removed the front-matter
reviewer framing (`Draft | v1 — for adversarial review`, "circulated for
adversarial review" paragraph). Verified: `grep -c "^## " PHASE1_SUBMISSION_V1.md`
→ 8 headings total = "What this document is" + exactly 7 numbered sections, no
more, no `# Appendix` miscounted (checked with a `#{1,2}` split, not a naive
`## ` grep which would have missed the Appendices' single-`#` headers).

**01 and 06 answered inside §1/§2, not left posed** — per the task's own
instruction:
- **01** ("what is actually quantum about this") — §1's opening now states
  directly: a real coherent process used as a modelling language, not an
  asymptotic advantage, naming the §4.1 disjunct taken.
- **06** ("benchmark or paper") — §2 now states: "a benchmark-and-instrument
  proposal that uses a quantum-inspired method as its first test subject, not
  a method paper with a benchmark attached." **This is a synthesis of content
  already elsewhere in the document (§1's audit-the-benchmark framing, §2(a)'s
  own "certifying benchmark" proposal), not a new strategic decision invented
  here** — flagged explicitly in `REVIEW_TARGETS.md` for human sign-off before
  freeze, since the review itself called this "the most consequential
  strategic question here" and an implementer's synthesis should not be the
  final word on it without the team seeing it stated plainly first.

### 2. Page budget

Cut §7 from 709 → 522 words (26%, not the full ~50% suggested, because the two
pieces the task said to keep — the QA-provenance argument and the cross-model
adversarial-split table — are most of what remained; further cuts would have
started removing the "genuinely differentiating" content the task explicitly
protects). Freed space was spent on the required additions (c-Myc, Braket/
Classiq, the 01/06 answers) — **net arithmetic, stated precisely rather than
claimed as a clean win**: §7 saved 187 words; §1/§2/§3 additions cost 234; net
+47 words on the ~2233-word body (+2%), against a document whose *total* word
count (body + appendix + now-removed front-matter/§8) fell from 4044 to 3653
(-10%), since front-matter/§8 was never counted against the 6pp/3pp allowance
to begin with.

**PDF rendering not performed — disclosed, not silently skipped.** No
`pandoc`/`wkhtmltopdf`/`weasyprint` available in this environment (checked;
did not install new system software mid-task). Word-count is the same proxy
the source audit itself used ("2233 words... a realistic 5-6 pages"), applied
consistently before/after. **Recommend an actual PDF render + page count
before freeze** (2026-09-14, per this task's own text) — this task narrows
the gap and makes the arithmetic explicit; it does not certify the page count.

### 3. c-Myc added; AWS Braket/Classiq sentence added, corrected from the
task's own suggested wording

c-Myc (1NKP) now has a dedicated paragraph in §1 (real content: 4-operator
consensus, `results/MYC_MAX/`, residue 943, honestly reports no ground truth
rather than improvising one).

**Braket/Classiq: the task's own suggested sentence ("we evaluated the
provided infrastructure...") would have been false, checked before writing
anything** — `TASK-0182`'s own Done section records Braket execution as
blocked on missing credentials, and a later organiser confirmation
([[TASK-0221]]) that Braket/Classiq access is **Phase-2-only, not required or
available for Phase 1** — neither was ever run or evaluated. Wrote the
accurate version instead: confirmed with organisers as Phase-2-only,
irrelevant to the verdict either way (set by qubit count/depth, not provider
choice). Flagged here because implementing the literally-suggested wording
would have introduced a new factual error while fixing three others.

### 4. `PHASE1_SUBMISSION_DRAFT.md` archived, not deleted

Renamed to `ARCHIVE-PHASE1_SUBMISSION_DRAFT-v0.md`. Found before renaming: the
file already carried a `SUPERSEDED — do not edit or cite` banner (from an
earlier pass), so the "mistaken for current" risk was already mitigated in
content; the rename addresses the audit's actual stated risk (two
similarly-named files in a directory listing, filename pattern-matching, not
content). **Blast radius checked, not assumed zero**: ~20 Done task files cite
this filename by name in historical prose (line-number references into a
frozen document). **Deliberate scope decision, disclosed**: did not update
those ~20 files — they are frozen historical records, not executable
references, and `grep -rln` confirmed no tooling/CI config references the
filename. Added a note to the archived file's own banner flagging its
residual "unexplained ligand" (MYR) inversion — TASK-0332's fix, not applied
here (Berke sign-off required for that specific biology correction) — so a
reader who does follow an old line-reference in still sees the correction.

### 5. §6 — diagram drawn, disclosure box demoted to a precise, confirmed note

Drew a real pipeline diagram: ASCII box-and-arrow in the `.md`, an equivalent
inline SVG in the `.html` (both apo → ENM ensemble → quantum-inspired
transport → classical verification → 3 artefacts). Deleted the "diagram not
yet drawn" half of the old box.

**Did not delete the demo/report-contradiction disclosure — verified it is
still true, not resolved.** Checked directly against `origin/main` (fetched
live): `backend/quantum.py`'s deployed `occupation` observable is validated
"by P@5 vs the holo drug-contact pocket" with no floor/residualisation
anywhere in `backend/`/`frontend/` (`git grep` on both, on `main`) —
confirmed, not inferred from the archived reviewer's snapshot the way the
source audit had to. Rewrote the disclosure to be precise about what was
checked and how, and reduced it from being the section's *entire* content to
a scoped note alongside the new diagram, per the audit's own distinction
("disclosing defects in place of content is not the same move as disclosing
them alongside it"). **Did not attempt to fix `main`'s backend** — reconciling
the live demo (add a floor, or gate P@5 behind one) is a real engineering
change to a deployed branch, tracked separately as [[TASK-0184]]'s own TODO,
outside a documentation-hygiene task's reasonable scope and risk budget.

### 6. §7 repo statistics regenerated and pinned

338/310/549 → **359 task files · 328 done · 580 commits, as of `ffcfaca`,
2026-09-07** (re-measured directly, not copied from the source audit's own
2026-09-07-morning snapshot, which is already one task-file-count behind —
the register moved even within this task's own session). Pinned to a SHA per
the task's own suggested format, with the explicit understanding (stated in
this Done section, matching the task's own text) that this needs regenerating
again at actual freeze.

### Verification

- `python3 .ai/tools/doc_parity.py PHASE1_SUBMISSION_V1.md PHASE1_SUBMISSION_V1.html --verbose`
  → **found and fixed a real, pre-existing parity fragility, not just re-ran a
  clean check**: my §8 deletion removed the only source of literal "03"/"04"/
  "05"/"06" digit tokens in the `.md`, which had been coincidentally satisfying
  the `.html`'s decorative zero-padded section-number badges (`<div
  class="num">03</div>` etc. for §3-6) — a false-pass masked by unrelated
  content, not a real content match. Root-caused (confirmed via `git stash` that
  parity was genuinely OK before my edits, i.e. this was my own regression, not
  pre-existing) and fixed at the source: dropped the leading zero from all 7
  badges (`01`→`1` … `07`→`7`) rather than padding new filler text into the
  `.md` to fake a match. Re-ran: `parity OK`.
- `grep -c "^## " PHASE1_SUBMISSION_V1.md` combined with a `#{1,2}` split
  confirms exactly 7 numbered sections + 3 appendices, no stray 8th.
- `git grep -n "p_at_5|P@5|precision_at" origin/main -- backend frontend` — the
  §6 disclosure's own factual claim, checked live before being restated with
  more precision than the source audit could give it (no `.git` in that
  audit's snapshot).
- `grep -rln PHASE1_SUBMISSION_DRAFT .github .ai/tools` → no hits, confirms the
  rename does not break any tooling/CI.

### Not done / explicitly out of scope

- Real PDF render + exact page count (§2 above) — no renderer available,
  recommended before freeze.
- Fixing V1's own "unexplained ligand" (MYR) inversion — [[TASK-0332]] item 1,
  requires Berke's structural sign-off, explicitly that task's scope not this
  one's.
- Reconciling `main`'s live demo (§5 above) — [[TASK-0184]]'s own tracked TODO,
  a deployed-branch engineering change, not a documentation edit.
- Updating ~20 Done task files' historical citations of the renamed DRAFT
  file (§4 above) — deliberate, disclosed.

**Files**: `documentation/{PHASE1_SUBMISSION_V1.md,PHASE1_SUBMISSION_V1.html,
REVIEW_TARGETS.md,ARCHIVE-PHASE1_SUBMISSION_DRAFT-v0.md}` (renamed from
`PHASE1_SUBMISSION_DRAFT.md`).

**Moved TODO/IN_PROGRESS -> DONE.**
