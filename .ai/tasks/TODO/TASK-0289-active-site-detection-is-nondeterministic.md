# TASK-0289 — `detect_active_site` is non-deterministic: a silent network fallback changes scientific results

- Status: TODO — **BLOCKER**
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

**It also threatens [[TASK-0288]] Finding F directly.** A broad UniProt
annotation (an entire nucleotide pocket) makes any adjacent pocket abut
the active site (`min_A ≈ 1.3 Å`); a narrow 3-residue ligand-derived site
does not. **Heterogeneous provenance across targets could manufacture the
observed 9/28 contact spike without any benchmark defect at all** — and
the `n_seed/N` control in [[TASK-0288]] (spike group 0.054 vs rest 0.030,
MWU p=0.072) points the same way.

## Scope

- [ ] Record `source` per target for every target in the taxonomy, twice,
      and report how many are unstable and what the tier distribution is.
      *(A first pass was started by the Reviewer thread and is still
      running at filing time — do not assume it completed.)*
- [ ] Make detection **deterministic**: cache the resolved active site to
      disk on first successful resolution, keyed by (pdb_id, chain), and
      read from that cache thereafter. Network only on a cache miss.
- [ ] Make the fallback **loud**: distinguish "UniProt says there is no
      annotation" (a real negative, fall through) from "the UniProt call
      failed" (an error — retry, then raise). A bare `except Exception`
      must not silently downgrade a scientific input.
- [ ] Propagate `source` through `prep()` into every result JSON so
      provenance is auditable after the fact.
- [ ] Recompute `min_A` for all targets under the fixed path; diff against
      the committed taxonomy and report every target that moves.
- [ ] Re-run [[TASK-0288]] Finding F on the corrected values.

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
