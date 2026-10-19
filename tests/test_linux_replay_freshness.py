"""A complete synthetic replay must work before each isolated fault is injected."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfWriter

from tools import check_repository, verify_linux


def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str = "") -> tuple[Path, list[int]]:
    root = tmp_path / "source"
    (root / "tmp").mkdir(parents=True)
    profile = root / "RUNTIME-linux.json"
    profile.write_text("{}\n")
    input_name = sorted(verify_linux.REPLAY_COPIED_INPUTS)[0]
    source = root / input_name
    source.parent.mkdir(parents=True)
    source.write_text("fixed input\n")
    output_names = ["data/fresh.csv", *verify_linux.REPLAY_ATLAS_OUTPUTS]

    def produce(directory: Path, names: list[str]) -> None:
        for name in names:
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name.endswith(".pdf"):
                writer = PdfWriter()
                writer.add_blank_page(width=200, height=200)
                writer.write(path)
            elif name.endswith(".csv"):
                path.write_text("value\n1.0\n")
            elif name.endswith(".html"):
                path.write_text("fixed HTML")
            else:
                path.write_text("{}\n")

    produce(root, output_names)
    expected = {name: verify_linux.digest(root / name) for name in output_names}
    baseline = root / "evidence/linux-research-v1.json"
    baseline.parent.mkdir()
    baseline.write_text(json.dumps({"output_sha256": expected}))
    paths = [path for path in root.rglob("*") if path.is_file()]
    original = {path: path.read_bytes() for path in paths}
    monkeypatch.setattr(verify_linux, "ROOT", root)
    monkeypatch.setattr(verify_linux, "PROFILE", profile)
    monkeypatch.setattr(check_repository, "public_files", lambda: [
        path for path in root.rglob("*") if path.is_file() and path.relative_to(root).parts[0] != "tmp"
    ])
    counts = [0]

    def build(command: list[str], **kwargs: object) -> None:
        directory = kwargs["cwd"]
        assert isinstance(directory, Path)
        if command[3].endswith("make_figures.py"):
            counts[0] += 1
            # Crucial positive control: even matching source outputs are absent.
            assert all(not (directory / name).exists() for name in output_names)
            if fault == "child":
                raise subprocess.CalledProcessError(7, command)
            if fault == "child_delete":
                source.unlink()
                raise subprocess.CalledProcessError(7, command)
            if fault == "source":
                (directory / input_name).write_text("changed input\n")
            if fault == "original":
                source.write_text("changed original\n")
            if fault == "original_added":
                (root / "data/extra.csv").write_text("unexpected original addition\n")
            if fault != "noop" and not (fault == "stale" and counts[0] == 2):
                produce(directory, [output_names[0]])
            if fault == "extra":
                (directory / "unexpected.txt").write_text("extra\n")
            if fault == "drift":
                (directory / output_names[0]).write_text("value\n2.0\n")
            if fault in {"link", "hardlink", "directory"}:
                target = directory / output_names[0]
                target.unlink()
                if fault == "link":
                    target.symlink_to(root / output_names[0])
                elif fault == "hardlink":
                    os.link(root / output_names[0], target)
                else:
                    target.mkdir()
        elif fault != "noop" and not (fault == "stale" and counts[0] == 2):
            produce(directory, output_names[1:])
        if fault != "original":
            assert all(path.read_bytes() == data for path, data in original.items())

    monkeypatch.setattr(verify_linux.subprocess, "run", build)
    return root, counts


def test_complete_fixture_produces_every_output_twice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, counts = fixture(tmp_path, monkeypatch)
    report = verify_linux.replay({}, 4)
    assert counts == [2]
    assert report["linux_baseline_gate"] == "PASS"
    assert report["historical_scientific_equivalence"] == "PASS"
    assert report["source_checkout_unchanged"] is True
    assert [item["generated_count"] for item in report["pass_inventory"]] == [5, 5]
    assert json.loads((root / "tmp/linux-verification.json").read_text()) == report


@pytest.mark.parametrize(("fault", "message"), [
    ("noop", "missing freshly generated"),
    ("stale", "missing freshly generated"),
    ("source", "modified copied source"),
    ("original", "changed the source checkout"),
    ("original_added", "changed the source checkout"),
    ("extra", "file inventory changed"),
    ("drift", "baseline byte drift"),
    ("link", "symbolic link"),
    ("hardlink", "unlinked regular file"),
    ("directory", "unlinked regular file"),
])
def test_freshness_fault_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str, message: str,
) -> None:
    root, counts = fixture(tmp_path, monkeypatch, fault)
    with pytest.raises(RuntimeError, match=message):
        verify_linux.replay({}, 4)
    report = json.loads((root / "tmp/linux-verification.json").read_text())
    assert report["classification"] == "blocked_linux_migration"
    assert message in report["blocking_error"]
    assert report["historical_scientific_equivalence"] == "NOT_RUN"
    if fault == "stale":
        assert counts == [2]
        assert [item["generated_count"] for item in report["pass_inventory"]] == [5, 0]


@pytest.mark.parametrize("fault", ["child", "child_delete"])
def test_failed_child_propagates_exit_and_persists_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str,
) -> None:
    root, _ = fixture(tmp_path, monkeypatch, fault)
    with pytest.raises(subprocess.CalledProcessError) as error:
        verify_linux.replay({}, 4)
    assert error.value.returncode == 7
    report = json.loads((root / "tmp/linux-verification.json").read_text())
    assert report["child_exit_code"] == 7
    assert report["classification"] == "blocked_linux_migration"
    assert report["source_checkout_unchanged"] is (fault == "child")


def test_removed_source_output_cannot_reduce_frozen_inventory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, counts = fixture(tmp_path, monkeypatch)
    paths = [path for path in check_repository.public_files() if path != root / "data/fresh.csv"]
    monkeypatch.setattr(check_repository, "public_files", lambda: paths)
    with pytest.raises(RuntimeError, match="output inventory changed before replay"):
        verify_linux.replay({}, 4)
    assert counts == [0]


def test_symlinked_parent_is_rejected_before_deletion(tmp_path: Path) -> None:
    external = tmp_path / "external"
    external.mkdir()
    victim = external / "result.csv"
    victim.write_text("preserve")
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "data").symlink_to(external, target_is_directory=True)
    with pytest.raises(RuntimeError, match="symbolic link"):
        verify_linux.fresh_replay_passes(stage, {}, ["data/result.csv"], {}, 4, {"pass_inventory": []})
    assert hashlib.sha256(victim.read_bytes()).hexdigest() == hashlib.sha256(b"preserve").hexdigest()


@pytest.mark.parametrize("name", ["../outside", "/absolute", "data/../outside", "data//out", "./out"])
def test_unsafe_member_spelling_is_rejected(tmp_path: Path, name: str) -> None:
    with pytest.raises(RuntimeError, match="Unsafe Linux replay member"):
        verify_linux.replay_path(tmp_path, name)


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "parent"])
def test_linked_receipt_cannot_overwrite_victim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    root, counts = fixture(tmp_path, monkeypatch)
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "linux-verification.json"
    victim.write_bytes(b"preserve these exact bytes")
    receipt = root / "tmp/linux-verification.json"
    if kind == "symlink":
        receipt.symlink_to(victim)
    elif kind == "hardlink":
        os.link(victim, receipt)
    else:
        receipt.parent.rmdir()
        receipt.parent.symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match="symbolic link|unlinked regular file"):
        verify_linux.replay({}, 4)
    assert victim.read_bytes() == b"preserve these exact bytes"
    assert counts == [0]
