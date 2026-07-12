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
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

RNG = np.random.default_rng(0)

# ===========================================================================
# CONTRACT — reconciled against the real shipped API (TASK-0052, 2026-07-12)
# ===========================================================================
# This section originally *assumed* an API (`build_labels(apo, holo,
# allosteric_ligand, func_ligands, ...)`, `protocol.FrozenConfig`,
# `protocol.lopo`) before labels.py (TASK-0004) / protocol.py (TASK-0006)
# shipped. Reading the live tree found real discrepancies (SEAM-0003) --
# this is what actually exists, and the 3 CONTRACT tests below now call it
# for real rather than xfail-ing against a stale assumption:
#
# labels.build_labels(apo, holo, target_config: dict,
#                      cutoff=4.5, terminal_fraction=0.05) -> Labels
#   Labels.pocket             : (N,) bool over APO residues, or None if the
#                                allosteric ligand didn't resolve
#   Labels.pocket_raw         : (N,) bool, pocket BEFORE exclusion (diagnostic only)
#   Labels.active_site        : (N,) bool -- the functional/catalytic seed
#                                set (excluded from pocket by construction)
#   Labels.functional_provenance / .drug_ligand : str / str|None
#   target_config keys used: "drug_ligand" (the allosteric ligand code --
#   never derives from func_ligand), "func_ligand" (list of codes to exclude)
#   Rules (asserted inside build_labels itself, TASK-0070/SEAM-0003):
#     pocket & active_site == empty set; pocket & terminal == empty set.
#     apo<->holo mapping is sequence ALIGNMENT (holo_pocket_mask's
#     Needleman-Wunsch), never resnum equality.
#
# protocol.frozen_context(blocked_targets) / protocol.ceiling_context()
#   Context managers (not a FrozenConfig object) -- see TASK-0006. No
#   `.freeze()`/`.hash`/`.require_frozen()` exists; the equivalent
#   guarantee (reject use before/after the wrong phase) is "no active
#   context = unguarded" plus assert_readable's runtime raise. This file's
#   own FrozenConfig class below is kept as the reference mechanics spec
#   (GATE-B1's three unit tests are pipeline-agnostic and still valid on
#   their own terms) but it is NOT what protocol.py actually implements --
#   see this task's Done section for the explicit equivalence check
#   against `_SealedLabels`/GATE-B2 below, including a real gap found.
#
# protocol.leave_one_protein_out(targets) -> yields (train, held_out)
#   Does NOT itself wrap/seal held_out's labels (TASK-0006's own docstring:
#   "composability over magic") -- the caller brackets selection in
#   `with frozen_context({held_out}): ...`; reading held_out's label via
#   protocol.py's gated accessors (get_pocket_mask/get_labels/
#   get_functional_indices/get_superpose_report) inside that block raises
#   LeakageError. This is GATE-B2's real mechanism, verified below.
#
# protocol.permutation_null / floor_baselines / ceiling_supervised — none
# of these exist under those names; GATE-B4's permutation_null and GATE-C's
# floor_baselines are this *file's own* reference implementations (used by
# the self-validating meta-tests), not a claim that protocol.py has them.
# No CONTRACT test in this file assumed otherwise, so nothing to fix here.
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
# Contract tests — reconciled against the real API (TASK-0052, 2026-07-12)
# ---------------------------------------------------------------------------
# Not xfail stubs anymore: each of the 3 tests below calls the real
# allostery.labels/protocol code. The only thing that may still legitimately
# skip is real RCSB access (network/prody) -- _skip mirrors the file's own
# custom __main__ runner (only AssertionError is treated as FAIL; anything
# printed-and-returned reads as PASS), kept dependency-light (no pytest
# import) so `python test_leakage_gate.py` standalone still works per this
# file's own docstring, not just `pytest test_leakage_gate.py`.
def _skip(reason):
    print(f"  SKIP (real-structure fetch unavailable): {reason}")


def _load_real_target(apo_id, holo_id, chains):
    from allostery.clean import clean
    from allostery.labels import ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue
    import prody

    prody.confProDy(verbosity="none")
    apo = clean(apo_id, chains=chains)
    holo = clean(holo_id, chains=chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(
        " or ".join(f"chain {c}" for c in chains)
    )
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )
    return apo, holo


