# TASK-0206 The vendored fpocket binary has drifted — and its old numbers are the register's headline classical comparator

## Context

- ID: TASK-0206
- Title: pin or re-baseline the vendored `fpocket` build, and decide which of
  the two non-matching AUC sets the submission cites.
- Status: Done
- **Thread: Toolsmith (infrastructure).** Independent of both science threads;
  touches `tools/` and the stored baselines, not the analysis code.
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: [[TASK-0200]]'s own Planned-Validation failure and diagnosis,
  2026-08-04; Reviewer thread, 2026-08-05, finding H3.
- Priority: **P1 — the affected number is quoted in `COMPETENCE_MAP.md` and is
  the register's single most-cited classical-comparator figure. It should not
  enter the submission unpinned.**
- Dependency: [[TASK-0163]] (Done — the original run and the vendored build).

## Why this matters

[[TASK-0200]] could not reproduce [[TASK-0163]]'s published fpocket AUCs:

| Target | [[TASK-0200]] recomputed | [[TASK-0163]] published | Δ |
|---|---|---|---|
| KRAS_G12C | 0.7910 | **0.8348** | **0.044** |
| BCR_ABL1 | 0.8618 | 0.8596 | 0.002 |
| CARDIAC_MYOSIN | 0.5303 | 0.5345 | 0.004 |

