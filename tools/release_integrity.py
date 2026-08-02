"""Mechanical manifest, deterministic archive, and detached release identity tooling."""
from __future__ import annotations

if __name__ == "__main__":
    import sys as _bootstrap_sys

    if not _bootstrap_sys.flags.isolated or not _bootstrap_sys.dont_write_bytecode:
        raise SystemExit("Unsafe startup: run Python with -I -B before tools/release_integrity.py")

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]


def load_public_files_function() -> Any:
    path = ROOT / "tools" / "check_repository.py"
    specification = importlib.util.spec_from_file_location("_astra_check_repository", path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Cannot load repository checker from {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module.public_files


_PUBLIC_FILES_FUNCTION: Any | None = None


def public_files() -> list[Path]:
    """Load repository policy only for commands that require the public inventory."""
    global _PUBLIC_FILES_FUNCTION
    if _PUBLIC_FILES_FUNCTION is None:
        _PUBLIC_FILES_FUNCTION = load_public_files_function()
    return _PUBLIC_FILES_FUNCTION()


DIST = ROOT / "dist"
MANIFEST = ROOT / "MANIFEST.sha256"
SPEC_PATH = ROOT / "RELEASE_SPEC.json"
RUNTIME_PATH = ROOT / "RUNTIME.json"
IDENTITY_SCHEMA = "https://github.com/jkolantree/astra/schemas/release-identity-v1"
GIT_CONTROL_VARIABLES = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_SYSTEM",
    "GIT_DIR",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_QUARANTINE_PATH",
    "GIT_REPLACE_REF_BASE",
    "GIT_WORK_TREE",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name in GIT_CONTROL_VARIABLES or name.startswith("GIT_"):
            environment.pop(name)
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        }
    )
    environment.update(
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": str(ROOT.resolve()),
            "GIT_NO_REPLACE_OBJECTS": "1",
        }
    )
    return environment


def git(arguments: list[str], *, cwd: Path | None = None, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=cwd or ROOT,
        env=git_environment(),
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


def verify_git_runtime() -> None:
    runtime = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    expected = runtime["git"]
    completed = subprocess.run(
        ["git", "version", "--build-options"],
        check=True,
        capture_output=True,
        text=True,
        env=git_environment(),
    )
    lines = completed.stdout.splitlines()
    version = lines[0].removeprefix("git version ") if lines else ""
    build_match = re.search(r"(?m)^built from commit: ([0-9a-f]{40})$", completed.stdout)
    executable = shutil.which("git", path=git_environment().get("PATH"))
    observed = {
        "version": version,
        "build_commit": build_match.group(1) if build_match else "",
        "executable_sha256": sha256(Path(executable)) if executable else "",
    }
    required = {key: expected[key] for key in observed}
    if observed != required:
        raise RuntimeError(f"Git runtime drift: expected {required}, observed {observed}")


def verify_python_runtime() -> None:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise RuntimeError("Release verification requires Python isolated mode: use -I -B")
    expected = str(json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))["python"])
    observed = platform.python_version()
    if observed != expected:
        raise RuntimeError(f"Python runtime drift: expected {expected}, observed {observed}")


def release_spec() -> dict[str, Any]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    validated_release_allowlist(spec)
    return spec