def test_labels_allosteric_ligand_only():
    """BCR-ABL1: label from asciminib (AY7), NEVER nilotinib (NIL) -- the
    original bug (`labels.pick_drug`'s own docstring names it: "that
    heuristic is exactly what produced the original BCR_ABL1 bug"). Real
    network-gated check against 1OPL(apo)/5MO4(holo); ASCIMINIB was
    v2-doc-era shorthand for a since-resolved RCSB code (AY7,
    config/targets.yaml, TASK-0003) -- using the placeholder name here
    would be testing a value that was never real, not the actual bug."""
    try:
        import prody  # noqa: F401
    except ImportError as exc:
        return _skip(f"prody not installed: {exc!r}")

    from allostery.labels import build_labels

    try:
        apo, holo = _load_real_target("1OPL", "5MO4", ["A"])
    except Exception as exc:
        return _skip(f"{exc!r}")

    lab = build_labels(apo, holo, {"drug_ligand": "AY7", "func_ligand": ["NIL"]})
    assert lab.drug_ligand == "AY7", "did not resolve the allosteric ligand explicitly"
    assert lab.pocket is not None, "AY7 not found in holo -- pocket undetermined"
    assert (lab.pocket & lab.active_site).sum() == 0, "active-site residues leaked into pocket"
    assert 3 <= lab.pocket.sum() <= 0.15 * len(lab.pocket), "pocket size implausible"


def test_labels_alignment_not_resnum():
    """A +19 residue-number offset between apo/holo (the ABL1 1a/1b
    hazard, SYSTEMS_allosteric_corrected_v2.md) must not move the
    physical pocket label -- confirms build_labels' sequence-alignment
    mapping (not resnum equality) is what actually runs end-to-end, not
    just exercised in holo_pocket_mask's own unit tests in isolation.
    Synthetic (fast, no network): resnum equality would look for apo
    resnum 501+ (doesn't exist) and silently return an all-False mask
    instead of the correct physical residues."""
    from allostery.labels import LigandGroup, build_labels

    class _Struct:
        def __init__(self, coords, resnums, resnames, ligand_groups=None):
            self.coords = coords
            self.resnums = np.asarray(resnums)
            self.resnames = list(resnames)
            self.ligand_groups = ligand_groups or []

    n = 12
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    coords = np.column_stack([2.3 * np.cos(theta), 2.3 * np.sin(theta), 1.5 * np.arange(n, dtype=float)])
    seq3 = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS"]

    apo = _Struct(coords, np.arange(1, n + 1), seq3)

    offset = 19
    drug = LigandGroup("LIG", 501, "A", np.array([coords[5]]), 1)
    func = LigandGroup("FUNC", 502, "A", np.array([coords[10]]), 1)
    holo = _Struct(coords, np.arange(1 + offset, n + 1 + offset), seq3, [drug, func])

    labels = build_labels(apo, holo, {"drug_ligand": "LIG", "func_ligand": ["FUNC"]}, cutoff=4.5)

    assert labels.pocket is not None, "ligand contact resolution failed"
    assert labels.pocket[5], "physical residue 5 not labelled under a +19 holo renumber"
    assert not (labels.pocket & labels.active_site).any()


def test_protocol_lopo_seals_heldout_labels():
    """GATE-B2's real mechanism: leave_one_protein_out + frozen_context +
    assert_readable -- not a _SealedLabels wrapper object (see this task's
    Done section for the explicit equivalence check, including the one
    real gap found: protocol.py's gate is opt-in/cooperative, not a hard
    data seal like _SealedLabels below). Confirms the actual guarantee:
    for held-out p, reading p's label during the with frozen_context
    block raises."""
    from allostery.protocol import LeakageError, assert_readable, frozen_context, leave_one_protein_out

    proteins = ["A", "B", "C"]
    for train, held_out in leave_one_protein_out(proteins):
        assert held_out not in train, "held-out protein leaked into its own training fold"
        with frozen_context({held_out}):
            try:
                assert_readable(held_out)
            except LeakageError:
                pass
            else:
                raise AssertionError(
                    f"held-out protein {held_out!r}'s label was readable during selection"
                )


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
