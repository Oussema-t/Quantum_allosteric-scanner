# PROFILING — where the time actually goes

Measured with `time.perf_counter` on cached structures (so this is **compute only** — it
excludes the RCSB/UniProt network fetch, which is measured separately). GNM cutoff 8 Å.

| Protein | N (residues) | parse (BioPython) | GNM eigh | site_potentials (incl 1000-perm test) |
|---|---:|---:|---:|---:|
| 4OBE/A (KRAS)      | 169 | 207 ms | 8.5 ms  | 107 ms |
| 1SUG/A (PTP1B)     | 298 | 68 ms  | 29 ms   | 134 ms |
| 3H1V/X (glucokinase)| 446 | 149 ms | 305 ms  | 333 ms |
| 1OPL/A (ABL)       | 451 | 197 ms | 326 ms  | 585 ms |

## What dominates
- **For proteins ≤ ~450 residues, compute is sub-second.** The GNM eigendecomposition is
  8–326 ms; the full analysis is < 0.6 s. **Compute is NOT the bottleneck at these sizes.**
- The GNM eigh grows ~**O(N³)**: 8 → 29 → 305 → 326 ms as N goes 169 → 451. Extrapolating,
  N≈1500 (the app's cap) is on the order of ~10 s — so **only very large proteins (>800)
  make compute the bottleneck.**
- The real user-visible slowness is **(1) Render free-tier cold start (30–60 s after idle)**
  and **(2) RCSB/UniProt network round-trips (seconds)** — neither is Python/CPU.

## What was done about it (see CHANGES.md)
1. **Result cache** (param-keyed): a repeated request returns instantly — removes re-fetch,
   re-parse, and re-compute in one shot. This is the biggest win for the observed pattern.
2. **Keep-warm**: `.github/workflows/keepalive.yml` pings `/api/health` every 10 min so the
   instance never cold-starts. (Also documented for an external uptime monitor.)
3. Structure/JSON network responses are already cached (`data_layer.fetch` on disk,
   `rcsb._get_json` in memory).

## What was deliberately NOT done
- **Sparse/truncated eigensolver** — would speed up big proteins but **changes the numbers**:
  our descriptors (msf, V_C covariance, average-mixing matrix, Laplacian spectrum) are
  full-spectrum. `scripts/verify_eigensolver.py` shows truncating to 10 modes shifts the
  shipped MSF by ~45%. Kept dense `eigh`. A truncated GNM would be a separate, validated
  modelling change.
- **Job queue + progress-bar polling** — a real responsiveness win, but a large add-only
  frontend change across many endpoints; deferred to its own pass to keep this diff safe.

## Bottom line
Big-protein *first-load* still needs either a stronger host (compute) or the deferred job
queue (so the UI doesn't block) — the caching here makes everything after the first hit
fast, and keep-warm removes the cold start. No scientific output changed.
