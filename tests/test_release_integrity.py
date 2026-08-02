from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import check_repository as repository
from tools import release_integrity as release
from tools import verify as verifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GITHUB_CONTEXT_VARIABLES = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_EVENT_PATH",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_REF_TYPE",
    "GITHUB_REPOSITORY",
    "GITHUB_REPOSITORY_ID",
    "GITHUB_SERVER_URL",
    "GITHUB_SHA",
)


@pytest.fixture(autouse=True)
def isolate_github_actions_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """Require each test to declare its complete simulated GitHub context."""
    for name in GITHUB_CONTEXT_VARIABLES:
        monkeypatch.delenv(name, raising=False)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure_release_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[str], dict[str, str]]:
    names = [
        "SPPT_ASTRA_preprint_v1.0.1.pdf",
        "SPPT_ASTRA_preprint_v1.0.1.html",
        "SPPT_ASTRA_technical_supplement_v1.0.1.pdf",
        "SPPT_ASTRA_technical_supplement_v1.0.1.html",
        "SPPT_ASTRA_v1.0.1_source.tar.gz",
        "SHA256SUMS",
        "release-identity-v1.0.1.json",
    ]
    dist = tmp_path / "dist"
    dist.mkdir()
    manifest = tmp_path / "MANIFEST.sha256"
    manifest.write_text("0" * 64 + "  README.md\n", encoding="utf-8")
    spec = {
        "version": "1.0.1",
        "tag": "v1.0.1",
        "repository": "https://example.invalid/astra",
        "repository_id": 1,
        "release_date": "2026-08-01",
        "build_epoch": "2026-08-01T00:00:00Z",
        "build_epoch_unix": 1785542400,
        "release_asset_allowlist": names,
    }
    spec_path = tmp_path / "RELEASE_SPEC.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    for index, name in enumerate(names[:5]):
        (dist / name).write_bytes(f"asset-{index}".encode())
    tagged_documents = {
        f"manuscript/{name}": (dist / name).read_bytes() for name in names[:4]
    }
    sums = "".join(f"{digest(dist / name)}  {name}\n" for name in names[:5])
    (dist / names[5]).write_text(sums, encoding="utf-8", newline="\n")
    tag = {"tag_object": "a" * 40, "commit": "b" * 40, "tree": "c" * 40}
    assets = [
        {"name": name, "bytes": (dist / name).stat().st_size, "sha256": digest(dist / name)}
        for name in names[:6]
    ]
    identity = {
        "schema": release.IDENTITY_SCHEMA,
        "repository": "https://example.invalid/astra",
        "repository_id": 1,
        "version": "1.0.1",
        "tag": "v1.0.1",
        "annotated_tag_object": tag["tag_object"],
        "commit": tag["commit"],
        "tree": tag["tree"],
        "release_date": "2026-08-01",
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
    (dist / names[6]).write_bytes(release.canonical_json_bytes(identity))
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(release, "DIST", dist)
    monkeypatch.setattr(release, "MANIFEST", manifest)
    monkeypatch.setattr(release, "SPEC_PATH", spec_path)
    monkeypatch.setattr(release, "verify_python_runtime", lambda: None)
    monkeypatch.setattr(release, "verify_git_runtime", lambda: None)
    monkeypatch.setattr(release, "tag_identity", lambda *args, **kwargs: tag)
    monkeypatch.setattr(
        release,
        "tagged_file_bytes",
        lambda _commit, relative: tagged_documents[str(relative)],
    )
    monkeypatch.setattr(release, "verify_archive", lambda *args, **kwargs: None)
    release.verify_release_assets()
    return names, tag


def test_one_byte_release_asset_mutation_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names, _ = configure_release_fixture(tmp_path, monkeypatch)
    target = release.DIST / names[0]
    target.write_bytes(target.read_bytes() + b"x")
    with pytest.raises(RuntimeError, match="checksum mismatch|differs from tagged manuscript"):
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


@pytest.mark.parametrize("mutation", ["whitespace", "schema", "extra-field"])
def test_any_detached_identity_byte_or_shape_mutation_is_rejected(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names, _ = configure_release_fixture(tmp_path, monkeypatch)
    path = release.DIST / names[6]
    if mutation == "whitespace":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        identity = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "schema":
            identity["schema"] = "https://example.invalid/wrong-schema"
        else:
            identity["unexpected"] = True
        path.write_bytes(release.canonical_json_bytes(identity))
    with pytest.raises(RuntimeError, match="identity mismatch|exact canonical"):
        release.verify_release_assets()


def test_checksum_or_identity_mismatch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names, _ = configure_release_fixture(tmp_path, monkeypatch)
    checksum_path = release.DIST / names[5]
    checksum_path.write_text(
        checksum_path.read_text(encoding="utf-8").replace(names[0], "wrong.pdf"),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="SHA256SUMS mismatch"):
        release.verify_release_assets()


def test_coordinated_document_replacement_cannot_claim_tagged_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names, tag = configure_release_fixture(tmp_path, monkeypatch)
    target = release.DIST / names[0]
    target.write_bytes(b"coordinated replacement")
    sums_path = release.DIST / names[5]
    sums_path.write_text(
        "".join(f"{digest(release.DIST / name)}  {name}\n" for name in names[:5]),
        encoding="utf-8",
        newline="\n",
    )
    identity = release.expected_detached_identity(release.release_spec(), tag, names)
    (release.DIST / names[6]).write_bytes(release.canonical_json_bytes(identity))

    with pytest.raises(RuntimeError, match="tagged manuscript"):
        release.verify_release_assets()


def test_noncanonical_source_archive_bytes_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "source.tar.gz"
    archive.write_bytes(b"noncanonical")
    monkeypatch.setattr(
        release,
        "canonical_source_archive_bytes",
        lambda *args, **kwargs: b"canonical",
    )
    with pytest.raises(RuntimeError, match="canonical"):
        release.verify_archive(archive, commit="a" * 40, prefix="source", epoch=0)


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
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=path, check=True)
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


def test_nested_annotated_tag_is_not_accepted_as_a_direct_release_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialize_git_repository(tmp_path)
    monkeypatch.setattr(release, "ROOT", tmp_path)
    subprocess.run(
        ["git", "tag", "-a", "inner", "-m", "inner"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "tag", "-a", "v1.0.1", "inner", "-m", "outer"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    with pytest.raises(RuntimeError, match="directly target"):
        release.tag_identity("v1.0.1")


def test_duplicate_tag_headers_cannot_spoof_a_direct_release_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialize_git_repository(tmp_path)
    monkeypatch.setattr(release, "ROOT", tmp_path)
    subprocess.run(
        ["git", "tag", "-a", "inner", "-m", "inner"],
        cwd=tmp_path,
        check=True,
    )
    inner = subprocess.run(
        ["git", "rev-parse", "refs/tags/inner"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    payload = (
        f"object {inner}\n"
        "type tag\n"
        "tag outer\n"
        "tagger Test <test@example.invalid> 0 +0000\n"
        f"object {commit}\n"
        "type commit\n"
        "tag v1.0.1\n\n"
        "spoofed duplicate headers\n"
    )
    tag_object = subprocess.run(
        ["git", "hash-object", "--literally", "-t", "tag", "-w", "--stdin"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        input=payload.encode("utf-8"),
    ).stdout.decode("ascii").strip()
    subprocess.run(
        ["git", "update-ref", "refs/tags/v1.0.1", tag_object],
        cwd=tmp_path,
        check=True,
    )

    with pytest.raises(RuntimeError, match="exactly one canonical"):
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


def test_hostile_inherited_numeric_kernel_environment_is_overridden(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    variable_names = (
        "OPENBLAS_CORETYPE",
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "NPY_DISABLE_CPU_FEATURES",
    )
    for name in variable_names:
        monkeypatch.setenv(name, "hostile")
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "TEMP_ROOT", tmp_path / "tmp" / "verification")
    environment = verifier.configure_environment()
    assert environment["OPENBLAS_CORETYPE"] == "HASWELL"
    assert all(environment[name] == "1" for name in variable_names[1:5])
    runtime = json.loads((PROJECT_ROOT / "RUNTIME.json").read_text(encoding="utf-8"))
    assert environment["NPY_DISABLE_CPU_FEATURES"] == ",".join(
        runtime["numeric_kernel"]["numpy_disabled_cpu_features"]
    )


def test_hostile_pytest_and_python_controller_environment_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hostile = {
        "PYTEST_ADDOPTS": "--collect-only",
        "PYTEST_PLUGINS": "hostile_plugin",
        "PYTHONPATH": "hostile-path",
        "PYTHONHOME": "hostile-home",
        "PLAYWRIGHT_BROWSERS_PATH": "hostile-browser",
        "PYPANDOC_PANDOC": "hostile-pandoc",
    }
    for name, value in hostile.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "TEMP_ROOT", tmp_path / "tmp" / "verification")

    environment = verifier.configure_environment()

    assert not hostile.keys() & environment.keys()
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"


def test_verifier_rejects_redirected_temporary_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    temporary_root = tmp_path / "tmp"
    temporary_root.mkdir()
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda self: self == temporary_root or original_is_symlink(self),
    )
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "TEMP_ROOT", temporary_root / "verification")

    with pytest.raises(RuntimeError, match="symbolic link or junction"):
        verifier.configure_environment()


def test_verifier_requires_isolated_python(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(verifier.sys, "flags", SimpleNamespace(isolated=0))
    with pytest.raises(RuntimeError, match="isolated mode"):
        verifier.require_isolated_mode()


@pytest.mark.parametrize("script_name", ["verify.py", "release_integrity.py"])
def test_controller_refuses_nonisolated_startup_before_shadowable_imports(
    script_name: str, tmp_path: Path
) -> None:
    probe = subprocess.run(
        [sys.executable, "-B", "-c", "import sys; print(sys.flags.isolated)"],
        check=True,
        capture_output=True,
        text=True,
    )
    if probe.stdout.strip() == "1":
        pytest.skip("This embedded interpreter forces isolated mode for every child process.")
    (tmp_path / "platform.py").write_text(
        'raise RuntimeError("HOSTILE_PLATFORM_IMPORTED")\n', encoding="utf-8"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(tmp_path)
    completed = subprocess.run(
        [sys.executable, "-B", str(PROJECT_ROOT / "tools" / script_name)],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert "Unsafe startup" in output
    assert "HOSTILE_PLATFORM_IMPORTED" not in output


def test_hostile_git_repository_selectors_are_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    selectors = {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_PARAMETERS",
    }
    for name in selectors:
        monkeypatch.setenv(name, "hostile")

    environment = release.git_environment()

    assert not selectors & environment.keys()
    assert environment["GIT_NO_REPLACE_OBJECTS"] == "1"
    assert environment["GIT_CONFIG_KEY_0"] == "safe.directory"
    assert Path(environment["GIT_CONFIG_VALUE_0"]).resolve() == release.ROOT.resolve()


def test_release_allowlist_rejects_path_traversal() -> None:
    names = ["a.pdf", "a.html", "s.pdf", "s.html", "../README.md", "SHA256SUMS", "id.json"]
    with pytest.raises(RuntimeError, match="portable basename"):
        release.validated_release_allowlist({"release_asset_allowlist": names})


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("tag", "tag must equal"),
        ("asset", "version-bound"),
        ("epoch", "ISO and Unix"),
    ],
)
def test_release_spec_identity_fields_must_agree(mutation: str, message: str) -> None:
    version = "1.0.1"
    spec = {
        "version": version,
        "tag": f"v{version}",
        "repository": "https://example.invalid/astra",
        "repository_id": 1,
        "release_date": "2026-08-01",
        "build_epoch": "2026-08-01T00:00:00Z",
        "build_epoch_unix": 1785542400,
        "release_asset_allowlist": [
            f"SPPT_ASTRA_preprint_v{version}.pdf",
            f"SPPT_ASTRA_preprint_v{version}.html",
            f"SPPT_ASTRA_technical_supplement_v{version}.pdf",
            f"SPPT_ASTRA_technical_supplement_v{version}.html",
            f"SPPT_ASTRA_v{version}_source.tar.gz",
            "SHA256SUMS",
            f"release-identity-v{version}.json",
        ],
    }
    if mutation == "tag":
        spec["tag"] = "v9.9.9"
    elif mutation == "asset":
        spec["release_asset_allowlist"][0] = "SPPT_ASTRA_preprint_v9.9.9.pdf"
    else:
        spec["build_epoch_unix"] += 1
    with pytest.raises(RuntimeError, match=message):
        release.validated_release_allowlist(spec)


def test_tag_event_name_must_equal_release_spec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(release, "verify_python_runtime", lambda: None)
    monkeypatch.setattr(release, "verify_git_runtime", lambda: None)
    with pytest.raises(RuntimeError, match="does not equal declared release tag"):
        release.verify_release_tag("v9.9.9")


def test_github_repository_context_must_bind_declared_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = {
        "repository": "https://github.com/jkolantree/astra",
        "repository_id": 1319077150,
    }
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "attacker/fork")
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "1319077150")
    with pytest.raises(RuntimeError, match="does not equal declared repository"):
        release.verify_github_repository_context(spec)


def test_github_repository_context_must_bind_repository_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = {
        "repository": "https://github.com/jkolantree/astra",
        "repository_id": 1319077150,
    }
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "jkolantree/astra")
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "1")
    with pytest.raises(RuntimeError, match="repository ID"):
        release.verify_github_repository_context(spec)


