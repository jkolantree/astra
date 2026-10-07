"""One synthetic integration fixture, not an empirical forward model."""

import argparse
import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import expm

import astra_layers
import astra_reservoir
import boundary_state
import coupling_state
import sppt_core
from astra_layers import EdgeType
from core_contracts import (
    CalibrationDeclaration,
    Quantity,
    StageContract,
    observe_mass,
    scalar,
)
from research_candidate import QuantityType

FIELDS = {
    "case_id",
    "times_s",
    "initial_mass_kg",
    "conductance_per_s",
    "capture_fraction",
    "reference_mass_kg",
    "boundary",
    "channel",
    "detector_count_per_kg",
    "efficiency",
    "reset_after_intervals",
    "archive_retention",
    "calibration",
}


def validate_case(
    record: object,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    float,
    boundary_state.LinearBoundaryParameters,
    coupling_state.StatefulChannelParameters,
    CalibrationDeclaration,
]:
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise ValueError("Exact synthetic case fields required")
    if not isinstance(record["case_id"], str) or not record["case_id"].startswith("synthetic:"):
        raise ValueError("This adapter admits synthetic cases only")
    if not isinstance(record["times_s"], list) or not 3 <= len(record["times_s"]) <= 129:
        raise ValueError("Three to 129 explicit time samples required")
    times = np.array([scalar(x, "time", minimum=0) for x in record["times_s"]])
    if times[0] != 0 or np.any(np.diff(times) <= 0):
        raise ValueError("Strictly increasing times starting at zero required")
    if not np.allclose(np.diff(times), times[1], rtol=1e-12, atol=0):
        raise ValueError("Discrete channel requires a uniform exposure grid")
    mass = record["initial_mass_kg"]
    if not isinstance(mass, list) or len(mass) != 2:
        raise ValueError("This fixture requires exactly two tracer reservoirs")
    mass = np.array([scalar(x, "initial mass", minimum=0) for x in mass])
    if not np.isfinite(mass.sum()) or mass.sum() <= 0:
        raise ValueError("Finite positive total tracer mass required")
    conductance = scalar(record["conductance_per_s"], "conductance", minimum=0)
    scalar(record["capture_fraction"], "capture fraction", minimum=0, maximum=1)
    if scalar(record["reference_mass_kg"], "reference mass", minimum=0) == 0:
        raise ValueError("Positive reference mass required")
    scalar(record["detector_count_per_kg"], "response", minimum=0)
    if record["efficiency"] is not None:
        scalar(record["efficiency"], "efficiency", minimum=0, maximum=1)
    scalar(record["archive_retention"], "retention", minimum=0, maximum=1)
    reset = record["reset_after_intervals"]
    if isinstance(reset, bool) or not isinstance(reset, int) or not 1 <= reset <= len(times) - 1:
        raise ValueError("Reset must follow a represented complete interval")
    keys = {"bulk_decay", "boundary_to_bulk", "direct_gain", "boundary_drive", "boundary_time"}
    if not isinstance(record["boundary"], dict) or set(record["boundary"]) != keys:
        raise ValueError("Exact boundary parameters required")
    boundary = {k: scalar(v, "boundary " + k, minimum=0) for k, v in record["boundary"].items()}
    p = boundary_state.LinearBoundaryParameters(**boundary)
    p.validate()
    keys = {"persistence", "drive", "direct_gain", "memory_gain", "interaction_gain", "offset"}
    if not isinstance(record["channel"], dict) or set(record["channel"]) != keys:
        raise ValueError("Exact channel parameters required")
    channel = {k: scalar(v, "channel " + k, minimum=0) for k, v in record["channel"].items()}
    q = coupling_state.StatefulChannelParameters(**channel)
    q.validate()
    cal = CalibrationDeclaration.from_mapping(record["calibration"])
    if cal.unit != "count/kg":
        raise ValueError("Declared detector calibration unit must be count/kg")
    return times, mass, conductance, p, q, cal


