"""Quantum-allosteric signal propagation – Cleveland Clinic Challenge 2026."""
from pathlib import Path

import prody

__version__ = "0.1.0"

# Every script/test in this package fetches structures via
# `prody.parsePDB`/`fetchPDB` with a bare PDB ID, never a path, and none
# pass an explicit `folder=`. ProDy's own `fetchPDB` (`proteins/localpdb.py`)
# defaults an unset `folder` kwarg to `'.'` -- literally the process's cwd
# at call time -- regardless of `pathPDBFolder()` (that setting only
# short-circuits re-downloading a *compressed* .pdb.gz already cached
# there; a `compressed=False` request, which is what every call site here
# uses, still decompresses into `folder`, i.e. cwd, even on a cache hit --
# confirmed directly against ProDy's own source, not assumed). That is
# what scattered ~280 downloaded .pdb files across the repo root,
# depending on which directory a script happened to be run from.
#
# Fixed at the single import point every submodule shares, not at each of
# the ~40 call sites: wrap `parsePDB`/`fetchPDB` so an unset `folder`
# defaults to this package's own dedicated, already-gitignored cache
# (anchored to this file's own location, not cwd) instead of ProDy's `.`.
# An explicit `folder=` passed by any caller is still honored untouched.
_PDB_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "pdb_cache"
_PDB_CACHE_DIR.mkdir(exist_ok=True)
prody.pathPDBFolder(str(_PDB_CACHE_DIR))

_orig_parsePDB = prody.parsePDB
_orig_fetchPDB = prody.fetchPDB


def _parsePDB_default_folder(*args, **kwargs):
    kwargs.setdefault("folder", str(_PDB_CACHE_DIR))
    return _orig_parsePDB(*args, **kwargs)


def _fetchPDB_default_folder(*args, **kwargs):
    kwargs.setdefault("folder", str(_PDB_CACHE_DIR))
    return _orig_fetchPDB(*args, **kwargs)


prody.parsePDB = _parsePDB_default_folder
prody.fetchPDB = _fetchPDB_default_folder
