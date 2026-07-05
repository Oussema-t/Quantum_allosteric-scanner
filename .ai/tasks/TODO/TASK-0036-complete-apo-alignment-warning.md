# TASK-0036 Surface an explicit warning when `complete_apo` skips Kabsch alignment

## Context

- ID: TASK-0036
- Title: when apo/holo share fewer than 3 residues, `complete_apo` silently
  skips holo-to-apo Kabsch alignment (falling straight to interpolation for
  every missing residue) with no explicit flag in the returned summary
  beyond `align_rmsd: None`
- Status: TODO
- Owner: Implementer
- Source: review of all `Oussema-t`-authored commits, 2026-07-05 session —
  Medium-severity finding #6
- Scope: `backend/discovery.py::complete_apo`

## ⚠️ Before implementing

**Do a short review before adding a warning field** — confirm this code
path is actually reachable in practice (i.e., is there a realistic
apo/holo pair in `systems.py` or a plausible user-entered pair with <3
shared residues?), and check whether the frontend's completion-summary
banner (`frontend/app.js::renderStructInfo`'s completion card) would
actually surface a new warning field if one were added, so the fix isn't
invisible to the user it's meant to inform.

## Intent Contract

- Outcome: a caller (or the biologist using the UI) can tell, from the
  returned summary alone, whether holo-coordinate borrowing was actually
  attempted and failed vs. never attempted at all — not just infer it from
  a null RMSD.
- In Scope:
  - add an explicit field to `complete_apo`'s summary dict, e.g.
    `"holo_alignment": "ok" | "skipped_insufficient_overlap" | "no_holo"`,
    alongside the existing `align_rmsd`.
  - surface it in the frontend's completion banner
    (`renderStructInfo`'s `comp` block) with a short human-readable note
    when it's not `"ok"`.
- Out Of Scope: changing the interpolation fallback behavior itself — this
  task only makes the existing behavior visible, not different.
- Constraints And Invariants: CLAUDE.md convention 4 — ADD-only; the new
  field is additive to the `/api/load` response, existing fields unchanged.
- Planned Validation: construct a synthetic/real case with <3 shared
  apo/holo residues (or a mocked one if no real benchmark target
  triggers it), confirm the new field reads
  `"skipped_insufficient_overlap"` and the frontend banner shows it; run a
  normal benchmark target (e.g. KRAS_G12C with completion) and confirm the
  field reads `"ok"` with no visible change to the existing banner.

## TODO

- [ ] Confirm this path is realistically reachable (see callout).
- [ ] Add the explicit summary field.
- [ ] Surface it in the frontend completion banner.
- [ ] Test both the normal and insufficient-overlap cases.

## Dependency

- None.

## Open Questions

- Is there a real benchmark target/pair that actually exercises the <3
  shared-residues path today, or would this only ever trigger on a
  user-entered non-benchmark pair? Affects how the test case is
  constructed (real vs. synthetic).

## Done

(not yet)
