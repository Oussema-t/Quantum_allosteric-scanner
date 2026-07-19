"""TASK-0135 coverage -- runlog.py's environment fingerprint + incremental
JSONL run logger."""
import json

import pytest

from allostery.runlog import RunLogger, environment_fingerprint


class TestEnvironmentFingerprint:
    def test_has_expected_top_level_keys(self):
        fp = environment_fingerprint()
        for key in ("hostname", "pid", "platform", "thread_env", "versions", "timestamp"):
            assert key in fp

    def test_thread_env_covers_the_known_blas_vars(self):
        fp = environment_fingerprint()
        for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            assert var in fp["thread_env"]

    def test_versions_include_numpy(self):
        fp = environment_fingerprint()
        assert fp["versions"]["numpy"] is not None

    def test_pid_matches_current_process(self):
        import os

        assert environment_fingerprint()["pid"] == os.getpid()


class TestRunLogger:
    def test_creates_parent_dir_and_writes_start_record(self, tmp_path):
        log_path = tmp_path / "sub" / "run.jsonl"
        RunLogger(log_path, run_name="unit_test")
        assert log_path.exists()
        lines = log_path.read_text().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["event"] == "run_start"
        assert record["run_name"] == "unit_test"
        assert "environment" in record

    def test_step_appends_a_line_with_wall_and_cpu_time(self, tmp_path):
        log_path = tmp_path / "run.jsonl"
        log = RunLogger(log_path, run_name="unit_test")
        log.step("trial_0", value=1.23)
        lines = log_path.read_text().splitlines()
        assert len(lines) == 2
        record = json.loads(lines[1])
        assert record["event"] == "step"
        assert record["label"] == "trial_0"
        assert record["value"] == 1.23
        assert "wall_elapsed_s" in record
        assert "cpu_elapsed_s" in record

    def test_finish_appends_a_final_record(self, tmp_path):
        log_path = tmp_path / "run.jsonl"
        log = RunLogger(log_path, run_name="unit_test")
        log.step("trial_0")
        log.finish(best=0.5)
        lines = log_path.read_text().splitlines()
        assert len(lines) == 3
        record = json.loads(lines[-1])
        assert record["event"] == "run_finish"
        assert record["best"] == 0.5

    def test_every_line_is_independently_valid_json(self, tmp_path):
        """Partial-run robustness (P-0005): a killed run must still leave
        a fully parseable trace up to the last flushed line."""
        log_path = tmp_path / "run.jsonl"
        log = RunLogger(log_path, run_name="unit_test")
        for i in range(5):
            log.step(f"trial_{i}", value=i)
        for line in log_path.read_text().splitlines():
            json.loads(line)  # must not raise

    def test_elapsed_time_is_monotonically_non_decreasing_across_steps(self, tmp_path):
        log_path = tmp_path / "run.jsonl"
        log = RunLogger(log_path, run_name="unit_test")
        log.step("a")
        log.step("b")
        lines = [json.loads(line) for line in log_path.read_text().splitlines()[1:]]
        assert lines[1]["wall_elapsed_s"] >= lines[0]["wall_elapsed_s"]
        assert lines[1]["cpu_elapsed_s"] >= lines[0]["cpu_elapsed_s"]
