# TASK-0289 — `detect_active_site` is non-deterministic: a silent network fallback changes scientific results

- Status: Done as a DEFECT RECORD. **All remedial scope moved to [[TASK-0290]] — do not implement from this file.**
- Assignee: unassigned
- Priority: **Critical — invalidates an unknown fraction of every distance-based result in this register**
- Filed: 2026-08-29 by Reviewer thread (found while writing up [[TASK-0288]])
- Related: [[TASK-0288]], [[TASK-0284]], [[TASK-0258]], [[TASK-0287]], [[TASK-0253]]

## The defect

`backend/active_site.py:174-187`:

```python
for fn in (lambda: _from_uniprot(pdb_id, chain),
           lambda: _from_ligands(pdb_id, chain, holo_pdb),
           lambda: _from_site_records(pdb_id, chain)):
    try:
        res = fn()
    except Exception:
        res = None
    if res and res.get("active_site"):
        return res
```

Three tiers, each guarded by a **bare `except Exception`**. `_from_uniprot`
performs a live network fetch. When that call throws for any transient
reason — rate limit, timeout, DNS — the function **silently** drops to a
different tier and returns a **different active site**, with no error, no
warning, and no retry. The `source` field records which tier answered, but
`task0242_two_stage_dryrun.prep()` discards it.

## Reproduction (three consecutive calls, one process)

```
HCV_NS5B_POO
  rep0: n_seed=32  min_A= 1.333  seed=[48, 52, 54, 193, 200, 221, ...]
  rep1: n_seed= 3  min_A=17.936  seed=[220, 318, 319]
  rep2: n_seed= 3  min_A=17.936  seed=[220, 318, 319]
```

**A 16.6 Å swing in `min_A` on one of the register's flagship "distal"
exemplars, from call order alone.** `MKK7_IBRUTINIB` and `KRAS_G12C` were
stable within that process but `MKK7_IBRUTINIB` differed *between*
processes in the same session (1.324 Å / res A164 vs 1.37 Å / res A136).

## Why this is critical

`min_A` is the anchor of the pocket taxonomy ([[TASK-0258]]), the near/far
category, and every distance-based comparison in this register. If the
active site differs between runs, so does everything derived from it.

**It appeared to threaten [[TASK-0288]] Finding F — tested, and it does
not.** With fresh provenance-recorded seed sizes, `n_seed` vs `min_A` is
**rho=−0.148, p=0.45**, and spike vs rest on `n_seed` is **MWU p=0.44**.
7 of the 9 spike targets are `uniprot`-sourced, the same tier as most of
the far group. Decisive counterexamples: **`TRP_SYNTHASE_F6F` has a
2-residue active site and sits in the spike (1.29 Å); `PKR_MITAPIVAT` has
26 and sits in the far group (11.69 Å)**. The `n_seed/N` control that
originally raised the alarm (p=0.072) was itself computed from
tier-contaminated `n_seed` values and does not survive fresh measurement.

The defect remains **Critical on its own merits** — it silently
substitutes one scientific input for another — but it does not explain
Finding F.

## Scope

> **Superseded 2026-08-29.** The measurement item below is done. The five
> remediation items that followed it were **byte-for-byte duplicates of
> [[TASK-0290]]'s scope** and have been removed from this file so two
> implementers cannot pick up the same work and collide on
> `backend/active_site.py`. **[[TASK-0290]] is the single owner of the
> fix and the recompute.** This file remains as the evidence record of
> what the defect is and how it was measured.

- [x] **DONE.** Sweep run over all 33 taxonomy targets, two consecutive
      calls each (`scripts/task0289_active_site_provenance_sweep.py`).
      **3/33 unstable**: `DHPS_GC7` (22 ligand → 28 uniprot),
      `NAMPT_NPA1R` (18 ligand → 10 uniprot), and **`HIV1_RT`
      (0 residues / source `none` → 7 uniprot)** — [[TASK-0253]]'s
      empty-seed failure mode occurring live. Tier distribution:
      24–26 `uniprot`, 3–5 `ligand`, 1 `pdb_site`, 1 `none`.
      Note `HCV_NS5B_POO` was stable at `3, uniprot` across both warm
      calls — its 32-residue cold-start result was the ligand fallback,
      so the **committed** taxonomy value (17.94 Å) is on the correct tier.

## Constraint

Do **not** fix by simply pinning to whichever tier reproduces the current
committed numbers. The point is a defensible, recorded provenance per
target — not agreement with results that may themselves be artifacts.

## Note

This is the same class as [[TASK-0253]]'s silent-empty-seed defect: a
failure mode that produced plausible-looking numbers instead of an error.
That one was caught by a guard added after the fact. **Consider whether
any remaining bare `except Exception` in the scientific path can silently
substitute one input for another.**