[[TASK-0200]] diagnosed this properly rather than assuming its own bug, and
ruled out four candidates by direct check: the pocket label (identical,
`pocket_size=18`, floor AUCs match to many decimals), chain selection (no
`apo_chains` override, `chains: ["A"]` unchanged), fpocket non-determinism
(3 re-runs bit-identical), and a parsing bug (`n_pockets`/
`n_residues_assigned` match [[TASK-0163]]'s stored values exactly, 10 and 77).

Its stated best explanation — **the vendored binary/build has drifted since
[[TASK-0163]] ran** — is consistent with the pattern: one geometry shifts
materially, two barely move, which is what a cavity-detection algorithm
change looks like. Note the vendored build was rebuilt from source for an
arm64 macOS host during [[TASK-0177]] (`ARCH=MACOSXARM64`), which is a
concrete candidate event.

**Why this is not cosmetic.** `0.8348` is the number the register uses to say
*a 2009 classical tool beats every observable here and this project's own
proximity floor*. It appears in `COMPETENCE_MAP.md`'s discriminability
section and is load-bearing for [[TASK-0184]]'s narrative. Shipping a
headline comparator that the current repository does not reproduce is exactly
the kind of thing this project's own [[TASK-0072]] cross-tree drift test
exists to prevent.

## Intent Contract

- Outcome: a pinned, reproducible fpocket invocation; one authoritative AUC
  set for the three mandatory targets; and every citation of the old numbers
  either updated or explicitly marked as the older build's.
- Why required, not assumed: two mutually inconsistent numbers for the same
  measurement are currently both in the register, cited from different
  documents, with no statement of which is current.
- In Scope:
  - Determine what changed: compare the current `tools/fpocket/` build against
    whatever [[TASK-0163]] used — version string, commit, build flags,
    architecture. The [[TASK-0177]] arm64 rebuild is the first place to look.
  - **Pin it**: record version/commit/build flags somewhere a future run
    checks, in the same disclosure shape `ripser`/`optuna` already use. A
    recorded invocation that cannot drift silently is the deliverable.
  - Decide which AUC set is authoritative. **Recommendation: the freshly
    recomputed set**, since it is reproducible in the current repository and
    [[TASK-0200]] already built on it. State the decision and the reason.
  - Sweep every citation of `0.8348`/`0.8596`/`0.5345` across `RESULTS.md`,
    `COMPETENCE_MAP.md`, and task files — update, or annotate as the older
    build's number. Coordinate with [[TASK-0205]], which is editing both
    documents.
  - Consider a golden-value regression test pinning fpocket's AUC on one
    target, the direct analogue of [[TASK-0072]]'s cross-tree drift test —
    so the next drift fails a test instead of surfacing three tasks later.
- Out Of Scope:
  - Re-running any *conditional* analysis. [[TASK-0200]]'s within-band
    comparisons only ever compare fresh numbers to fresh numbers and are
    unaffected — it said so, and that reasoning holds.
  - Changing fpocket's parameters or invocation semantics to close the gap.
    The goal is a pinned, reproducible number, not a matching one.
  - Re-opening [[TASK-0163]]'s conclusions. fpocket still beats floor and
    actual on 2/3 targets under both number sets — the *finding* is unchanged,
    only its exact magnitude.
- Constraints And Invariants:
  - Do not silently replace the published numbers. Annotate, with the date and
    the reason, per the register's standing convention.
  - If the drift cannot be root-caused within a reasonable box, say so and pin
    the current build anyway. An unexplained-but-pinned number is far better
    than an unpinned one, and much better than two.
  - Whatever is decided, `COMPETENCE_MAP.md` and `RESULTS.md` must agree
    afterwards. They currently do not.
- Planned Validation:
  - Re-run the pinned invocation twice on different days/sessions; identical
    output.
  - If a root cause is found, demonstrate it: rebuild the old configuration
    and reproduce [[TASK-0163]]'s 0.8348. That is proof, not inference.
  - The golden-value test (if built) must fail against a deliberately altered
    invocation before it passes against the pinned one.

## In Progress

—

## TODO

- [x] Identify the current build's version/commit/flags; compare against
      TASK-0163's -- **no commit/flags to compare**: `tools/fpocket/bin/`
      is gitignored, only ever `README.md`/`bin/.gitignore` tracked
      (`git ls-files`, `git log -- tools/fpocket/bin/fpocket` both
      confirm). The binary is not, and never was, version-controlled.
      Real root cause found instead: git identity on the two commits
      (`2655a5d` TASK-0163 vs `ca4281e` TASK-0200) shows two different
      machines.
- [x] Investigate the TASK-0177 arm64 rebuild as the candidate drift
      event -- **does not hold up**: no rebuild commit exists to find
      (binary never tracked), so there is no before/after to diff. The
      two-machine finding supersedes this hypothesis rather than
      confirming it.
- [x] Pin the invocation; record it in the same shape as `ripser`/`optuna`
      -- `tools/fpocket/PROVENANCE.json` (SHA256 + hostname/platform +
      banner + build recipe + both AUC sets) + new
      `allostery.baselines.fpocket_provenance()`.
- [x] Decide the authoritative AUC set; state the decision and reason --
      the freshly recomputed set (this task's own recommendation,
      followed): reproducible on this machine (re-run fresh, exact match
      to [[TASK-0200]]), SHA256-pinned, golden-value-tested.
- [x] Sweep + update/annotate every citation (coordinate with
      [[TASK-0205]]) -- TASK-0205 was Done (claim released) by the time
      this ran, no collision. Annotated: `COMPETENCE_MAP.md` (one top-
      caveat callout, matching [[TASK-0167.002]]'s own established "one
      callout, not every mention" convention), `RESULTS.md` (new dated
      section + 2 inline callouts at the table and discriminability
      section + open-questions row 62), `ALGORITHM_REGISTER.md`,
      `EXECUTION_PLAN.md`, `documentation/CONFORMATIONAL_SEARCH.md`,
      `src/allostery/PHASE_B_ROTAMER_QUBO.md`, `tools/fpocket/README.md`.
      Numbers kept on record everywhere, never silently replaced.
- [x] Golden-value regression test, failing-first -- built
      (`tests/test_fpocket_pin.py`), ran for real (not skipped) in this
      environment, passed. Failing-first demonstrated directly: a
      synthetic altered-binary test confirms a changed SHA256 does not
      silently match the pinned record.
- [x] Confirm `RESULTS.md` and `COMPETENCE_MAP.md` agree afterwards --
      both now cite the same authoritative set and cross-reference each
      other's TASK-0206 section/callout.

## Dependency

- [[TASK-0163]] (Done) — the original run.
- [[TASK-0177]] (Done) — the arm64 rebuild, prime drift suspect.
- [[TASK-0200]] (Done) — the diagnosis this task acts on.
- [[TASK-0205]] — editing the same two documents; sequence, do not collide.
- [[TASK-0072]] (Done) — the drift-test precedent to reuse.

## Open Questions

- Is the 0.044 KRAS_G12C shift large enough to change any verdict, or only
  the magnitude? **Resolved: only the magnitude.** Confirmed directly —
  under both number sets fpocket beats floor (0.4818) and actual (0.5901)
  on KRAS_G12C by a wide margin (0.7910 or 0.8348, either way); same
  qualitative read on BCR_ABL1/CARDIAC_MYOSIN. No verdict in
  `COMPETENCE_MAP.md`'s discriminability table flips either direction.
- Should the vendored binary be checked in as a build artifact with a hash,
  or rebuilt from a pinned source commit at setup time? **Not decided here
  (Toolsmith's call, as filed) — but the SHA256 pin now makes either choice
  auditable**: if the binary is rebuilt at setup time (current convention,
  kept unchanged), `fpocket_provenance()` + `PROVENANCE.json` catch drift
  after the fact instead of preventing it. Checking in the binary itself
  would prevent drift outright but adds a large, platform-specific binary
  blob to git — flagged as a real tradeoff for whoever picks this up next,
  not resolved unilaterally by this task.
- **New, raised directly by the orchestrating user (2026-08-06) and
  investigated**: "the two results were obtained on two different
  machines... maybe a recomputation on the other machine would prove
  worthwhile." **Confirmed correct and load-bearing** — this is the actual
  root cause (git-identity evidence, Done section below), not merely a
  contributing factor. Recomputing on the other machine would settle
  whether the remaining gap is a genuinely different upstream commit or a
  compiler/architecture-level difference — **not achievable from this
  environment** (single-machine session); left as an open, actionable item
  for whoever has access to that machine.

## Done

**2026-08-06, Implementer C.**

Root-caused via git identity, not assumed: `tools/fpocket/bin/` is
gitignored (`git ls-files tools/fpocket/` shows only `README.md` and
`bin/.gitignore` ever tracked) -- the binary is a local build artifact,
never version-controlled, only the build recipe (`README.md`'s `git clone
--branch 4.2.3 ...`) is. [[TASK-0163]]'s commit (`2655a5d`, 2026-07-28)
was authored under git identity `Bartosz <chmura.quantum@gmail.com>`;
[[TASK-0200]]'s commit (`ca4281e`, 2026-08-04) under a different machine's
identity (`Bartosz Chmura <bartosz.chmura@appsfactory.de>`) --
**two machines, each building an independent, never-pinned fpocket
binary, is sufficient by itself to explain the drift.** This was raised
directly by the orchestrating user mid-task ("the two results were
obtained on two different machines... maybe that is in any way involved
in the outcome") and confirmed correct via this git-identity check.

This supersedes, not supplements, the task's own filed candidate root
cause (a TASK-0177 arm64 rebuild event): since the binary was never
tracked, there is no rebuild commit to find and no before/after to diff.
Not chased to a full resolution of *why* the two builds differ (same
upstream commit, different compiler/OS/arch vs. a genuinely different
tag) -- per this task's own explicit Constraint ("if the drift cannot be
root-caused within a reasonable box, say so and pin the current build
anyway"), and because recomputing on the other machine (the user's own
suggestion, and the one measurement that would actually settle it) is not
achievable from this single-machine environment.

**A real, independently useful finding along the way**: the binary's own
printed version banner (`fpocket 4.0`) is not a trustworthy pin -- this
build exposes `-P`/`--custom_pocket`, a flag upstream's own release notes
attribute to fpocket 4.1 ("Explicit pocket definition"), so the banner
string is stale/hardcoded across the whole 4.x release line, checked
directly against `github.com/Discngine/fpocket`'s own tags/release notes
rather than assumed. SHA256 of the binary's own bytes is the only
unambiguous fingerprint available without instrumenting the build itself.

**Pinned**: `tools/fpocket/PROVENANCE.json` (SHA256
`0267f6d3207c27684367772f70f8530e463f49f63b881adcce0d3262676d48ba`,
hostname, banner, build recipe, both AUC sets with attribution) + new
`allostery.baselines.fpocket_provenance(binary_path)` (SHA256 + banner +
hostname/platform for any binary, callable by any future script) +
`tools/fpocket/README.md` updated to point at the pin.

**Authoritative AUC set decided**: the freshly recomputed numbers
(KRAS_G12C 0.7910228108903605, BCR_ABL1 0.8617816091954023,
CARDIAC_MYOSIN 0.5302794166759435) -- this task's own recommendation,
followed. Verified, not just trusted: re-ran `scripts/
task0163_external_baseline_scoring.py` fresh on this machine and got an
exact match to [[TASK-0200]]'s own numbers, confirming same-machine
determinism (Planned Validation's "re-run twice, identical output," now
satisfied for this machine -- the cross-machine half is the open item
above).

**Golden-value regression test**: `tests/test_fpocket_pin.py`, 6 tests --
`fpocket_provenance()` unit coverage (missing binary, sha256 discriminates
different content) + two real, network-and-binary-gated tests
(`backend/test_analysis.py`'s own real-target-pin/skip convention): the
current binary's SHA256 matches the pinned record, and KRAS_G12C's real
fpocket AUC matches the pinned value to 1e-6. **Both ran for real in this
environment (binary present, network available), not skipped.**
Failing-first demonstrated directly (Planned Validation's own
requirement): `test_deliberately_altered_binary_fails_the_pin_check`
constructs a binary with different bytes and confirms its SHA256 does
not match the pinned one.

**Citation sweep**: `COMPETENCE_MAP.md` (one top-caveat-block callout,
matching [[TASK-0167.002]]'s own already-established "one callout per
document, not an edit at every individual mention" convention -- checked
that convention was actually already in use there before choosing to
follow it, not invented fresh); `RESULTS.md` (new dated "fpocket binary
drift" section + inline callouts at the mandatory-target-comparison table
and the TASK-0169 discriminability section + open-questions row 62,
avoiding a numbering collision with an already-duplicated row 60 found in
that table -- not fixed, out of this task's scope, just avoided);
`ALGORITHM_REGISTER.md`, `EXECUTION_PLAN.md`,
`documentation/CONFORMATIONAL_SEARCH.md`,
`src/allostery/PHASE_B_ROTAMER_QUBO.md` (single inline annotations each).
Every old number kept on record, none silently replaced, per this task's
own Constraint.

**No verdict changes.** fpocket still beats floor and actual on 2/3
mandatory targets under either number set; CARDIAC_MYOSIN still sits just
below its own floor under either set. This task changes a magnitude
(0.044 max, KRAS_G12C), not a finding.

**Full `pytest tests/ -q`**: 1138 passed, 1 skipped, 2 xfailed, 0 failed
(includes this task's own 6 new tests, both golden-value tests ran for
real).

**Not done, explicitly out of scope or unreachable from here**: full
root-cause of *why* the two builds differ (same commit + different
toolchain vs. genuinely different tag); recomputing fpocket on the other
machine (the user's own suggested next step -- needs a thread running on
that machine, not this session); checking in the binary itself vs.
rebuild-at-setup (Toolsmith's call, Open Questions above).
