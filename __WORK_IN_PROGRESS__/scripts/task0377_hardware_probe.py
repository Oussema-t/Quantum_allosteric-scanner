"""TASK-0377 -- hardware probe: like-for-like capacity measurement, not a
ΔΔG calculation of any kind (explicitly out of scope, see the task file's
"UNBLOCKED" section).

Must run unmodified on any machine, including one with every MD engine
absent -- this script is stdlib-only, on purpose: the box being probed may
have nothing installed beyond a bare Python 3. Every step degrades to a
recorded "absent"/"skipped" result rather than raising, per the task's own
Constraint ("must degrade, never fail").

Run: ../.venv/bin/python3 -u scripts/task0377_hardware_probe.py
(or plain python3 -- no venv packages are required by this script itself)
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("results/tasks/0377_hardware_probe")

ENGINES = ["openmm", "gmx", "pmemd.cuda", "sander"]

# Reference costs from TASK-0377's own Staging table, reproduced here so the
# derived wall-time arithmetic is traceable to one place.
TIER1_GPU_DAYS_REFERENCE = 10.0
TIER2_GPU_HOURS_REFERENCE = 2000.0


def _run(cmd, timeout=10):
    """Best-effort subprocess run. Returns (ok, stdout_stripped) -- never
    raises; a failure is a legitimate probe result, not a script bug."""
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode == 0, p.stdout.strip()
    except Exception as e:  # noqa: BLE001 -- degrade, never fail, by design
        return False, f"<probe error: {type(e).__name__}: {e}>"


def _sysctl(key):
    ok, out = _run(["sysctl", "-n", key])
    return out if ok else None


def cpu_info():
    system = platform.system()
    info = {
        "python_reported_machine": platform.machine(),
        "physical_cores": None,
        "logical_cores": os.cpu_count(),
        "model": None,
        "running_under_translation": None,
        "running_under_translation_caveat": None,
    }
    if system == "Darwin":
        info["model"] = _sysctl("machdep.cpu.brand_string")
        phys = _sysctl("hw.physicalcpu")
        info["physical_cores"] = int(phys) if phys and phys.isdigit() else None
        # Rosetta translation check -- TASK-0375's own arch-breakage concern.
        # Found live while running this probe: `sysctl -n sysctl.proc_
        # translated` invoked via this script's own subprocess.run returns
        # "1" consistently, but the identical command typed directly in an
        # interactive shell on the same machine returns "0", and
        # `platform.machine()` (which Rosetta-translated processes report as
        # x86_64, not arm64) shows "arm64" throughout. That is inconsistent
        # with genuine Rosetta translation of the Python process itself --
        # most likely an artifact of how THIS specific coding-agent sandbox
        # spawns subprocesses, not a fact about the underlying machine a
        # human would see running commands directly. Recorded as a caveat
        # rather than silently trusted either way; re-verify by hand outside
        # any agent sandbox before treating this value as ground truth.
        translated = _sysctl("sysctl.proc_translated")
        info["running_under_translation"] = (
            translated == "1" if translated in ("0", "1") else None
        )
        info["running_under_translation_caveat"] = (
            "Value came from a python3 subprocess.run() call. In this "
            "session, the same sysctl typed directly in an interactive "
            "shell returned '0' (native) while this script's subprocess "
            "call returns '1' (translated) -- and platform.machine() == "
            "'arm64' throughout, which genuine Rosetta translation would "
            "not show. Treat the raw value below as sandbox-context-"
            "dependent, not settled."
        )
    elif system == "Linux":
        try:
            text = Path("/proc/cpuinfo").read_text()
            for line in text.splitlines():
                if line.lower().startswith("model name"):
                    info["model"] = line.split(":", 1)[1].strip()
                    break
            info["physical_cores"] = len(
                {
                    line.split(":", 1)[1].strip()
                    for line in text.splitlines()
                    if line.lower().startswith("physical id")
                }
            ) or None
        except Exception as e:  # noqa: BLE001
            info["model"] = f"<probe error: {type(e).__name__}: {e}>"
    else:
        info["model"] = f"<unhandled platform.system()={system!r}>"
    return info


def ram_info():
    system = platform.system()
    if system == "Darwin":
        mem = _sysctl("hw.memsize")
        return {"total_gb": round(int(mem) / 1e9, 2) if mem else None}
    if system == "Linux":
        try:
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return {"total_gb": round(kb / 1e6, 2)}
        except Exception as e:  # noqa: BLE001
            return {"total_gb": None, "error": str(e)}
    return {"total_gb": None, "note": f"unhandled platform {system!r}"}


def gpu_info():
    system = platform.system()
    # NVIDIA path first -- works on Linux and Windows, and is what Tier 1/2
    # actually need (pmemd.cuda / GROMACS-CUDA both require it).
    if shutil.which("nvidia-smi"):
        ok, out = _run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ]
        )
        if ok and out:
            gpus = [line.strip() for line in out.splitlines() if line.strip()]
            cuda_ok, cuda_out = _run(["nvcc", "--version"])
            return {
                "vendor": "nvidia",
                "cuda_capable": True,
                "devices": gpus,
                "cuda_version": cuda_out if cuda_ok else "nvcc not found (driver may still support CUDA runtime)",
            }
    if system == "Darwin":
        ok, out = _run(["system_profiler", "SPDisplaysDataType"])
        chipset = None
        if ok:
            for line in out.splitlines():
                if "Chipset Model" in line:
                    chipset = line.split(":", 1)[1].strip()
                    break
        return {
            "vendor": "apple" if chipset and "Apple" in chipset else "unknown",
            "cuda_capable": False,
            "devices": [chipset] if chipset else [],
            "note": (
                "Apple Silicon integrated GPU: no CUDA, ever -- pmemd.cuda "
                "and GROMACS-CUDA cannot use this GPU regardless of what is "
                "installed. Only an OpenMM Metal/OpenCL backend could "
                "target it, at materially lower throughput than a discrete "
                "NVIDIA card."
                if chipset and "Apple" in chipset
                else "GPU vendor not identified by this probe."
            ),
        }
    return {"vendor": "unknown", "cuda_capable": False, "devices": [], "note": "no NVIDIA GPU found and not on Darwin -- probe has no further detection path"}


def engine_versions():
    results = {}
    # openmm: python import, not a CLI.
    try:
        import openmm  # type: ignore

        results["openmm"] = {"present": True, "version": openmm.version.version}
    except Exception as e:  # noqa: BLE001
        results["openmm"] = {"present": False, "reason": f"{type(e).__name__}: {e}"}

    for exe in ("gmx", "pmemd.cuda", "sander"):
        path = shutil.which(exe)
        if not path:
            results[exe] = {"present": False, "reason": "not found on PATH"}
            continue
        ok, out = _run([exe, "--version"])
        if not ok:
            ok, out = _run([exe, "-version"])
        results[exe] = {"present": True, "path": path, "version": out[:300] if ok else "<found on PATH, --version failed>"}
    return results


def run_benchmark(engines):
    """Tier-1/Tier-2 wall-time estimation needs a real ns/day figure from a
    real engine run. None is present on this pass (see `engines`) -- report
    the skip explicitly rather than fabricate a number. A future machine
    with an engine installed should extend this function, not replace it,
    so the JSON schema stays comparable across probes."""
    any_present = any(v.get("present") for v in engines.values())
    if not any_present:
        return {
            "ran": False,
            "reason": "no MD engine present on this machine -- nothing to benchmark",
            "ns_per_day": None,
        }
    return {
        "ran": False,
        "reason": "an engine is present but this probe does not yet implement running it -- extend run_benchmark(), do not fabricate ns/day",
        "ns_per_day": None,
    }


def derive_wall_times(benchmark):
    ns_per_day = benchmark.get("ns_per_day")
    if ns_per_day is None:
        return {
            "tier1_estimated_wall_days": None,
            "tier2_estimated_wall_hours": None,
            "note": "no ns/day measured on this machine -- cannot derive a wall-time estimate here",
        }
    # Reference costs are themselves given in GPU-days/GPU-hours on
    # whatever hardware produced TASK-0377's own estimate -- this arithmetic
    # is a placeholder scaling once a real ns/day exists on both machines,
    # not a claim this script can resolve alone (needs the *reference*
    # hardware's own ns/day too, which is not yet on record anywhere).
    return {
        "tier1_estimated_wall_days": None,
        "tier2_estimated_wall_hours": None,
        "note": "ns/day was measured, but TASK-0377's ~10 GPU-day / ~2000 GPU-h reference costs are not pinned to a stated reference ns/day -- scaling requires that number too, which this probe cannot supply on its own",
    }


def main():
    started = datetime.now(timezone.utc).isoformat()
    cpu = cpu_info()
    ram = ram_info()
    gpu = gpu_info()
    engines = engine_versions()
    benchmark = run_benchmark(engines)
    wall_times = derive_wall_times(benchmark)

    record = {
        "task": "TASK-0377",
        "probe_started_utc": started,
        "hostname": socket.gethostname(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "arch": platform.machine(),
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "cpu": cpu,
        "ram": ram,
        "gpu": gpu,
        "engines": engines,
        "benchmark": benchmark,
        "derived_wall_times": wall_times,
        "reference_costs_from_task_0377": {
            "tier1_gpu_days": TIER1_GPU_DAYS_REFERENCE,
            "tier2_gpu_hours": TIER2_GPU_HOURS_REFERENCE,
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    safe_host = record["hostname"].replace(".", "_").replace(" ", "_")
    out_path = OUT / f"{safe_host}_{record['arch']}.json"
    out_path.write_text(json.dumps(record, indent=2))

    print(f"=== TASK-0377 hardware probe: {record['hostname']} ({record['arch']}) ===")
    print(f"CPU: {cpu.get('model')} | physical={cpu.get('physical_cores')} logical={cpu.get('logical_cores')} | translated={cpu.get('running_under_translation')}")
    print(f"RAM: {ram.get('total_gb')} GB")
    print(f"GPU: vendor={gpu.get('vendor')} cuda_capable={gpu.get('cuda_capable')} devices={gpu.get('devices')}")
    if gpu.get("note"):
        print(f"  note: {gpu['note']}")
    for name, v in engines.items():
        status = "present" if v.get("present") else "ABSENT"
        extra = v.get("version") or v.get("reason")
        print(f"engine {name}: {status} ({extra})")
    print(f"benchmark: ran={benchmark['ran']} ({benchmark['reason']})")
    print(f"wall-time estimate: {wall_times['note']}")
    print(f"written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
