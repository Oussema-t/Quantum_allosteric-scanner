"""Central configuration — every tunable is an env var with a documented default.

No magic numbers elsewhere: import from here. Defaults are chosen to preserve current
behaviour exactly (caching/limits are opt-out-safe), so nothing scientific changes.
"""
import os


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    # ── caches (RCSB data is immutable per PDB id, so caching never changes results) ──
    STRUCTURE_CACHE_DIR = os.environ.get("QAS_STRUCTURE_CACHE_DIR", "./pdb_cache")
    RESULT_CACHE_DIR = os.environ.get("QAS_RESULT_CACHE_DIR", "./result_cache")
    RESULT_CACHE_ENABLED = os.environ.get("QAS_RESULT_CACHE", "1") != "0"
    RESULT_CACHE_MAX = _int("QAS_RESULT_CACHE_MAX", 256)     # in-memory LRU entries

    # ── GNM / eigensolver ──
    # NOTE: the current GNM descriptors (msf, V_C covariance, average-mixing matrix, the
    # reported Laplacian spectrum) use the FULL eigenspectrum, so a truncated sparse
    # solve would change the numbers. Dense eigh is therefore kept unconditionally until a
    # truncated GNM is separately validated. These knobs exist for that future work only.
    SPARSE_THRESHOLD = _int("QAS_SPARSE_THRESHOLD", 100000)  # effectively "never" today
    N_MODES = _int("QAS_N_MODES", 10)
    N_BOOTSTRAP = _int("QAS_N_BOOTSTRAP", 200)
    N_PERM = _int("QAS_N_PERM", 1000)

    # ── frontend render caps (drawing limits only — never touch the computed values) ──
    MAX_PLOT_POINTS = _int("QAS_MAX_PLOT_POINTS", 4000)

    # ── misc ──
    HEALTH_PATH = os.environ.get("QAS_HEALTH_PATH", "/api/health")


config = Config()