def test_github_actions_tag_context_binds_distinct_tag_object_and_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit = "a" * 40
    tag_object = "b" * 40
    event_path = tmp_path / "event.json"

    def write_event(after: str) -> None:
        event_path.write_text(
            json.dumps(
                {
                    "ref": "refs/tags/v1.0.1",
                    "before": "0" * 40,
                    "after": after,
                    "created": True,
                    "deleted": False,
                    "forced": False,
                    "repository": {"full_name": "jkolantree/astra", "id": 1319077150},
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(release, "verify_python_runtime", lambda: None)
    monkeypatch.setattr(release, "verify_git_runtime", lambda: None)
    monkeypatch.setattr(
        release,
        "release_spec",
        lambda: {
            "tag": "v1.0.1",
            "repository": "https://github.com/jkolantree/astra",
            "repository_id": 1319077150,
        },
    )
    monkeypatch.setattr(release, "verify_github_repository_context", lambda _spec: None)
    monkeypatch.setattr(
        release,
        "tag_identity",
        lambda _tag, require_head=True: {
            "tag_object": tag_object,
            "commit": commit,
            "tree": "c" * 40,
        },
    )
    monkeypatch.setattr(release, "assert_clean_worktree", lambda: None)
    monkeypatch.setattr(release, "verify_manifest", lambda **_kwargs: None)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_REPOSITORY", "jkolantree/astra")
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "1319077150")
    monkeypatch.delenv("GITHUB_SHA", raising=False)

    with pytest.raises(RuntimeError, match="requires a tag ref"):
        release.verify_release_tag("v1.0.1")
    monkeypatch.setenv("GITHUB_REF_TYPE", "tag")
    monkeypatch.setenv("GITHUB_REF_NAME", "v1.0.1")
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1.0.1")
    with pytest.raises(RuntimeError, match="canonical GITHUB_SHA"):
        release.verify_release_tag("v1.0.1")
    monkeypatch.setenv("GITHUB_SHA", tag_object)
    write_event(tag_object)
    with pytest.raises(RuntimeError, match="event commit.*does not equal tagged commit"):
        release.verify_release_tag("v1.0.1")
    monkeypatch.setenv("GITHUB_SHA", commit)
    write_event(commit)
    with pytest.raises(RuntimeError, match="event tag object.*does not equal tagged tag object"):
        release.verify_release_tag("v1.0.1")
    write_event(tag_object)
    release.verify_release_tag("v1.0.1")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    with pytest.raises(RuntimeError, match="requires a push event"):
        release.verify_release_tag("v1.0.1")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"created": False}, "new-ref creation"),
        ({"deleted": True}, "tag-deletion"),
        ({"forced": True}, "forced tag updates"),
        ({"before": "1" * 40}, "absent prior ref"),
        ({"after": None}, "canonical object ID"),
        ({"after": 7}, "canonical object ID"),
        ({"after": "2" * 39}, "canonical object ID"),
        ({"after": "z" * 40}, "canonical object ID"),
        ({"after": "A" * 40}, "canonical object ID"),
        ({"ref": "refs/tags/v9.9.9"}, "push-event ref"),
        (
            {"repository": {"full_name": "attacker/fork", "id": 1319077150}},
            "push-event repository",
        ),
        (
            {"repository": {"full_name": "jkolantree/astra", "id": 1}},
            "push-event repository ID",
        ),
    ],
)
def test_github_tag_event_rejects_noncreation_payloads(
    mutation: dict[str, object],
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit = "a" * 40
    tag_object = "b" * 40
    payload: dict[str, object] = {
        "ref": "refs/tags/v1.0.4",
        "before": "0" * 40,
        "after": tag_object,
        "created": True,
        "deleted": False,
        "forced": False,
        "repository": {"full_name": "jkolantree/astra", "id": 1319077150},
    }
    payload.update(mutation)
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_TYPE", "tag")
    monkeypatch.setenv("GITHUB_REF_NAME", "v1.0.4")
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1.0.4")
    monkeypatch.setenv("GITHUB_SHA", commit)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "jkolantree/astra")
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "1319077150")
    spec = {
        "tag": "v1.0.4",
        "repository": "https://github.com/jkolantree/astra",
        "repository_id": 1319077150,
    }

    with pytest.raises(RuntimeError, match=message):
        release.github_release_tag_event(spec, required=True)


