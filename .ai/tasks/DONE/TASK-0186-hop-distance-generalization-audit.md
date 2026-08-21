# TASK-0186 Active-site to pocket distance generalization audit -- three axes

## Context

- ID: TASK-0186
- Title: check whether TASK-0169's "trivial 1-hop" finding on KRAS_G12C
  generalizes across the full pocket-scoreable benchmark set, separating
  three independent notions of "close": Euclidean distance, spatial
  contact-graph hop-distance, and primary-sequence (chain/backbone)
  hop-distance.
- Status: Done
- Owner: Architect/Planner (this thread) -- a read-only diagnostic, no
  scoring/label/code changes.
- Claimed By: Architect
- Claimed At: 2026-07-31 20:53
- Source: orchestrating collaborator (Bartosz), 2026-07-31: *"the active
  sites are within a 8A cutoff 1-hop range away from allosteric pockets --
  and that NOT ONLY in KRAS... In such a formulation, the whole challenge is
  somewhat a hoax. A signal just does one hop, and no propagation really
  takes place."* Extended same session: distinguish spatial-graph hop
  distance from primary-sequence (chain) hop distance explicitly -- a
  single Euclidean or spatial-hop number conflates "adjacent in the linear
  chain" (trivial) with "far in sequence but folded close" (a real
  tertiary-structure effect).
- Priority: **P0 -- gating.** Cheap once the environment is fixed
  (~10-15 min compute across 7 targets, network-bound), and the answer
  changes how much of TASK-0176's program is worth building as specified.

## Why this matters

TASK-0169 found KRAS_G12C's labelled pocket comes within 3.75 A (Euclidean,
min Ca-Ca) of the active site and flagged it "trivial" for that one target.
It did not check whether that generalizes, and Euclidean distance is not
the mechanistically relevant metric anyway -- a residue can be
geometrically close but several hops away in a sparse contact graph, or far
in 3-D but 1-hop away via a single long contact. **Spatial contact-graph
hop-count** (same 8.0 A convention as TASK-0067) is what actually
determines whether a propagation observable needs to do any real work to
"find" the pocket.

A second distinction turned out to matter once this was scoped in detail:
spatial closeness on its own doesn't say whether that closeness is
*interesting*. Two residues adjacent in the primary sequence are also
almost always 1-hop in any reasonable spatial contact graph (consecutive
Ca atoms are ~3.8 A apart) -- that case is doubly trivial, no tertiary fold
required at all. The case worth caring about is spatially close **despite**
being far apart in sequence -- that is a genuine fold-mediated shortcut,
and it is also the *static*, ENM-free baseline for [[TASK-0187]]'s dynamic
shortcut hypothesis: the ratio (sequence hops) / (spatial hops) measures
how much the native fold alone already compresses sequence separation,
before any conformational sampling is applied.

If most/all pocket-scoreable targets turn out spatially 1-hop from the
active site, that is not a tuning problem -- every propagation-based
observable in the register has been trivially advantaged by benchmark
construction, independent of any mechanism hypothesis tested to date, and
TASK-0176's "distal allosteric site" framing needs correcting before the
submission is written. If it does not generalize, KRAS_G12C's 1-hop-ness is
a known, already-documented single-target defect (TASK-0169) and this
audit closes as a clean negative -- also a useful, cheap result.