def build_contracts() -> list[StageContract]:
    mass = QuantityType("captured", "tracer-mass", "kg", ("tracer",))
    boundary = QuantityType("boundary", "normalized-context", "1", ("bulk", "boundary"))
    channel = QuantityType("channel", "normalized-context", "1", ("gain",))
    counts = QuantityType("detector", "expected-count", "count", ("tracer",))
    archive = QuantityType("archive", "expected-retained-record", "record-equivalent", ("stock",))
    return [
        StageContract(
            "boundary-drive",
            EdgeType.CONTROL,
            mass,
            boundary,
            "Explicit normalization by reference mass drives a synthetic boundary model",
            "synthetic:linear-boundary",
            ("Gamma:C6",),
        ),
        StageContract(
            "stateful-channel",
            EdgeType.OBSERVATION,
            boundary,
            channel,
            "Bulk component drives a declared discrete context channel",
            "synthetic:stateful-channel",
            ("Xi:C4",),
        ),
        StageContract(
            "detector",
            EdgeType.OBSERVATION,
            mass,
            counts,
            "Context modulates expected detector response; no physical mass removal",
            "synthetic:first-moment",
            ("october_framework:RI001",),
            context_type=channel,
        ),
        StageContract(
            "record-retention",
            EdgeType.ARCHIVE,
            counts,
            archive,
            "One expected count maps to one expected record-equivalent per bin, then retention reset",
            "synthetic:record-ledger",
            ("Layers:C-05",),
        ),
        StageContract(
            "validation-receipt",
            EdgeType.CERTIFICATE,
            archive,
            archive,
            "Finite mass and record ledger controls only",
            "synthetic:engineering-checks",
            ("Layers:C-06",),
            ("mass-accounting", "record-accounting"),
        ),
    ]


