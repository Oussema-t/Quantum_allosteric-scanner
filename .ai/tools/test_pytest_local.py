#!/usr/bin/env python3
"""Tests for pytest_local.py's interpreter resolution (TASK-0069).

The original bug (TASK-0069, found live 2026-07-12) was a *silent* wrong-
venv pick: once a repo-root `.venv/` existed, `wip-*` presets resolved to
it instead of `__WORK_IN_PROGRESS__/.venv/`, and still ran *something*
without erroring until a WIP-only dependency (matplotlib) was actually
imported. So these assert on the *resolved interpreter path*, per the
task's own Planned Validation #1 -- a "did pytest exit 0" check would not
have caught it.

`_resolve_interpreter` takes its two candidate venv-python paths as
arguments (defaulting to the real module constants), so resolution can be
exercised against fabricated layouts without touching this repo's own
`.venv/` -- a shared filesystem resource other live threads use
(TASK-0026.005's Done section flags renaming it as unsafe).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pytest_local as pl  # noqa: E402


def _make_fake_python(tmp_path: Path, name: str) -> Path:
    p = tmp_path / name / "bin" / "python3"
    p.parent.mkdir(parents=True)
    p.write_text("#!/bin/sh\n")
    return p


class TestResolveInterpreterPreferWip:
    """`prefer_wip=True` -- every preset except `backend`, plus --file mode."""

    def test_prefers_wip_venv_when_both_exist(self, tmp_path):
        wip = _make_fake_python(tmp_path, "wip_venv")
        root = _make_fake_python(tmp_path, "root_venv")
        assert pl._resolve_interpreter(True, wip_venv_python=wip, repo_venv_python=root) == str(wip)

    def test_falls_back_to_root_venv_when_no_wip_venv(self, tmp_path):
        wip = tmp_path / "wip_venv" / "bin" / "python3"  # not created
        root = _make_fake_python(tmp_path, "root_venv")
        assert pl._resolve_interpreter(True, wip_venv_python=wip, repo_venv_python=root) == str(root)

    def test_falls_back_to_sys_executable_when_no_venv_at_all(self, tmp_path):
        wip = tmp_path / "wip_venv" / "bin" / "python3"
        root = tmp_path / "root_venv" / "bin" / "python3"
        assert pl._resolve_interpreter(True, wip_venv_python=wip, repo_venv_python=root) == sys.executable


class TestResolveInterpreterBackend:
    """`prefer_wip=False` -- the `backend` preset only."""

    def test_backend_ignores_the_wip_venv_even_when_present(self, tmp_path):
        wip = _make_fake_python(tmp_path, "wip_venv")
        root = _make_fake_python(tmp_path, "root_venv")
        assert pl._resolve_interpreter(False, wip_venv_python=wip, repo_venv_python=root) == str(root)

    def test_backend_falls_back_to_sys_executable_when_no_root_venv(self, tmp_path):
        wip = _make_fake_python(tmp_path, "wip_venv")  # exists, must be ignored
        root = tmp_path / "root_venv" / "bin" / "python3"  # not created
        assert pl._resolve_interpreter(False, wip_venv_python=wip, repo_venv_python=root) == sys.executable


class TestPreferWipDerivation:
    """`prefer_wip` is derived from each preset's `extra_pythonpath`
    (WIP_SRC for every WIP-oriented preset and --file mode, None for
    `backend`) -- so the same signal drives PYTHONPATH and venv choice
    with no third PRESETS field. Guards that mapping against a future
    preset being added without the flag being reconsidered."""

    def test_only_backend_has_a_none_pythonpath(self):
        wip_oriented = {name for name, (_, epp) in pl.PRESETS.items() if epp is not None}
        backend_like = {name for name, (_, epp) in pl.PRESETS.items() if epp is None}
        assert backend_like == {"backend"}
        assert "wip-all" in wip_oriented and "all" in wip_oriented and "cross-tree" in wip_oriented

    def test_file_mode_is_wip_oriented(self):
        # run_file passes WIP_SRC -> prefer_wip=True; assert the constant
        # it uses is truthy so the derivation `extra_pythonpath is not
        # None` holds.
        assert pl.WIP_SRC


class TestPlannedValidationResolvedPathAssertions:
    """Planned Validation #1/#2 shape, run against the *real* current repo
    layout (one root `.venv/`, no `__WORK_IN_PROGRESS__/.venv/`): today's
    behavior must be unchanged -- every preset resolves to the root venv,
    exactly as before this task. (#1's WIP-venv-present case is covered by
    the fabricated-layout tests above, since creating a second real venv
    in this repo is out of scope and slow.)"""

    def test_current_repo_all_presets_resolve_to_the_one_existing_venv(self):
        if not pl.REPO_VENV_PYTHON.exists():
            # CI with no venv -- resolution is sys.executable for all, still uniform
            expected = sys.executable
        elif pl.WIP_VENV_PYTHON.exists():
            import pytest
            pytest.skip("a __WORK_IN_PROGRESS__/.venv now exists -- this uniform-resolution "
                        "assertion no longer applies; the fabricated-layout tests cover the split")
        else:
            expected = str(pl.REPO_VENV_PYTHON)
        assert pl._resolve_interpreter(True) == expected
        assert pl._resolve_interpreter(False) == expected


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
