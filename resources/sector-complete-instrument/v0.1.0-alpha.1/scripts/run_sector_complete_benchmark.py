#!/usr/bin/env python3
"""Run the frozen ASTRA sector-complete synthetic benchmark."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import astra_sector_complete as sci  # noqa: E402

SEED = 20260807
SAMPLES_PER_GENERATOR = 600
CLASSIFICATION_REPLICATES = 400
DETECTOR_ERROR = 0.02


def save_matrix_csv(path: Path, row_labels: tuple[str, ...], col_labels: tuple[str, ...], matrix: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["outcome"] + list(col_labels))
        for label, row in zip(row_labels, matrix, strict=True):
            writer.writerow([label] + [f"{float(value):.12g}" for value in row])


def save_heatmap(path_stem: Path, row_labels: tuple[str, ...], col_labels: tuple[str, ...], matrix: np.ndarray, title: str) -> None:
    fig = plt.figure(figsize=(7.4, 4.8))
    ax = fig.add_subplot(111)
    image = ax.imshow(matrix, aspect="auto", vmin=0.0, vmax=1.0)
    ax.set_xticks(np.arange(len(col_labels)), labels=[label.replace("_", "\n") for label in col_labels])
    ax.set_yticks(np.arange(len(row_labels)), labels=[label.replace("_", " ") for label in row_labels])
    ax.set_xlabel("candidate generator")
    ax.set_ylabel("observed outcome")
    ax.set_title(title)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center")
    fig.colorbar(image, ax=ax, label="conditional probability")
    fig.tight_layout()
    fig.savefig(path_stem.with_suffix(".png"), dpi=300)
    plt.close(fig)


def save_eigenvalue_plot(path_stem: Path, local_values: np.ndarray, complete_values: np.ndarray) -> None:
    fig = plt.figure(figsize=(7.0, 4.5))
    ax = fig.add_subplot(111)
    x = np.arange(1, 4)
    width = 0.35
    ax.bar(x - width / 2, local_values, width, label="local observation")
    ax.bar(x + width / 2, complete_values, width, label="sector-complete observation")
    ax.set_yscale("symlog", linthresh=1e-6)
    ax.set_xlabel("ordered Fisher eigenvalue")
    ax.set_ylabel("eigenvalue (samples = 1000)")
    ax.set_title("Sector coverage removes the local Fisher null direction")
    ax.set_xticks(x)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path_stem.with_suffix(".png"), dpi=300)
    plt.close(fig)


def save_line_plot(path_stem: Path, x: np.ndarray, ys: list[tuple[str, np.ndarray]], xlabel: str, ylabel: str, title: str) -> None:
    fig = plt.figure(figsize=(7.0, 4.5))
    ax = fig.add_subplot(111)
    for label, y in ys:
        ax.plot(x, y, label=label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if len(ys) > 1:
        ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path_stem.with_suffix(".png"), dpi=300)
    plt.close(fig)


def classification_confusion(
    response: np.ndarray,
    rng: np.random.Generator,
    samples: int,
    replicates: int,
) -> np.ndarray:
    n = response.shape[1]
    confusion = np.zeros((n, n), dtype=int)
    for true_idx in range(n):
        for _ in range(replicates):
            counts = sci.sample_counts(response[:, true_idx], samples, rng)
            _, scores = sci.classify_pure_generator(counts, response, sci.GENERATOR_ORDER)
            ties = np.flatnonzero(np.isclose(scores, scores.max(), atol=1e-12, rtol=0.0))
            pred_idx = int(rng.choice(ties))
            confusion[pred_idx, true_idx] += 1
    return confusion


def save_confusion_plot(path_stem: Path, confusion: np.ndarray, title: str) -> None:
    normalized = confusion / confusion.sum(axis=0, keepdims=True)
    fig = plt.figure(figsize=(6.6, 5.1))
    ax = fig.add_subplot(111)
    image = ax.imshow(normalized, vmin=0.0, vmax=1.0)
    labels = [label.replace("_", "\n") for label in sci.GENERATOR_ORDER]
    ax.set_xticks(np.arange(4), labels=labels)
    ax.set_yticks(np.arange(4), labels=labels)
    ax.set_xlabel("true generator")
    ax.set_ylabel("classified generator")
    ax.set_title(title)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{normalized[i, j]:.2f}", ha="center", va="center")
    fig.colorbar(image, ax=ax, label="classification fraction")
    fig.tight_layout()
    fig.savefig(path_stem.with_suffix(".png"), dpi=300)
    plt.close(fig)


def main() -> None:
    data_dir = ROOT / "data"
    figures_dir = ROOT / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    local_labels, generators, local_ideal = sci.response_matrix(sci.local_povm())
    complete_labels, _, complete_ideal = sci.response_matrix(sci.sector_complete_povm())

    local_confusion = sci.symmetric_confusion_matrix(len(local_labels), DETECTOR_ERROR)
    complete_confusion = sci.symmetric_confusion_matrix(len(complete_labels), DETECTOR_ERROR)
    local_noisy = sci.apply_detector_confusion(local_ideal, local_confusion)
    complete_noisy = sci.apply_detector_confusion(complete_ideal, complete_confusion)

    local_classes = sci.exact_equivalence_classes(local_ideal, generators)
    complete_classes = sci.exact_equivalence_classes(complete_ideal, generators)

    fisher_local = sci.mixture_fisher_information(local_noisy, samples=1000)
    fisher_complete = sci.mixture_fisher_information(complete_noisy, samples=1000)
    eig_local = np.sort(np.linalg.eigvalsh(fisher_local))
    eig_complete = np.sort(np.linalg.eigvalsh(fisher_complete))

    mi_local_ideal = sci.mutual_information_uniform(local_ideal)
    mi_complete_ideal = sci.mutual_information_uniform(complete_ideal)
    mi_local_noisy = sci.mutual_information_uniform(local_noisy)
    mi_complete_noisy = sci.mutual_information_uniform(complete_noisy)

    rng = np.random.default_rng(SEED)
    confusion_local_counts = classification_confusion(
        local_noisy, rng, SAMPLES_PER_GENERATOR, CLASSIFICATION_REPLICATES
    )
    confusion_complete_counts = classification_confusion(
        complete_noisy, rng, SAMPLES_PER_GENERATOR, CLASSIFICATION_REPLICATES
    )
    local_accuracy = float(np.trace(confusion_local_counts) / confusion_local_counts.sum())
    complete_accuracy = float(np.trace(confusion_complete_counts) / confusion_complete_counts.sum())

    noise_grid = np.linspace(0.0, 0.40, 41)
    mi_noise_local: list[float] = []
    mi_noise_complete: list[float] = []
    for error in noise_grid:
        local_at_error = sci.apply_detector_confusion(
            local_ideal, sci.symmetric_confusion_matrix(len(local_labels), float(error))
        )
        complete_at_error = sci.apply_detector_confusion(
            complete_ideal, sci.symmetric_confusion_matrix(len(complete_labels), float(error))
        )
        mi_noise_local.append(sci.mutual_information_uniform(local_at_error))
        mi_noise_complete.append(sci.mutual_information_uniform(complete_at_error))

    lengths = np.linspace(0.0, 6.0, 61)
    finite_tv: list[float] = []
    finite_string_probability: list[float] = []
    for length in lengths:
        _, p = sci.measurement_probabilities(sci.finite_boundary_state(float(length)), sci.sector_complete_povm())
        _, p_absorb = sci.measurement_probabilities(sci.output_state("absorb"), sci.sector_complete_povm())
        finite_tv.append(float(0.5 * np.sum(np.abs(p - p_absorb))))
        finite_string_probability.append(float(p[complete_labels.index("string_sector")]))

    deltas = np.linspace(0.0, 0.40, 41)
    broken_reflect_probability: list[float] = []
    broken_string_probability: list[float] = []
    for delta in deltas:
        _, p = sci.measurement_probabilities(sci.broken_duality_state(float(delta)), sci.sector_complete_povm())
        broken_reflect_probability.append(float(p[complete_labels.index("left_local")]))
        broken_string_probability.append(float(p[complete_labels.index("string_sector")]))

    # Out-of-set model mismatch: a hybrid output is compared with four pure candidates.
    hybrid_weights = np.array([0.10, 0.20, 0.25, 0.45], dtype=float)
    hybrid_p = complete_noisy @ hybrid_weights
    mismatch_samples = 5000
    mismatch_counts = sci.sample_counts(hybrid_p, mismatch_samples, rng)
    mismatch_best, mismatch_scores = sci.classify_pure_generator(
        mismatch_counts, complete_noisy, generators
    )
    best_index = generators.index(mismatch_best)
    mismatch_deviance = sci.multinomial_deviance(mismatch_counts, complete_noisy[:, best_index])
    mismatch_df = len(complete_labels) - 1
    mismatch_log_pvalue = float(chi2.logsf(mismatch_deviance, mismatch_df))
    # Four pure candidates were searched and the best one was selected before
    # this diagnostic.  The Bonferroni-adjusted value is a conservative
    # reporting bound, not a calibrated global p-value for every possible model.
    mismatch_pvalue = (
        0.0
        if mismatch_log_pvalue < math.log(np.finfo(float).tiny)
        else float(math.exp(mismatch_log_pvalue))
    )
    mismatch_pvalue_adjusted = (
        0.0
        if mismatch_log_pvalue < math.log(np.finfo(float).tiny / 4.0)
        else float(min(1.0, 4.0 * math.exp(mismatch_log_pvalue)))
    )
    mismatch_logsf_json = (
        mismatch_log_pvalue if math.isfinite(mismatch_log_pvalue) else None
    )

    defect_expectation = {
        generator: sci.expectation(sci.output_state(generator), sci.defect_observable())
        for generator in generators
    }
    excitation_expectation = {
        generator: sci.expectation(sci.output_state(generator), sci.global_excitation_observable())
        for generator in generators
    }

    payload = {
        "status": "synthetic methods benchmark only; not evidence for real duality defects, hidden matter, or dark matter",
        "version": "0.1.0-alpha.1",
        "seed": SEED,
        "samples_per_generator": SAMPLES_PER_GENERATOR,
        "classification_replicates": CLASSIFICATION_REPLICATES,
        "detector_error_rate": DETECTOR_ERROR,
        "generator_order": list(generators),
        "local_outcomes": list(local_labels),
        "sector_complete_outcomes": list(complete_labels),
        "local_equivalence_classes": local_classes,
        "sector_complete_equivalence_classes": complete_classes,
        "mutual_information_bits": {
            "local_ideal": mi_local_ideal,
            "sector_complete_ideal": mi_complete_ideal,
            "local_with_detector_error": mi_local_noisy,
            "sector_complete_with_detector_error": mi_complete_noisy,
        },
        "fisher_information": {
            "local_matrix": fisher_local.tolist(),
            "sector_complete_matrix": fisher_complete.tolist(),
            "local_eigenvalues": eig_local.tolist(),
            "sector_complete_eigenvalues": eig_complete.tolist(),
            "local_rank": sci.matrix_rank_with_tolerance(fisher_local),
            "sector_complete_rank": sci.matrix_rank_with_tolerance(fisher_complete),
        },
        "classification": {
            "local_confusion_counts": confusion_local_counts.tolist(),
            "sector_complete_confusion_counts": confusion_complete_counts.tolist(),
            "local_accuracy": local_accuracy,
            "sector_complete_accuracy": complete_accuracy,
        },
        "conservation_exchange_ledger": {
            "trace": "one for every output state",
            "global_excitation_expectation": excitation_expectation,
            "defect_occupation_expectation": defect_expectation,
            "energy": "not modeled",
            "charge": "not modeled",
            "entropy": "not asserted conserved for reduced channels",
            "accessible_information": "measurement- and sector-dependent",
        },
        "model_mismatch_control": {
            "hybrid_weights_in_generator_order": hybrid_weights.tolist(),
            "counts": mismatch_counts.tolist(),
            "best_pure_candidate": mismatch_best,
            "pure_candidate_log_likelihoods": mismatch_scores.tolist(),
            "deviance": mismatch_deviance,
            "degrees_of_freedom": mismatch_df,
            "chi_square_pvalue": mismatch_pvalue,
            "chi_square_logsf": mismatch_logsf_json,
            "chi_square_logsf_status": "underflow_to_zero" if mismatch_logsf_json is None else "representable",
            "selection_adjusted_pvalue_upper_bound": mismatch_pvalue_adjusted,
            "pvalue_status": "underflow_to_zero" if mismatch_pvalue == 0.0 else "representable",
            "selection_note": "best-of-four pure candidate selected before this diagnostic; adjusted value is a conservative Bonferroni bound",
            "rejection_rule": "reject pure candidate set when the selection-adjusted upper bound is below 0.001",
            "rejected": bool(mismatch_pvalue_adjusted < 0.001),
        },
        "typed_transduction_record": sci.default_transduction_record().to_dict(),
        "sector_records": [record.__dict__ if hasattr(record, "__dict__") else {field: getattr(record, field) for field in record.__dataclass_fields__} for record in sci.default_sector_records()],
        "dark_matter_interpretation_status": "proposed_only",
    }

    json_path = data_dir / "sector_complete_benchmark.json"
    def write_utf8_lf(path: Path, text: str) -> None:
        path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))

    write_utf8_lf(json_path, json.dumps(payload, indent=2) + "\n")

    save_matrix_csv(data_dir / "local_response_matrix.csv", local_labels, generators, local_noisy)
    save_matrix_csv(data_dir / "sector_complete_response_matrix.csv", complete_labels, generators, complete_noisy)

    with (data_dir / "detector_noise_information.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["detector_error_rate", "local_mutual_information_bits", "sector_complete_mutual_information_bits"])
        writer.writerows(zip(noise_grid, mi_noise_local, mi_noise_complete, strict=True))

    with (data_dir / "finite_boundary_control.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["length_over_xi", "tv_from_absorb", "string_outcome_probability"])
        writer.writerows(zip(lengths, finite_tv, finite_string_probability, strict=True))

    with (data_dir / "broken_duality_control.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["reflection_admixture", "left_local_probability", "string_probability"])
        writer.writerows(zip(deltas, broken_reflect_probability, broken_string_probability, strict=True))

    save_heatmap(
        figures_dir / "figure_01_local_response_matrix",
        local_labels,
        generators,
        local_noisy,
        "Local observables leave absorb and string transmit equivalent",
    )
    save_heatmap(
        figures_dir / "figure_02_sector_complete_response_matrix",
        complete_labels,
        generators,
        complete_noisy,
        "Declared sector observables separate all four generators",
    )
    save_eigenvalue_plot(
        figures_dir / "figure_03_fisher_eigenvalues", eig_local, eig_complete
    )
    save_line_plot(
        figures_dir / "figure_04_information_vs_detector_noise",
        noise_grid,
        [
            ("local observation", np.array(mi_noise_local)),
            ("sector-complete observation", np.array(mi_noise_complete)),
        ],
        "symmetric detector error rate",
        "mutual information I(K;D) [bits]",
        "Information gain is protocol-dependent and degrades with detector noise",
    )
    save_line_plot(
        figures_dir / "figure_05_finite_boundary_control",
        lengths,
        [
            ("TV distance from absorb", np.array(finite_tv)),
            ("string-outcome probability", np.array(finite_string_probability)),
        ],
        "finite boundary length L/xi",
        "probability or total-variation distance",
        "Finite boundary control approaches ideal string transmission",
    )
    save_line_plot(
        figures_dir / "figure_06_broken_duality_control",
        deltas,
        [
            ("left-local outcome", np.array(broken_reflect_probability)),
            ("string-sector outcome", np.array(broken_string_probability)),
        ],
        "declared reflection admixture",
        "outcome probability",
        "Breaking the ideal matching condition restores reflection",
    )
    save_confusion_plot(
        figures_dir / "figure_07_local_classification_confusion",
        confusion_local_counts,
        "Local classification retains the absorb/string ambiguity",
    )
    save_confusion_plot(
        figures_dir / "figure_08_sector_complete_classification_confusion",
        confusion_complete_counts,
        "Sector-complete classification resolves the synthetic generators",
    )

    config = {
        "version": "0.1.0-alpha.1",
        "seed": SEED,
        "samples_per_generator": SAMPLES_PER_GENERATOR,
        "classification_replicates": CLASSIFICATION_REPLICATES,
        "detector_error_rate": DETECTOR_ERROR,
        "basis": list(sci.BASIS),
        "input_basis": sci.INPUT_BASIS,
        "generator_outputs": sci.GENERATOR_OUTPUT,
        "finite_boundary_closure": "string survival = 1 - exp(-L/xi); remainder maps to environment",
        "broken_duality_closure": "random-unitary mixture of string transmission and reflection",
        "model_mismatch_hybrid_weights": hybrid_weights.tolist(),
    }
    write_utf8_lf(data_dir / "benchmark_config.json", json.dumps(config, indent=2) + "\n")

    digest = hashlib.sha256(json_path.read_bytes()).hexdigest()
    write_utf8_lf(
        data_dir / "sector_complete_benchmark.json.sha256",
        f"{digest}  sector_complete_benchmark.json\n",
    )

    # Hard gates.
    assert local_classes == [["reflect"], ["absorb", "string_transmit"], ["local_transmit"]]
    assert complete_classes == [["reflect"], ["absorb"], ["local_transmit"], ["string_transmit"]]
    assert sci.matrix_rank_with_tolerance(fisher_local) == 2
    assert sci.matrix_rank_with_tolerance(fisher_complete) == 3
    assert mi_complete_noisy > mi_local_noisy
    assert complete_accuracy > 0.99
    assert 0.70 < local_accuracy < 0.80
    assert mismatch_pvalue_adjusted < 0.001
    assert all(np.isclose(value, 1.0, atol=1e-12) for value in excitation_expectation.values())

    print(json.dumps({
        "local_equivalence_classes": local_classes,
        "sector_complete_equivalence_classes": complete_classes,
        "local_fisher_rank": sci.matrix_rank_with_tolerance(fisher_local),
        "sector_complete_fisher_rank": sci.matrix_rank_with_tolerance(fisher_complete),
        "local_mutual_information_bits": mi_local_noisy,
        "sector_complete_mutual_information_bits": mi_complete_noisy,
        "local_classification_accuracy": local_accuracy,
        "sector_complete_classification_accuracy": complete_accuracy,
        "model_mismatch_pvalue": mismatch_pvalue,
        "model_mismatch_selection_adjusted_pvalue_upper_bound": mismatch_pvalue_adjusted,
        "model_mismatch_logsf": mismatch_logsf_json,
        "result_sha256": digest,
    }, indent=2))


if __name__ == "__main__":
    main()