def test_restore_rejects_invalid_event_before_any_git_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    event_path = tmp_path / "invalid-tag-event.json"
    event_path.write_text(
        json.dumps(
            {
                "ref": "refs/tags/v1.0.4",
                "before": "0" * 40,
                "after": "A" * 40,
                "created": True,
                "deleted": False,
                "forced": False,
                "repository": {"full_name": "jkolantree/astra", "id": 1319077150},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(release, "verify_python_runtime", lambda: None)
    monkeypatch.setattr(release, "verify_git_runtime", lambda: None)
    monkeypatch.setattr(
        release,
        "release_spec",
        lambda: {
            "tag": "v1.0.4",
            "repository": "https://github.com/jkolantree/astra",
            "repository_id": 1319077150,
        },
    )
    monkeypatch.setattr(
        release,
        "git",
        lambda *_args, **_kwargs: pytest.fail("Git must not run for an invalid event"),
    )
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_TYPE", "tag")
    monkeypatch.setenv("GITHUB_REF_NAME", "v1.0.4")
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1.0.4")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "jkolantree/astra")
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "1319077150")

    with pytest.raises(RuntimeError, match="canonical object ID"):
        release.restore_authoritative_release_tag()


def test_restore_authoritative_tag_repairs_v103_checkout_peeled_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Retain v1.0.3 here to reproduce the exact published negative tag trial.
    origin = tmp_path / "origin.git"
    decoy = tmp_path / "decoy.git"
    author = tmp_path / "author"
    runner = tmp_path / "runner"
    subprocess.run(["git", "init", "--bare", "-q", origin], check=True)
    subprocess.run(["git", "init", "--bare", "-q", decoy], check=True)
    subprocess.run(["git", "clone", "-q", origin, author], check=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=author, check=True)
    subprocess.run(["git", "config", "user.name", "Jacko T."], cwd=author, check=True)
    subprocess.run(
        ["git", "config", "user.email", "307349551+jkolantree@users.noreply.github.com"],
        cwd=author,
        check=True,
    )
    (author / "README.md").write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=author, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "candidate"], cwd=author, check=True)
    subprocess.run(
        ["git", "tag", "-a", "v1.0.3", "-m", "SPPT/ASTRA v1.0.3"],
        cwd=author,
        check=True,
    )
    subprocess.run(
        ["git", "push", "-q", "origin", "HEAD:main", "refs/tags/v1.0.3"],
        cwd=author,
        check=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=author,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tag_object = subprocess.run(
        ["git", "rev-parse", "refs/tags/v1.0.3"],
        cwd=author,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    runner.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=runner, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(decoy)], cwd=runner, check=True)
    subprocess.run(
        [
            "git",
            "fetch",
            "-q",
            str(origin),
            "+refs/tags/v1.0.3:refs/tags/v1.0.3",
        ],
        cwd=runner,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "fetch",
            "-q",
            "--no-tags",
            str(origin),
            f"+{commit}:refs/tags/v1.0.3",
        ],
        cwd=runner,
        check=True,
    )
    subprocess.run(["git", "checkout", "-q", "--detach", commit], cwd=runner, check=True)
    observed_type = subprocess.run(
        ["git", "cat-file", "-t", "refs/tags/v1.0.3"],
        cwd=runner,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert observed_type == "commit"

    monkeypatch.setattr(release, "ROOT", runner)
    monkeypatch.setattr(release, "verify_python_runtime", lambda: None)
    monkeypatch.setattr(release, "verify_git_runtime", lambda: None)
    monkeypatch.setattr(
        release,
        "release_spec",
        lambda: {"tag": "v1.0.3", "repository": str(origin), "repository_id": 1319077150},
    )
    monkeypatch.setattr(release, "verify_github_repository_context", lambda _spec: None)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_TYPE", "tag")
    monkeypatch.setenv("GITHUB_REF_NAME", "v1.0.3")
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1.0.3")
    monkeypatch.setenv("GITHUB_SHA", commit)
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "jkolantree/astra")
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "1319077150")
    event_path = tmp_path / "tag-event.json"
    def write_event(after: str) -> None:
        event_path.write_text(
            json.dumps(
                {
                    "ref": "refs/tags/v1.0.3",
                    "before": "0" * 40,
                    "after": after,
                    "created": True,
                    "deleted": False,
                    "forced": False,
                    "repository": {"full_name": "jkolantree/astra", "id": 1319077150},
                }
            ),
            encoding="utf-8",
        )

    write_event("f" * 40)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))

    with pytest.raises(RuntimeError, match="event tag object.*restored tag object"):
        release.restore_authoritative_release_tag()

    write_event(tag_object)
    identity = release.restore_authoritative_release_tag()
    assert identity["tag_object"] == tag_object
    assert identity["commit"] == commit
    restored_type = subprocess.run(
        ["git", "cat-file", "-t", "refs/tags/v1.0.3"],
        cwd=runner,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert restored_type == "tag"
    remote_tag_after = subprocess.run(
        ["git", "rev-parse", "refs/tags/v1.0.3"],
        cwd=origin,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert remote_tag_after == tag_object

    subprocess.run(["git", "tag", "-d", "v1.0.3"], cwd=author, check=True)
    subprocess.run(
        ["git", "tag", "-a", "v1.0.3", "-m", "Replacement annotation"],
        cwd=author,
        check=True,
    )
    replacement_tag_object = subprocess.run(
        ["git", "rev-parse", "refs/tags/v1.0.3"],
        cwd=author,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert replacement_tag_object != tag_object
    subprocess.run(
        ["git", "push", "-q", "--force", str(origin), "refs/tags/v1.0.3"],
        cwd=author,
        check=True,
    )
    write_event(tag_object)
    with pytest.raises(RuntimeError, match="event tag object.*restored tag object"):
        release.restore_authoritative_release_tag()


def test_tag_workflow_does_not_shell_interpolate_ref_name() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "verify.yml").read_text(
        encoding="utf-8"
    )
    git_index = workflow.index("Install and verify exact Git for Windows")
    python_index = workflow.index("Install exact Python")
    restore_index = workflow.index("release_integrity.py restore-tag-ref")
    dependency_index = workflow.index("pip install --require-hashes")
    verify_index = workflow.index("release_integrity.py verify-tag")
    assert git_index < python_index < restore_index < dependency_index < verify_index
    assert "verify-tag --ref-name" not in workflow
    assert "github.ref_name" not in workflow
    assert "git fetch" not in workflow


def test_clean_worktree_rejects_hidden_index_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_git(arguments, **kwargs):
        assert arguments == ["ls-files", "-v", "-z"]
        assert kwargs.get("binary") is True
        return b"h src/sppt_core.py\0"

    monkeypatch.setattr(release, "git", fake_git)
    with pytest.raises(RuntimeError, match="hide worktree changes"):
        release.assert_clean_worktree()


def test_tracked_paths_use_nul_delimiting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release, "git", lambda *args, **kwargs: b"README.md\0odd\nname.txt\0")
    assert release.tracked_paths() == {"README.md", "odd\nname.txt"}


def test_clear_dist_rejects_redirected_distribution_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    dist = root / "dist"
    dist.mkdir(parents=True)
    victim = dist / "allowed.pdf"
    victim.write_bytes(b"preserve")
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda self: self == dist or original_is_symlink(self),
    )
    monkeypatch.setattr(release, "ROOT", root)
    monkeypatch.setattr(release, "DIST", dist)

    with pytest.raises(RuntimeError, match="distribution directory"):
        release.clear_dist({victim.name})
    assert victim.read_bytes() == b"preserve"


