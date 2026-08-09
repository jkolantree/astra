"""Local prototype for the SPPT conservation-to-calibration bridge.

This module is deliberately namespaced under an unpromoted successor draft.
It implements only contract-level checks; it is not a planetary solver and does
not alter the SPPT v1.0.6 core API.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from statistics import NormalDist
from collections.abc import Mapping, Sequence
from typing import Literal

import numpy as np


def _finite_array(name: str, value: object, ndim: int) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != ndim:
        raise ValueError(f"{name} must have ndim={ndim}; got shape {array.shape}.")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values.")
    return array


def _finite_scalar(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite.")
    return number


def _finite_vector(name: str, value: object) -> np.ndarray:
    vector = _finite_array(name, value, 1)
    if vector.size == 0:
        raise ValueError(f"{name} must not be empty.")
    return vector


@dataclass(frozen=True, slots=True)
class ConservationReport:
    passed: bool
    structural_errors: tuple[str, ...]
    dynamic_residual: float | None
    weighted_residual: float | None


@dataclass(frozen=True, slots=True)
class ConservationContract:
    """Strict contract for a directed reservoir/species balance."""

    incidence: np.ndarray
    stoichiometry: np.ndarray
    conserved_weights: np.ndarray
    state_units: tuple[str, ...]
    residual_tolerance: float = 1e-10

    def _structure_errors(self) -> list[str]:
        errors: list[str] = []
        B = _finite_array("incidence", self.incidence, 2)
        N = _finite_array("stoichiometry", self.stoichiometry, 2)
        weights = _finite_array("conserved_weights", self.conserved_weights, 1)
        tolerance = _finite_scalar("residual_tolerance", self.residual_tolerance)
        if tolerance < 0.0:
            errors.append("residual_tolerance must be nonnegative")
        if B.shape[0] == 0:
            errors.append("incidence must contain at least one reservoir")
        if B.shape[1] == 0:
            errors.append("incidence must contain at least one internal edge")
        if N.shape[0] != weights.size:
            errors.append("stoichiometry species dimension must match conserved_weights")
        if len(self.state_units) != weights.size:
            errors.append("state_units length must match conserved_weights")
        if not all(isinstance(unit, str) and unit.strip() for unit in self.state_units):
            errors.append("state_units must contain nonempty strings")

        for edge, column in enumerate(B.T):
            minus = int(np.count_nonzero(column == -1.0))
            plus = int(np.count_nonzero(column == 1.0))
            nonzero = int(np.count_nonzero(column))
            if minus != 1 or plus != 1 or nonzero != 2:
                errors.append(
                    f"incidence edge {edge} must have exactly one -1 tail and one +1 head"
                )
        if B.size and not np.allclose(np.sum(B, axis=0), 0.0, atol=tolerance, rtol=0.0):
            errors.append("each incidence column must sum to zero")
        if N.size and not np.allclose(N.T @ weights, 0.0, atol=tolerance, rtol=0.0):
            errors.append("conserved_weights must lie in the stoichiometric nullspace")
        return errors

    def validate_structure(self) -> None:
        errors = self._structure_errors()
        if errors:
            raise ValueError("; ".join(errors))

    def audit(
        self,
        dMdt: object,
        edge_flux: object,
        reaction_rate: object,
        source: object,
        escape: object,
    ) -> ConservationReport:
        errors = self._structure_errors()
        if errors:
            return ConservationReport(False, tuple(errors), None, None)
        B = _finite_array("incidence", self.incidence, 2)
        N = _finite_array("stoichiometry", self.stoichiometry, 2)
        weights = _finite_array("conserved_weights", self.conserved_weights, 1)
        derivative = _finite_array("dMdt", dMdt, 2)
        flux = _finite_array("edge_flux", edge_flux, 2)
        reactions = _finite_array("reaction_rate", reaction_rate, 2)
        source_array = _finite_array("source", source, 2)
        escape_array = _finite_array("escape", escape, 2)
        expected = B @ flux + reactions @ N.T + source_array - escape_array
        if derivative.shape != expected.shape:
            return ConservationReport(
                False,
                (f"dMdt shape {derivative.shape} does not match expected {expected.shape}",),
                None,
                None,
            )
        dynamic_residual = float(np.max(np.abs(derivative - expected)))
        internal_weighted = float(np.sum((B @ flux) @ weights))
        reaction_weighted = float(np.sum((reactions @ N.T) @ weights))
        weighted_residual = internal_weighted + reaction_weighted
        tolerance = float(self.residual_tolerance)
        passed = dynamic_residual <= tolerance and abs(weighted_residual) <= tolerance
        return ConservationReport(
            passed,
            (),
            dynamic_residual,
            weighted_residual,
        )


@dataclass(frozen=True, slots=True)
class ThermalEdgeContract:
    """Typed successor edge with an absolute-temperature entropy law."""

    edge_id: str
    tail: int
    head: int
    conductance: float
    temperature_units: str = "K"
    flux_units: str = "W"

    def validate(self) -> None:
        if not isinstance(self.edge_id, str) or not self.edge_id.strip():
            raise ValueError("edge_id must be a nonempty string")
        if not isinstance(self.tail, int) or not isinstance(self.head, int) or self.tail == self.head:
            raise ValueError("thermal edge tail/head must be distinct integer ports")
        conductance = _finite_scalar("conductance", self.conductance)
        if conductance <= 0.0:
            raise ValueError("conductance must be strictly positive")
        if not isinstance(self.temperature_units, str) or not self.temperature_units.strip():
            raise ValueError("temperature_units must be nonempty")
        if not isinstance(self.flux_units, str) or not self.flux_units.strip():
            raise ValueError("flux_units must be nonempty")

    def flux(self, tail_temperature: float, head_temperature: float) -> float:
        self.validate()
        tail_value = _finite_scalar("tail_temperature", tail_temperature)
        head_value = _finite_scalar("head_temperature", head_temperature)
        if tail_value <= 0.0 or head_value <= 0.0:
            raise ValueError("absolute temperatures must be strictly positive")
        return float(self.conductance * (tail_value - head_value))

    def entropy_production(self, tail_temperature: float, head_temperature: float) -> float:
        tail_value = _finite_scalar("tail_temperature", tail_temperature)
        head_value = _finite_scalar("head_temperature", head_temperature)
        if tail_value <= 0.0 or head_value <= 0.0:
            raise ValueError("absolute temperatures must be strictly positive")
        production = self.flux(tail_value, head_value) * (1.0 / head_value - 1.0 / tail_value)
        if production < -1e-12 or not math.isfinite(production):
            raise ValueError("thermal edge entropy production must be finite and nonnegative")
        return max(0.0, float(production))


@dataclass(frozen=True, slots=True)
class StrictSPPTAdapterAudit:
    passed: bool
    edge_flux: tuple[float, ...]
    edge_entropy_production: tuple[float, ...]
    conservation_report: ConservationReport
    thermodynamic_report: ThermodynamicAuditReport


@dataclass(frozen=True, slots=True)
class StrictSPPTAdapter:
    """Successor-only adapter binding incidence columns to typed thermal edges."""

    conservation: ConservationContract
    edges: tuple[ThermalEdgeContract, ...]

    def validate(self) -> None:
        self.conservation.validate_structure()
        if len(self.edges) != self.conservation.incidence.shape[1]:
            raise ValueError("one typed edge contract is required per incidence column")
        for edge_index, edge in enumerate(self.edges):
            edge.validate()
            if edge.tail < 0 or edge.head < 0 or edge.tail >= self.conservation.incidence.shape[0] or edge.head >= self.conservation.incidence.shape[0]:
                raise ValueError("thermal edge endpoint lies outside the incidence matrix")
            column = self.conservation.incidence[:, edge_index]
            if column[edge.tail] != -1.0 or column[edge.head] != 1.0:
                raise ValueError("thermal edge endpoints disagree with incidence orientation")

    def audit(self, temperatures: object, *, dt: float = 1.0) -> StrictSPPTAdapterAudit:
        self.validate()
        state = _finite_vector("temperatures", temperatures)
        if state.size != self.conservation.incidence.shape[0]:
            raise ValueError("temperature count must match conservation reservoirs")
        timestep = _finite_scalar("dt", dt)
        if timestep <= 0.0:
            raise ValueError("dt must be strictly positive")
        flux_values = tuple(edge.flux(state[edge.tail], state[edge.head]) for edge in self.edges)
        entropy_values = tuple(edge.entropy_production(state[edge.tail], state[edge.head]) * timestep for edge in self.edges)
        edge_flux = np.asarray(flux_values, dtype=float).reshape(-1, 1)
        dMdt = self.conservation.incidence @ edge_flux
        reaction_rate = np.zeros((1, self.conservation.stoichiometry.shape[1]), dtype=float)
        source = np.zeros_like(dMdt)
        escape = np.zeros_like(dMdt)
        conservation_report = self.conservation.audit(dMdt, edge_flux, reaction_rate, source, escape)
        terms = tuple(
            ThermodynamicTerm(
                term_id=f"{edge.edge_id}:entropy",
                source=edge.edge_id,
                destination="internal",
                process="thermal-conductance",
                quantity="entropy-production",
                units=f"{edge.flux_units}/{edge.temperature_units}",
                internal_or_external="internal",
                energy_delta=0.0,
                entropy_flow=0.0,
                entropy_production=entropy,
            )
            for edge, entropy in zip(self.edges, entropy_values)
        )
        ledger = ThermodynamicLedger(terms=terms)
        thermodynamic_report = ledger.audit(0.0, float(sum(entropy_values)))
        return StrictSPPTAdapterAudit(
            passed=conservation_report.passed and thermodynamic_report.passed,
            edge_flux=flux_values,
            edge_entropy_production=entropy_values,
            conservation_report=conservation_report,
            thermodynamic_report=thermodynamic_report,
        )


@dataclass(frozen=True, slots=True)
class ThermodynamicTerm:
    term_id: str
    source: str
    destination: str
    process: str
    quantity: str
    units: str
    internal_or_external: Literal["internal", "external"]
    energy_delta: float
    entropy_flow: float
    entropy_production: float

    def validate(self) -> None:
        for name in ("term_id", "source", "destination", "process", "quantity", "units"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")
        if self.internal_or_external not in {"internal", "external"}:
            raise ValueError("internal_or_external must be internal or external")
        _finite_scalar("energy_delta", self.energy_delta)
        _finite_scalar("entropy_flow", self.entropy_flow)
        production = _finite_scalar("entropy_production", self.entropy_production)
        if production < 0.0:
            raise ValueError("entropy_production must be nonnegative")


@dataclass(frozen=True, slots=True)
class ThermodynamicAuditReport:
    passed: bool
    energy_residual: float
    entropy_residual: float
    total_entropy_production: float
    errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ThermodynamicLedger:
    terms: tuple[ThermodynamicTerm, ...]
    energy_tolerance: float = 1e-10
    entropy_tolerance: float = 1e-10

    def audit(self, observed_energy_delta: float, observed_entropy_delta: float) -> ThermodynamicAuditReport:
        errors: list[str] = []
        energy_tolerance = _finite_scalar("energy_tolerance", self.energy_tolerance)
        entropy_tolerance = _finite_scalar("entropy_tolerance", self.entropy_tolerance)
        if energy_tolerance < 0.0 or entropy_tolerance < 0.0:
            errors.append("ledger tolerances must be nonnegative")
        identifiers = [term.term_id for term in self.terms]
        if len(set(identifiers)) != len(identifiers):
            errors.append("term_id values must be unique")
        for term in self.terms:
            try:
                term.validate()
            except ValueError as exc:
                errors.append(str(exc))
        observed_energy = _finite_scalar("observed_energy_delta", observed_energy_delta)
        observed_entropy = _finite_scalar("observed_entropy_delta", observed_entropy_delta)
        total_energy = float(sum(term.energy_delta for term in self.terms))
        total_entropy_flow = float(sum(term.entropy_flow for term in self.terms))
        total_production = float(sum(term.entropy_production for term in self.terms))
        energy_residual = observed_energy - total_energy
        entropy_residual = observed_entropy - total_entropy_flow - total_production
        if abs(energy_residual) > energy_tolerance:
            errors.append("energy balance exceeds tolerance")
        if abs(entropy_residual) > entropy_tolerance:
            errors.append("entropy balance exceeds tolerance")
        if total_production < -entropy_tolerance:
            errors.append("total entropy production violates the second-law gate")
        return ThermodynamicAuditReport(
            not errors,
            energy_residual,
            entropy_residual,
            total_production,
            tuple(errors),
        )


def transfer_signature(
    A: object,
    B: object,
    C: object,
    D: object | None = None,
    *,
    horizon: int | None = None,
) -> np.ndarray:
    """Return a finite Markov/transfer signature for a linear design.

    The signature is ``[D, C B, C A B, ...]`` flattened in row-major order.
    The default horizon is twice the state dimension, which is a useful finite
    discriminating signature for minimal linear candidates.  It is not by
    itself a proof of rational transfer equality: exact promotion still needs
    a canonical transfer-function/pole check or an independent rank argument.
    A caller may request a longer horizon for an epsilon/practical comparison,
    but the horizon must be positive.
    """

    matrix_a = _finite_array("A", A, 2)
    matrix_b = _finite_array("B", B, 2)
    matrix_c = _finite_array("C", C, 2)
    if matrix_a.shape[0] == 0 or matrix_a.shape[0] != matrix_a.shape[1]:
        raise ValueError("A must be a nonempty square matrix")
    if matrix_b.shape[0] != matrix_a.shape[0]:
        raise ValueError("B row count must match A state dimension")
    if matrix_c.shape[1] != matrix_a.shape[0]:
        raise ValueError("C column count must match A state dimension")
    steps = max(2 * matrix_a.shape[0], 1) if horizon is None else int(horizon)
    if steps < 1:
        raise ValueError("horizon must be a positive integer")
    if D is None:
        direct = np.zeros((matrix_c.shape[0], matrix_b.shape[1]), dtype=float)
    else:
        direct = _finite_array("D", D, 2)
        if direct.shape != (matrix_c.shape[0], matrix_b.shape[1]):
            raise ValueError("D must have shape (C rows, B columns)")

    powers = matrix_b.copy()
    blocks = [direct.ravel()]
    for _ in range(steps):
        blocks.append((matrix_c @ powers).ravel())
        powers = matrix_a @ powers
        if not np.all(np.isfinite(powers)):
            raise ValueError("state transition powers must remain finite")
    return np.concatenate(blocks)


def normalized_signature_residual(
    left: object,
    right: object,
    *,
    absolute_tolerance: float = 1e-10,
    relative_tolerance: float = 1e-8,
) -> float:
    """Return the largest scale-aware residual, where ``<= 1`` is equivalent."""

    a = _finite_vector("left signature", left)
    b = _finite_vector("right signature", right)
    if a.shape != b.shape:
        raise ValueError("signatures must have identical shapes")
    atol = _finite_scalar("absolute_tolerance", absolute_tolerance)
    rtol = _finite_scalar("relative_tolerance", relative_tolerance)
    if atol < 0.0 or rtol < 0.0:
        raise ValueError("signature tolerances must be nonnegative")
    scale = np.maximum(np.maximum(np.abs(a), np.abs(b)), np.finfo(float).tiny)
    allowed = np.maximum(atol + rtol * scale, np.finfo(float).tiny)
    return float(np.max(np.abs(a - b) / allowed))


@dataclass(frozen=True, slots=True)
class RankCondition:
    rank: int
    full_rank: bool
    singular_values: tuple[float, ...]
    threshold: float
    condition_number: float


def matrix_rank_condition(
    matrix: object,
    *,
    absolute_tolerance: float = 1e-12,
    relative_tolerance: float = 1e-9,
) -> RankCondition:
    """Return scale-aware rank and conditioning diagnostics."""

    array = _finite_array("matrix", matrix, 2)
    atol = _finite_scalar("absolute_tolerance", absolute_tolerance)
    rtol = _finite_scalar("relative_tolerance", relative_tolerance)
    if atol < 0.0 or rtol < 0.0:
        raise ValueError("rank tolerances must be nonnegative")
    if min(array.shape) == 0:
        return RankCondition(0, False, (), max(atol, 0.0), math.inf)
    singular = np.linalg.svd(array, compute_uv=False)
    threshold = max(atol, rtol * float(singular[0]))
    rank = int(np.count_nonzero(singular > threshold))
    full_rank = rank == min(array.shape)
    condition = float(singular[0] / singular[-1]) if full_rank and singular[-1] > 0.0 else math.inf
    return RankCondition(rank, full_rank, tuple(float(value) for value in singular), threshold, condition)


def controllability_matrix(A: object, B: object) -> np.ndarray:
    matrix_a = _finite_array("A", A, 2)
    matrix_b = _finite_array("B", B, 2)
    if matrix_a.shape[0] == 0 or matrix_a.shape[0] != matrix_a.shape[1]:
        raise ValueError("A must be a nonempty square matrix")
    if matrix_b.shape[0] != matrix_a.shape[0]:
        raise ValueError("B row count must match A state dimension")
    powers = matrix_b.copy()
    blocks = []
    for _ in range(matrix_a.shape[0]):
        blocks.append(powers)
        powers = matrix_a @ powers
    return np.hstack(blocks)


def observability_matrix(A: object, C: object) -> np.ndarray:
    matrix_a = _finite_array("A", A, 2)
    matrix_c = _finite_array("C", C, 2)
    if matrix_a.shape[0] == 0 or matrix_a.shape[0] != matrix_a.shape[1]:
        raise ValueError("A must be a nonempty square matrix")
    if matrix_c.shape[1] != matrix_a.shape[0]:
        raise ValueError("C column count must match A state dimension")
    powers = matrix_c.copy()
    blocks = []
    for _ in range(matrix_a.shape[0]):
        blocks.append(powers)
        powers = powers @ matrix_a
    return np.vstack(blocks)


def _complex_pairs(values: object) -> np.ndarray:
    complex_values = np.asarray(values, dtype=complex).reshape(-1)
    if not np.all(np.isfinite(complex_values)):
        raise ValueError("pole/zero values must be finite")
    ordered = sorted(complex_values.tolist(), key=lambda value: (float(value.real), float(value.imag)))
    return np.asarray([(float(value.real), float(value.imag)) for value in ordered], dtype=float).reshape(-1, 2)


def _cancel_common_poles_and_zeros(
    poles: np.ndarray,
    zeros: np.ndarray,
    *,
    tolerance: float = 1e-7,
) -> tuple[np.ndarray, np.ndarray]:
    pole_values = [complex(real, imag) for real, imag in poles]
    zero_values = [complex(real, imag) for real, imag in zeros]
    remaining_poles: list[complex] = []
    for pole in pole_values:
        matches = [
            (index, zero)
            for index, zero in enumerate(zero_values)
            if abs(pole - zero) <= tolerance * max(1.0, abs(pole), abs(zero))
        ]
        if matches:
            zero_values.pop(matches[0][0])
        else:
            remaining_poles.append(pole)
    return _complex_pairs(remaining_poles), _complex_pairs(zero_values)


def pole_zero_signature(
    A: object,
    B: object,
    C: object,
    D: object | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return sorted SISO pole/zero pairs for a state-space candidate."""

    matrix_a = _finite_array("A", A, 2)
    matrix_b = _finite_array("B", B, 2)
    matrix_c = _finite_array("C", C, 2)
    if matrix_b.shape[1] != 1 or matrix_c.shape[0] != 1:
        raise ValueError("pole_zero_signature currently requires a SISO candidate")
    if D is None:
        matrix_d = np.zeros((1, 1), dtype=float)
    else:
        matrix_d = _finite_array("D", D, 2)
    if matrix_d.shape != (1, 1):
        raise ValueError("SISO D must have shape (1, 1)")
    poles = np.linalg.eigvals(matrix_a)
    try:
        from scipy.signal import ss2tf
    except ImportError as exc:  # pragma: no cover - exact runtime supplies SciPy
        raise RuntimeError("SISO pole/zero checks require scipy.signal.ss2tf") from exc
    numerator, denominator = ss2tf(matrix_a, matrix_b, matrix_c, matrix_d)
    numerator = np.trim_zeros(np.asarray(numerator[0], dtype=float), trim="f")
    denominator = np.trim_zeros(np.asarray(denominator, dtype=float), trim="f")
    zeros = np.roots(numerator) if numerator.size > 1 else np.asarray([], dtype=complex)
    return _cancel_common_poles_and_zeros(_complex_pairs(poles), _complex_pairs(zeros))