def validated_release_allowlist(spec: dict[str, Any]) -> list[str]:
    raw = spec.get("release_asset_allowlist")
    if not isinstance(raw, list) or len(raw) != 7:
        raise RuntimeError("Release asset allowlist must have exactly seven unique entries")
    allowlist: list[str] = []
    for value in raw:
        if not isinstance(value, str):
            raise RuntimeError("Release asset names must be strings")
        if (
            not value
            or value in {".", ".."}
            or "/" in value
            or "\\" in value
            or ":" in value
            or any(ord(character) < 32 for character in value)
        ):
            raise RuntimeError(f"Release asset name must be a portable basename: {value!r}")
        allowlist.append(value)
    if len(set(allowlist)) != 7:
        raise RuntimeError("Release asset allowlist must have exactly seven unique entries")
    if allowlist[5] != "SHA256SUMS":
        raise RuntimeError("The sixth release asset must be SHA256SUMS")
    version = spec.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise RuntimeError("Release version must be a three-component numeric version")
    if spec.get("tag") != f"v{version}":
        raise RuntimeError("Release tag must equal 'v' plus the release version")
    repository = spec.get("repository")
    if not isinstance(repository, str) or not repository.startswith("https://"):
        raise RuntimeError("Release repository must be an explicit HTTPS URL")
    if type(spec.get("repository_id")) is not int or spec["repository_id"] <= 0:
        raise RuntimeError("Release repository ID must be a positive integer")
    expected_allowlist = [
        f"SPPT_ASTRA_preprint_v{version}.pdf",
        f"SPPT_ASTRA_preprint_v{version}.html",
        f"SPPT_ASTRA_technical_supplement_v{version}.pdf",
        f"SPPT_ASTRA_technical_supplement_v{version}.html",
        f"SPPT_ASTRA_v{version}_source.tar.gz",
        "SHA256SUMS",
        f"release-identity-v{version}.json",
    ]
    if allowlist != expected_allowlist:
        raise RuntimeError("Release asset allowlist must be exactly version-bound and ordered")
    release_date = spec.get("release_date")
    build_epoch = spec.get("build_epoch")
    if not isinstance(release_date, str) or build_epoch != f"{release_date}T00:00:00Z":
        raise RuntimeError("Release build epoch must be midnight UTC on the release date")
    try:
        parsed_epoch = datetime.strptime(build_epoch, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=UTC
        )
    except (TypeError, ValueError) as error:
        raise RuntimeError("Release build epoch is not canonical UTC") from error
    if type(spec.get("build_epoch_unix")) is not int or spec["build_epoch_unix"] != int(
        parsed_epoch.timestamp()
    ):
        raise RuntimeError("Release ISO and Unix build epochs disagree")
    return allowlist


def manifest_entries() -> dict[str, str]:
    if not MANIFEST.is_file():
        raise RuntimeError("MANIFEST.sha256 is missing")
    entries: dict[str, str] = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        digest, separator, path = line.partition("  ")
        if separator != "  " or len(digest) != 64 or path in entries:
            raise RuntimeError(f"Malformed or duplicate manifest line: {line!r}")
        entries[path] = digest
    return entries


def render_manifest() -> str:
    entries = []
    for path in public_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative == MANIFEST.name:
            continue
        entries.append(f"{sha256(path)}  {relative}")
    return "\n".join(entries) + "\n"


def write_manifest() -> None:
    atomic_write_repository_bytes(MANIFEST, render_manifest().encode("utf-8"))
    print(f"Wrote {MANIFEST.name} mechanically from admitted public files.")


def tracked_paths(revision: str = "HEAD") -> set[str]:
    output = git(["ls-tree", "-r", "--name-only", "-z", revision], binary=True)
    assert isinstance(output, bytes)
    try:
        return {value.decode("utf-8") for value in output.split(b"\0") if value}
    except UnicodeDecodeError as exc:
        raise RuntimeError("Tracked paths must be valid UTF-8") from exc


def verify_manifest(*, require_tracked: bool = False, revision: str = "HEAD") -> None:
    expected = render_manifest()
    actual = MANIFEST.read_text(encoding="utf-8") if MANIFEST.is_file() else ""
    if actual != expected:
        raise RuntimeError("Tracked manifest is stale or mismatched")
    if require_tracked:
        manifest_paths = set(manifest_entries()) | {MANIFEST.name}
        tracked = tracked_paths(revision)
        if tracked != manifest_paths:
            missing = sorted(manifest_paths - tracked)
            unexpected = sorted(tracked - manifest_paths)
            raise RuntimeError(
                f"Tracked inventory differs from manifest: missing={missing}, unexpected={unexpected}"
            )


def assert_clean_worktree() -> None:
    flags = git(["ls-files", "-v", "-z"], binary=True)
    assert isinstance(flags, bytes)
    hidden = []
    for record in flags.split(b"\0"):
        if not record:
            continue
        tag = record[:1]
        if tag == b"S" or tag.islower():
            hidden.append(record[2:].decode("utf-8", errors="replace"))
    if hidden:
        raise RuntimeError(
            "Index flags that can hide worktree changes block the release: " + ", ".join(hidden)
        )
    status = str(git(["status", "--porcelain=v1", "--untracked-files=all"]))
    if status.strip():
        raise RuntimeError(f"Dirty or unexplained worktree blocks the release.\n{status}")


