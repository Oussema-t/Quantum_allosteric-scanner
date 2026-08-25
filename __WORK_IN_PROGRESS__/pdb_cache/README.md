# This is the research-scaffold PDB cache

Every script under `__WORK_IN_PROGRESS__/` (`scripts/`, `tests/`, `src/allostery/`)
downloads/parses structures here — not to whatever the process's cwd happens to be.

This is enforced at one place: `__WORK_IN_PROGRESS__/src/allostery/__init__.py`
monkeypatches `prody.parsePDB`/`prody.fetchPDB` so an **unset** `folder=` kwarg
defaults to this directory (an absolute path anchored to that file's own
location, not cwd). Importing `allostery` (directly, or transitively through
any `allostery.*` submodule) is what applies the patch.

**Do not reassign `prody.parsePDB`/`prody.fetchPDB` after importing `allostery`
unless your replacement wraps whatever `prody.parsePDB` currently is** (i.e.
`_orig = prody.parsePDB` immediately before defining your wrapper, at your own
module's import time) rather than a function object imported by name from
another module. Importing someone else's already-bound wrapper and assigning
it directly discards whatever composition came before it, because that
function's closure captured its own `_orig_parsePDB` reference before
`allostery`'s patch necessarily applied. This exact mistake (`prody.parsePDB =
_parsePDB_all_altloc`, imported by name from `task0255_hop_angstrom_calibration.py`)
scattered fetched structures into `__WORK_IN_PROGRESS__/` and the repo root in
`task0258_allosteric_distance_taxonomy.py` / `task0259_ctqw_devils_advocate_profile.py`
— fixed 2026-08-26 by importing the *module* for its side effect instead of
reassigning to its exported name. If you need an altloc (or similar) default on
top of the folder default, define your own local wrapper the way
`task0243_stage1_and_rerun.py` and its siblings do — capture `prody.parsePDB`
fresh at your own patch site, don't import someone else's closure.

## Not the same directory as `backend/`'s cache

The repo-root `pdb_cache/` (sibling of this file, one level up) is a
**separate, intentional** cache for the deployed QAS web app —
`backend/data_layer.py` / `backend/rcsb_extract.py`'s own
`os.environ.get("PDB_CACHE", "./pdb_cache")`, used when running
`uvicorn backend.main:app` from the repo root. It is unrelated to this
directory and unrelated to `allostery`; don't merge the two or assume a
structure fetched by one is available via the other's default resolution.
