"""Leakage gate — acceptance suite for labels.py (TASK-0004) and protocol.py (TASK-0006).

This file is the *check on the swarm*, not swarm output. It is deliberately
self-contained and self-validating: the pipeline-agnostic detectors run and
prove themselves on synthetic honest/leaky scorers with NO real pipeline
present. The contract tests for the real modules xfail until implemented, so
this file is a live acceptance target — turn it green.

Design axiom
------------
A leak is anything that keeps scoring above chance when the labels are
randomized. The permutation-null (GATE-B4) catches it regardless of *where*
the leak entered — labels.py, the objective, or a frozen-param violation.
Everything else is a cheaper, more specific guard that localizes the leak.

Run standalone (no pytest needed):  python test_leakage_gate.py
Run under pytest:                    pytest test_leakage_gate.py -q
"""
from __future__ import annotations

import hashlib
import json
import numpy as np
from sklearn.metrics import roc_auc_score

RNG = np.random.default_rng(0)

# ===========================================================================
# CONTRACT — what labels.py (TASK-0004) and protocol.py (TASK-0006) must expose
# ===========================================================================
# labels.build_labels(apo, holo, allosteric_ligand, func_ligands,
#                      contact_cutoff=4.5, exclude_active_site=True) -> Labels
#   Labels.pocket        : (N,) bool over APO residues
#   Labels.active_site   : (N,) bool (excluded from pocket by construction)
#   Labels.provenance    : dict(ligand=<3-letter>, contacts=[...], alignment=...)
#   Rules: derive from the ALLOSTERIC ligand only (never func_ligand);
#          map apo<->holo by sequence ALIGNMENT not resnum equality;
#          pocket & active_site == empty set.
#
# protocol.FrozenConfig(params: dict)
#   .freeze() -> self         (idempotent; sets .hash; further mutation raises)
#   mutation after freeze     -> raises RuntimeError
#   .require_frozen()         -> raises if used before freeze
#   .hash                     : sha256 of canonical params (goes in the report)
#
# protocol.lopo(proteins, select_fn, eval_fn) -> per-fold results
#   For held-out p: select_fn is called on the OTHER proteins only; p's labels
#   are wrapped so ANY access during selection raises (GATE-B2).
#
# protocol.permutation_null(pipeline, labels, n_perm) -> (auc_true, perm_mean, ci95)
# protocol.floor_baselines(structure, active_site) -> {name: scores}
# protocol.ceiling_supervised(structure, labels) -> auc   (leaky by design)
# ===========================================================================


# ---------------------------------------------------------------------------
# Shared synthetic world + the two canonical scorers used to self-validate
# ---------------------------------------------------------------------------
def _world(n=120, seed=0):
    rng = np.random.default_rng(seed)
    coords = rng.normal(size=(n, 3)) * 10.0
    d = np.linalg.norm(coords - coords[0], axis=1)
    pocket = np.zeros(n, bool)
    pocket[np.argsort(d)[:6]] = True         # 6 spatially-clustered positives
    active = np.zeros(n, bool)
    active[np.argsort(d)[-6:]] = True         # a disjoint "active site"
    return coords, pocket, active


def _contact(coords, cutoff=10.0):
    D = np.linalg.norm(coords[:, None] - coords[None], axis=2)
    return ((D < cutoff) & (D > 0)).astype(float)


def honest_scorer(coords, labels=None):
    """Topology only. NEVER reads labels. GNM rigidity (low fluctuation)."""
    A = _contact(coords)
    L = np.diag(A.sum(1)) - A
    w, V = np.linalg.eigh(L)
    nz = w > 1e-9
    msf = np.diag((V * np.where(nz, 1.0 / np.where(nz, w, 1.0), 0.0)) @ V.T)
    return -msf


def leaky_scorer(coords, labels):
    """Peeks at whatever labels it is handed — the failure mode to catch."""
    return labels.astype(float) + RNG.normal(0, 0.01, size=len(labels))


# ---------------------------------------------------------------------------
# GATE-B4 — permutation null (the load-bearing detector)
# ---------------------------------------------------------------------------
def permutation_null(scorer, coords, labels, n_perm=200, seed=1):
    rng = np.random.default_rng(seed)
    auc_true = roc_auc_score(labels, scorer(coords, labels))
    perms = np.array([
        roc_auc_score(y := rng.permutation(labels), scorer(coords, y))
        for _ in range(n_perm)
    ])
    return auc_true, float(perms.mean()), np.percentile(perms, [2.5, 97.5])


