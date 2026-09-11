# Working copy of the Phase 1 Concept Proposal

`PHASE1_SUBMISSION_V4.md` is a **verbatim copy** of
`origin/bartosz:__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V4.md` at commit `9f1d521` (file last changed in 48033c8, 2026-09-11)
(the source of `01_Concept_Proposal.pdf`). Nothing on the `bartosz` branch is modified by this copy.

Rule for edits here: additions must agree with what the existing text already states — same cohort
labels (fpocket track vs PASSer track), same family convention noted where counts differ, per-structure
AUC only, no best-of-N numbers without the search budget in the same sentence. Any number that differs
from his is reported as a second measurement on a second cohort, never as a correction of his.

Render: `python3 submission/tools/submission_build_latex.py --md submission/phase1/PHASE1_SUBMISSION_V4.md --outdir <dir> --appendix-heading Appendix --no-change-report`
(needs pandoc, tectonic, pdfplumber — all user-local).

**Version note.** V1–V3 also exist on `bartosz`; V4 is the current one and the only one that matches
the circulated `01_Concept_Proposal.pdf`. The build tool's `DEFAULT_MD` still points at V2, so the
`--md` flag must always be given explicitly.
