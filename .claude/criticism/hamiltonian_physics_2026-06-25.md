# Cross-repo Physics Review: CCC vs QAS Hamiltonian Layer

**File reviewed:** `src/allostery/potentials.py`, `src/allostery/hamiltonians.py`
**Reference implementation:** `Quantum_allosteric-scanner/backend/analysis.py`
**Review created:** 2026-06-25
**Review ID:** CRIT-003

Context: QAS (`Quantum_allosteric-scanner`) is a colleague's deployed web app implementing
GNM-based allostery analysis. CCC implements the same five potential functions but diverges
in formula and purpose. This review captures the physics disagreements to resolve before
proposing any code to the colleague.

---

## PHY-1 — GNM contact cutoff: 10.0 Å (CCC) vs 8.0 Å (QAS)

CCC's `hamiltonians.contact_matrix` and `potentials.*` default to `cutoff=10.0`.
QAS `analysis.gnm_context` uses `cutoff=8.0` throughout.

The GNM literature (Bahar et al. 1997, Tirion 1996) establishes 7–8 Å as the standard
for Cα-only contact networks. At 10 Å many secondary-structure contacts that are
physically screened become included, inflating the degree matrix and softening the
spectral gap. The 8 Å value is the accepted GNM standard; 10 Å is more typical for
elastic-network models that use all heavy atoms.

Neither value is wrong in principle, but they are not interchangeable: MSF correlations
with B-factors, spectral gaps, and the ranking from CTQW will all differ. Using different
defaults in CCC and QAS makes cross-validation impossible.

**Action needed:** benchmark Pearson(MSF, B-factor) at 7, 8, 9, 10 Å across the 6
benchmark proteins. The cutoff with the highest correlation is the defensible default.

---

## PHY-2 — V_C formula divergence (proxy vs rigorous DCC)

**CCC `potentials.V_C`:**
```python
W = contact_matrix(coords, cutoff=cutoff, weight="invdist")
centrality = W.sum(axis=1)          # invdist row-sum
return np.diag(-centrality_norm)
```
This is an inverse-distance centrality heuristic — it does not compute any covariance.

**QAS `analysis.V_covariance`:**
```python
Cov = (U * winv) @ U.T              # Kirchhoff pseudo-inverse = GNM covariance
nDCC = Cov / outer(sqrt(diag), sqrt(diag))   # normalised DCC
return _z(abs(nDCC).sum(1))         # mean absolute coupling per residue
```
This is the correct GNM dynamic cross-correlation (DCC) — the standard measure of
collective coupling in the protein physics literature (Haliloglu & Bahar 1999).

The two quantities measure different things. The CCC version will reward residues with
many nearby contacts regardless of their dynamic behavior. The QAS version rewards
residues that co-fluctuate globally with the rest of the network — which is the physically
meaningful quantity for identifying allosteric conduits.

**Action needed:** replace CCC's `V_C` with the GNM DCC formula, keeping the same
diagonal-matrix output convention.

---

## PHY-3 — V_R formula divergence (no MSF term in CCC)

**CCC `potentials.V_R`:**
```python
score = -(degree_norm / (b_norm + 0.1))
return np.diag(score)
```
Rewards high-degree, low-B residues. No clustering or fluctuation term.

**QAS `analysis.V_rigidity`:**
```python
return _z(_z(deg) + _z(clust) + (-_z(msf)))
```
Combines three complementary rigidity signals: connectivity (degree), local topology
(clustering coefficient), and dynamics (mean-square fluctuation from GNM). The MSF term
is the physically essential one: a residue can have high degree and still be flexible
(loop regions in a protein core); the MSF from GNM captures the actual dynamical
rigidity, not just the static contact count.

The CCC version is a reasonable proxy but will misrank loop-core boundary residues
where degree and flexibility decorrelate.

**Action needed:** adopt the three-term formulation from QAS in CCC's `V_R`, expressed
as a diagonal penalty/reward matrix consistent with the `build_H_new` convention.

---

## PHY-4 — Weighting schemes in `contact_matrix()` are unvalidated

CCC implements five weight schemes (`binary`, `gaussian`, `exponential`, `harmonic`,
`invdist`). QAS uses `binary` only (the GNM standard).

No benchmark has been run to show that any weighted scheme improves B-factor
correlation or AUC over binary. Without that, the weighted Hamiltonians H5
(gaussian), H6 (exponential), H11 (exponential normalised) and the `weight="invdist"`
call inside `V_C` are physically unjustified. The harmonic and invdist schemes in
particular diverge strongly near self-contacts and require careful numerical regularisation
that is currently handled only with a small epsilon that is not validated.

**Action needed:** for each weight scheme, compute Pearson(predicted_MSF, B-factor) on
the 6 benchmark proteins. Schemes that do not improve over binary should be documented
as "available but not recommended" and should not appear in `build_H_new` by default.