def assert_tag_absent(tag: str) -> None:
    completed = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
        cwd=ROOT,
        env=git_environment(),
        check=False,
    )
    if completed.returncode == 0:
        raise RuntimeError(f"Release tag already exists: {tag}")
    if completed.returncode != 1:
        raise RuntimeError(f"Unable to determine whether release tag exists: {tag}")


def tag_identity(tag: str, *, require_head: bool = True) -> dict[str, str]:
    object_type = str(git(["cat-file", "-t", f"refs/tags/{tag}"])).strip()
    if object_type != "tag":
        raise RuntimeError(f"Release tag must be annotated; observed object type {object_type!r}")
    tag_object = str(git(["rev-parse", f"refs/tags/{tag}"])).strip()
    commit = str(git(["rev-parse", f"refs/tags/{tag}^{{commit}}"])).strip()
    tag_payload = str(git(["cat-file", "-p", f"refs/tags/{tag}"]))
    header_block = tag_payload.partition("\n\n")[0]
    header_lines = header_block.splitlines()
    expected_keys = ["object", "type", "tag", "tagger"]
    observed_keys = [line.split(" ", 1)[0] for line in header_lines]
    if observed_keys != expected_keys or any(" " not in line for line in header_lines):
        raise RuntimeError(
            f"Release tag {tag} must use exactly one canonical object/type/tag/tagger header"
        )
    headers = dict(line.split(" ", 1) for line in header_lines)
    if headers.get("type") != "commit" or headers.get("object") != commit:
        raise RuntimeError(f"Release tag {tag} must directly target a commit")
    if headers.get("tag") != tag:
        raise RuntimeError(f"Annotated tag's internal name differs from {tag}")
    tree = str(git(["rev-parse", f"{commit}^{{tree}}"])).strip()
    head = str(git(["rev-parse", "HEAD"])).strip()
    if require_head and commit != head:
        raise RuntimeError(f"Tag {tag} targets {commit}, not current HEAD {head}")
    return {"tag_object": tag_object, "commit": commit, "tree": tree}


def verify_github_repository_context(spec: dict[str, Any]) -> None:
    """Bind a GitHub Actions run to the repository declared by the release."""
    server = os.environ.get("GITHUB_SERVER_URL")
    repository = os.environ.get("GITHUB_REPOSITORY")
    repository_id = os.environ.get("GITHUB_REPOSITORY_ID")
    in_actions = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
    if in_actions and (not server or not repository or not repository_id):
        raise RuntimeError("GitHub Actions repository context is incomplete")
    if not server and not repository:
        return
    if not server or not repository:
        raise RuntimeError("GitHub repository context is incomplete")
    observed = f"{server.rstrip('/')}/{repository.strip('/')}"
    expected = str(spec["repository"]).rstrip("/")
    if observed.casefold() != expected.casefold():
        raise RuntimeError(
            f"GitHub repository context {observed!r} does not equal declared repository {expected!r}"
        )
    expected_id = str(spec["repository_id"])
    if repository_id not in {None, "", expected_id}:
        raise RuntimeError(
            f"GitHub repository ID {repository_id!r} does not equal declared ID {expected_id!r}"
        )
    if in_actions and repository_id != expected_id:
        raise RuntimeError(
            f"GitHub repository ID {repository_id!r} does not equal declared ID {expected_id!r}"
        )


