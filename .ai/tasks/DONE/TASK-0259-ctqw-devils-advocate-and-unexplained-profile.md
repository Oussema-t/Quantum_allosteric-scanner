# TASK-0259 — Devil's advocate for CTQW, and what the large-unexplained cases have in common

- Status: DONE
- Assignee: Reviewer thread
- Filed & completed: 2026-08-25
- Related: [[TASK-0250]], [[TASK-0254]], [[TASK-0257]], [[TASK-0258]], `documentation/CTQW_CONTRIBUTION_BRIEF.html` §07 item 4

## Done

Two questions, one join. Only new computation: GNM-vs-B-factor validity on
[[TASK-0243]]'s frozen set (which [[TASK-0250]] never covered — it scored the
15 *register* targets, and the two sets barely overlap, so the pre-registered
subgroup test had never been runnable).

### A — The pre-registered subgroup test FAILED, in the opposite direction

The brief committed us to updating if CTQW's marginal were positive on
ENM-valid targets and negative on ENM-invalid ones. It is the reverse.

| group | n | CTQW added-last | CTQW Shapley |
|---|---|---|---|
| ENM valid (PASS/MARGINAL) | 16 | **−0.21%** | −0.3% |
| ENM invalid (FAIL) | 4 | **+7.73%** | +18.3% |

Mann-Whitney (valid > invalid): **p=0.9674**. Spearman(ENM validity r, CTQW
added-last) = −0.119, p=0.617. On ENM-valid targets alone CTQW's added-last
median is −0.21%, Wilcoxon p=0.782, positive on 6/16.

**CTQW looks best exactly where its own physical model does not fit.**
`MKK7_IBRUTINIB`, the +49%-Shapley target, is an ENM **FAIL** (geometry solo
0.878, CTQW solo 0.943 — both high, but the dynamics model is invalid there,
so dynamics cannot be what is doing the work). n=4 in the FAIL group, so this
is weak evidence — but it is evidence against the mechanistic story, not for it.

### B — The unexplained share is crypticity, and almost nothing else

| correlate of the unexplained share | Spearman rho | p |
|---|---|---|
| **apo crypticity (fraction of pocket already open)** | **−0.771** | **0.0001** |
| ENM validity (GNM–B-factor r) | +0.002 | 0.99 |
| pocket-to-active-site min distance | −0.236 | 0.32 |
| pocket size | +0.213 | 0.37 |
| active-site size | −0.140 | 0.55 |

Median unexplained: **55% on cryptic targets (apo-open <50%) vs 24% on
already-open targets (≥80%)**. The five largest-unexplained targets are all
contact-adjacent, apo-open median 50% vs 82% for the rest.

**The residual is not mysterious physics — it is pocket-not-yet-formed.**
Where the pocket has not opened in apo, neither fpocket nor geometry can see
it, so nothing in the model can. Confirmed from the other side: fpocket's own
Shapley share correlates **+0.518 (p=0.019)** with apo-openness — it works
precisely when the pocket is already there.

### C — The one live hypothesis left for CTQW

Crypticity is exactly the regime a dynamics method should own. Does CTQW
deliver there?

| | value |
|---|---|
| rho(apo-open, CTQW added-last) | −0.186, p=0.43 |
| cryptic subgroup (n=3) CTQW added-last | +1.91% |
| open subgroup (n=9) CTQW added-last | −0.10% |
| Mann-Whitney (cryptic > open) | p=0.30 |

Directionally favourable, nowhere near significance, **n=3**. This is the only
regime in which CTQW has not been fairly tested, and it cannot be tested on
the current benchmark — 9/20 targets are already open. Testing it requires a
cryptic-enriched target set, which is what the brief's §08 already argues for
on independent grounds.

**Script:** `scripts/task0259_ctqw_devils_advocate_profile.py`.
**Data:** `results/tasks/0259_ctqw_devils_advocate/profile.json`.

**2026-08-26 fix (unrelated to the finding above, numbers unaffected):** this
script's own `prody.parsePDB = _parsePDB_all_altloc` (imported by name from
`task0255_hop_angstrom_calibration.py`) was silently discarding
`allostery/__init__.py`'s folder-default patch, scattering fetched PDB files
into cwd instead of `pdb_cache/` — same bug as
[[TASK-0258]]'s identically-patterned script. Fixed by importing the module
for its patching side effect instead of reassigning to its exported name; see
`pdb_cache/README.md` for the general rule. Already-run results untouched.