@dataclass(frozen=True, slots=True)
class LinearEquivalenceReport:
    markov_residual: float
    pole_residual: float
    zero_residual: float
    exact_equivalent: bool
    practical_equivalent: bool


def compare_linear_models(
    left: Mapping[str, object],
    right: Mapping[str, object],
    *,
    absolute_tolerance: float = 1e-10,
    relative_tolerance: float = 1e-8,
) -> LinearEquivalenceReport:
    """Compare observable transfer evidence plus SISO poles and zeros."""

    left_signature = transfer_signature(left["A"], left["B"], left["C"], left.get("D"))
    right_signature = transfer_signature(right["A"], right["B"], right["C"], right.get("D"))
    markov_residual = normalized_signature_residual(
        left_signature,
        right_signature,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
    )
    left_poles, left_zeros = pole_zero_signature(left["A"], left["B"], left["C"], left.get("D"))
    right_poles, right_zeros = pole_zero_signature(right["A"], right["B"], right["C"], right.get("D"))
    pole_residual = normalized_signature_residual(
        left_poles.ravel(),
        right_poles.ravel(),
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
    )
    zero_residual = normalized_signature_residual(
        left_zeros.ravel() if left_zeros.size else np.zeros(1),
        right_zeros.ravel() if right_zeros.size else np.zeros(1),
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
    )
    exact_equivalent = (
        np.array_equal(left_signature, right_signature)
        and np.array_equal(left_poles, right_poles)
        and np.array_equal(left_zeros, right_zeros)
    )
    practical_equivalent = max(markov_residual, pole_residual, zero_residual) <= 1.0
    return LinearEquivalenceReport(
        markov_residual,
        pole_residual,
        zero_residual,
        exact_equivalent,
        practical_equivalent,
    )