def github_release_tag_event(
    spec: dict[str, Any], *, required: bool
) -> tuple[str, str] | None:
    """Return the exact GitHub tag ref and peeled event commit, when applicable."""
    in_actions = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
    if not in_actions:
        if required:
            raise RuntimeError("Release-tag restoration requires GitHub Actions")
        return None
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    if event_name != "push":
        raise RuntimeError(
            f"GitHub release verification requires a push event, observed {event_name!r}"
        )
    ref_type = os.environ.get("GITHUB_REF_TYPE")
    if ref_type != "tag":
        raise RuntimeError(f"GitHub release verification requires a tag ref, observed {ref_type!r}")
    tag = str(spec["tag"])
    ref_name = os.environ.get("GITHUB_REF_NAME")
    if ref_name != tag:
        raise RuntimeError(
            f"GitHub tag name {ref_name!r} does not equal declared release tag {tag!r}"
        )
    expected_ref = f"refs/tags/{tag}"
    observed_ref = os.environ.get("GITHUB_REF")
    if observed_ref != expected_ref:
        raise RuntimeError(
            f"GitHub tag ref {observed_ref!r} does not equal declared ref {expected_ref!r}"
        )
    verify_github_repository_context(spec)
    event_commit = os.environ.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", event_commit):
        raise RuntimeError("GitHub release verification is missing a canonical GITHUB_SHA")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GitHub release verification is missing GITHUB_EVENT_PATH")
    try:
        payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError("GitHub push-event payload is unreadable or invalid") from error
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub push-event payload must be a JSON object")
    if payload.get("ref") != expected_ref:
        raise RuntimeError("GitHub push-event ref does not equal the declared release ref")
    if payload.get("created") is not True:
        raise RuntimeError("Release-tag verification requires a new-ref creation event")
    if payload.get("deleted") is not False:
        raise RuntimeError("Release-tag verification rejects tag-deletion events")
    if payload.get("forced") is not False:
        raise RuntimeError("Release-tag verification rejects forced tag updates")
    if payload.get("before") != "0" * 40:
        raise RuntimeError("Release-tag verification requires an absent prior ref")
    if payload.get("after") != event_commit:
        raise RuntimeError("GitHub push-event after value does not equal GITHUB_SHA")
    payload_repository = payload.get("repository")
    payload_full_name = (
        payload_repository.get("full_name") if isinstance(payload_repository, dict) else None
    )
    if not isinstance(payload_full_name, str) or payload_full_name.casefold() != str(
        os.environ["GITHUB_REPOSITORY"]
    ).casefold():
        raise RuntimeError("GitHub push-event repository does not equal GITHUB_REPOSITORY")
    payload_repository_id = (
        payload_repository.get("id") if isinstance(payload_repository, dict) else None
    )
    if payload_repository_id != spec["repository_id"]:
        raise RuntimeError("GitHub push-event repository ID does not equal the declared ID")
    return expected_ref, event_commit


def restore_authoritative_release_tag() -> dict[str, str]:
    """Replace checkout's runner-local tag ref from the declared repository."""
    verify_python_runtime()
    verify_git_runtime()
    spec = release_spec()
    event = github_release_tag_event(spec, required=True)
    if event is None:  # pragma: no cover - required=True makes this unreachable
        raise RuntimeError("GitHub tag event context is unavailable")
    expected_ref, event_commit = event
    git(
        [
            "fetch",
            "--no-tags",
            "--no-recurse-submodules",
            str(spec["repository"]),
            f"+{expected_ref}:{expected_ref}",
        ]
    )
    identity = tag_identity(str(spec["tag"]), require_head=True)
    if event_commit != identity["commit"]:
        raise RuntimeError(
            f"GitHub event commit {event_commit!r} does not equal restored tag commit "
            f"{identity['commit']!r}"
        )
    return identity


def verify_release_tag(ref_name: str) -> None:
    """Verify an offline tag event against the exact declared release identity."""
    verify_python_runtime()
    verify_git_runtime()
    spec = release_spec()
    if ref_name != spec["tag"]:
        raise RuntimeError(
            f"Tag event {ref_name!r} does not equal declared release tag {spec['tag']!r}"
        )
    event = github_release_tag_event(spec, required=False)
    ref_type = os.environ.get("GITHUB_REF_TYPE")
    if event is None and ref_type not in {None, "", "tag"}:
        raise RuntimeError(f"Release-tag verification received ref type {ref_type!r}")
    if event is None:
        verify_github_repository_context(spec)
    identity = tag_identity(spec["tag"], require_head=True)
    if event is not None:
        _, event_commit = event
        if event_commit != identity["commit"]:
            raise RuntimeError(
                f"GitHub event commit {event_commit!r} does not equal tagged commit {identity['commit']!r}"
            )
    assert_clean_worktree()
    verify_manifest(require_tracked=True, revision=identity["commit"])


def assert_safe_archive_member(name: str, *, is_file: bool, is_directory: bool) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise RuntimeError(f"Unsafe archive path: {name!r}")
    if any(part in {".git", "__pycache__", ".pytest_cache", ".venv", "dist", "tmp"} for part in path.parts):
        raise RuntimeError(f"Excluded path present in archive: {name!r}")
    if not (is_file or is_directory):
        raise RuntimeError(f"Archive links/devices are forbidden: {name!r}")