**Known trap, stated up front:** running this against the *incumbent*
4.5 A ligand-contact label risks measuring an artifact of how that label is
built (exactly TASK-0177's motivation) rather than a real biological
finding. This task runs against the incumbent label first because
TASK-0177's consensus label does not exist yet, and every output artifact
says so. **Must be re-run against TASK-0177's `core`/`consensus` labels
once available, all three reported side by side, never substituted** --
same convention TASK-0177 itself uses.

## Intent Contract

- Outcome: per-target distributions on three axes (Euclidean min-distance;
  spatial contact-graph hop-count, min/mean/median/max + fraction at
  <=1/<=2/<=3 hops; primary-sequence chain-hop-count, same statistics) plus
  a per-target "fold compression ratio" (chain-hop / spatial-hop, static
  fold only, no ENM), for all 7 pocket-scoreable `status: verified` targets
  (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN, PTP1B, GLUCOKINASE, CASPASE1,
  CASPASE7 -- MYC_MAX excluded, no folded-state pocket). Written to
  `results/tasks/0186_hop_distance_audit/results.json` and a short
  `RESULTS.md` entry.
- Why required, not assumed: TASK-0169 checked one target with one metric;
  the generalization claim and both new metrics (spatial-hop, chain-hop)
  are new.

- In Scope:
  - `scripts/hop_distance_generalization_audit.py` -- read-only, reuses
    `clean.clean_from_config`/`load_target_config`, `labels.build_labels`,
    `baselines.hop_from_seed` (8.0 A cutoff) exactly as already wired in
    `run_challenge.py`, for the Euclidean and spatial-hop axes. Chain-hop
    is new code (no existing backbone-only graph builder was found in this
    codebase, grepped for one before writing) -- a simple per-chain BFS on
    `CleanResult.chain_ids`, same `n+1`-unreachable convention as
    `hop_from_seed` for cross-chain pairs. **Written and believed correct;
    not yet executed against real data** (see blocker below).
  - Run against the incumbent 4.5 A label across all 7 targets.
  - Report per-target AND an aggregate (how many of 7 targets have median
    spatial-hop <= 1? <= 2? what is the typical fold-compression ratio?).

- Out Of Scope:
  - Any change to `labels.py`, `baselines.py`, `targets.yaml`, or any scored
    cell. This is a diagnostic, not a fix.
  - Re-running against TASK-0177's label (does not exist yet; tracked as
    this task's own follow-up).
  - Deciding what to do about the finding -- TASK-0176/0184's call, this
    task only produces the numbers.

- Constraints And Invariants:
  - Spatial-hop graph cutoff fixed at 8.0 A -- reuse TASK-0067's retained
    contact scale, do not introduce a new geometric constant.
  - Chain-hop uses array position (modeled-residue index), not raw resnum
    arithmetic -- robust to numbering gaps (`CleanResult.gap_pairs`),
    correctly disconnected across `chain_ids` boundaries for multi-chain
    targets.
  - Both the incumbent-label caveat and the three-axis distinction stated
    explicitly in every output artifact, not just this file.

- Planned Validation:
  - Sanity: KRAS_G12C's Euclidean result must reproduce TASK-0169's already-
    published 3.75 A finding. If it doesn't match, the script has a bug --
    blocking, must be resolved before trusting any other target's number.
  - Report whichever way the aggregate comes out; no threshold is being
    tuned to produce a comfortable answer.

## In Progress

- 2026-07-31 20:5x (Architect, this thread): script written
  (`scripts/hop_distance_generalization_audit.py`), covering all three axes
  plus the fold-compression ratio.
- 2026-07-31 21:0x (Architect, this thread): **blocked getting the run
  environment up.** Neither the repo-root `.venv` nor
  `__WORK_IN_PROGRESS__/` had this package's dependencies installed (only
  `pip` itself) -- installed `pyyaml`/`numpy`/`networkx`/`scipy`/
  `scikit-learn` successfully, but `prody` (required by `clean.py` for
  PDB fetch/parse) has no prebuilt wheel for this Python/platform
  (cp313-macosx) and its sdist build fails: `clang++` cannot find
  `<cmath>` because this machine's Xcode Command Line Tools install is
  incomplete -- `/Library/Developer/CommandLineTools/usr/include/c++/v1/`
  has 11 entries where a working libc++ has hundreds (no `cmath`,
  `vector`, `string`, etc. at all). Confirmed via a minimal `#include
  <cmath>` compile, independent of pip/prody. Not caused by anything in
  this session; pre-existing local machine state. No local workaround
  found (no Homebrew gcc/llvm installed, no wheel at any index, no second
  Python version under `pyenv` to fall back to).
  - **This blocked nothing else in this session's work** -- the script and
    both new task files (this one, TASK-0187) were unaffected while blocked.
