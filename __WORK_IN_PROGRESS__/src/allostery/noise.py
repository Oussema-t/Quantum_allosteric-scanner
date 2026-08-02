"""TASK-0068 -- NISQ noise-model simulation on `coarse.py`'s coarse-grained
graph. Trotterized circuit simulation under depolarizing + amplitude-
damping gate noise, reporting top-5 ranking degradation vs. circuit depth
and error rate, and whether dephasing-assisted transport (ENAQT) is more
noise-robust than the coherent walk -- `HOLO_DIRECTION_MODULE.md`'s named
scoreable NISQ result. Closes SEAM-0010.

Graph -> qubit encoding (new for this task, documented since it is a real
physics/design decision, not ported from anywhere else in this repo):
one qubit per coarse-grained node (`coarse.coarse_grain`'s own node
budget; this task's own Intent Contract: "one qubit per node, one
2-qubit gate per coupling edge"). The walk lives in the single-excitation
subspace (exactly one qubit in |1>, the rest |0>) -- the standard
XY-model realization of a single-particle continuous-time quantum walk.
For graph edge (i, j) with weight `w_ij`:

    exp(-i * w_ij * dt * (X_i X_j + Y_i Y_j) / 2)
      = RXX(w_ij * dt) . RYY(w_ij * dt)

exactly (not a per-edge approximation: `[X_i X_j, Y_i Y_j] = 0`), and
this operator, restricted to the single-excitation subspace, hops
amplitude between nodes i and j with exactly the tight-binding/CTQW
off-diagonal matrix element `H_ij` -- so the *noiseless* circuit built
here is a real gate-model reproduction of this repo's own
`propagators.ctqw` restricted to `H_coarse`, not an unrelated toy walk.
First-order Trotter composes these exact single-edge unitaries edge by
edge; the approximation enters only from non-commuting edges sharing a
qubit, consistent with `coarse.trotter_cost`'s own error-budget framing.

Multi-index seeds are not supported here (single representative seed
qubit only) -- an equal-superposition "W-state" prep over several seed
qubits in the single-excitation subspace is a real circuit-construction
problem of its own, out of this task's scope; same complexity-avoidance
precedent as `scripts/run_challenge.py`'s TASK-0090 workaround.

Noise: depolarizing error on every 2-qubit `rxx`/`ryy` gate (the actual
Trotter-step gates) plus amplitude damping on every qubit once per
Trotter layer (attached to an explicit per-layer identity gate --
qiskit-aer's own idiom for idle-qubit decoherence, since amplitude
damping has no natural "per 2-qubit gate" home). ENAQT is realized as an
*additional* per-layer phase-damping channel on every qubit -- the same
physical picture `propagators.haken_strobl`'s Lindblad dephasing term
already uses, now as an explicit gate-model channel so it can be measured
under the *same* depolarizing/amplitude-damping gate noise as the
coherent case.
"""
from __future__ import annotations

import numpy as np


def build_xy_walk_circuit(
    H_coarse: np.ndarray,
    t: float,
    trotter_steps: int,
    source: int,
    dephasing_gamma: float = 0.0,
):
    """First-order Trotterized XY-model circuit realizing a single-particle
    CTQW on `H_coarse`, seeded at qubit `source`.

    `dephasing_gamma > 0` inserts an additional per-layer phase-damping
    channel on every qubit (the ENAQT comparison circuit) -- folded into
    the *noise model* the caller attaches at simulation time, not into
    this circuit's own gates (phase damping is not a unitary gate); this
    function only marks where the per-layer boundary is via explicit
    identity gates, same as the amplitude-damping attachment point.

    Returns a plain `qiskit.QuantumCircuit` (no `save_density_matrix`
    instruction yet -- that instruction only exists once `qiskit_aer` has
    been imported, since it monkey-patches `QuantumCircuit`; added by
    `simulate_occupation` instead, which owns that import).
    """
    from qiskit import QuantumCircuit

    n = H_coarse.shape[0]
    ii, jj = np.nonzero(np.triu(H_coarse, k=1))
    edges = list(zip(ii.tolist(), jj.tolist(), H_coarse[ii, jj].tolist()))
    dt = t / trotter_steps

    qc = QuantumCircuit(n)
    qc.x(int(source))
    for _ in range(trotter_steps):
        for i, j, w in edges:
            if w == 0.0:
                continue
            qc.rxx(w * dt, i, j)
            qc.ryy(w * dt, i, j)
        # per-layer boundary: identity gates are the attachment point for
        # amplitude damping / phase damping in the noise model, not the
        # circuit itself (those are non-unitary channels).
        for q in range(n):
            qc.id(q)
    return qc


def build_noise_model(depolarizing_prob: float, amp_damping_prob: float, dephasing_prob: float = 0.0):
    """Depolarizing error on every `rxx`/`ryy` gate, amplitude damping
    (+ optional phase damping, the ENAQT channel) on every per-layer `id`
    gate. `dephasing_prob=0.0` recovers the coherent-walk-under-gate-noise
    case (this task's own primary comparator)."""
    from qiskit_aer.noise import NoiseModel, amplitude_damping_error, depolarizing_error, phase_damping_error

    nm = NoiseModel()
    if depolarizing_prob > 0:
        nm.add_all_qubit_quantum_error(depolarizing_error(depolarizing_prob, 2), ["rxx", "ryy"])
    idle_error = amplitude_damping_error(amp_damping_prob)
    if dephasing_prob > 0:
        idle_error = idle_error.compose(phase_damping_error(dephasing_prob))
    if amp_damping_prob > 0 or dephasing_prob > 0:
        nm.add_all_qubit_quantum_error(idle_error, ["id"])
    return nm


