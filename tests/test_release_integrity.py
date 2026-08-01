from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from tools import check_repository as repository
from tools import release_integrity as release
from tools import verify as verifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure_release_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[str], dict[str, str]]:
    names = ["a.pdf", "a.html", "s.pdf", "s.html", "source.tar.gz", "SHA256SUMS", "identity.json"]
    dist = tmp_path / "dist"
    dist.mkdir()
    manifest = tmp_path / "MANIFEST.sha256"
    manifest.write_text("0" * 64 + "  README.md\n", encoding="utf-8")
    spec = {
        "version": "1.0.1",
        "tag": "v1.0.1",
        "build_epoch": "2026-08-01T00:00:00Z",
        "release_asset_allowlist": names,
    }
    spec_path = tmp_path / "RELEASE_SPEC.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    for index, name in enumerate(names[:5]):
        (dist / name).write_bytes(f"asset-{index}".encode())
    sums = "".join(f"{digest(dist / name)}  {name}\n" for name in names[:5])
    (dist / names[5]).write_text(sums, encoding="utf-8", newline="\n")
    tag = {"tag_object": "a" * 40, "commit": "b" * 40, "tree": "c" * 40}
    assets = [
        {"name": name, "bytes": (dist / name).stat().st_size, "sha256": digest(dist / name)}
        for name in names[:6]
    ]
    identity = {
        "version": "1.0.1",
        "tag": "v1.0.1",
        "annotated_tag_object": tag["tag_object"],
        "commit": tag["commit"],
        "tree": tag["tree"],
        "build_epoch": "2026-08-01T00:00:00Z",
        "tracked_manifest": {
            "name": manifest.name,
            "bytes": manifest.stat().st_size,
            "sha256": digest(manifest),
        },
        "assets": assets,
        "sha256sums_sha256": digest(dist / names[5]),
        "identity_excludes_self": True,
    }
    (dist / names[6]).write_text(json.dumps(identity), encoding="utf-8")
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(release, "DIST", dist)
    monkeypatch.setattr(release, "MANIFEST", manifest)
    monkeypatch.setattr(release, "SPEC_PATH", spec_path)
    monkeypatch.setattr(release, "tag_identity", lambda *args, **kwargs: tag)
    monkeypatch.setattr(release, "verify_archive", lambda *args, **kwargs: None)
    release.verify_release_assets()
    return names, tag


def test_one_byte_release_asset_mutation_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names, _ = configure_release_fixture(tmp_path, monkeypatch)
    target = release.DIST / names[0]
    target.write_bytes(target.read_bytes() + b"x")
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        release.verify_release_assets()


def test_detached_identity_commit_or_tree_mismatch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names, _ = configure_release_fixture(tmp_path, monkeypatch)
    path = release.DIST / names[6]
    identity = json.loads(path.read_text(encoding="utf-8"))
    identity["tree"] = "d" * 40
    path.write_text(json.dumps(identity), encoding="utf-8")
    with pytest.raises(RuntimeError, match="identity mismatch for tree"):
        release.verify_release_assets()


def test_checksum_or_identity_mismatch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names, _ = configure_release_fixture(tmp_path, monkeypatch)
    checksum_path = release.DIST / names[5]
    checksum_path.write_text(checksum_path.read_text(encoding="utf-8").replace("a.pdf", "x.pdf"), encoding="utf-8")
    with pytest.raises(RuntimeError, match="SHA256SUMS mismatch"):
        release.verify_release_assets()


def test_source_mutation_and_stale_generated_output_fail_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.py"
    generated = tmp_path / "generated.json"
    source.write_text("x = 1\n", encoding="utf-8")
    generated.write_text("{}\n", encoding="utf-8")
    manifest = tmp_path / "MANIFEST.sha256"
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(release, "MANIFEST", manifest)
    monkeypatch.setattr(release, "public_files", lambda: [generated, manifest, source])
    release.write_manifest()
    release.verify_manifest()
    source.write_bytes(source.read_bytes() + b"x")
    with pytest.raises(RuntimeError, match="stale or mismatched"):
        release.verify_manifest()
    source.write_text("x = 1\n", encoding="utf-8")
    release.write_manifest()
    generated.write_text('{"stale": true}\n', encoding="utf-8")
    with pytest.raises(RuntimeError, match="stale or mismatched"):
        release.verify_manifest()


def initialize_git_repository(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Jacko T."], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "307349551+jkolantree@users.noreply.github.com"],
        cwd=path,
        check=True,
    )
    (path / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=path, check=True)