- 2026-08-01 (Architect, this thread): **unblocked -- the user repaired the
  machine's Xcode Command Line Tools independently** (confirmed: a plain
  `#include <cmath>` compile now succeeds, header search path now resolves
  through the SDK's own `c++/v1` instead of the broken toolchain copy,
  CLT package install-time advanced). Re-ran the dependency install
  (`scipy`/`scikit-learn`/`prody` all built cleanly this time) and the
  script. **First run failed** with `AttributeError:
  'CleanResult' object has no attribute 'ligand_groups'` on every target
  -- `build_labels` needs `holo.ligand_groups`/`heavy_atom_coords`, which
  plain `clean_from_config` does not attach; missed on first write because
  `run_challenge.py::_load_apo_holo` does this as a second step the
  simplified script skipped. Fixed by porting that exact helper (not
  cross-imported, this is a separate script) into
  `hop_distance_generalization_audit.py`. **Second run succeeded on all 7
  targets.** Sanity check passed: KRAS_G12C min Euclidean = 3.7530 A,
  matching TASK-0169's published 3.75 A to 4 decimal places.

## TODO

- [x] Write the diagnostic script, reusing existing loaders only.
- [x] Unblock: environment fixed by the user (Xcode CLT reinstalled).
- [x] First live run across all 7 targets, incumbent label.
- [x] Sanity-check KRAS_G12C against TASK-0169's 3.75 A finding. Passes.
- [x] Write the `RESULTS.md` entry (row 47, added 2026-08-01).
- [ ] **Follow-up (blocked on TASK-0177):** re-run against `core`/
      `consensus` once TASK-0177's consensus label lands; report all three
      labels side by side.