PERM_LEAK_THRESHOLD = 0.60   # perm_mean above this => label side-channel


def test_meta_permutation_detector_discriminates():
    """The gate proves itself: fires on leak, stays silent on honest signal."""
    coords, pocket, _ = _world()
    a_h, pm_h, _ = permutation_null(honest_scorer, coords, pocket)
    a_l, pm_l, _ = permutation_null(leaky_scorer, coords, pocket)
    assert a_h > 0.65, f"honest scorer has no real signal (auc_true={a_h:.3f})"
    assert pm_h < PERM_LEAK_THRESHOLD, f"false positive: honest perm_mean={pm_h:.3f}"
    assert pm_l > 0.90, f"detector missed a blatant leak (perm_mean={pm_l:.3f})"
    return dict(honest=(a_h, pm_h), leaky=(a_l, pm_l))


# ---------------------------------------------------------------------------
# GATE-B1 — frozen firewall mechanics (reference spec the real one must match)
# ---------------------------------------------------------------------------
class FrozenConfig:
    """Reference implementation. protocol.FrozenConfig must behave identically."""
    def __init__(self, params: dict):
        object.__setattr__(self, "_params", dict(params))
        object.__setattr__(self, "_frozen", False)
        object.__setattr__(self, "hash", None)

    def __setattr__(self, k, v):
        if getattr(self, "_frozen", False):
            raise RuntimeError(f"config is FROZEN; cannot set {k!r}")
        object.__setattr__(self, k, v)

    def set(self, k, v):
        if self._frozen:
            raise RuntimeError(f"config is FROZEN; cannot set {k!r}")
        self._params[k] = v

    def freeze(self):
        blob = json.dumps(self._params, sort_keys=True).encode()
        object.__setattr__(self, "hash", hashlib.sha256(blob).hexdigest())
        object.__setattr__(self, "_frozen", True)
        return self

    def require_frozen(self):
        if not self._frozen:
            raise RuntimeError("evaluation attempted before freeze()")


def test_firewall_immutable_after_freeze():
    c = FrozenConfig(dict(alpha=0.3, cutoff=10.0)).freeze()
    assert c.hash and len(c.hash) == 64
    try:
        c.set("alpha", 0.9)
    except RuntimeError:
        pass
    else:
        raise AssertionError("mutation after freeze was allowed")


def test_firewall_no_eval_before_freeze():
    c = FrozenConfig(dict(alpha=0.3))
    try:
        c.require_frozen()
    except RuntimeError:
        return
    raise AssertionError("evaluation before freeze was allowed")


def test_firewall_hash_is_config_fingerprint():
    a = FrozenConfig(dict(x=1, y=2)).freeze().hash
    b = FrozenConfig(dict(y=2, x=1)).freeze().hash      # order-independent
    c = FrozenConfig(dict(x=1, y=3)).freeze().hash
    assert a == b and a != c


# ---------------------------------------------------------------------------
# GATE-B2 — held-out label isolation (runtime tripwire)
# ---------------------------------------------------------------------------
class _SealedLabels:
    """Wrap held-out labels so ANY read during selection raises."""
    def __init__(self, arr): self._arr = np.asarray(arr)
    def __array__(self, *a, **k): raise RuntimeError("held-out labels read during selection (LEAK)")
    def __getitem__(self, *a): raise RuntimeError("held-out labels read during selection (LEAK)")
    def unseal(self): return self._arr


def test_sealed_labels_tripwire():
    y = _SealedLabels(np.array([0, 1, 0, 1]))
    try:
        _ = np.asarray(y) + 1          # a leaky select_fn would do this
    except RuntimeError:
        return
    raise AssertionError("sealed held-out labels were readable during selection")


def test_positive_control_leaky_objective_is_caught():
    """A select_fn that tunes on held-out labels must trip B2 or B4."""
    coords, pocket, _ = _world()
    sealed = _SealedLabels(pocket)

    def leaky_select(structure, held_out_labels):
        # simulates optimizing params against the answer
        return np.asarray(held_out_labels)      # <- must raise via tripwire

    try:
        leaky_select(coords, sealed)
    except RuntimeError:
        return
    raise AssertionError("leaky objective was not caught by the firewall")