def canonical_graph_label(adjacency: object, *, decimals: int = 12, max_nodes: int = 8) -> tuple[float, ...]:
    """Canonicalize small weighted graph labels under simultaneous relabeling."""

    matrix = _finite_array("adjacency", adjacency, 2)
    if matrix.shape[0] == 0 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("adjacency must be a nonempty square matrix")
    if matrix.shape[0] > max_nodes:
        raise ValueError(f"canonical_graph_label is bounded to at most {max_nodes} nodes")
    import itertools

    labels = []
    for permutation in itertools.permutations(range(matrix.shape[0])):
        relabeled = matrix[np.ix_(permutation, permutation)]
        labels.append(tuple(float(value) for value in np.round(relabeled, decimals=decimals).ravel()))
    return min(labels)


@dataclass(frozen=True, slots=True)
class ObservationalEquivalenceClass:
    class_id: str
    candidate_ids: tuple[str, ...]
    signature_kind: Literal["exact", "epsilon", "posterior"]
    maximum_residual: float
    tolerance: float
    design_id: str
    status: Literal["identified", "equivalent", "unknown"]

    def validate(self) -> None:
        if not isinstance(self.class_id, str) or not self.class_id.strip():
            raise ValueError("class_id and design_id must be nonempty")
        if not isinstance(self.design_id, str) or not self.design_id.strip():
            raise ValueError("class_id and design_id must be nonempty")
        if not self.candidate_ids:
            raise ValueError("candidate_ids must not be empty")
        if not all(isinstance(candidate, str) and candidate.strip() for candidate in self.candidate_ids):
            raise ValueError("candidate_ids must contain nonempty strings")
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("candidate_ids must be unique")
        if self.signature_kind not in {"exact", "epsilon", "posterior"}:
            raise ValueError("unsupported signature_kind")
        if self.status not in {"identified", "equivalent", "unknown"}:
            raise ValueError("unsupported equivalence status")
        residual = _finite_scalar("maximum_residual", self.maximum_residual)
        tolerance = _finite_scalar("tolerance", self.tolerance)
        if residual < 0.0 or tolerance < 0.0:
            raise ValueError("residual and tolerance must be nonnegative")


def partition_equivalence_classes(
    signatures: Mapping[str, object],
    design_id: str,
    *,
    signature_kind: Literal["exact", "epsilon", "posterior"] = "epsilon",
    absolute_tolerance: float = 1e-10,
    relative_tolerance: float = 1e-8,
) -> tuple[ObservationalEquivalenceClass, ...]:
    """Partition candidate signatures into deterministic observational classes.

    The partition uses complete-linkage grouping: a candidate joins a class
    only when it is equivalent to every existing member.  This avoids treating
    a non-transitive chain of pairwise epsilon matches as one class.  The
    returned residual is the largest normalized pairwise residual in each
    class; singleton classes are *identified*, while multi-candidate classes
    remain *equivalent* rather than being promoted as topology truth.
    """

    if not isinstance(design_id, str) or not design_id.strip():
        raise ValueError("design_id must be a nonempty string")
    if signature_kind not in {"exact", "epsilon", "posterior"}:
        raise ValueError("unsupported signature_kind")
    if not signatures:
        raise ValueError("signatures must contain at least one candidate")
    normalized = {
        candidate_id: _finite_vector(f"signature {candidate_id}", signature)
        for candidate_id, signature in signatures.items()
    }
    candidate_ids = sorted(normalized)
    if not all(isinstance(candidate, str) and candidate.strip() for candidate in candidate_ids):
        raise ValueError("signature candidate IDs must be nonempty strings")
    if signature_kind == "exact":
        absolute_tolerance = 0.0
        relative_tolerance = 0.0

    unassigned = set(candidate_ids)
    classes: list[ObservationalEquivalenceClass] = []
    class_number = 1
    while unassigned:
        seed = min(unassigned)
        members = [seed]
        unassigned.remove(seed)
        for candidate in sorted(tuple(unassigned)):
            if all(
                normalized_signature_residual(
                    normalized[candidate],
                    normalized[member],
                    absolute_tolerance=absolute_tolerance,
                    relative_tolerance=relative_tolerance,
                )
                <= 1.0
                for member in members
            ):
                members.append(candidate)
                unassigned.remove(candidate)
        residuals = [
            normalized_signature_residual(
                normalized[left],
                normalized[right],
                absolute_tolerance=absolute_tolerance,
                relative_tolerance=relative_tolerance,
            )
            for index, left in enumerate(members)
            for right in members[index + 1 :]
        ]
        maximum_residual = max(residuals, default=0.0)
        record = ObservationalEquivalenceClass(
            class_id=f"{design_id}:class-{class_number:02d}",
            candidate_ids=tuple(members),
            signature_kind=signature_kind,
            maximum_residual=maximum_residual,
            tolerance=1.0,
            design_id=design_id,
            status="identified" if len(members) == 1 else "equivalent",
        )
        record.validate()
        classes.append(record)
        class_number += 1
    return tuple(classes)