def simulate_occupation(circuit, noise_model=None) -> np.ndarray:
    """Run `circuit` (from `build_xy_walk_circuit`) and return each
    qubit's marginal P(|1>) -- the circuit-model analogue of
    `propagators.ctqw`'s occupation vector. Sums to ~1 under noiseless
    evolution (single-excitation subspace is conserved by the XY
    Hamiltonian); noise can leak probability out of that subspace, so a
    noisy result's sum is itself a diagnostic, not assumed to be 1."""
    from qiskit_aer import AerSimulator

    circuit = circuit.copy()
    circuit.save_density_matrix()
    sim = AerSimulator(method="density_matrix", noise_model=noise_model)
    result = sim.run(circuit).result()
    dm = result.data(0)["density_matrix"]
    n = circuit.num_qubits
    return np.array([dm.probabilities([q])[1] for q in range(n)])


def top_k_overlap(occ_a: np.ndarray, occ_b: np.ndarray, k: int) -> float:
    """Jaccard overlap of the top-k occupied nodes between two occupation
    vectors -- the ranking-degradation metric this task's own Intent
    Contract asks for ("top-5 ranking degradation"), not a raw numeric
    distance between the vectors."""
    k = min(k, len(occ_a))
    top_a = set(np.argsort(-occ_a)[:k].tolist())
    top_b = set(np.argsort(-occ_b)[:k].tolist())
    union = top_a | top_b
    return len(top_a & top_b) / len(union) if union else 1.0


def time_sampled_converged_occupation(
    H_coarse: np.ndarray,
    source: int,
    t_values,
    trotter_steps: int,
    dephasing_gamma: float = 0.0,
    noise_model=None,
) -> np.ndarray:
    """TASK-0182 -- circuit-realized approximation of `propagators.
    time_averaged_ctqw_converged`'s exact t->infinity closed form.

    A fixed-depth Trotter circuit only ever produces a snapshot at one
    `t`; there is no "infinite-time" circuit. This is the only way a
    circuit can approach a *time-averaged* observable: run the circuit at
    each `t` in `t_values` and average the resulting occupation vectors --
    the direct circuit-model analogue of `time_averaged_ctqw`'s own
    `np.linspace(0, t_max, n_steps)` Riemann-sum convention (same
    averaging idea, evaluated by simulation instead of the closed-form
    eigendecomposition). Caller picks `t_values`, typically
    `np.linspace(0, t_max, n_samples)` with `t_max` from
    `propagators.min_adequate_t_max(H_coarse, kind="time_averaged_ctqw")`
    -- not re-derived here, reused as-is.

    `trotter_steps` is held **fixed across every sampled `t`** (not scaled
    per-`t` the way `coarse.trotter_cost`'s high-accuracy prescription
    would), deliberately: TASK-0068 already found scaling step count with
    the high-accuracy error budget produces circuits that do not finish in
    NISQ-relevant time (3133 steps for a 10-qubit graph, a ~188,000-gate
    circuit killed after 69 CPU-minutes). A fixed, small `trotter_steps`
    keeps every sample at the same NISQ-plausible depth; the resulting
    approximation error (this function does not converge to the exact
    answer at fixed depth as `len(t_values) -> inf`, only as `trotter_steps
    -> inf` too) is exactly what this task's own noise-free-limit
    convergence check (Planned Validation, run before any noisy result is
    trusted) is for -- report the residual against
    `time_averaged_ctqw_converged`, do not assume it is negligible.
    """
    occs = [
        simulate_occupation(
            build_xy_walk_circuit(H_coarse, float(t), trotter_steps, source, dephasing_gamma),
            noise_model=noise_model,
        )
        for t in t_values
    ]
    return np.mean(occs, axis=0)


def run_noise_sweep(
    H_coarse: np.ndarray,
    source: int,
    t: float,
    trotter_steps_grid,
    error_rates,
    k: int = 5,
    dephasing_gamma: float = 0.0,
) -> list:
    """Sweep circuit depth (via `trotter_steps_grid`, driven by the
    caller's own `coarse.trotter_cost`-informed choice, not re-derived
    here) and gate error rate, reporting top-k ranking degradation
    (`top_k_overlap` against the noiseless, same-depth circuit) at each
    point. `dephasing_gamma` is fixed across the sweep -- comparing
    `dephasing_gamma=0.0` vs. `>0.0` sweeps (two separate calls) is how
    this task's own headline ENAQT-vs-coherent-noise-robustness question
    gets answered, not a parameter swept jointly with error rate.

    Returns a list of row-dicts: `trotter_steps`, `error_rate`,
    `occ_noiseless`, `occ_noisy`, `top_k_overlap`, `noisy_occ_sum`
    (subspace-leakage diagnostic).
    """
    rows = []
    for steps in trotter_steps_grid:
        qc = build_xy_walk_circuit(H_coarse, t, int(steps), source, dephasing_gamma)
        occ_noiseless = simulate_occupation(qc, noise_model=None)
        for err in error_rates:
            noise_model = build_noise_model(
                depolarizing_prob=err, amp_damping_prob=err, dephasing_prob=dephasing_gamma
            )
            occ_noisy = simulate_occupation(qc, noise_model=noise_model)
            rows.append({
                "trotter_steps": int(steps),
                "error_rate": float(err),
                "dephasing_gamma": float(dephasing_gamma),
                "occ_noiseless": occ_noiseless.tolist(),
                "occ_noisy": occ_noisy.tolist(),
                "top_k_overlap": top_k_overlap(occ_noiseless, occ_noisy, k),
                "noisy_occ_sum": float(occ_noisy.sum()),
            })
    return rows