def run_case(record: dict[str, Any]) -> dict[str, Any]:
    times, initial, conductance, boundary_p, channel_p, calibration = validate_case(record)
    edge = astra_reservoir.Edge(0, 1, conductance)
    _, _, _, generator = astra_reservoir.system_matrices([1.0, 1.0], [edge], [0.0, 0.0])
    transported = np.array([expm(generator * t) @ initial for t in times])
    if not np.all(np.isfinite(transported)) or np.any(transported < 0):
        raise ValueError("Transport left the finite nonnegative inventory domain")
    incidence = sppt_core.incidence_matrix(2, [(0, 1)])
    tendency_errors, inventory_rates = [], []
    for mass in transported:
        flux = conductance * (mass[0] - mass[1])
        tendency = sppt_core.species_tendency(
            incidence,
            [[flux]],
            np.empty((2, 0)),
            np.empty((1, 0)),
            np.zeros((2, 1)),
            np.zeros((2, 1)),
        )
        tendency_errors.append(float(np.max(np.abs(tendency[:, 0] - generator @ mass))))
        inventory_rates.append(sppt_core.weighted_inventory_tendency(tendency, [1.0]))
    # Preparation ends before exposure time starts; capture moves mass into a separate compartment.
    contracts = build_contracts()
    # An available sample of volume 1 m^3 fixes concentration numerically to its mass;
    # capturing capture_fraction m^3 moves that fraction into a separate compartment.
    captured_kg = float(transported[-1, 1]) * record["capture_fraction"]
    reset = boundary_state.compartment_closure_reset(
        float(transported[-1, 1]), record["capture_fraction"], float(transported[-1, 1])
    )
    captured = Quantity(QuantityType("captured", "tracer-mass", "kg", ("tracer",)), (captured_kg,))
    contracts[0].accept(captured)
    contracts[2].accept(captured)
    drive = captured_kg / record["reference_mass_kg"]
    scalar(drive, "normalized boundary drive", minimum=0)
    boundary = boundary_state.exact_linear_step(times, boundary_p, step_amplitude=drive)
    if not np.all(np.isfinite(boundary)) or np.any(boundary < -1e-12):
        raise ValueError("Boundary output outside declared nonnegative context domain")
    # Remove only insignificant cancellation at t=0; no physical inventory is clipped.
    boundary = np.maximum(boundary, 0.0)
    for column in boundary.T:
        contracts[1].accept(Quantity(contracts[0].output_type, tuple(map(float, column))))
    memory, context = coupling_state.simulate_stateful_channel(boundary[0, :-1], channel_p)
    if not np.all(np.isfinite(context)) or np.any(context < 0) or not np.all(np.isfinite(memory)):
        raise ValueError("Context output outside finite nonnegative domain")
    observations = []
    for gain in context:
        produced_context = Quantity(contracts[1].output_type, (float(gain),))
        contracts[2].accept_context(produced_context)
        efficiency = (
            None
            if record["efficiency"] is None
            else record["efficiency"] / (1.0 + produced_context.values[0])
        )
        observed = observe_mass(captured, record["detector_count_per_kg"], efficiency=efficiency)
        if (
            observed.get("empirical_admission") is not False
            or observed.get("no_record_probability") is not None
        ):
            raise ValueError("Detector cannot supply empirical admission or no-record likelihood")
        if record["efficiency"] is None:
            if (
                observed.get("status") != "unavailable-response"
                or observed.get("expected_counts") is not None
            ):
                raise ValueError("Unknown response cannot become a count prediction")
        else:
            if observed.get("status") != "first-moment-only":
                raise ValueError("Expected a first-moment observation record")
            actual_output = Quantity.from_fields(
                observed.get("output_type"), observed.get("expected_counts")
            )
            contracts[3].accept(actual_output)
        observations.append(observed)
    counts = (
        None if record["efficiency"] is None else [sum(o["expected_counts"]) for o in observations]
    )
    stock = erased = 0.0
    trace = [0.0]
    if counts is not None:
        for i, count in enumerate(counts):
            dt = float(times[i + 1] - times[i])
            stock = float(
                astra_layers.archive_state([0.0, dt], [count / dt, 0.0], [0.0, 0.0], initial=stock)[
                    -1
                ]
            )
            if i + 1 == record["reset_after_intervals"]:
                removed = stock * (1.0 - record["archive_retention"])
                erased += removed
                stock -= removed
            trace.append(stock)
        residual = sum(counts) - stock - erased
        if not all(np.isfinite(x) for x in [stock, erased, residual]) or abs(
            residual
        ) > 1e-10 * max(1.0, sum(counts)):
            raise ValueError("Archive record balance failed")
        archive_report = {
            "stock": stock,
            "erased": erased,
            "expected_input_records": sum(counts),
            "balance_residual": residual,
            "trace": trace,
            "unit": "expected record-equivalent",
            "physical_mass_kg": None,
        }
        contracts[4].accept(Quantity(contracts[3].output_type, (stock,)))
    else:
        archive_report = {
            "stock": None,
            "erased": None,
            "expected_input_records": None,
            "balance_residual": None,
            "trace": None,
            "unit": "expected record-equivalent",
            "physical_mass_kg": None,
        }
    mass_residual = float(
        transported[-1, 0] + reset.external_after + reset.captured_after - initial.sum()
    )
    if abs(mass_residual) > 1e-10 * max(1.0, float(initial.sum())) or max(tendency_errors) > 1e-10:
        raise ValueError("Common physical inventory contract failed")
    graph = astra_layers.LayeredGraph(
        nodes={"bulk", "sample", "boundary", "channel", "detector", "archive"},
        edges=[
            astra_layers.TypedEdge(
                "bulk", "sample", EdgeType.PHYSICAL, "conservative tracer exchange", "kg/s"
            ),
            astra_layers.TypedEdge(
                "sample", "boundary", EdgeType.CONTROL, "normalized synthetic boundary drive"
            ),
            astra_layers.TypedEdge("boundary", "channel", EdgeType.OBSERVATION, "stateful context"),
            astra_layers.TypedEdge(
                "channel", "detector", EdgeType.OBSERVATION, "context-modulated response"
            ),
            astra_layers.TypedEdge("detector", "archive", EdgeType.ARCHIVE, "record retention"),
        ],
    )
    graph.validate()
    return {
        "case_id": record["case_id"],
        "status": "COMPLETED_SYNTHETIC" if counts is not None else "INCOMPLETE_OBSERVATION",
        "synthetic": True,
        "empirical_admission": False,
        "core_release_promoted": False,
        "transport": {
            "times_s": times.tolist(),
            "mass_kg": transported.tolist(),
            "mass_closure_residual_kg": mass_residual,
            "sppt_generator_max_residual": max(tendency_errors),
            "inventory_tendency_kg_s": inventory_rates,
        },
        "capture": asdict(reset),
        "exposure_times_s": times.tolist(),
        "boundary_context": boundary.tolist(),
        "channel_memory": memory.tolist(),
        "channel_context": context.tolist(),
        "observations": observations,
        "archive": archive_report,
        "calibration": calibration.assessment(),
        "contracts": [asdict(x) for x in contracts],
        "physical_edge_count": len(graph.by_type(EdgeType.PHYSICAL)),
        "scope": "Two synthetic preparation reservoirs; exposure after preparation; first moments and expected record ledger only. No observation likelihood, empirical calibration or common SCM/planetary dynamics.",
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    # Exclusive creation prevents accidental source overwrite and stale report reuse.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump({"status": "RUNNING"}, stream)
        stream.flush()
        result = run_case(json.loads(args.case.read_text()))
        result["case_sha256"] = hashlib.sha256(args.case.read_bytes()).hexdigest()
        stream.seek(0)
        stream.truncate()
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "empirical_admission": False}))


if __name__ == "__main__":
    main()