@dataclass(frozen=True, slots=True)
class InterventionDesign:
    design_id: str
    control_ports: tuple[str, ...]
    observation_ports: tuple[str, ...]
    objective: str
    budget: float
    safety_constraints: tuple[str, ...]
    expected_minimum_separation: float

    def validate(self) -> None:
        if not self.design_id.strip() or not self.objective.strip():
            raise ValueError("design_id and objective must be nonempty")
        if not self.control_ports or not self.observation_ports:
            raise ValueError("at least one control and observation port are required")
        budget = _finite_scalar("budget", self.budget)
        separation = _finite_scalar("expected_minimum_separation", self.expected_minimum_separation)
        if budget < 0.0 or separation < 0.0:
            raise ValueError("budget and expected separation must be nonnegative")
        if not self.safety_constraints:
            raise ValueError("at least one safety constraint is required")


@dataclass(frozen=True, slots=True)
class InterventionOption:
    """A complete candidate design that can be compared under a budget."""

    option_id: str
    control_ports: tuple[str, ...]
    observation_ports: tuple[str, ...]
    cost: float
    expected_minimum_separation: float
    safety_ok: bool
    safety_reason: str = ""
    utility_kind: Literal["normalized_euclidean", "fisher"] = "normalized_euclidean"
    response_separation: float | None = None
    fisher_separation: float | None = None

    def validate(self) -> None:
        if not isinstance(self.option_id, str) or not self.option_id.strip():
            raise ValueError("option_id must be a nonempty string")
        if not self.control_ports or not self.observation_ports:
            raise ValueError("an intervention option needs controls and observations")
        if not all(isinstance(value, str) and value.strip() for value in (*self.control_ports, *self.observation_ports)):
            raise ValueError("ports must contain nonempty strings")
        cost = _finite_scalar("cost", self.cost)
        separation = _finite_scalar("expected_minimum_separation", self.expected_minimum_separation)
        if cost < 0.0 or separation < 0.0:
            raise ValueError("cost and expected separation must be nonnegative")
        if not isinstance(self.safety_ok, bool):
            raise ValueError("safety_ok must be boolean")
        if not isinstance(self.safety_reason, str):
            raise ValueError("safety_reason must be a string")
        if self.utility_kind not in {"normalized_euclidean", "fisher"}:
            raise ValueError("unsupported intervention utility kind")
        for name, value in (("response_separation", self.response_separation), ("fisher_separation", self.fisher_separation)):
            if value is not None and _finite_scalar(name, value) < 0.0:
                raise ValueError(f"{name} must be nonnegative")
        if self.utility_kind == "fisher" and self.fisher_separation is None:
            raise ValueError("fisher utility requires fisher_separation")


@dataclass(frozen=True, slots=True)
class InterventionSelection:
    selected_option_id: str | None
    total_cost: float
    expected_minimum_separation: float
    feasible: bool
    considered_option_ids: tuple[str, ...]
    rejected_option_ids: tuple[str, ...]

    def validate(self) -> None:
        if self.selected_option_id is not None and (
            not isinstance(self.selected_option_id, str) or not self.selected_option_id.strip()
        ):
            raise ValueError("selected_option_id must be nonempty or null")
        cost = _finite_scalar("total_cost", self.total_cost)
        separation = _finite_scalar("expected_minimum_separation", self.expected_minimum_separation)
        if cost < 0.0 or separation < 0.0:
            raise ValueError("selection cost and separation must be nonnegative")
        if not isinstance(self.feasible, bool):
            raise ValueError("feasible must be boolean")
        for name, values in (("considered_option_ids", self.considered_option_ids), ("rejected_option_ids", self.rejected_option_ids)):
            if not all(isinstance(value, str) and value.strip() for value in values):
                raise ValueError(f"{name} must contain nonempty strings")
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must not contain duplicates")
        if self.feasible and self.selected_option_id is None:
            raise ValueError("a feasible selection requires a selected option")
        if not self.feasible and self.selected_option_id is not None:
            raise ValueError("an infeasible selection cannot select an option")


def minimum_pairwise_separation(signatures: Mapping[str, object]) -> float:
    """Return the minimum relative Euclidean separation among candidates."""

    if len(signatures) < 2:
        return 0.0
    normalized = {
        candidate_id: _finite_vector(f"signature {candidate_id}", signature)
        for candidate_id, signature in signatures.items()
    }
    values = list(normalized.values())
    reference_shape = values[0].shape
    if any(value.shape != reference_shape for value in values[1:]):
        raise ValueError("all intervention signatures must have identical shapes")
    separations: list[float] = []
    for index, left in enumerate(values):
        for right in values[index + 1 :]:
            scale = max(float(np.linalg.norm(left)), float(np.linalg.norm(right)), np.finfo(float).tiny)
            separations.append(float(np.linalg.norm(left - right) / scale))
    return min(separations)