def canonical_source_archive_bytes(commit: str, *, prefix: str, epoch: int) -> bytes:
    tar_bytes = git(["archive", "--format=tar", f"--prefix={prefix}/", commit], binary=True)
    assert isinstance(tar_bytes, bytes)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as archive:
        for member in archive.getmembers():
            assert_safe_archive_member(
                member.name, is_file=member.isfile(), is_directory=member.isdir()
            )
    output = io.BytesIO()
    with gzip.GzipFile(
        filename="", fileobj=output, mode="wb", compresslevel=9, mtime=epoch
    ) as compressed:
        compressed.write(tar_bytes)
    return output.getvalue()


def build_source_archive(commit: str, destination: Path, *, prefix: str, epoch: int) -> None:
    atomic_write_repository_bytes(
        destination,
        canonical_source_archive_bytes(commit, prefix=prefix, epoch=epoch),
    )


def parse_sha256sums(path: Path) -> dict[str, str]:
    sums: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        if separator != "  " or len(digest) != 64 or name in sums:
            raise RuntimeError(f"Malformed checksum line: {line!r}")
        sums[name] = digest
    return sums


def verify_archive(path: Path, *, commit: str, prefix: str, epoch: int) -> None:
    expected_archive = canonical_source_archive_bytes(commit, prefix=prefix, epoch=epoch)
    if path.read_bytes() != expected_archive:
        raise RuntimeError("Source archive is not the exact canonical tagged build")
    tracked = tracked_paths(commit)
    entries = manifest_entries()
    expected_files = tracked
    observed_files: set[str] = set()
    with tarfile.open(path, mode="r:gz") as archive:
        for member in archive.getmembers():
            assert_safe_archive_member(
                member.name, is_file=member.isfile(), is_directory=member.isdir()
            )
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] != prefix:
                raise RuntimeError(f"Archive member lacks exact prefix {prefix!r}: {member.name}")
            relative = PurePosixPath(*parts[1:]).as_posix()
            if member.isdir():
                continue
            observed_files.add(relative)
            extracted = archive.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"Cannot read archive member {member.name}")
            data = extracted.read()
            if relative == MANIFEST.name:
                if sha256_bytes(data) != sha256(MANIFEST):
                    raise RuntimeError("Archived manifest bytes differ from release commit")
            elif entries.get(relative) != sha256_bytes(data):
                raise RuntimeError(f"Archived file fails tracked manifest: {relative}")
    if observed_files != expected_files:
        raise RuntimeError(
            f"Archive inventory mismatch: missing={sorted(expected_files-observed_files)}, "
            f"unexpected={sorted(observed_files-expected_files)}"
        )


def verify_git_archive_inventory() -> None:
    verify_python_runtime()
    verify_git_runtime()
    verify_manifest(require_tracked=True)
    destination = ROOT / "tmp" / "git-archive-inventory.tar.gz"
    ensure_safe_directory(destination.parent)
    assert_safe_repository_descendant(destination)
    build_source_archive(
        "HEAD",
        destination,
        prefix="SPPT_ASTRA_inventory_check",
        epoch=int(release_spec()["build_epoch_unix"]),
    )
    verify_archive(
        destination,
        commit="HEAD",
        prefix="SPPT_ASTRA_inventory_check",
        epoch=int(release_spec()["build_epoch_unix"]),
    )
    print("Git-archive inventory and manifest bytes verified.")


def is_link_or_junction(path: Path) -> bool:
    junction_check = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(junction_check and junction_check())


def assert_safe_repository_descendant(path: Path) -> None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError(f"Output path is outside the repository: {path}") from exc
    expected = ROOT.resolve().joinpath(*relative.parts)
    current = ROOT
    for part in relative.parts:
        current /= part
        if is_link_or_junction(current):
            raise RuntimeError(f"Unsafe symbolic link or junction in output path: {current}")
        if current != path and current.exists() and not current.is_dir():
            raise RuntimeError(f"Non-directory component in output path: {current}")
    if path.resolve() != expected:
        raise RuntimeError(f"Output path resolves outside its expected location: {path}")


