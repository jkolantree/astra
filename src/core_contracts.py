"""Integrated development core contracts; declarations confer no empirical status."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any, Never

from numpy.typing import ArrayLike

from astra_layers import EdgeType
from research_candidate import Operator, QuantityType, forward_chain


def scalar(
    value: object, name: str, *, minimum: float | None = None, maximum: float | None = None
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(name + " must be a finite real scalar")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(name + " outside declared domain")
    return float(value)


def quantity_type(value: object) -> QuantityType:
    if not isinstance(value, QuantityType) or not isinstance(value.basis, tuple):
        raise ValueError("Explicit immutable QuantityType required")
    value.validate()
    return value


@dataclass(frozen=True)
class Quantity:
    type: QuantityType
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        quantity_type(self.type)
        if not isinstance(self.values, tuple) or len(self.values) != len(self.type.basis):
            raise ValueError("Values must match the ordered named basis")
        for value in self.values:
            scalar(value, "quantity value")
            if (
                self.type.quantity in {"tracer-mass", "expected-count", "expected-retained-record"}
                and value < 0
            ):
                raise ValueError(
                    "Inventory, expected count and expected record quantities cannot be negative"
                )

    @classmethod
    def from_fields(cls, type_fields: object, values: object) -> Quantity:
        if not isinstance(type_fields, dict) or set(type_fields) != {
            "space",
            "quantity",
            "unit",
            "basis",
        }:
            raise ValueError("Producer must supply exact quantity type fields")
        if not isinstance(type_fields["basis"], list) or not isinstance(values, list):
            raise ValueError("Producer coordinates and ordered basis must be lists")
        fields = dict(type_fields)
        fields["basis"] = tuple(fields["basis"])
        return cls(QuantityType(**fields), tuple(values))


@dataclass(frozen=True)
class StageContract:
    stage_id: str
    edge_type: EdgeType
    input_type: QuantityType
    output_type: QuantityType
    mechanism: str
    model_id: str
    source_claim_keys: tuple[str, ...]
    failure_scope: tuple[str, ...] = ()
    context_type: QuantityType | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_type", EdgeType(self.edge_type))
        quantity_type(self.input_type)
        quantity_type(self.output_type)
        if self.context_type is not None:
            quantity_type(self.context_type)
        if any(
            not isinstance(v, str) or not v.strip()
            for v in (self.stage_id, self.mechanism, self.model_id)
        ):
            raise ValueError("Stage identity, mechanism and model must be explicit")
        if (
            not isinstance(self.source_claim_keys, tuple)
            or not self.source_claim_keys
            or any(not isinstance(v, str) or ":" not in v for v in self.source_claim_keys)
        ):
            raise ValueError("Source-local namespaced claim keys required")
        if self.edge_type is EdgeType.PHYSICAL and (
            self.input_type.quantity != self.output_type.quantity
            or self.input_type.unit != self.output_type.unit
        ):
            raise ValueError(
                "A physical transport contract cannot cast conserved quantities or units"
            )
        if not isinstance(self.failure_scope, tuple) or any(
            not isinstance(x, str) or not x.strip() for x in self.failure_scope
        ):
            raise ValueError("Failure scopes must be explicit immutable strings")
        if self.edge_type is EdgeType.CERTIFICATE and not self.failure_scope:
            raise ValueError("Certificate must declare the failures it tests")

    def accept(self, value: object) -> None:
        if not isinstance(value, Quantity) or value.type != self.input_type:
            raise ValueError(
                "Space, quantity, unit and ordered basis must match the input contract"
            )

    def accept_context(self, value: object) -> None:
        if (
            self.context_type is None
            or not isinstance(value, Quantity)
            or value.type != self.context_type
        ):
            raise ValueError("Context input must match its explicit quantity contract")


def compose(first: StageContract, second: StageContract) -> tuple[QuantityType, QuantityType]:
    if first.output_type != second.input_type:
        raise ValueError("Composition requires equal space, quantity, unit and ordered basis")
    return first.input_type, second.output_type


@dataclass(frozen=True)
class CalibrationDeclaration:
    status: str
    artifact_sha256s: tuple[str, ...]
    training_root: str
    calibration_root: str
    holdout_root: str
    unit: str

    def __post_init__(self) -> None:
        if self.status not in ("planned", "declared-verified"):
            raise ValueError("Only planned or declared-verified calibration is represented")
        if not isinstance(self.artifact_sha256s, tuple) or any(
            not isinstance(v, str) or re.fullmatch("[0-9a-f]{64}", v) is None
            for v in self.artifact_sha256s
        ):
            raise ValueError("Artifact identities must be SHA256 declarations")
        if self.status == "declared-verified" and not self.artifact_sha256s:
            raise ValueError("A declared verification needs declared artifact identities")
        roots = (self.training_root, self.calibration_root, self.holdout_root)
        if any(not isinstance(v, str) or not v.strip() for v in roots) or len(set(roots)) != 3:
            raise ValueError("Three distinct explicit root declarations required")
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("Calibration unit required")

    @classmethod
    def from_mapping(cls, record: object) -> CalibrationDeclaration:
        expected = {
            "status",
            "artifact_sha256s",
            "training_root",
            "calibration_root",
            "holdout_root",
            "unit",
        }
        if (
            not isinstance(record, Mapping)
            or set(record) != expected
            or not isinstance(record["artifact_sha256s"], list)
        ):
            raise ValueError("Exact declaration fields and hash list required")
        values = dict(record)
        values["artifact_sha256s"] = tuple(values["artifact_sha256s"])
        return cls(**values)

    def assessment(self) -> dict[str, bool | str]:
        return {
            "declaration_valid": True,
            "calibration_declared": self.status == "declared-verified",
            "calibration_ready": False,
            "empirical_admission": False,
            "readiness_status": "not-assessed-declaration-only",
            "artifact_bytes_resolved": False,
            "split_provenance_authenticated": False,
        }


class ObservationStatus(StrEnum):
    # Preserve the earlier public str/format behavior while using the modern base.
    __str__ = Enum.__str__
    __format__ = Enum.__format__

    FIRST_MOMENT = "first-moment-only"
    UNKNOWN_RESPONSE = "unavailable-response"


def observe_mass(
    mass: object, response_count_per_kg: object, *, efficiency: object
) -> dict[str, Any]:
    if (
        not isinstance(mass, Quantity)
        or mass.type.quantity != "tracer-mass"
        or mass.type.unit != "kg"
    ):
        raise ValueError("Detector requires typed tracer mass in kg")
    if any(v < 0 for v in mass.values):
        raise ValueError("Detector mass must be nonnegative")
    response = scalar(response_count_per_kg, "response", minimum=0)
    if efficiency is None:
        return {
            "status": ObservationStatus.UNKNOWN_RESPONSE.value,
            "expected_counts": None,
            "normalized_count_response": None,
            "no_record_probability": None,
            "reason": "Efficiency is unknown, not zero",
            "empirical_admission": False,
        }
    efficiency = scalar(efficiency, "efficiency", minimum=0, maximum=1)
    output = QuantityType("detector", "expected-count", "count", mass.type.basis)
    gain = response * efficiency
    scalar(gain, "effective response", minimum=0)
    matrix = tuple(
        tuple(gain if i == j else 0.0 for j in range(len(mass.values)))
        for i in range(len(mass.values))
    )
    operator = Operator(
        "synthetic:detector",
        mass.type,
        output,
        "observation",
        "detector-response",
        matrix,
        "synthetic:declared-response",
    )
    if sum(mass.values) == 0:
        counts = [0.0] * len(mass.values)
        normalized = None
    else:
        report = forward_chain(mass.values, [operator])
        counts, normalized = report["expected_counts"], report["normalized_count_response"]
    return {
        "status": ObservationStatus.FIRST_MOMENT.value,
        "expected_counts": counts,
        "normalized_count_response": normalized,
        "no_record_probability": None,
        "empirical_admission": False,
        "output_type": {
            "space": output.space,
            "quantity": output.quantity,
            "unit": output.unit,
            "basis": list(output.basis),
        },
    }


def observation_likelihood(observation: object, outcome: object) -> Never:
    raise NotImplementedError(
        "First moments provide no count/no-record or correlated-daughter likelihood"
    )


def exclusion_from_null(observation: object) -> Never:
    raise NotImplementedError(
        "A null exclusion requires an explicit justified likelihood and nonzero candidate response"
    )


def finite_reduction_diagnostics(
    transition: ArrayLike, groups: object, outputs: object
) -> dict[str, bool | float | str]:
    """Finite-chain algebra only; separate lumpability from immediate output sufficiency."""
    import numpy as np

    matrix = np.asarray(transition, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("A finite nonempty square transition matrix is required")
    n = matrix.shape[0]
    if (
        not np.all(np.isfinite(matrix))
        or np.any(matrix < 0)
        or not np.allclose(matrix.sum(axis=1), 1, atol=1e-12, rtol=0)
    ):
        raise ValueError("A nonnegative row-stochastic transition matrix is required")
    if (
        not isinstance(groups, (list, tuple))
        or len(groups) != n
        or any(type(g) is not int or g < 0 for g in groups)
    ):
        raise ValueError("One nonnegative integer group per full state is required")
    if not isinstance(outputs, (list, tuple)) or len(outputs) != n:
        raise ValueError("One scalar deterministic output per full state is required")
    observed = [scalar(x, "declared output") for x in outputs]
    lumpable = output_constant = True
    unique = sorted(set(groups))
    aggregate = np.array(
        [[sum(matrix[i, j] for j in range(n) if groups[j] == g) for g in unique] for i in range(n)]
    )
    for group in unique:
        indices = [i for i, g in enumerate(groups) if g == group]
        lumpable = lumpable and bool(
            np.allclose(aggregate[indices], aggregate[indices[0]], atol=1e-12, rtol=0)
        )
        output_constant = output_constant and all(
            observed[i] == observed[indices[0]] for i in indices
        )
    return {
        "strong_lumpability_at_tolerance": lumpable,
        "row_probability_tolerance": 1e-12,
        "instantaneous_declared_output_constant_on_fibers": output_constant,
        "scope": "Specified finite transition matrix and scalar deterministic outputs only; no generic necessity claim for output sufficiency.",
    }


def first_order_rank(jacobian_blocks: object) -> dict[str, int | str]:
    import numpy as np

    from coupling_state import local_sensitivity_rank

    if not isinstance(jacobian_blocks, (list, tuple)) or not jacobian_blocks:
        raise ValueError("Nonempty declared Jacobian blocks required")
    blocks = [np.asarray(x, dtype=float) for x in jacobian_blocks]
    if any(x.ndim != 2 or 0 in x.shape or not np.all(np.isfinite(x)) for x in blocks):
        raise ValueError("Finite nonempty two-dimensional Jacobian blocks required")
    if any(x.shape[1] != blocks[0].shape[1] for x in blocks):
        raise ValueError("Parameter columns must agree")
    return {
        "first_order_numerical_rank": local_sensitivity_rank(blocks),
        "nonlinear_local_identifiability": "not-assessed",
        "global_identifiability": "not-assessed",
        "scope": "Rank is a first-order sensitivity diagnostic only; singular injective maps may have zero rank.",
    }