def fisher_information_from_jacobian(
    jacobian: object,
    covariance: object,
) -> np.ndarray:
    """Return ``J.T Sigma^-1 J`` after a strict SPD covariance check."""

    J = _finite_array("jacobian", jacobian, 2)
    Sigma = _finite_array("covariance", covariance, 2)
    if Sigma.shape[0] == 0 or Sigma.shape[0] != Sigma.shape[1] or Sigma.shape[0] != J.shape[0]:
        raise ValueError("covariance must be square and match jacobian rows")
    if not np.allclose(Sigma, Sigma.T, atol=1e-12, rtol=0.0):
        raise ValueError("covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(Sigma)
    if np.any(eigenvalues <= 0.0):
        raise ValueError("covariance must be strictly positive definite")
    information = J.T @ np.linalg.solve(Sigma, J)
    if not np.all(np.isfinite(information)):
        raise ValueError("Fisher information must be finite")
    return information


def fisher_pairwise_separation(
    signatures: Mapping[str, object],
    covariance: object,
) -> float:
    """Return the weakest Mahalanobis separation among candidate responses."""

    if len(signatures) < 2:
        return 0.0
    normalized = {
        candidate_id: _finite_vector(f"signature {candidate_id}", signature)
        for candidate_id, signature in signatures.items()
    }
    values = list(normalized.values())
    reference_shape = values[0].shape
    if any(value.shape != reference_shape for value in values[1:]):
        raise ValueError("all intervention signatures must have identical shapes")
    Sigma = _finite_array("covariance", covariance, 2)
    if Sigma.shape != (reference_shape[0], reference_shape[0]):
        raise ValueError("covariance dimension must match response signatures")
    eigenvalues = np.linalg.eigvalsh(Sigma)
    if not np.allclose(Sigma, Sigma.T, atol=1e-12, rtol=0.0) or np.any(eigenvalues <= 0.0):
        raise ValueError("covariance must be symmetric positive definite")
    separations: list[float] = []
    for index, left in enumerate(values):
        for right in values[index + 1 :]:
            delta = left - right
            squared = float(delta @ np.linalg.solve(Sigma, delta))
            separations.append(math.sqrt(max(squared, 0.0)))
    return min(separations)


def intervention_option_from_signatures(
    *,
    option_id: str,
    control_ports: tuple[str, ...],
    observation_ports: tuple[str, ...],
    cost: float,
    candidate_signatures: Mapping[str, object],
    safety_ok: bool,
    safety_reason: str = "",
    noise_covariance: object | None = None,
) -> InterventionOption:
    """Build an option from responses, optionally using Fisher utility."""

    response_separation = minimum_pairwise_separation(candidate_signatures)
    fisher_separation = None
    if noise_covariance is None:
        separation = response_separation
        utility_kind: Literal["normalized_euclidean", "fisher"] = "normalized_euclidean"
    else:
        fisher_separation = fisher_pairwise_separation(candidate_signatures, noise_covariance)
        separation = fisher_separation
        utility_kind = "fisher"
    option = InterventionOption(
        option_id=option_id,
        control_ports=control_ports,
        observation_ports=observation_ports,
        cost=cost,
        expected_minimum_separation=separation,
        safety_ok=safety_ok,
        safety_reason=safety_reason,
        utility_kind=utility_kind,
        response_separation=response_separation,
        fisher_separation=fisher_separation,
    )
    option.validate()
    return option


def rank_interventions(
    options: Sequence[InterventionOption],
    *,
    budget: float,
) -> tuple[InterventionOption, ...]:
    """Rank safe, affordable options by expected class separation.

    Ties are deterministic: lower cost first, then lexical option ID.  This is
    a transparent utility rule, not a claim that the expected separation is a
    calibrated causal effect.
    """

    available_budget = _finite_scalar("budget", budget)
    if available_budget < 0.0:
        raise ValueError("budget must be nonnegative")
    validated: list[InterventionOption] = []
    seen: set[str] = set()
    for option in options:
        option.validate()
        if option.option_id in seen:
            raise ValueError("option_id values must be unique")
        seen.add(option.option_id)
        if option.safety_ok and option.cost <= available_budget:
            validated.append(option)
    return tuple(
        sorted(
            validated,
            key=lambda option: (
                -option.expected_minimum_separation,
                option.cost,
                option.option_id,
            ),
        )
    )


def select_intervention(
    options: Sequence[InterventionOption],
    *,
    budget: float,
) -> InterventionSelection:
    """Select the highest-utility safe option and preserve rejection IDs."""

    available_budget = _finite_scalar("budget", budget)
    ranked = rank_interventions(options, budget=available_budget)
    all_ids = tuple(option.option_id for option in options)
    selected = ranked[0] if ranked else None
    rejected = tuple(option_id for option_id in all_ids if selected is None or option_id != selected.option_id)
    if selected is None:
        return InterventionSelection(None, 0.0, 0.0, False, all_ids, rejected)
    return InterventionSelection(
        selected.option_id,
        selected.cost,
        selected.expected_minimum_separation,
        True,
        all_ids,
        rejected,
    )


@dataclass(frozen=True, slots=True)
class PredictionScore:
    mean_log_score: float
    mean_crps: float
    coverage: float
    sample_count: int
    interval_level: float


def _prediction_arrays(
    observed: object,
    predicted_mean: object,
    sigma: object,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = _finite_vector("observed", observed)
    mean = _finite_vector("predicted_mean", predicted_mean)
    if y.shape != mean.shape:
        raise ValueError("observed and predicted_mean must have identical shapes")
    raw_sigma = np.asarray(sigma, dtype=float)
    if raw_sigma.ndim == 0:
        raw_sigma = np.full(y.shape, float(raw_sigma))
    elif raw_sigma.ndim == 1 and raw_sigma.shape == y.shape:
        raw_sigma = raw_sigma.copy()
    else:
        raise ValueError("sigma must be a scalar or a vector matching observed")
    if not np.all(np.isfinite(raw_sigma)) or np.any(raw_sigma <= 0.0):
        raise ValueError("sigma must be finite and strictly positive")
    return y, mean, raw_sigma


def gaussian_log_score(observed: object, predicted_mean: object, sigma: object) -> float:
    """Return the mean Gaussian log predictive density; higher is better."""

    y, mean, spread = _prediction_arrays(observed, predicted_mean, sigma)
    z = (y - mean) / spread
    values = -0.5 * z**2 - np.log(spread) - 0.5 * math.log(2.0 * math.pi)
    return float(np.mean(values))


def gaussian_crps(observed: object, predicted_mean: object, sigma: object) -> float:
    """Return the mean closed-form CRPS for a Gaussian predictive distribution."""

    y, mean, spread = _prediction_arrays(observed, predicted_mean, sigma)
    z = (y - mean) / spread
    erf_values = np.array([math.erf(float(value)) for value in z], dtype=float)
    cdf = 0.5 * (1.0 + erf_values / math.sqrt(2.0))
    pdf = np.exp(-0.5 * z**2) / math.sqrt(2.0 * math.pi)
    values = spread * (z * (2.0 * cdf - 1.0) + 2.0 * pdf - 1.0 / math.sqrt(math.pi))
    return float(np.mean(values))


def gaussian_interval_coverage(
    observed: object,
    predicted_mean: object,
    sigma: object,
    *,
    interval_level: float = 0.9,
) -> float:
    """Return empirical central-interval coverage for Gaussian predictions."""

    y, mean, spread = _prediction_arrays(observed, predicted_mean, sigma)
    level = _finite_scalar("interval_level", interval_level)
    if not 0.0 < level < 1.0:
        raise ValueError("interval_level must lie strictly between zero and one")
    z = NormalDist().inv_cdf(0.5 + 0.5 * level)
    lower = mean - z * spread
    upper = mean + z * spread
    return float(np.mean((y >= lower) & (y <= upper)))


def score_gaussian_predictions(
    observed: object,
    predicted_mean: object,
    sigma: object,
    *,
    interval_level: float = 0.9,
) -> PredictionScore:
    """Compute log score, CRPS, coverage, and sample count on one held-out set."""

    y, mean, spread = _prediction_arrays(observed, predicted_mean, sigma)
    return PredictionScore(
        mean_log_score=gaussian_log_score(y, mean, spread),
        mean_crps=gaussian_crps(y, mean, spread),
        coverage=gaussian_interval_coverage(y, mean, spread, interval_level=interval_level),
        sample_count=int(y.size),
        interval_level=float(interval_level),
    )


def calibrate_gaussian_scale(
    observed: object,
    predicted_mean: object,
    *,
    minimum_sigma: float = 1e-12,
) -> float:
    """Estimate predictive scale from calibration residuals only."""

    y = _finite_vector("calibration observed", observed)
    mean = _finite_vector("calibration predicted_mean", predicted_mean)
    if y.shape != mean.shape:
        raise ValueError("calibration arrays must have identical shapes")
    if y.size < 2:
        raise ValueError("at least two calibration observations are required")
    floor = _finite_scalar("minimum_sigma", minimum_sigma)
    if floor <= 0.0:
        raise ValueError("minimum_sigma must be strictly positive")
    scale = float(np.std(y - mean, ddof=1))
    if not math.isfinite(scale):
        raise ValueError("calibration residual scale must be finite")
    return max(scale, floor)


@dataclass(frozen=True, slots=True)
class SeededDataSplit:
    seed: int
    fit_indices: tuple[int, ...]
    calibration_indices: tuple[int, ...]
    test_indices: tuple[int, ...]

    def validate(self, sample_count: int) -> None:
        if sample_count < 3:
            raise ValueError("sample_count must be at least three")
        groups = (self.fit_indices, self.calibration_indices, self.test_indices)
        if any(not group for group in groups):
            raise ValueError("fit, calibration, and test splits must be nonempty")
        flattened = [index for group in groups for index in group]
        if len(flattened) != sample_count or len(set(flattened)) != sample_count:
            raise ValueError("data splits must be disjoint and cover every sample")
        if any(index < 0 or index >= sample_count for index in flattened):
            raise ValueError("split indices must lie within the sample range")


def seeded_three_way_split(
    sample_count: int,
    *,
    fit_fraction: float = 0.6,
    calibration_fraction: float = 0.2,
    seed: int = 0,
) -> SeededDataSplit:
    """Create deterministic fit/calibration/test indices with one seed."""

    if not isinstance(sample_count, int) or sample_count < 3:
        raise ValueError("sample_count must be an integer of at least three")
    fit = _finite_scalar("fit_fraction", fit_fraction)
    calibration = _finite_scalar("calibration_fraction", calibration_fraction)
    if fit <= 0.0 or calibration <= 0.0 or fit + calibration >= 1.0:
        raise ValueError("fit and calibration fractions must be positive and sum below one")
    fit_count = max(1, int(math.floor(sample_count * fit)))
    calibration_count = max(1, int(math.floor(sample_count * calibration)))
    if fit_count + calibration_count >= sample_count:
        calibration_count = sample_count - fit_count - 1
    if calibration_count < 1:
        raise ValueError("fractions leave no nonempty test split")
    permutation = np.random.default_rng(seed).permutation(sample_count).tolist()
    split = SeededDataSplit(
        seed=int(seed),
        fit_indices=tuple(permutation[:fit_count]),
        calibration_indices=tuple(permutation[fit_count : fit_count + calibration_count]),
        test_indices=tuple(permutation[fit_count + calibration_count :]),
    )
    split.validate(sample_count)
    return split


def apply_data_split(values: object, split: SeededDataSplit) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    array = np.asarray(values)
    if array.ndim == 0 or array.shape[0] != len(split.fit_indices) + len(split.calibration_indices) + len(split.test_indices):
        raise ValueError("values first dimension must match the split population")
    split.validate(array.shape[0])
    return array[list(split.fit_indices)], array[list(split.calibration_indices)], array[list(split.test_indices)]


@dataclass(frozen=True, slots=True)
class PosteriorPredictiveCheck:
    coverage: float
    interval_level: float
    observed_discrepancy: float
    replicated_discrepancy_mean: float
    discrepancy_p_value: float
    draw_count: int
    observation_count: int


def posterior_predictive_check(
    observed: object,
    predictive_samples: object,
    *,
    interval_level: float = 0.9,
) -> PosteriorPredictiveCheck:
    """Compare observed coverage and a variance discrepancy to replicated draws."""

    y = _finite_vector("observed", observed)
    samples = _finite_array("predictive_samples", predictive_samples, 2)
    if samples.shape[0] < 2 or samples.shape[1] != y.size:
        raise ValueError("predictive_samples must be (draws, observations) with at least two draws")
    level = _finite_scalar("interval_level", interval_level)
    if not 0.0 < level < 1.0:
        raise ValueError("interval_level must lie strictly between zero and one")
    alpha = (1.0 - level) / 2.0
    lower = np.quantile(samples, alpha, axis=0)
    upper = np.quantile(samples, 1.0 - alpha, axis=0)
    coverage = float(np.mean((y >= lower) & (y <= upper)))
    observed_discrepancy = float(np.mean((y - np.mean(y)) ** 2))
    replicated_discrepancies = np.mean((samples - np.mean(samples, axis=1, keepdims=True)) ** 2, axis=1)
    p_value = float(np.mean(replicated_discrepancies >= observed_discrepancy))
    return PosteriorPredictiveCheck(
        coverage=coverage,
        interval_level=level,
        observed_discrepancy=observed_discrepancy,
        replicated_discrepancy_mean=float(np.mean(replicated_discrepancies)),
        discrepancy_p_value=p_value,
        draw_count=int(samples.shape[0]),
        observation_count=int(samples.shape[1]),
    )


@dataclass(frozen=True, slots=True)
class SimulationBasedCalibrationReport:
    ranks: tuple[int, ...]
    bin_counts: tuple[int, ...]
    bins: int
    draw_count: int
    chi_square: float
    maximum_bin_deviation: float
    status: Literal["pass", "fail", "unknown"]


def simulation_based_calibration(
    true_values: object,
    posterior_samples: object,
    *,
    bins: int = 10,
) -> SimulationBasedCalibrationReport:
    """Return deterministic SBC ranks and a conservative uniformity diagnostic."""

    truth = _finite_vector("true_values", true_values)
    samples = _finite_array("posterior_samples", posterior_samples, 2)
    if samples.shape[1] != truth.size or samples.shape[0] < 2:
        raise ValueError("posterior_samples must be (draws, cases)")
    if not isinstance(bins, int) or bins < 2:
        raise ValueError("bins must be an integer of at least two")
    ranks = tuple(int(np.count_nonzero(samples[:, index] < truth[index])) for index in range(truth.size))
    bucket_indices = [min(bins - 1, int(rank * bins / (samples.shape[0] + 1))) for rank in ranks]
    counts = np.bincount(bucket_indices, minlength=bins)
    expected = truth.size / bins
    chi_square = float(np.sum((counts - expected) ** 2 / expected)) if expected > 0.0 else math.inf
    maximum_deviation = float(np.max(np.abs(counts - expected)) / max(expected, 1.0))
    # Small SBC campaigns cannot support a meaningful pass/fail claim.
    if truth.size < 20:
        status: Literal["pass", "fail", "unknown"] = "unknown"
    elif maximum_deviation <= 0.5:
        status = "pass"
    else:
        status = "fail"
    return SimulationBasedCalibrationReport(
        ranks=ranks,
        bin_counts=tuple(int(value) for value in counts),
        bins=bins,
        draw_count=int(samples.shape[0]),
        chi_square=chi_square,
        maximum_bin_deviation=maximum_deviation,
        status=status,
    )


@dataclass(frozen=True, slots=True)
class CalibratedPredictionAudit:
    audit_id: str
    fit_data_id: str
    calibration_data_id: str
    test_data_id: str
    candidate_id: str
    baseline_id: str
    heldout_log_score: float
    baseline_heldout_log_score: float
    coverage: float
    target_coverage: float
    calibration_status: Literal["pass", "fail", "unknown"]
    result: Literal["promote", "demote", "defer"]
    candidate_crps: float | None = None
    baseline_crps: float | None = None
    baseline_coverage: float | None = None
    interval_level: float = 0.9
    coverage_tolerance: float = 0.05
    sample_count: int | None = None

    def validate(self) -> None:
        identifiers = (
            self.audit_id,
            self.fit_data_id,
            self.calibration_data_id,
            self.test_data_id,
            self.candidate_id,
            self.baseline_id,
        )
        if not all(isinstance(value, str) and value.strip() for value in identifiers):
            raise ValueError("audit and dataset identifiers must be nonempty")
        if len({self.fit_data_id, self.calibration_data_id, self.test_data_id}) != 3:
            raise ValueError("fit, calibration, and test datasets must be distinct")
        _finite_scalar("heldout_log_score", self.heldout_log_score)
        _finite_scalar("baseline_heldout_log_score", self.baseline_heldout_log_score)
        coverage = _finite_scalar("coverage", self.coverage)
        target = _finite_scalar("target_coverage", self.target_coverage)
        if not (0.0 <= coverage <= 1.0 and 0.0 <= target <= 1.0):
            raise ValueError("coverage values must lie in [0, 1]")
        if self.baseline_coverage is not None:
            baseline_coverage = _finite_scalar("baseline_coverage", self.baseline_coverage)
            if not 0.0 <= baseline_coverage <= 1.0:
                raise ValueError("baseline_coverage must lie in [0, 1]")
        for name, value in (("candidate_crps", self.candidate_crps), ("baseline_crps", self.baseline_crps)):
            if value is not None and _finite_scalar(name, value) < 0.0:
                raise ValueError(f"{name} must be nonnegative")
        interval_level = _finite_scalar("interval_level", self.interval_level)
        tolerance = _finite_scalar("coverage_tolerance", self.coverage_tolerance)
        if not 0.0 < interval_level < 1.0 or tolerance < 0.0:
            raise ValueError("interval_level must lie in (0, 1) and coverage_tolerance must be nonnegative")
        if self.sample_count is not None:
            if not isinstance(self.sample_count, int) or self.sample_count < 1:
                raise ValueError("sample_count must be a positive integer when supplied")
        if self.calibration_status not in {"pass", "fail", "unknown"}:
            raise ValueError("unsupported calibration_status")
        if self.result not in {"promote", "demote", "defer"}:
            raise ValueError("unsupported result")
        if self.result == "promote" and self.calibration_status != "pass":
            raise ValueError("promotion requires a passing calibration status")


def run_calibrated_prediction_audit(
    *,
    audit_id: str,
    fit_data_id: str,
    calibration_data_id: str,
    test_data_id: str,
    candidate_id: str,
    baseline_id: str,
    calibration_observed: object,
    candidate_calibration_mean: object,
    baseline_calibration_mean: object,
    test_observed: object,
    candidate_test_mean: object,
    baseline_test_mean: object,
    target_coverage: float = 0.9,
    coverage_tolerance: float = 0.05,
    interval_level: float = 0.9,
    minimum_sigma: float = 1e-12,
) -> CalibratedPredictionAudit:
    """Calibrate scales on one split and compare candidates on held-out data.

    Model means must already be fit using ``fit_data_id``.  This function only
    estimates predictive scales from the calibration split and evaluates log
    score, CRPS, and interval coverage on the distinct test split.  A failed
    calibration defers promotion rather than treating a point estimate as
    scientific confirmation.
    """

    target = _finite_scalar("target_coverage", target_coverage)
    tolerance = _finite_scalar("coverage_tolerance", coverage_tolerance)
    level = _finite_scalar("interval_level", interval_level)
    if not 0.0 <= target <= 1.0 or tolerance < 0.0:
        raise ValueError("target_coverage must lie in [0, 1] and tolerance must be nonnegative")
    if not 0.0 < level < 1.0:
        raise ValueError("interval_level must lie strictly between zero and one")

    candidate_sigma = calibrate_gaussian_scale(
        calibration_observed,
        candidate_calibration_mean,
        minimum_sigma=minimum_sigma,
    )
    baseline_sigma = calibrate_gaussian_scale(
        calibration_observed,
        baseline_calibration_mean,
        minimum_sigma=minimum_sigma,
    )
    candidate_score = score_gaussian_predictions(
        test_observed,
        candidate_test_mean,
        candidate_sigma,
        interval_level=level,
    )
    baseline_score = score_gaussian_predictions(
        test_observed,
        baseline_test_mean,
        baseline_sigma,
        interval_level=level,
    )
    calibration_pass = abs(candidate_score.coverage - target) <= tolerance
    status: Literal["pass", "fail"] = "pass" if calibration_pass else "fail"
    if status == "pass" and candidate_score.mean_log_score > baseline_score.mean_log_score:
        result: Literal["promote", "demote", "defer"] = "promote"
    elif status == "pass":
        result = "demote"
    else:
        result = "defer"
    audit = CalibratedPredictionAudit(
        audit_id=audit_id,
        fit_data_id=fit_data_id,
        calibration_data_id=calibration_data_id,
        test_data_id=test_data_id,
        candidate_id=candidate_id,
        baseline_id=baseline_id,
        heldout_log_score=candidate_score.mean_log_score,
        baseline_heldout_log_score=baseline_score.mean_log_score,
        coverage=candidate_score.coverage,
        target_coverage=target,
        calibration_status=status,
        result=result,
        candidate_crps=candidate_score.mean_crps,
        baseline_crps=baseline_score.mean_crps,
        baseline_coverage=baseline_score.coverage,
        interval_level=level,
        coverage_tolerance=tolerance,
        sample_count=candidate_score.sample_count,
    )
    audit.validate()
    return audit


@dataclass(frozen=True, slots=True)
class BridgeProtocol:
    """A serializable, five-stage bridge record with no dynamic fields."""

    protocol_id: str
    status: Literal["local_unpromoted_successor_prototype"]
    conservation_contract: ConservationContract
    thermodynamic_ledger: ThermodynamicLedger
    equivalence_class: ObservationalEquivalenceClass
    intervention_design: InterventionDesign
    prediction_audit: CalibratedPredictionAudit
    intervention_options: tuple[InterventionOption, ...] = ()
    intervention_selection: InterventionSelection | None = None

    def validate(self) -> None:
        if not isinstance(self.protocol_id, str) or not self.protocol_id.strip():
            raise ValueError("protocol_id must be a nonempty string")
        if self.status != "local_unpromoted_successor_prototype":
            raise ValueError("unsupported bridge protocol status")
        self.conservation_contract.validate_structure()
        energy_tolerance = _finite_scalar("energy_tolerance", self.thermodynamic_ledger.energy_tolerance)
        entropy_tolerance = _finite_scalar("entropy_tolerance", self.thermodynamic_ledger.entropy_tolerance)
        if energy_tolerance < 0.0 or entropy_tolerance < 0.0:
            raise ValueError("ledger tolerances must be nonnegative")
        term_ids = []
        for term in self.thermodynamic_ledger.terms:
            term.validate()
            term_ids.append(term.term_id)
        if len(set(term_ids)) != len(term_ids):
            raise ValueError("thermodynamic term IDs must be unique")
        self.equivalence_class.validate()
        self.intervention_design.validate()
        option_ids: list[str] = []
        for option in self.intervention_options:
            option.validate()
            option_ids.append(option.option_id)
        if len(set(option_ids)) != len(option_ids):
            raise ValueError("intervention option IDs must be unique")
        if self.intervention_selection is not None:
            self.intervention_selection.validate()
            if self.intervention_selection.selected_option_id is not None and (
                self.intervention_selection.selected_option_id not in option_ids
            ):
                raise ValueError("selected intervention is absent from intervention_options")
        self.prediction_audit.validate()


def _term_to_dict(term: ThermodynamicTerm) -> dict[str, object]:
    return {
        "term_id": term.term_id,
        "source": term.source,
        "destination": term.destination,
        "process": term.process,
        "quantity": term.quantity,
        "units": term.units,
        "internal_or_external": term.internal_or_external,
        "energy_delta": term.energy_delta,
        "entropy_flow": term.entropy_flow,
        "entropy_production": term.entropy_production,
    }


def _option_to_dict(option: InterventionOption) -> dict[str, object]:
    return {
        "option_id": option.option_id,
        "control_ports": list(option.control_ports),
        "observation_ports": list(option.observation_ports),
        "cost": option.cost,
        "expected_minimum_separation": option.expected_minimum_separation,
        "safety_ok": option.safety_ok,
        "safety_reason": option.safety_reason,
        "utility_kind": option.utility_kind,
        "response_separation": option.response_separation,
        "fisher_separation": option.fisher_separation,
    }


def _selection_to_dict(selection: InterventionSelection) -> dict[str, object]:
    return {
        "selected_option_id": selection.selected_option_id,
        "total_cost": selection.total_cost,
        "expected_minimum_separation": selection.expected_minimum_separation,
        "feasible": selection.feasible,
        "considered_option_ids": list(selection.considered_option_ids),
        "rejected_option_ids": list(selection.rejected_option_ids),
    }


def protocol_to_dict(protocol: BridgeProtocol) -> dict[str, object]:
    """Convert a validated protocol to JSON-compatible deterministic data."""

    protocol.validate()
    payload: dict[str, object] = {
        "protocol_id": protocol.protocol_id,
        "status": protocol.status,
        "conservation_contract": {
            "state_units": list(protocol.conservation_contract.state_units),
            "incidence": protocol.conservation_contract.incidence.tolist(),
            "stoichiometry": protocol.conservation_contract.stoichiometry.tolist(),
            "conserved_weights": protocol.conservation_contract.conserved_weights.tolist(),
            "residual_tolerance": protocol.conservation_contract.residual_tolerance,
        },
        "thermodynamic_ledger": {
            "terms": [_term_to_dict(term) for term in protocol.thermodynamic_ledger.terms],
            "energy_tolerance": protocol.thermodynamic_ledger.energy_tolerance,
            "entropy_tolerance": protocol.thermodynamic_ledger.entropy_tolerance,
        },
        "equivalence_class": {
            "class_id": protocol.equivalence_class.class_id,
            "candidate_ids": list(protocol.equivalence_class.candidate_ids),
            "signature_kind": protocol.equivalence_class.signature_kind,
            "maximum_residual": protocol.equivalence_class.maximum_residual,
            "tolerance": protocol.equivalence_class.tolerance,
            "design_id": protocol.equivalence_class.design_id,
            "status": protocol.equivalence_class.status,
        },
        "intervention_design": {
            "design_id": protocol.intervention_design.design_id,
            "control_ports": list(protocol.intervention_design.control_ports),
            "observation_ports": list(protocol.intervention_design.observation_ports),
            "objective": protocol.intervention_design.objective,
            "budget": protocol.intervention_design.budget,
            "safety_constraints": list(protocol.intervention_design.safety_constraints),
            "expected_minimum_separation": protocol.intervention_design.expected_minimum_separation,
        },
        "prediction_audit": {
            "audit_id": protocol.prediction_audit.audit_id,
            "fit_data_id": protocol.prediction_audit.fit_data_id,
            "calibration_data_id": protocol.prediction_audit.calibration_data_id,
            "test_data_id": protocol.prediction_audit.test_data_id,
            "candidate_id": protocol.prediction_audit.candidate_id,
            "baseline_id": protocol.prediction_audit.baseline_id,
            "heldout_log_score": protocol.prediction_audit.heldout_log_score,
            "baseline_heldout_log_score": protocol.prediction_audit.baseline_heldout_log_score,
            "coverage": protocol.prediction_audit.coverage,
            "target_coverage": protocol.prediction_audit.target_coverage,
            "calibration_status": protocol.prediction_audit.calibration_status,
            "result": protocol.prediction_audit.result,
            "candidate_crps": protocol.prediction_audit.candidate_crps,
            "baseline_crps": protocol.prediction_audit.baseline_crps,
            "baseline_coverage": protocol.prediction_audit.baseline_coverage,
            "interval_level": protocol.prediction_audit.interval_level,
            "coverage_tolerance": protocol.prediction_audit.coverage_tolerance,
            "sample_count": protocol.prediction_audit.sample_count,
        },
    }
    if protocol.intervention_options:
        payload["intervention_options"] = [
            _option_to_dict(option) for option in protocol.intervention_options
        ]
    if protocol.intervention_selection is not None:
        payload["intervention_selection"] = _selection_to_dict(protocol.intervention_selection)
    return payload


def canonical_protocol_json(protocol: BridgeProtocol) -> str:
    """Return canonical UTF-8 JSON text with stable key ordering and LF."""

    return json.dumps(
        protocol_to_dict(protocol),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        separators=(",", ": "),
    ) + "\n"


def write_protocol_json(path: str | Path, protocol: BridgeProtocol) -> None:
    destination = Path(path)
    destination.write_text(canonical_protocol_json(protocol), encoding="utf-8", newline="\n")


def _tuple_strings(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be a JSON string array")
    return tuple(value)


def _assert_keys(payload: Mapping[str, object], allowed: set[str], name: str) -> None:
    if not all(isinstance(key, str) for key in payload):
        raise ValueError(f"{name} keys must be strings")
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(f"{name} contains unsupported fields: {sorted(unknown)}")


def protocol_from_dict(payload: Mapping[str, object]) -> BridgeProtocol:
    """Parse and validate a protocol payload without accepting dynamic fields."""

    _assert_keys(
        payload,
        {
            "protocol_id",
            "status",
            "conservation_contract",
            "thermodynamic_ledger",
            "equivalence_class",
            "intervention_design",
            "intervention_options",
            "intervention_selection",
            "prediction_audit",
        },
        "protocol",
    )
    conservation = payload["conservation_contract"]
    ledger = payload["thermodynamic_ledger"]
    equivalence = payload["equivalence_class"]
    design = payload["intervention_design"]
    prediction = payload["prediction_audit"]
    if not all(isinstance(value, Mapping) for value in (conservation, ledger, equivalence, design, prediction)):
        raise ValueError("protocol component records must be JSON objects")
    _assert_keys(
        conservation,
        {"state_units", "incidence", "stoichiometry", "conserved_weights", "residual_tolerance"},
        "conservation_contract",
    )
    _assert_keys(ledger, {"terms", "energy_tolerance", "entropy_tolerance"}, "thermodynamic_ledger")
    _assert_keys(
        equivalence,
        {"class_id", "candidate_ids", "signature_kind", "maximum_residual", "tolerance", "design_id", "status"},
        "equivalence_class",
    )
    _assert_keys(
        design,
        {"design_id", "control_ports", "observation_ports", "objective", "budget", "safety_constraints", "expected_minimum_separation"},
        "intervention_design",
    )
    _assert_keys(
        prediction,
        {
            "audit_id",
            "fit_data_id",
            "calibration_data_id",
            "test_data_id",
            "candidate_id",
            "baseline_id",
            "heldout_log_score",
            "baseline_heldout_log_score",
            "coverage",
            "target_coverage",
            "calibration_status",
            "result",
            "candidate_crps",
            "baseline_crps",
            "baseline_coverage",
            "interval_level",
            "coverage_tolerance",
            "sample_count",
        },
        "prediction_audit",
    )
    conservation = conservation  # type narrowing for runtime-compatible Python
    ledger = ledger
    equivalence = equivalence
    design = design
    prediction = prediction
    terms_payload = ledger["terms"]
    if not isinstance(terms_payload, list):
        raise ValueError("thermodynamic terms must be a JSON array")
    for term in terms_payload:
        if not isinstance(term, Mapping):
            raise ValueError("each thermodynamic term must be a JSON object")
        _assert_keys(
            term,
            {
                "term_id",
                "source",
                "destination",
                "process",
                "quantity",
                "units",
                "internal_or_external",
                "energy_delta",
                "entropy_flow",
                "entropy_production",
            },
            "thermodynamic_term",
        )
    terms = tuple(ThermodynamicTerm(**term) for term in terms_payload)
    options_payload = payload.get("intervention_options", [])
    if not isinstance(options_payload, list):
        raise ValueError("intervention_options must be a JSON array")
    for option in options_payload:
        if not isinstance(option, Mapping):
            raise ValueError("each intervention option must be a JSON object")
        _assert_keys(
            option,
            {
                "option_id",
                "control_ports",
                "observation_ports",
                "cost",
                "expected_minimum_separation",
                "safety_ok",
                "safety_reason",
                "utility_kind",
                "response_separation",
                "fisher_separation",
            },
            "intervention_option",
        )
    options = tuple(
        InterventionOption(
            option_id=option["option_id"],
            control_ports=_tuple_strings(option["control_ports"], "control_ports"),
            observation_ports=_tuple_strings(option["observation_ports"], "observation_ports"),
            cost=option["cost"],
            expected_minimum_separation=option["expected_minimum_separation"],
            safety_ok=option["safety_ok"],
            safety_reason=option.get("safety_reason", ""),
            utility_kind=option.get("utility_kind", "normalized_euclidean"),
            response_separation=option.get("response_separation"),
            fisher_separation=option.get("fisher_separation"),
        )
        for option in options_payload
    )
    selection_payload = payload.get("intervention_selection")
    selection = None
    if selection_payload is not None:
        if not isinstance(selection_payload, Mapping):
            raise ValueError("intervention_selection must be a JSON object")
        _assert_keys(
            selection_payload,
            {
                "selected_option_id",
                "total_cost",
                "expected_minimum_separation",
                "feasible",
                "considered_option_ids",
                "rejected_option_ids",
            },
            "intervention_selection",
        )
        selection = InterventionSelection(
            selected_option_id=selection_payload["selected_option_id"],
            total_cost=selection_payload["total_cost"],
            expected_minimum_separation=selection_payload["expected_minimum_separation"],
            feasible=selection_payload["feasible"],
            considered_option_ids=_tuple_strings(selection_payload["considered_option_ids"], "considered_option_ids"),
            rejected_option_ids=_tuple_strings(selection_payload["rejected_option_ids"], "rejected_option_ids"),
        )
    protocol = BridgeProtocol(
        protocol_id=payload["protocol_id"],
        status=payload["status"],
        conservation_contract=ConservationContract(
            incidence=np.asarray(conservation["incidence"], dtype=float),
            stoichiometry=np.asarray(conservation["stoichiometry"], dtype=float),
            conserved_weights=np.asarray(conservation["conserved_weights"], dtype=float),
            state_units=_tuple_strings(conservation["state_units"], "state_units"),
            residual_tolerance=conservation["residual_tolerance"],
        ),
        thermodynamic_ledger=ThermodynamicLedger(
            terms=terms,
            energy_tolerance=ledger["energy_tolerance"],
            entropy_tolerance=ledger["entropy_tolerance"],
        ),
        equivalence_class=ObservationalEquivalenceClass(
            class_id=equivalence["class_id"],
            candidate_ids=_tuple_strings(equivalence["candidate_ids"], "candidate_ids"),
            signature_kind=equivalence["signature_kind"],
            maximum_residual=equivalence["maximum_residual"],
            tolerance=equivalence["tolerance"],
            design_id=equivalence["design_id"],
            status=equivalence["status"],
        ),
        intervention_design=InterventionDesign(
            design_id=design["design_id"],
            control_ports=_tuple_strings(design["control_ports"], "control_ports"),
            observation_ports=_tuple_strings(design["observation_ports"], "observation_ports"),
            objective=design["objective"],
            budget=design["budget"],
            safety_constraints=_tuple_strings(design["safety_constraints"], "safety_constraints"),
            expected_minimum_separation=design["expected_minimum_separation"],
        ),
        prediction_audit=CalibratedPredictionAudit(
            audit_id=prediction["audit_id"],
            fit_data_id=prediction["fit_data_id"],
            calibration_data_id=prediction["calibration_data_id"],
            test_data_id=prediction["test_data_id"],
            candidate_id=prediction["candidate_id"],
            baseline_id=prediction["baseline_id"],
            heldout_log_score=prediction["heldout_log_score"],
            baseline_heldout_log_score=prediction["baseline_heldout_log_score"],
            coverage=prediction["coverage"],
            target_coverage=prediction["target_coverage"],
            calibration_status=prediction["calibration_status"],
            result=prediction["result"],
            candidate_crps=prediction.get("candidate_crps"),
            baseline_crps=prediction.get("baseline_crps"),
            baseline_coverage=prediction.get("baseline_coverage"),
            interval_level=prediction.get("interval_level", 0.9),
            coverage_tolerance=prediction.get("coverage_tolerance", 0.05),
            sample_count=prediction.get("sample_count"),
        ),
        intervention_options=options,
        intervention_selection=selection,
    )
    protocol.validate()
    return protocol


def read_protocol_json(path: str | Path) -> BridgeProtocol:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("protocol JSON root must be an object")
    return protocol_from_dict(payload)


def example_protocol() -> BridgeProtocol:
    """Return the deterministic example used by the round-trip tests."""

    option = intervention_option_from_signatures(
        option_id="surface-plus-deep",
        control_ports=("surface-input",),
        observation_ports=("surface-output", "deep-sensor"),
        cost=1.0,
        candidate_signatures={
            "candidate-a": [1.0, 0.0],
            "candidate-b": [1.2, 0.0],
        },
        safety_ok=True,
    )
    selection = select_intervention((option,), budget=1.0)
    protocol = BridgeProtocol(
        protocol_id="sppt-bridge-demo-v0.1.0",
        status="local_unpromoted_successor_prototype",
        conservation_contract=ConservationContract(
            incidence=np.array([[-1.0], [1.0]]),
            stoichiometry=np.zeros((1, 0)),
            conserved_weights=np.array([1.0]),
            state_units=("normalized_temperature",),
        ),
        thermodynamic_ledger=ThermodynamicLedger(
            terms=(
                ThermodynamicTerm(
                    term_id="internal-dissipation-1",
                    source="reservoir-edge",
                    destination="internal-state",
                    process="normalized-heat-transfer",
                    quantity="entropy-production",
                    units="normalized",
                    internal_or_external="internal",
                    energy_delta=0.0,
                    entropy_flow=0.0,
                    entropy_production=0.1,
                ),
            )
        ),
        equivalence_class=ObservationalEquivalenceClass(
            class_id="design-1:class-01",
            candidate_ids=("candidate-a", "candidate-b"),
            signature_kind="epsilon",
            maximum_residual=0.0,
            tolerance=1.0,
            design_id="design-1",
            status="equivalent",
        ),
        intervention_design=InterventionDesign(
            design_id="design-1",
            control_ports=("surface-input",),
            observation_ports=("surface-output", "deep-sensor"),
            objective="maximize minimum Fisher/separation utility",
            budget=1.0,
            safety_constraints=("conservation", "entropy", "bounded-input"),
            expected_minimum_separation=option.expected_minimum_separation,
        ),
        prediction_audit=CalibratedPredictionAudit(
            audit_id="prediction-audit-1",
            fit_data_id="fit-1",
            calibration_data_id="calibration-1",
            test_data_id="test-1",
            candidate_id="candidate-a",
            baseline_id="candidate-b",
            heldout_log_score=-0.8,
            baseline_heldout_log_score=-1.1,
            coverage=0.9,
            target_coverage=0.9,
            calibration_status="pass",
            result="promote",
            candidate_crps=0.08,
            baseline_crps=0.13,
            baseline_coverage=0.8,
            interval_level=0.9,
            coverage_tolerance=0.05,
            sample_count=20,
        ),
        intervention_options=(option,),
        intervention_selection=selection,
    )
    protocol.validate()
    return protocol