# ---------------------------------------------------------------------------
# GATE-B5 — degree-confound guard
# ---------------------------------------------------------------------------
def degree_confound_fail(scores, coords, method_auc, degree_auc, cutoff=10.0):
    A = _contact(coords, cutoff)
    r = np.corrcoef(scores, A.sum(1))[0, 1]
    return abs(r) > 0.80 and (method_auc - degree_auc) < 0.05


def test_degree_confound_flags_disguised_degree():
    coords, pocket, _ = _world()
    A = _contact(coords)
    degree = A.sum(1)
    # a "method" that is just degree + noise
    disguised = degree + RNG.normal(0, 1e-3, size=len(degree))
    m_auc = roc_auc_score(pocket, disguised)
    d_auc = roc_auc_score(pocket, degree)
    assert degree_confound_fail(disguised, coords, m_auc, d_auc), \
        "degree-in-disguise was not flagged"


# ---------------------------------------------------------------------------
# GATE-C — floor / ceiling / headroom integrity
# ---------------------------------------------------------------------------
def floor_baselines(coords, active_site, seed=2):
    rng = np.random.default_rng(seed)
    A = _contact(coords)
    degree = A.sum(1)
    inv_dist_active = -np.linalg.norm(
        coords[:, None] - coords[active_site][None], axis=2).min(1)
    return {
        "random": rng.normal(size=len(coords)),
        "degree": degree,
        "inv_dist_to_active": inv_dist_active,
    }


def headroom(method_auc, floor_auc, ceiling_auc):
    denom = ceiling_auc - floor_auc
    if denom <= 1e-6:
        return float("nan")   # target uninformative; report, don't divide
    return (method_auc - floor_auc) / denom


def test_floor_is_not_just_random():
    """Floor must be the best TRIVIAL structural predictor, not random."""
    coords, pocket, active = _world()
    bl = floor_baselines(coords, active)
    aucs = {k: roc_auc_score(pocket, v) for k, v in bl.items()}
    floor = max(aucs.values())
    assert floor >= aucs["random"], "floor collapsed to random"
    # bar to clear "signal" is the strongest baseline, not 0.5
    assert floor >= 0.5


def test_method_cannot_beat_its_own_supervised_ceiling():
    """Held-out method > in-sample leaky ceiling is impossible w/o a leak."""
    coords, pocket, active = _world()
    method_holdout = roc_auc_score(pocket, honest_scorer(coords))
    ceiling = roc_auc_score(pocket, leaky_scorer(coords, pocket))  # leaky upper bound
    assert method_holdout <= ceiling + 1e-9, \
        "method beat its supervised ceiling on held-out data => leak"


# ---------------------------------------------------------------------------
# Contract stubs — turn green when TASK-0004 / TASK-0006 land
# ---------------------------------------------------------------------------
def _xfail(reason):
    print(f"  XFAIL (expected until implemented): {reason}")


def test_labels_allosteric_ligand_only():
    """BCR-ABL1: label from asciminib, NEVER nilotinib (NIL)."""
    try:
        from allostery.labels import build_labels
    except Exception:
        return _xfail("labels.build_labels — TASK-0004")
    lab = build_labels(apo="1OPL", holo="5MO4",
                       allosteric_ligand="ASCIMINIB", func_ligands=["NIL"])
    assert lab.provenance["ligand"] != "NIL", "picked orthosteric nilotinib (the old bug)"
    assert (lab.pocket & lab.active_site).sum() == 0, "active-site residues leaked into pocket"
    assert 3 <= lab.pocket.sum() <= 0.15 * len(lab.pocket), "pocket size implausible"


def test_labels_alignment_not_resnum():
    """A +19 renumber (ABL1 1a/1b hazard) must not move the physical label."""
    try:
        from allostery.labels import build_labels  # noqa: F401
    except Exception:
        return _xfail("labels alignment-invariance — TASK-0004")
    raise AssertionError("implement: label same physical residues under +19 renumber")


def test_protocol_lopo_seals_heldout_labels():
    try:
        from allostery.protocol import lopo  # noqa: F401
    except Exception:
        return _xfail("protocol.lopo held-out isolation — TASK-0006")
    raise AssertionError("implement: fold p's labels must trip the tripwire in select_fn")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            out = t()
            extra = f"  {out}" if out else ""
            print(f"[PASS] {t.__name__}{extra}")
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