def test_dirty_or_unexplained_worktree_blocks_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialize_git_repository(tmp_path)
    monkeypatch.setattr(release, "ROOT", tmp_path)
    release.assert_clean_worktree()
    (tmp_path / "unexplained.txt").write_text("dirty", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Dirty or unexplained"):
        release.assert_clean_worktree()


def test_unannotated_existing_and_wrong_target_tags_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialize_git_repository(tmp_path)
    monkeypatch.setattr(release, "ROOT", tmp_path)
    subprocess.run(["git", "tag", "v1.0.1"], cwd=tmp_path, check=True)
    with pytest.raises(RuntimeError, match="must be annotated"):
        release.tag_identity("v1.0.1")
    with pytest.raises(RuntimeError, match="already exists"):
        release.assert_tag_absent("v1.0.1")
    subprocess.run(["git", "tag", "-d", "v1.0.1"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "tag", "-a", "v1.0.1", "-m", "release"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("second\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=tmp_path, check=True)
    with pytest.raises(RuntimeError, match="not current HEAD"):
        release.tag_identity("v1.0.1")


@pytest.mark.parametrize(
    ("name", "is_file", "is_directory"),
    [
        ("../escape", True, False),
        ("root/.git/config", True, False),
        ("root/__pycache__/x.pyc", True, False),
        ("root/link", False, False),
        ("C:\\absolute", True, False),
    ],
)
def test_path_traversal_git_caches_and_archive_links_are_rejected(
    name: str, is_file: bool, is_directory: bool
) -> None:
    with pytest.raises(RuntimeError):
        release.assert_safe_archive_member(
            name, is_file=is_file, is_directory=is_directory
        )


def test_dependency_lock_drift_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "requirements.in").write_text("numpy==2.3.5\n", encoding="utf-8")
    (tmp_path / "requirements-lock.txt").write_text("numpy==2.3.4\n", encoding="utf-8")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="not fully hash-pinned"):
        repository.check_dependency_lock()


@pytest.mark.parametrize(("observed", "message"), [(None, "missing"), ("9.9.9", "drift")])
def test_missing_or_drifting_installed_dependency_is_rejected(
    observed: str | None, message: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(verifier, "locked_distributions", lambda: {"example": "1.2.3"})

    def observed_version(_name: str) -> str:
        if observed is None:
            raise verifier.importlib.metadata.PackageNotFoundError
        return observed

    monkeypatch.setattr(verifier.importlib.metadata, "version", observed_version)
    with pytest.raises(RuntimeError, match=message):
        verifier.verify_installed_distributions()


def test_duplicate_evidence_cannot_be_double_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory = json.loads((PROJECT_ROOT / "SOURCE_INVENTORY.json").read_text(encoding="utf-8"))
    for item in inventory["artifacts"]:
        if "synthetic_topology_ensemble" in item["canonical_relative_path"]:
            item["relationship"] = "independent evidence"
    (tmp_path / "SOURCE_INVENTORY.json").write_text(json.dumps(inventory), encoding="utf-8")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="not explicitly deduplicated"):
        repository.check_source_inventory()


def test_weakened_theorem_hypothesis_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    matrix = json.loads((PROJECT_ROOT / "CLAIM_MATRIX.json").read_text(encoding="utf-8"))
    claim = next(item for item in matrix["claims"] if item["id"] == "SPPT-C005")
    claim["hypotheses"] = [value.replace("strictly positive", "nonnegative") for value in claim["hypotheses"]]
    (tmp_path / "CLAIM_MATRIX.json").write_text(json.dumps(matrix), encoding="utf-8")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="Weakened hypothesis"):
        repository.check_claim_matrix()


def test_numerical_agreement_cannot_be_promoted_to_proof_or_external_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    matrix = json.loads((PROJECT_ROOT / "CLAIM_MATRIX.json").read_text(encoding="utf-8"))
    claim = next(item for item in matrix["claims"] if item["id"] == "ASTRA-C011")
    claim["statement"] += " This is proof and external validation."
    (tmp_path / "CLAIM_MATRIX.json").write_text(json.dumps(matrix), encoding="utf-8")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="promoted to proof"):
        repository.check_claim_matrix()


def test_private_metadata_and_nonallowlisted_files_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private = tmp_path / "README.md"
    private.write_text("C:\\Users\\Private\\secret\n", encoding="utf-8")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="local Windows path"):
        repository.check_text_privacy([private])
    (tmp_path / "unexpected.exe").write_bytes(b"x")
    with pytest.raises(RuntimeError, match="Unexpected root file"):
        repository.public_files()


def test_root_git_and_cache_directories_are_excluded_from_public_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "README.md").write_text("ok\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("private", encoding="utf-8")
    (tmp_path / "tmp").mkdir()
    (tmp_path / "tmp" / "cache.bin").write_bytes(b"cache")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    assert [path.name for path in repository.public_files()] == ["README.md"]
