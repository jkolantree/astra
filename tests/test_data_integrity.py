from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GRAPH_NAMES = {"chain", "triangle", "surface_star", "deep_star"}
N_STARTS = 20


def assert_start_diagnostics(graph: dict[str, object], n_parameters: int) -> None:
    starts = graph["starts"]
    assert isinstance(starts, list)
    assert len(starts) == N_STARTS
    assert [item["start_index"] for item in starts] == list(range(N_STARTS))
    assert len({tuple(item["start_log_conductance"]) for item in starts}) == N_STARTS
    assert all(len(item["start_log_conductance"]) == n_parameters for item in starts)
    assert all(len(item["endpoint_log_conductance"]) == n_parameters for item in starts)
    assert all(isinstance(item["solver_success"], bool) for item in starts)
    assert all(item["status"] == int(item["status"]) for item in starts)
    assert all(item["nfev"] >= 1 for item in starts)
    assert sum(item["accepted"] for item in starts) == graph["accepted_starts"]
    selected = starts[graph["best_start"]]
    assert selected["accepted"] is True
    assert selected["nfev"] == graph["selected_nfev"]
    assert selected["cost"] == graph["selected_cost"]
    assert selected["optimality"] == graph["selected_optimality"]
    assert selected["scaled_optimality"] == graph["selected_scaled_optimality"]
    assert selected["active_mask"] == graph["selected_active_mask"]


def test_ensemble_preserves_all_negative_outcomes_and_diagnostics() -> None:
    payload = json.loads((ROOT / "data" / "synthetic_topology_ensemble.json").read_text(encoding="utf-8"))
    results = payload["results"]
    assert payload["n_seeds"] == 64
    assert payload["winner_counts"] == {"chain": 64}
    assert payload["selection_basis"].startswith("training BIC only")
    assert payload["triangle_lower_heldout_rmse_count"] == 23
    assert payload["triangle_shortcut_lower_bound_count"] == 29
    assert payload["optimizer_all_graphs_converged"] is True
    assert min(item["optimizer_min_accepted_starts"] for item in results) >= 1
    assert max(item["optimizer_max_scaled_optimality"] for item in results) <= 1.0e-4
    assert payload["mean_chain_heldout_rmse"] == pytest.approx(2.4863949733879747e-4)
    assert payload["mean_triangle_heldout_rmse"] == pytest.approx(2.6968520904664016e-4)
    assert sum(
        len(graph["starts"])
        for result in results
        for graph in result["optimizer_diagnostics"].values()
    ) == 64 * 4 * N_STARTS
    for result in results:
        diagnostics = result["optimizer_diagnostics"]
        assert set(diagnostics) == GRAPH_NAMES
        assert_start_diagnostics(diagnostics["chain"], 2)
        assert_start_diagnostics(diagnostics["surface_star"], 2)
        assert_start_diagnostics(diagnostics["deep_star"], 2)
        assert_start_diagnostics(diagnostics["triangle"], 3)
        assert min(graph["accepted_starts"] for graph in diagnostics.values()) == result[
            "optimizer_min_accepted_starts"
        ]
        assert max(
            graph["selected_optimality"] for graph in diagnostics.values()
        ) == result["optimizer_max_optimality"]
        assert max(
            graph["selected_scaled_optimality"] for graph in diagnostics.values()
        ) == result["optimizer_max_scaled_optimality"]
    assert any(
        not start["accepted"]
        for result in results
        for graph in result["optimizer_diagnostics"].values()
        for start in graph["starts"]
    )


def test_csv_and_json_are_duplicate_serializations_not_independent_evidence() -> None:
    payload = json.loads((ROOT / "data" / "synthetic_topology_ensemble.json").read_text(encoding="utf-8"))
    with (ROOT / "data" / "synthetic_topology_ensemble.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(payload["results"]) == 64
    for row, record in zip(rows, payload["results"], strict=True):
        assert int(row["seed"]) == record["seed"]
        assert row["winner"] == record["winner"]
        assert json.loads(row["optimizer_diagnostics"]) == record["optimizer_diagnostics"]
        for field in (
            "chain_bic",
            "triangle_bic",
            "delta_bic_triangle_minus_chain",
            "chain_heldout_rmse",
            "triangle_heldout_rmse",
            "surface_star_heldout_rmse",
            "deep_star_heldout_rmse",
            "triangle_shortcut_conductance",
            "optimizer_max_optimality",
            "optimizer_max_scaled_optimality",
        ):
            assert float(row[field]) == record[field]


def test_single_seed_output_records_convergence_and_post_selection_loss() -> None:
    payload = json.loads(
        (ROOT / "data" / "synthetic_topology_benchmark.json").read_text(encoding="utf-8")
    )
    records = payload["fits_ranked_by_bic"]
    assert records[0]["graph"] == "chain"
    chain = next(item for item in records if item["graph"] == "chain")
    triangle = next(item for item in records if item["graph"] == "triangle")
    assert triangle["heldout_rmse"] < chain["heldout_rmse"]
    assert all(item["optimizer_accepted"] >= 1 for item in records)
    assert all(item["optimizer_scaled_optimality"] <= 1.0e-4 for item in records)
    assert sum(len(item["optimizer_diagnostics"]) for item in records) == 4 * N_STARTS
    assert any(
        not diagnostic["accepted"]
        for item in records
        for diagnostic in item["optimizer_diagnostics"]
    )
    with (ROOT / "data" / "synthetic_topology_benchmark.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        csv_records = {row["graph"]: row for row in csv.DictReader(handle)}
    for record in records:
        diagnostics = record["optimizer_diagnostics"]
        assert len(diagnostics) == N_STARTS
        assert [item["start_index"] for item in diagnostics] == list(range(N_STARTS))
        assert len({tuple(item["start_log_conductance"]) for item in diagnostics}) == N_STARTS
        assert sum(item["accepted"] for item in diagnostics) == record["optimizer_accepted"]
        assert diagnostics[record["optimizer_best_start"]]["accepted"] is True
        assert json.loads(csv_records[record["graph"]]["optimizer_diagnostics"]) == diagnostics
