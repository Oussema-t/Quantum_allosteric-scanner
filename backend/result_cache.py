"""Param-keyed result cache — memoization only, never changes a computed value.

Key = SHA-256 of the canonical (sorted) JSON of EVERY parameter that affects the result.
If any param changes, the key changes, so a stale result can never be served. RCSB data
is immutable per PDB id, so a cache hit is byte-identical to recomputing. In-memory LRU +
optional disk tier (disk survives between requests while the instance is warm)."""
import hashlib
import json
import os
from collections import OrderedDict

from .config import config

_MEM = OrderedDict()          # key -> result (LRU)
_HITS = 0
_MISSES = 0


def _key(params):
    canonical = json.dumps(params, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _disk_path(key):
    return os.path.join(config.RESULT_CACHE_DIR, key + ".json")


def get(params):
    """Return a cached result dict for these params, or None."""
    global _HITS, _MISSES
    if not config.RESULT_CACHE_ENABLED:
        return None
    key = _key(params)
    if key in _MEM:
        _MEM.move_to_end(key)
        _HITS += 1
        return _MEM[key]
    path = _disk_path(key)
    if os.path.exists(path):
        try:
            with open(path, "r") as fh:
                result = json.load(fh)
            _MEM[key] = result
            _MEM.move_to_end(key)
            _HITS += 1
            return result
        except Exception:
            pass
    _MISSES += 1
    return None


def set(params, result):
    """Store a result for these params (in-memory + best-effort disk)."""
    if not config.RESULT_CACHE_ENABLED:
        return
    key = _key(params)
    _MEM[key] = result
    _MEM.move_to_end(key)
    while len(_MEM) > config.RESULT_CACHE_MAX:
        _MEM.popitem(last=False)
    try:
        os.makedirs(config.RESULT_CACHE_DIR, exist_ok=True)
        with open(_disk_path(key), "w") as fh:
            json.dump(result, fh)
    except Exception:
        pass


def info():
    total = _HITS + _MISSES
    return {"result_cache_hits": _HITS, "result_cache_misses": _MISSES,
            "result_cache_hit_rate": round(_HITS / total, 3) if total else None,
            "result_cache_size": len(_MEM)}
