"""ASTRA sector-complete instrument methods and synthetic benchmark utilities.

This module implements a deliberately small, auditable finite-dimensional model.
It is a methods calibration, not a model of a real duality defect, hidden matter,
or dark matter.

Core measurement equations
--------------------------
Unconditioned quantum channel (CPTP):

    p(d | rho, Gamma, u) = Tr[M_d E_{Gamma,u}(rho)]

Selected branch / quantum instrument:

    p(d | rho) = Tr[E_d(rho)]
    rho_d = E_d(rho) / p(d | rho)

The trace of a commutator is not used as an observation equation because
Tr([A, B]) = 0 under ordinary finite-dimensional conditions.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]

BASIS: tuple[str, ...] = (
    "vacuum_d0",
    "left_local_d0",
    "right_local_d0",
    "string_d0",
    "environment_d0",
    "vacuum_d1",
    "left_local_d1",
    "right_local_d1",
    "string_d1",
    "environment_d1",
)
BASIS_INDEX: dict[str, int] = {name: idx for idx, name in enumerate(BASIS)}
DIM = len(BASIS)
INPUT_BASIS = "left_local_d0"
GENERATOR_ORDER: tuple[str, ...] = (
    "reflect",
    "absorb",
    "local_transmit",
    "string_transmit",
)
GENERATOR_OUTPUT: dict[str, str] = {
    "reflect": "left_local_d0",
    "absorb": "environment_d0",
    "local_transmit": "right_local_d0",
    "string_transmit": "string_d1",
}


@dataclass(frozen=True, slots=True)
class SectorRecord:
    """Typed record for a plausible information-bearing sector."""

    sector_id: str
    carrier: str
    support_basis: tuple[str, ...]
    detector_or_bound: str
    calibration: str
    units: str
    unresolved_bound: str


@dataclass(frozen=True, slots=True)
class TransductionRecord:
    """Minimal ASTRA typed transduction schema."""

    model_id: str
    input_carrier: str
    input_sector: str
    output_carriers: tuple[str, ...]
    output_sectors: tuple[str, ...]
    selection_conditioning: str
    interface_state: str
    active_control_route: str
    observable_basis: tuple[str, ...]
    calibration_and_units: str
    conservation_exchange_ledger: dict[str, object]
    unresolved_sector_bounds: tuple[str, ...]
    model_mediated_inversion: str
    identifiability: dict[str, object]
    rejection_test: str
    interpretation_status: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for field_name in (
            "output_carriers",
            "output_sectors",
            "observable_basis",
            "unresolved_sector_bounds",
        ):
            payload[field_name] = list(payload[field_name])
        return payload


def basis_vector(name: str) -> ComplexArray:
    """Return a named computational-basis ket."""
    if name not in BASIS_INDEX:
        raise KeyError(f"Unknown basis state: {name}")
    ket = np.zeros(DIM, dtype=np.complex128)
    ket[BASIS_INDEX[name]] = 1.0
    return ket


def density_from_basis(name: str) -> ComplexArray:
    ket = basis_vector(name)
    return np.asarray(np.outer(ket, ket.conj()), dtype=np.complex128)


def projector(names: Iterable[str]) -> ComplexArray:
    out = np.zeros((DIM, DIM), dtype=np.complex128)
    for name in names:
        ket = basis_vector(name)
        out += np.outer(ket, ket.conj())
    return out


def swap_unitary(source: str, target: str) -> ComplexArray:
    """Return a permutation unitary swapping two named basis states."""
    u = np.eye(DIM, dtype=np.complex128)
    i = BASIS_INDEX[source]
    j = BASIS_INDEX[target]
    if i != j:
        u[[i, j], :] = u[[j, i], :]
    return u


def generator_unitary(name: str) -> ComplexArray:
    """Global unitary for one synthetic generator on the enlarged state space."""
    if name not in GENERATOR_OUTPUT:
        raise KeyError(f"Unknown generator: {name}")
    return swap_unitary(INPUT_BASIS, GENERATOR_OUTPUT[name])


def apply_unitary(rho: ArrayLike, unitary: ArrayLike) -> ComplexArray:
    r = np.asarray(rho, dtype=np.complex128)
    u = np.asarray(unitary, dtype=np.complex128)
    if r.shape != (DIM, DIM) or u.shape != (DIM, DIM):
        raise ValueError(f"rho and unitary must both be {DIM}x{DIM} matrices")
    return u @ r @ u.conj().T


def apply_random_unitary_channel(
    rho: ArrayLike,
    weighted_unitaries: Sequence[tuple[float, ArrayLike]],
) -> ComplexArray:
    """Apply a random-unitary CPTP channel with declared non-negative weights."""
    r = np.asarray(rho, dtype=np.complex128)
    weights = np.array([float(weight) for weight, _ in weighted_unitaries], dtype=float)
    if np.any(weights < 0) or not np.isclose(weights.sum(), 1.0, atol=1e-12):
        raise ValueError("Channel weights must be non-negative and sum to one")
    out = np.zeros_like(r)
    for weight, unitary in weighted_unitaries:
        out += weight * apply_unitary(r, unitary)
    return out


def output_state(name: str) -> ComplexArray:
    """Return the ideal output state for a named generator."""
    return apply_unitary(density_from_basis(INPUT_BASIS), generator_unitary(name))


def broken_duality_state(delta_reflect: float) -> ComplexArray:
    """String-transmission control with a reflected admixture.

    delta_reflect=0 gives ideal string transmission; delta_reflect=1 gives reflection.
    """
    if not 0.0 <= delta_reflect <= 1.0:
        raise ValueError("delta_reflect must lie in [0, 1]")
    return apply_random_unitary_channel(
        density_from_basis(INPUT_BASIS),
        (
            (1.0 - delta_reflect, generator_unitary("string_transmit")),
            (delta_reflect, generator_unitary("reflect")),
        ),
    )


def finite_boundary_state(length_over_xi: float) -> ComplexArray:
    """Finite-boundary control.

    The declared toy closure assumes string-sector survival

        s(L) = 1 - exp(-L/xi),

    while the unresolved remainder is deposited in the environment sector. This is a
    benchmark control only; it is not a physical law for duality defects.
    """
    if length_over_xi < 0:
        raise ValueError("length_over_xi must be non-negative")
    survival = 1.0 - float(np.exp(-length_over_xi))
    return apply_random_unitary_channel(
        density_from_basis(INPUT_BASIS),
        (
            (survival, generator_unitary("string_transmit")),
            (1.0 - survival, generator_unitary("absorb")),
        ),
    )


def local_povm() -> dict[str, ComplexArray]:
    left = projector(("left_local_d0", "left_local_d1"))
    right = projector(("right_local_d0", "right_local_d1"))
    null = np.eye(DIM, dtype=np.complex128) - left - right
    return {"left_local": left, "right_local": right, "no_local_signal": null}


def sector_complete_povm() -> dict[str, ComplexArray]:
    left = projector(("left_local_d0", "left_local_d1"))
    right = projector(("right_local_d0", "right_local_d1"))
    string = projector(("string_d0", "string_d1"))
    environment = projector(("environment_d0", "environment_d1"))
    other = np.eye(DIM, dtype=np.complex128) - left - right - string - environment
    return {
        "left_local": left,
        "right_local": right,
        "string_sector": string,
        "environment_sector": environment,
        "other": other,
    }


def defect_observable() -> ComplexArray:
    return projector(("vacuum_d1", "left_local_d1", "right_local_d1", "string_d1", "environment_d1"))


def global_excitation_observable() -> ComplexArray:
    return projector(
        (
            "left_local_d0",
            "right_local_d0",
            "string_d0",
            "environment_d0",
            "left_local_d1",
            "right_local_d1",
            "string_d1",
            "environment_d1",
        )
    )


def validate_density_matrix(rho: ArrayLike, *, atol: float = 1e-10) -> None:
    r = np.asarray(rho, dtype=np.complex128)
    if r.shape != (DIM, DIM):
        raise ValueError(f"Density matrix must be {DIM}x{DIM}")
    if not np.allclose(r, r.conj().T, atol=atol):
        raise ValueError("Density matrix is not Hermitian")
    if not np.isclose(np.trace(r), 1.0, atol=atol):
        raise ValueError("Density matrix must have trace one")
    if np.min(np.linalg.eigvalsh(r)) < -atol:
        raise ValueError("Density matrix is not positive semidefinite")


def validate_povm(povm: Mapping[str, ArrayLike], *, atol: float = 1e-10) -> None:
    total = np.zeros((DIM, DIM), dtype=np.complex128)
    for name, element in povm.items():
        e = np.asarray(element, dtype=np.complex128)
        if e.shape != (DIM, DIM):
            raise ValueError(f"POVM element {name} has wrong shape")
        if not np.allclose(e, e.conj().T, atol=atol):
            raise ValueError(f"POVM element {name} is not Hermitian")
        if np.min(np.linalg.eigvalsh(e)) < -atol:
            raise ValueError(f"POVM element {name} is not positive semidefinite")
        total += e
    if not np.allclose(total, np.eye(DIM), atol=atol):
        raise ValueError("POVM elements do not sum to identity")


def measurement_probabilities(
    rho: ArrayLike,
    povm: Mapping[str, ArrayLike],
) -> tuple[tuple[str, ...], FloatArray]:
    """Evaluate p(d|rho)=Tr[M_d rho]."""
    validate_density_matrix(rho)
    validate_povm(povm)
    r = np.asarray(rho, dtype=np.complex128)
    labels = tuple(povm.keys())
    values = np.array(
        [float(np.real_if_close(np.trace(np.asarray(povm[label]) @ r))) for label in labels],
        dtype=float,
    )
    values[np.abs(values) < 1e-14] = 0.0
    if np.any(values < -1e-10):
        raise ValueError("Measurement produced a negative probability")
    values = np.clip(values, 0.0, None)
    values /= values.sum()
    return labels, values


def response_matrix(
    povm: Mapping[str, ArrayLike],
    generators: Sequence[str] = GENERATOR_ORDER,
) -> tuple[tuple[str, ...], tuple[str, ...], FloatArray]:
    labels = tuple(povm.keys())
    matrix = np.column_stack([measurement_probabilities(output_state(g), povm)[1] for g in generators])
    return labels, tuple(generators), matrix


def symmetric_confusion_matrix(n_outcomes: int, error_rate: float) -> FloatArray:
    """Column-stochastic detector confusion matrix.

    Column j gives the observed-outcome distribution conditional on ideal outcome j.
    """
    if n_outcomes < 2:
        raise ValueError("Need at least two outcomes")
    if not 0.0 <= error_rate < 1.0:
        raise ValueError("error_rate must lie in [0, 1)")
    off = error_rate / (n_outcomes - 1)
    matrix = np.full((n_outcomes, n_outcomes), off, dtype=float)
    np.fill_diagonal(matrix, 1.0 - error_rate)
    return matrix


def apply_detector_confusion(response: ArrayLike, confusion: ArrayLike) -> FloatArray:
    m = np.asarray(response, dtype=float)
    c = np.asarray(confusion, dtype=float)
    if c.shape[1] != m.shape[0]:
        raise ValueError("Confusion matrix and response dimensions do not match")
    if np.any(c < 0) or not np.allclose(c.sum(axis=0), 1.0, atol=1e-12):
        raise ValueError("Confusion matrix must be non-negative and column-stochastic")
    out = c @ m
    return np.asarray(out / out.sum(axis=0, keepdims=True), dtype=np.float64)


def exact_equivalence_classes(response: ArrayLike, labels: Sequence[str], atol: float = 1e-12) -> list[list[str]]:
    m = np.asarray(response, dtype=float)
    if m.ndim != 2 or m.shape[1] != len(labels):
        raise ValueError("Response columns must correspond to labels")
    unused = set(range(m.shape[1]))
    classes: list[list[str]] = []
    while unused:
        i = min(unused)
        cls = [j for j in sorted(unused) if np.allclose(m[:, i], m[:, j], atol=atol, rtol=0.0)]
        for j in cls:
            unused.remove(j)
        classes.append([str(labels[j]) for j in cls])
    return classes


def pairwise_total_variation(response: ArrayLike) -> FloatArray:
    m = np.asarray(response, dtype=float)
    n = m.shape[1]
    out = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            out[i, j] = 0.5 * np.sum(np.abs(m[:, i] - m[:, j]))
    return out


def mutual_information_uniform(response: ArrayLike) -> float:
    """I(K;D) in bits for a uniform prior over response columns."""
    m = np.asarray(response, dtype=float)
    if np.any(m < 0) or not np.allclose(m.sum(axis=0), 1.0, atol=1e-10):
        raise ValueError("Response columns must be probability vectors")
    prior = np.full(m.shape[1], 1.0 / m.shape[1])
    marginal = m @ prior
    info = 0.0
    for k, pk in enumerate(prior):
        for d in range(m.shape[0]):
            q = m[d, k]
            if q > 0 and marginal[d] > 0:
                info += pk * q * np.log2(q / marginal[d])
    return float(info)


def mixture_fisher_information(response: ArrayLike, samples: int = 1000) -> FloatArray:
    """Multinomial Fisher information for four mixture weights at the uniform interior.

    The first three weights are free and the fourth is 1 minus their sum. A null
    eigenvalue therefore signals non-identification beyond the simplex constraint.
    """
    m = np.asarray(response, dtype=float)
    if m.shape[1] != 4:
        raise ValueError("This benchmark defines four generator weights")
    if samples <= 0:
        raise ValueError("samples must be positive")
    pi = np.full(4, 0.25, dtype=float)
    p = m @ pi
    if np.any(p <= 0):
        raise ValueError("Fisher information requires positive outcome probabilities")
    jac = m[:, :3] - m[:, [3]]
    return np.asarray(float(samples) * jac.T @ np.diag(1.0 / p) @ jac, dtype=np.float64)


def matrix_rank_with_tolerance(matrix: ArrayLike, rtol: float = 1e-10) -> int:
    values = np.linalg.svd(np.asarray(matrix, dtype=float), compute_uv=False)
    threshold = rtol * values.max() if values.size else 0.0
    return int(np.sum(values > threshold))


def expectation(rho: ArrayLike, observable: ArrayLike) -> float:
    r = np.asarray(rho, dtype=np.complex128)
    o = np.asarray(observable, dtype=np.complex128)
    return float(np.real_if_close(np.trace(o @ r)))


def sample_counts(probabilities: ArrayLike, samples: int, rng: np.random.Generator) -> NDArray[np.int64]:
    p = np.asarray(probabilities, dtype=float)
    if samples <= 0:
        raise ValueError("samples must be positive")
    if np.any(p < 0) or not np.isclose(p.sum(), 1.0, atol=1e-10):
        raise ValueError("probabilities must be normalized")
    return rng.multinomial(samples, p)


def log_likelihood_multinomial(counts: ArrayLike, probabilities: ArrayLike) -> float:
    n = np.asarray(counts, dtype=float)
    p = np.asarray(probabilities, dtype=float)
    if n.shape != p.shape:
        raise ValueError("counts and probabilities must have matching shapes")
    if np.any(p <= 0):
        return float("-inf")
    return float(np.sum(n * np.log(p)))


def classify_pure_generator(counts: ArrayLike, response: ArrayLike, labels: Sequence[str]) -> tuple[str, FloatArray]:
    m = np.asarray(response, dtype=float)
    scores = np.array([log_likelihood_multinomial(counts, m[:, j]) for j in range(m.shape[1])])
    best = int(np.flatnonzero(scores == scores.max())[0])
    return str(labels[best]), scores


def multinomial_deviance(counts: ArrayLike, model_probabilities: ArrayLike) -> float:
    n = np.asarray(counts, dtype=float)
    q = np.asarray(model_probabilities, dtype=float)
    if n.shape != q.shape or np.any(q <= 0):
        raise ValueError("Invalid counts/model probabilities")
    total = n.sum()
    empirical = n / total
    mask = n > 0
    return float(2.0 * np.sum(n[mask] * np.log(empirical[mask] / q[mask])))


def trace_commutator(a: ArrayLike, b: ArrayLike) -> complex:
    """Return Tr([A,B]); included as a regression guard for the rejected equation."""
    x = np.asarray(a, dtype=np.complex128)
    y = np.asarray(b, dtype=np.complex128)
    return complex(np.trace(x @ y - y @ x))


def default_sector_records() -> tuple[SectorRecord, ...]:
    return (
        SectorRecord(
            sector_id="local_left",
            carrier="local excitation",
            support_basis=("left_local_d0", "left_local_d1"),
            detector_or_bound="left local projector",
            calibration="projector completeness and detector confusion matrix",
            units="probability or counts",
            unresolved_bound="none inside declared benchmark",
        ),
        SectorRecord(
            sector_id="local_right",
            carrier="local excitation",
            support_basis=("right_local_d0", "right_local_d1"),
            detector_or_bound="right local projector",
            calibration="projector completeness and detector confusion matrix",
            units="probability or counts",
            unresolved_bound="none inside declared benchmark",
        ),
        SectorRecord(
            sector_id="string",
            carrier="nonlocal/string-labelled excitation",
            support_basis=("string_d0", "string_d1"),
            detector_or_bound="string-sector projector",
            calibration="synthetic exact basis label; no real-device calibration implied",
            units="probability or counts",
            unresolved_bound="real string/Wilson observable implementation remains outside benchmark",
        ),
        SectorRecord(
            sector_id="environment",
            carrier="absorbed/environment excitation",
            support_basis=("environment_d0", "environment_d1"),
            detector_or_bound="environment-sector projector",
            calibration="synthetic exact basis label; no calorimetry model implied",
            units="probability or counts",
            unresolved_bound="energy units are not modeled",
        ),
        SectorRecord(
            sector_id="defect_state",
            carrier="interface state",
            support_basis=("vacuum_d1", "left_local_d1", "right_local_d1", "string_d1", "environment_d1"),
            detector_or_bound="defect occupation observable",
            calibration="synthetic binary interface state",
            units="expectation value",
            unresolved_bound="does not represent a real topological defect Hilbert space",
        ),
    )


def default_transduction_record() -> TransductionRecord:
    return TransductionRecord(
        model_id="ASTRA-SCI-SYN-001",
        input_carrier="one synthetic local excitation",
        input_sector="left_local_d0",
        output_carriers=("left local", "right local", "string-labelled", "environment-labelled"),
        output_sectors=("local_left", "local_right", "string", "environment", "defect_state"),
        selection_conditioning="no postselection in primary benchmark; random-unitary controls are CPTP",
        interface_state="binary d0/d1 defect label included in enlarged Hilbert space",
        active_control_route="generator identity and control parameters are frozen before simulation",
        observable_basis=("local POVM", "sector-complete POVM", "defect occupation"),
        calibration_and_units="probabilities and multinomial counts; detector confusion is explicit",
        conservation_exchange_ledger={
            "probability": "trace is one for every output state",
            "energy": "not modeled",
            "charge": "not modeled",
            "entropy": "not asserted conserved for reduced channels",
            "accessible_information": "measurement- and sector-dependent",
        },
        unresolved_sector_bounds=(
            "the finite synthetic basis is declared; sectors outside it are not bounded",
            "no real string/Wilson observable or physical environment calibration is included",
        ),
        model_mediated_inversion="pure-generator likelihood classification plus Fisher-rank and equivalence-class audit",
        identifiability={
            "equivalence_classes": {
                "local": {
                    "reflect": ["reflect"],
                    "absorb_string": ["absorb", "string_transmit"],
                    "local_transmit": ["local_transmit"],
                },
                "sector_complete": {
                    "reflect": ["reflect"],
                    "absorb": ["absorb"],
                    "local_transmit": ["local_transmit"],
                    "string_transmit": ["string_transmit"],
                },
            },
            "fisher_rank": {"local": 2, "sector_complete": 3},
            "null_directions": [
                "local protocol has one mixture-simplex null direction under the frozen response",
            ],
        },
        rejection_test="out-of-set hybrid must fail pure-model goodness-of-fit; unresolved equivalence must be reported",
        interpretation_status="synthetic_methods_only",
    )