def ensure_safe_directory(path: Path) -> None:
    assert_safe_repository_descendant(path)
    if path.exists() and not path.is_dir():
        raise RuntimeError(f"Expected output directory but found a non-directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    assert_safe_repository_descendant(path)


def atomic_write_repository_bytes(destination: Path, value: bytes) -> None:
    ensure_safe_directory(destination.parent)
    assert_safe_repository_descendant(destination)
    if destination.exists() and not destination.is_file():
        raise RuntimeError(f"Expected output file but found a non-file: {destination}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    assert_safe_repository_descendant(destination)


def assert_safe_distribution_directory() -> None:
    expected = ROOT / "dist"
    observed_lexical = os.path.normcase(os.path.abspath(DIST))
    expected_lexical = os.path.normcase(os.path.abspath(expected))
    if observed_lexical != expected_lexical:
        raise RuntimeError(f"Unsafe or unexpected distribution directory: {DIST}")
    try:
        assert_safe_repository_descendant(DIST)
    except RuntimeError as exc:
        raise RuntimeError(f"Unsafe or unexpected distribution directory: {DIST}") from exc


def assert_safe_release_asset_directory(directory: Path) -> None:
    """Admit only the canonical dist root or a direct temporary staging sibling."""
    observed = os.path.normcase(os.path.abspath(directory))
    canonical = os.path.normcase(os.path.abspath(ROOT / "dist"))
    if observed == canonical:
        assert_safe_distribution_directory()
    else:
        temporary_root = ROOT / "tmp"
        try:
            relative = directory.relative_to(temporary_root)
        except ValueError as exc:
            raise RuntimeError(f"Unsafe release staging directory: {directory}") from exc
        if len(relative.parts) != 1 or not directory.name.startswith("release-dist-"):
            raise RuntimeError(f"Unsafe release staging directory: {directory}")
        assert_safe_repository_descendant(directory)
    if not directory.is_dir():
        raise RuntimeError(f"Release asset directory is missing or not a directory: {directory}")


def admitted_release_items(directory: Path, allowlist: set[str]) -> list[Path]:
    assert_safe_release_asset_directory(directory)
    items = list(directory.iterdir())
    unexpected = [
        path
        for path in items
        if is_link_or_junction(path) or not path.is_file() or path.name not in allowlist
    ]
    if unexpected:
        raise RuntimeError(
            "Unexpected item in disposable release directory: "
            + ", ".join(str(path) for path in unexpected)
        )
    return items


def remove_admitted_release_directory(directory: Path, allowlist: set[str]) -> None:
    for path in admitted_release_items(directory, allowlist):
        path.unlink()
    directory.rmdir()


def clear_dist(allowlist: set[str]) -> None:
    assert_safe_distribution_directory()
    ensure_safe_directory(DIST)
    assert_safe_distribution_directory()
    for path in admitted_release_items(DIST, allowlist):
        path.unlink()


def install_staged_distribution(staging: Path, allowlist: set[str]) -> None:
    """Atomically install a verified roster, restoring the prior dist on failure."""
    assert_safe_release_asset_directory(staging)
    assert_safe_distribution_directory()
    previous: Path | None = None
    if DIST.exists():
        if not DIST.is_dir():
            raise RuntimeError(f"Expected distribution directory but found a non-directory: {DIST}")
        admitted_release_items(DIST, allowlist)
        previous = staging.with_name(f"{staging.name}-previous")
        if previous.exists():
            raise RuntimeError(f"Reserved release backup path already exists: {previous}")
        os.replace(DIST, previous)
    try:
        os.replace(staging, DIST)
        verify_release_assets(DIST)
    except Exception:
        if DIST.exists():
            os.replace(DIST, staging)
        if previous is not None and previous.exists():
            os.replace(previous, DIST)
        raise
    if previous is not None:
        remove_admitted_release_directory(previous, allowlist)


def build_release_assets() -> None:
    verify_python_runtime()
    verify_git_runtime()
    spec = release_spec()
    allowlist = validated_release_allowlist(spec)
    allowset = set(allowlist)
    assert_clean_worktree()
    identity = tag_identity(spec["tag"], require_head=True)
    verify_manifest(require_tracked=True, revision=identity["commit"])
    source_assets = {
        allowlist[0]: ROOT / "manuscript" / allowlist[0],
        allowlist[1]: ROOT / "manuscript" / allowlist[1],
        allowlist[2]: ROOT / "manuscript" / allowlist[2],
        allowlist[3]: ROOT / "manuscript" / allowlist[3],
    }
    for source in source_assets.values():
        if not source.is_file():
            raise RuntimeError(f"Missing release document: {source}")
    staging_parent = ROOT / "tmp"
    ensure_safe_directory(staging_parent)
    staging = Path(tempfile.mkdtemp(prefix="release-dist-", dir=staging_parent))
    assert_safe_release_asset_directory(staging)
    try:
        for name, source in source_assets.items():
            shutil.copyfile(source, staging / name)

        archive_name = allowlist[4]
        archive_prefix = f"SPPT_ASTRA_v{spec['version']}"
        build_source_archive(
            identity["commit"],
            staging / archive_name,
            prefix=archive_prefix,
            epoch=int(spec["build_epoch_unix"]),
        )

        checksum_names = allowlist[:5]
        checksum_text = (
            "\n".join(f"{sha256(staging / name)}  {name}" for name in checksum_names) + "\n"
        )
        checksum_path = staging / "SHA256SUMS"
        checksum_path.write_text(checksum_text, encoding="utf-8", newline="\n")

        detached = expected_detached_identity(spec, identity, allowlist, staging)
        identity_path = staging / allowlist[6]
        identity_path.write_bytes(canonical_json_bytes(detached))
        verify_release_assets(staging)
        install_staged_distribution(staging, allowset)
    except Exception:
        if staging.exists():
            try:
                remove_admitted_release_directory(staging, allowset)
            except RuntimeError:
                pass
        raise
    print("Built and verified the exact seven-asset release roster.")


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def tagged_file_bytes(commit: str, relative: PurePosixPath) -> bytes:
    value = git(["show", f"{commit}:{relative.as_posix()}"], binary=True)
    assert isinstance(value, bytes)
    return value


def expected_detached_identity(
    spec: dict[str, Any],
    identity: dict[str, str],
    allowlist: list[str],
    distribution: Path | None = None,
) -> dict[str, Any]:
    if distribution is None:
        distribution = DIST
    bound_assets = [
        {
            "name": name,
            "bytes": (distribution / name).stat().st_size,
            "sha256": sha256(distribution / name),
        }
        for name in allowlist[:6]
    ]
    return {
        "schema": IDENTITY_SCHEMA,
        "repository": spec["repository"],
        "repository_id": spec["repository_id"],
        "version": spec["version"],
        "tag": spec["tag"],
        "annotated_tag_object": identity["tag_object"],
        "commit": identity["commit"],
        "tree": identity["tree"],
        "tracked_manifest": {
            "name": MANIFEST.name,
            "bytes": MANIFEST.stat().st_size,
            "sha256": sha256(MANIFEST),
        },
        "release_date": spec["release_date"],
        "build_epoch": spec["build_epoch"],
        "assets": bound_assets,
        "sha256sums_sha256": sha256(distribution / "SHA256SUMS"),
        "identity_excludes_self": True,
    }


def verify_release_assets(distribution: Path | None = None) -> None:
    verify_python_runtime()
    verify_git_runtime()
    spec = release_spec()
    allowlist = validated_release_allowlist(spec)
    if distribution is None:
        distribution = DIST
    assert_safe_release_asset_directory(distribution)
    items = list(distribution.iterdir())
    if any(is_link_or_junction(path) or not path.is_file() for path in items):
        raise RuntimeError("Release distribution contains a link or non-file item")
    roster = sorted(path.name for path in items)
    if roster != sorted(allowlist):
        raise RuntimeError(f"Release asset roster mismatch: {roster}")
    identity_path = distribution / allowlist[6]
    detached = json.loads(identity_path.read_text(encoding="utf-8"))
    identity = tag_identity(spec["tag"], require_head=True)
    for name in allowlist[:4]:
        relative = PurePosixPath("manuscript") / name
        if (distribution / name).read_bytes() != tagged_file_bytes(identity["commit"], relative):
            raise RuntimeError(f"Release document differs from tagged manuscript: {relative}")
    for key, expected in (
        ("schema", IDENTITY_SCHEMA),
        ("repository", spec["repository"]),
        ("repository_id", spec["repository_id"]),
        ("version", spec["version"]),
        ("tag", spec["tag"]),
        ("annotated_tag_object", identity["tag_object"]),
        ("commit", identity["commit"]),
        ("tree", identity["tree"]),
        ("release_date", spec["release_date"]),
        ("build_epoch", spec["build_epoch"]),
    ):
        if detached.get(key) != expected:
            raise RuntimeError(f"Detached release identity mismatch for {key}")
    if detached.get("identity_excludes_self") is not True:
        raise RuntimeError("Detached identity must explicitly exclude its own hash")
    manifest_record = detached.get("tracked_manifest", {})
    if manifest_record != {
        "name": MANIFEST.name,
        "bytes": MANIFEST.stat().st_size,
        "sha256": sha256(MANIFEST),
    }:
        raise RuntimeError("Detached identity tracked-manifest mismatch")
    sums_path = distribution / "SHA256SUMS"
    if detached.get("sha256sums_sha256") != sha256(sums_path):
        raise RuntimeError("Detached identity SHA256SUMS mismatch")
    sums = parse_sha256sums(sums_path)
    if set(sums) != set(allowlist[:5]):
        raise RuntimeError("SHA256SUMS roster mismatch")
    for name, digest in sums.items():
        if sha256(distribution / name) != digest:
            raise RuntimeError(f"Release asset checksum mismatch: {name}")
    expected_records = [
        {
            "name": name,
            "bytes": (distribution / name).stat().st_size,
            "sha256": sha256(distribution / name),
        }
        for name in allowlist[:6]
    ]
    if detached.get("assets") != expected_records:
        raise RuntimeError("Detached identity asset records mismatch")
    expected_detached = expected_detached_identity(spec, identity, allowlist, distribution)
    if identity_path.read_bytes() != canonical_json_bytes(expected_detached):
        raise RuntimeError("Detached release identity is not the exact canonical expected object")
    verify_archive(
        distribution / allowlist[4],
        commit=identity["commit"],
        prefix=f"SPPT_ASTRA_v{spec['version']}",
        epoch=int(spec["build_epoch_unix"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("write-manifest")
    verify_manifest_parser = subparsers.add_parser("verify-manifest")
    verify_manifest_parser.add_argument("--tracked", action="store_true")
    subparsers.add_parser("pretag")
    subparsers.add_parser("restore-tag-ref")
    verify_tag_parser = subparsers.add_parser("verify-tag")
    verify_tag_parser.add_argument("--ref-name")
    subparsers.add_parser("verify-git-archive")
    subparsers.add_parser("build-assets")
    subparsers.add_parser("verify-assets")
    args = parser.parse_args()
    if args.command == "write-manifest":
        write_manifest()
    elif args.command == "verify-manifest":
        if args.tracked:
            verify_git_runtime()
        verify_manifest(require_tracked=args.tracked)
        if args.tracked:
            print("Manifest bytes and tracked Git inventory verified.")
        else:
            print("Manifest bytes verified against admitted public files.")
    elif args.command == "pretag":
        verify_git_runtime()
        spec = release_spec()
        assert_clean_worktree()
        verify_manifest(require_tracked=True)
        assert_tag_absent(spec["tag"])
        print(f"Pre-tag gate passed for locally absent annotated tag {spec['tag']}.")
    elif args.command == "restore-tag-ref":
        identity = restore_authoritative_release_tag()
        print(
            "Restored authoritative annotated release tag "
            f"{identity['tag_object']} at commit {identity['commit']}."
        )
    elif args.command == "verify-tag":
        ref_name = args.ref_name or os.environ.get("GITHUB_REF_NAME", "")
        verify_release_tag(ref_name)
        print(f"Annotated release tag {ref_name} directly targets the verified HEAD commit.")
    elif args.command == "verify-git-archive":
        verify_git_archive_inventory()
    elif args.command == "build-assets":
        build_release_assets()
    elif args.command == "verify-assets":
        verify_python_runtime()
        verify_git_runtime()
        assert_clean_worktree()
        verify_manifest(require_tracked=True)
        verify_release_assets()
        print("Release assets and detached identity verified.")


if __name__ == "__main__":
    main()
