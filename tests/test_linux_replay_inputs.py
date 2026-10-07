"""Copied integration fixtures cannot be admitted as regenerated Linux outputs."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import check_repository, verify_linux
from tools.verify_linux import (
    REPLAY_ATLAS_OUTPUTS,
    REPLAY_COPIED_INPUTS,
    check_scientific_files,
    digest,
    replay_output_names,
)
from tools.verify_linux_baseline import check_outputs, check_replay_tree

ROOT = Path(__file__).resolve().parents[1]


class ReplayInputSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.expected = json.loads(
            (ROOT / "evidence/linux-research-v1.json").read_text()
        )["output_sha256"]

    def test_current_tree_retains_exact_frozen_57_output_keys(self) -> None:
        names = {p.relative_to(ROOT).as_posix() for p in check_repository.public_files()}
        self.assertTrue(REPLAY_COPIED_INPUTS <= names)
        selected = replay_output_names(names)
        self.assertEqual(len(selected), 57)
        self.assertEqual(set(selected), set(self.expected))
        self.assertFalse(REPLAY_COPIED_INPUTS.intersection(selected))

    def test_historical_tree_without_new_inputs_has_same_output_keys(self) -> None:
        self.assertEqual(set(replay_output_names(set(self.expected))), set(self.expected))

    def test_neighbour_data_file_is_not_silently_excluded(self) -> None:
        extra = "data/integrated-core/unreviewed.json"
        selected = replay_output_names(set(self.expected) | REPLAY_COPIED_INPUTS | {extra})
        self.assertIn(extra, selected)
        observed = {name: self.expected.get(name, "unreviewed") for name in selected}
        with self.assertRaisesRegex(RuntimeError, "output inventory changed"):
            check_outputs(self.expected, observed)

    def test_missing_generated_data_still_fails_frozen_inventory(self) -> None:
        missing = next(name for name in self.expected if name.startswith("data/"))
        selected = replay_output_names(set(self.expected) - {missing})
        observed = {name: self.expected[name] for name in selected}
        with self.assertRaisesRegex(RuntimeError, "output inventory changed"):
            check_outputs(self.expected, observed)

    def test_missing_atlas_output_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "missing declared Atlas outputs"):
            replay_output_names(set(self.expected) - {REPLAY_ATLAS_OUTPUTS[0]})

    def test_copied_fixture_mutation_is_rejected_as_source_drift(self) -> None:
        for name in sorted(REPLAY_COPIED_INPUTS):
            with self.subTest(path=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture = root / name
                fixture.parent.mkdir(parents=True)
                fixture.write_text('{"x": 1}\n')
                original = {name: digest(fixture)}
                fixture.write_text('{"x":1}\n')
                with self.assertRaisesRegex(RuntimeError, "modified copied source"):
                    check_replay_tree(root, original, set())

    def test_copied_fixture_comparison_is_byte_exact(self) -> None:
        for name in sorted(REPLAY_COPIED_INPUTS):
            with self.subTest(path=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                original, generated = root / "original", root / "generated"
                for tree in (original, generated):
                    target = tree / name
                    target.parent.mkdir(parents=True)
                    target.write_text('{"x": 1}\n')
                check_scientific_files(original, generated)
                (generated / name).write_text('{"x":1}\n')
                with self.assertRaisesRegex(RuntimeError, "modified copied input"):
                    check_scientific_files(original, generated)

    def test_generated_output_bytes_remain_separately_gated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "result.json"
            output.write_text("before")
            original = {output.name: digest(output)}
            output.write_text("after")
            check_replay_tree(root, original, {output.name})
            with self.assertRaisesRegex(RuntimeError, "baseline byte drift"):
                check_outputs(original, {output.name: digest(output)})

    def test_replay_rejects_mutated_fixture_before_recording_a_pass(self) -> None:
        # Replace generators with a bounded local stub; no scientific subprocess runs.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tmp").mkdir()
            names = set(REPLAY_ATLAS_OUTPUTS) | REPLAY_COPIED_INPUTS
            paths = []
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixed")
                paths.append(path)
            profile = root / "RUNTIME-linux.json"
            profile.write_text("{}\n")
            baseline = root / "evidence/linux-research-v1.json"
            baseline.parent.mkdir()
            baseline.write_text(json.dumps({"output_sha256": {
                name: digest(root / name) for name in REPLAY_ATLAS_OUTPUTS
            }}))
            paths.extend((profile, baseline))
            original = {path: path.read_bytes() for path in paths}

            def corrupt_fixture(*args: object, **kwargs: object) -> None:
                stage = kwargs["cwd"]
                if not isinstance(stage, Path):
                    raise TypeError("Expected an isolated replay stage")
                (stage / sorted(REPLAY_COPIED_INPUTS)[0]).write_text("changed")

            with (
                patch.object(verify_linux, "ROOT", root),
                patch.object(verify_linux, "PROFILE", profile),
                patch.object(check_repository, "public_files", return_value=paths),
                patch.object(verify_linux.subprocess, "run", side_effect=corrupt_fixture),
                self.assertRaisesRegex(RuntimeError, "modified copied source"),
            ):
                verify_linux.replay({}, 4, historical_required=False)
            self.assertTrue(all(path.read_bytes() == original[path] for path in paths))


if __name__ == "__main__":
    unittest.main()