def test_clear_dist_rejects_wrong_repository_descendant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    wrong = root / "other"
    wrong.mkdir(parents=True)
    victim = wrong / "allowed.pdf"
    victim.write_bytes(b"preserve")
    monkeypatch.setattr(release, "ROOT", root)
    monkeypatch.setattr(release, "DIST", wrong)

    with pytest.raises(RuntimeError, match="distribution directory"):
        release.clear_dist({victim.name})
    assert victim.read_bytes() == b"preserve"


def test_clear_dist_preflights_complete_roster_before_deleting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    dist = root / "dist"
    dist.mkdir(parents=True)
    allowed = dist / "SHA256SUMS"
    unexpected = dist / "old-release.pdf"
    allowed.write_bytes(b"preserve allowed")
    unexpected.write_bytes(b"preserve unexpected")
    monkeypatch.setattr(release, "ROOT", root)
    monkeypatch.setattr(release, "DIST", dist)

    with pytest.raises(RuntimeError, match="Unexpected item"):
        release.clear_dist({allowed.name})
    assert allowed.read_bytes() == b"preserve allowed"
    assert unexpected.read_bytes() == b"preserve unexpected"


def test_staged_distribution_failure_restores_prior_roster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    dist = root / "dist"
    staging = root / "tmp" / "release-dist-test"
    dist.mkdir(parents=True)
    staging.mkdir(parents=True)
    old_asset = dist / "allowed.pdf"
    new_asset = staging / "allowed.pdf"
    old_asset.write_bytes(b"old verified roster")
    new_asset.write_bytes(b"new staged roster")
    monkeypatch.setattr(release, "ROOT", root)
    monkeypatch.setattr(release, "DIST", dist)

    def reject_installed(_distribution=None) -> None:
        raise RuntimeError("post-install verification failed")

    monkeypatch.setattr(release, "verify_release_assets", reject_installed)
    with pytest.raises(RuntimeError, match="post-install verification failed"):
        release.install_staged_distribution(staging, {old_asset.name})

    assert old_asset.read_bytes() == b"old verified roster"
    assert new_asset.read_bytes() == b"new staged roster"


