from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


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