- [x] Feed the finding into TASK-0187 (positive-control target selection,
      see that task's own updated Step 0). TASK-0176/0184 narrative
      hand-off left as an explicit open item, see Done section.

## Dependency

- [[TASK-0169]] (Done) -- the single-target finding this generalizes.
- [[TASK-0067]] (Done) -- the 8.0 A contact-scale convention reused here.
- [[TASK-0177]] -- soft, for the follow-up re-score against the consensus
  label; this task's first pass does not block on it.
- [[TASK-0187]] -- this task's fold-compression-ratio output is the static
  baseline that task's dynamic (ENM-sampled) shortcut measurement compares
  against.

## Open Questions

- What counts as "generalizes"? No threshold fixed in advance beyond
  reporting the full distribution -- deliberately, since picking a
  threshold now would itself be a knob. Bartosz/Architect read the raw
  numbers once in and decide what they mean for TASK-0176's framing.
- Does this audit's finding change TASK-0177's C6 priority ordering? Yes --
  see the C6 amendment landing in the same session, which resequences C6 to
  run first in that task's checklist specifically because of this
  (expected) result.
- Is the local-toolchain blocker worth its own tooling task (e.g. document
  the fix in `LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md` so the next thread
  that hits this doesn't re-diagnose it from scratch)? Recommend yes, small,
  filed separately if it recurs -- not blocking this task's own resolution.

## Done

**2026-08-01, Architect.** Ran
`scripts/hop_distance_generalization_audit.py` against all 7 pocket-
scoreable `status: verified` targets, incumbent 4.5 A label. Full JSON:
`results/tasks/0186_hop_distance_audit/results.json`. `RESULTS.md` row 47.

| Target | n pocket | Euclid min/med (A) | Spatial-hop min/med | frac hop<=1 | Chain-hop min/med | Fold-compression mean |
|---|---|---|---|---|---|---|
| KRAS_G12C | 18 | 3.75 / 13.08 | 1 / 2.0 | **0.39** | 1 / 22.0 | 10.3x |
| BCR_ABL1 | 16 | 7.52 / 11.31 | 1 / 2.0 | 0.06 | 6 / 55.5 | 21.2x |
| CARDIAC_MYOSIN | 13 | 3.81 / 17.62 | 1 / 4.0 | 0.08 | 1 / 181.0 | 37.7x |
| PTP1B | 14 | 13.38 / 16.30 | **2** / 3.5 | **0.00** | 10 / 22.5 | 8.9x |
| GLUCOKINASE | 17 | 3.79 / 10.67 | 1 / 2.0 | 0.12 | 1 / 48.0 | 30.9x |
| CASPASE1 | 6 | 3.80 / 5.90 | 1 / 1.0 | **0.83** | 1 / 25.0 | 19.8x |
| CASPASE7 | 7 | 5.67 / 9.41 | 1 / 2.0 | 0.14 | 43 / 52.0 | 28.2x |

**Headline: partial generalization, uneven, not a clean "hoax" and not a
clean negative.**

1. **Min spatial-hop = 1 on 6 of 7 targets** -- every target except PTP1B
   has at least one pocket residue that is a direct contact-graph neighbour
   of the active site. TASK-0169's KRAS_G12C observation was not a
   one-off in that narrow sense.
2. **But how much of the pocket is trivially close varies by an order of
   magnitude.** CASPASE1 is the worst case in the whole set (83% of its
   pocket at hop<=1, median hop 1.0) -- more trivial than KRAS_G12C (39%,
   median 2.0), which was the only target previously checked. BCR_ABL1/
   GLUCOKINASE/CASPASE7 sit at 6-14%. **CARDIAC_MYOSIN and especially
   PTP1B are the non-trivial cases**: PTP1B has zero pocket residues at
   hop<=1 (min hop 2, median 3.5), CARDIAC_MYOSIN has only 8% at hop<=1
   (median 4.0).
3. **Sanity check passed exactly**: KRAS_G12C's Euclidean min (3.7530 A)
   matches TASK-0169's already-published 3.75 A finding to 4 decimal
   places -- confirms the script reproduces prior work rather than
   introducing a silent discrepancy.
4. **Chain-hop (primary sequence) tells a completely different story on
   every target** -- medians of 22-181 residues where spatial-hop is only
   1-4. The fold-compression ratio (chain-hop/spatial-hop) is large
   everywhere, 8.9x-37.7x, with no target below ~9x. **This is a static,
   ENM-free fact about these folds**: tertiary packing alone, no
   conformational sampling involved, already collapses tens to hundreds of
   sequence positions into a handful of contact-graph hops. Feeds directly
   into [[TASK-0187]] as the baseline its dynamic (ENM-sampled) shortcut
   measurement needs to beat to claim anything beyond what the static fold
   already does.
5. **Caveat that stands, not resolved by this task**: all of the above is
   against the *incumbent* 4.5 A label, which [[TASK-0114]] already showed
   moves at every 0.5 A step tested ("a still-moving slope, not a stable
   plateau") even though downstream floor-verdicts were comparatively
   stable there. CASPASE1's extreme 0.83 in particular should not be
   treated as a stable fact about that target's biology until re-checked
   against [[TASK-0177]]'s consensus label -- it could just as easily be an
   artifact of exactly which residues a shaky single-cutoff label happened
   to include. **Follow-up re-score against `core`/`consensus` remains
   explicitly open, tracked above, not silently assumed to be a formality.**

### Not attempted / left for a follow-up

- Re-score against [[TASK-0177]]'s consensus/core label (hard-blocked on
  that task landing).
- A decision on whether/how this changes TASK-0176's "distal allosteric
  site" framing for the submission -- this task reports the numbers, per
  its own Out Of Scope; TASK-0176/0184's call.
- Whether CASPASE1's extreme result specifically should exclude it from
  future "distal" claims, or whether it is a labeling artifact -- flagged
  above, not decided here.