def test_staged_distribution_preserves_unexpected_prior_roster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    dist = root / "dist"
    staging = root / "tmp" / "release-dist-test"
    dist.mkdir(parents=True)
    staging.mkdir(parents=True)
    prior = dist / "old-release.pdf"
    candidate = staging / "allowed.pdf"
    prior.write_bytes(b"preserve old release")
    candidate.write_bytes(b"candidate")
    monkeypatch.setattr(release, "ROOT", root)
    monkeypatch.setattr(release, "DIST", dist)

    with pytest.raises(RuntimeError, match="Unexpected item"):
        release.install_staged_distribution(staging, {candidate.name})

    assert prior.read_bytes() == b"preserve old release"
    assert candidate.read_bytes() == b"candidate"


def test_atomic_repository_write_does_not_mutate_external_hardlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    output_directory = root / "tmp"
    output_directory.mkdir(parents=True)
    external = tmp_path / "external.bin"
    external.write_bytes(b"preserve")
    destination = output_directory / "archive.tar.gz"
    os.link(external, destination)
    monkeypatch.setattr(release, "ROOT", root)

    release.atomic_write_repository_bytes(destination, b"replacement")

    assert external.read_bytes() == b"preserve"
    assert destination.read_bytes() == b"replacement"


def test_manifest_write_does_not_mutate_external_hardlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    readme = root / "README.md"
    readme.write_text("public\n", encoding="utf-8")
    external = tmp_path / "external-manifest.txt"
    external.write_bytes(b"preserve external")
    manifest = root / "MANIFEST.sha256"
    os.link(external, manifest)
    monkeypatch.setattr(release, "ROOT", root)
    monkeypatch.setattr(release, "MANIFEST", manifest)
    monkeypatch.setattr(release, "public_files", lambda: [manifest, readme])

    release.write_manifest()

    assert external.read_bytes() == b"preserve external"
    assert manifest.read_text(encoding="utf-8") == f"{release.sha256(readme)}  README.md\n"


def test_full_replay_runs_scientific_generation_twice(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[list[str]] = []
    monkeypatch.setattr(verifier, "verify_focused", lambda _environment: None)
    monkeypatch.setattr(verifier, "scientific_outputs", lambda: [])
    monkeypatch.setattr(verifier, "DOCUMENT_OUTPUTS", ())
    monkeypatch.setattr(
        verifier,
        "run",
        lambda command, *, environment: commands.append(command),
    )

    verifier.verify_full_replay({}, workers=1)

    assert sum("scripts/make_figures.py" in command for command in commands) == 2
    assert all(command[1:4] == ["-P", "-s", "-B"] for command in commands)


def test_focused_verification_requires_tracked_manifest_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []
    monkeypatch.setattr(verifier, "verify_runtime", lambda _environment: None)
    monkeypatch.setattr(verifier, "cffconvert_command", lambda: ["cffconvert", "--validate"])
    monkeypatch.setattr(
        verifier,
        "run",
        lambda command, *, environment: commands.append(command),
    )

    verifier.verify_focused({})

    pytest_command = next(command for command in commands if "pytest" in command)
    python_commands = [command for command in commands if command[0] == sys.executable]
    assert "addopts=" in pytest_command
    assert pytest_command[-1] == "tests"
    manifest_command = next(command for command in commands if "verify-manifest" in command)
    non_manifest_python = [command for command in python_commands if command is not manifest_command]
    assert all(command[1:4] == ["-P", "-s", "-B"] for command in non_manifest_python)
    assert manifest_command[1:3] == ["-I", "-B"]
    assert "--tracked" in manifest_command


def test_focused_verification_does_not_skip_a_missing_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands: list[list[str]] = []
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "verify_runtime", lambda _environment: None)
    monkeypatch.setattr(verifier, "cffconvert_command", lambda: ["cffconvert", "--validate"])
    monkeypatch.setattr(
        verifier,
        "run",
        lambda command, *, environment: commands.append(command),
    )

    verifier.verify_focused({})

    manifest_command = next(command for command in commands if "verify-manifest" in command)
    assert manifest_command[1:3] == ["-I", "-B"]
    assert "--tracked" not in manifest_command


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [("core_type", "SkylakeX"), ("threads", 2)],
)
def test_wrong_numeric_kernel_observation_is_rejected(
    field: str, wrong_value: str | int
) -> None:
    runtime = json.loads((PROJECT_ROOT / "RUNTIME.json").read_text(encoding="utf-8"))
    observation = {
        "cpu_features": {"AVX2": True, "FMA3": True},
        "libraries": [
            {
                "distribution": item["distribution"],
                "distribution_version": item["distribution_version"],
                "blas_provider": "scipy-openblas",
                "openblas_version": item["openblas_version"],
                "core_type": "Haswell",
                "threads": 1,
            }
            for item in runtime["numeric_kernel"]["libraries"]
        ],
    }
    observation["libraries"][0][field] = wrong_value
    with pytest.raises(RuntimeError, match="Numeric-kernel drift"):
        verifier.validate_numeric_kernel_observation(runtime, observation)


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
    private.write_text("Example City, USA\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="private location"):
        repository.check_text_privacy([private])
    private.write_text("Correspondence: TBD\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="placeholder contact"):
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


def test_ignored_output_root_link_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    redirected = tmp_path / "dist"
    redirected.mkdir()
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda self: self == redirected or original_is_symlink(self),
    )
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="symbolic link"):
        repository.public_files()


def test_cache_outside_disposable_root_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".mypy_cache").mkdir()
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="outside the disposable tmp root"):
        repository.check_cache_boundaries()


def test_cache_inside_disposable_root_is_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "tmp" / "mypy").mkdir(parents=True)
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    repository.check_cache_boundaries()
