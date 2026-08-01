"""Mechanical manifest, deterministic archive, and detached release identity tooling."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from tools.check_repository import public_files
except ModuleNotFoundError:  # Direct execution from tools/.
    from check_repository import public_files

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
MANIFEST = ROOT / "MANIFEST.sha256"
SPEC_PATH = ROOT / "RELEASE_SPEC.json"
RUNTIME_PATH = ROOT / "RUNTIME.json"
IDENTITY_SCHEMA = "https://github.com/jkolantree/astra/schemas/release-identity-v1"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(arguments: list[str], *, cwd: Path | None = None, binary: bool = False) -> str | bytes:
    environment = os.environ.copy()
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    completed = subprocess.run(
        ["git", *arguments],
        cwd=cwd or ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


def verify_git_runtime() -> None:
    runtime = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    expected = runtime["git"]
    completed = subprocess.run(
        ["git", "version", "--build-options"], check=True, capture_output=True, text=True
    )
    lines = completed.stdout.splitlines()
    version = lines[0].removeprefix("git version ") if lines else ""
    build_match = re.search(r"(?m)^built from commit: ([0-9a-f]{40})$", completed.stdout)
    executable = shutil.which("git")
    observed = {
        "version": version,
        "build_commit": build_match.group(1) if build_match else "",
        "executable_sha256": sha256(Path(executable)) if executable else "",
    }
    required = {key: expected[key] for key in observed}
    if observed != required:
        raise RuntimeError(f"Git runtime drift: expected {required}, observed {observed}")


def release_spec() -> dict[str, Any]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


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
    MANIFEST.write_text(render_manifest(), encoding="utf-8", newline="\n")
    print(f"Wrote {MANIFEST.name} mechanically from admitted public files.")


def tracked_paths(revision: str = "HEAD") -> set[str]:
    output = str(git(["ls-tree", "-r", "--name-only", revision]))
    return {line for line in output.splitlines() if line}


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
    status = str(git(["status", "--porcelain=v1", "--untracked-files=all"]))
    if status.strip():
        raise RuntimeError(f"Dirty or unexplained worktree blocks the release.\n{status}")


def assert_tag_absent(tag: str) -> None:
    completed = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode == 0:
        raise RuntimeError(f"Release tag already exists: {tag}")


def tag_identity(tag: str, *, require_head: bool = True) -> dict[str, str]:
    object_type = str(git(["cat-file", "-t", f"refs/tags/{tag}"])).strip()
    if object_type != "tag":
        raise RuntimeError(f"Release tag must be annotated; observed object type {object_type!r}")
    tag_object = str(git(["rev-parse", f"refs/tags/{tag}"])).strip()
    commit = str(git(["rev-parse", f"refs/tags/{tag}^{{commit}}"])).strip()
    tree = str(git(["rev-parse", f"{commit}^{{tree}}"])).strip()
    head = str(git(["rev-parse", "HEAD"])).strip()
    if require_head and commit != head:
        raise RuntimeError(f"Tag {tag} targets {commit}, not current HEAD {head}")
    return {"tag_object": tag_object, "commit": commit, "tree": tree}


def assert_safe_archive_member(name: str, *, is_file: bool, is_directory: bool) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise RuntimeError(f"Unsafe archive path: {name!r}")
    if any(part in {".git", "__pycache__", ".pytest_cache", ".venv", "dist", "tmp"} for part in path.parts):
        raise RuntimeError(f"Excluded path present in archive: {name!r}")
    if not (is_file or is_directory):
        raise RuntimeError(f"Archive links/devices are forbidden: {name!r}")


def build_source_archive(commit: str, destination: Path, *, prefix: str, epoch: int) -> None:
    tar_bytes = git(["archive", "--format=tar", f"--prefix={prefix}/", commit], binary=True)
    assert isinstance(tar_bytes, bytes)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as archive:
        for member in archive.getmembers():
            assert_safe_archive_member(
                member.name, is_file=member.isfile(), is_directory=member.isdir()
            )
    with destination.open("wb") as raw:
        with gzip.GzipFile(
            filename="", fileobj=raw, mode="wb", compresslevel=9, mtime=epoch
        ) as compressed:
            compressed.write(tar_bytes)


def parse_sha256sums(path: Path) -> dict[str, str]:
    sums: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        if separator != "  " or len(digest) != 64 or name in sums:
            raise RuntimeError(f"Malformed checksum line: {line!r}")
        sums[name] = digest
    return sums


def verify_archive(path: Path, *, commit: str, prefix: str) -> None:
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
    verify_git_runtime()
    verify_manifest(require_tracked=True)
    destination = ROOT / "tmp" / "git-archive-inventory.tar.gz"
    destination.parent.mkdir(parents=True, exist_ok=True)
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
    )
    print("Git-archive inventory and manifest bytes verified.")


def clear_dist(allowlist: set[str]) -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    resolved_dist = DIST.resolve()
    if resolved_dist != (ROOT / "dist").resolve():
        raise RuntimeError(f"Unexpected distribution directory: {resolved_dist}")
    for path in DIST.iterdir():
        if path.is_symlink() or not path.is_file() or path.name not in allowlist:
            raise RuntimeError(f"Unexpected item in disposable dist directory: {path}")
        path.unlink()


def build_release_assets() -> None:
    verify_git_runtime()
    spec = release_spec()
    allowlist = list(spec["release_asset_allowlist"])
    allowset = set(allowlist)
    if len(allowlist) != 7 or len(allowset) != 7:
        raise RuntimeError("Release asset allowlist must have exactly seven unique entries")
    assert_clean_worktree()
    identity = tag_identity(spec["tag"], require_head=True)
    verify_manifest(require_tracked=True, revision=identity["commit"])
    clear_dist(allowset)

    source_assets = {
        allowlist[0]: ROOT / "manuscript" / allowlist[0],
        allowlist[1]: ROOT / "manuscript" / allowlist[1],
        allowlist[2]: ROOT / "manuscript" / allowlist[2],
        allowlist[3]: ROOT / "manuscript" / allowlist[3],
    }
    for name, source in source_assets.items():
        if not source.is_file():
            raise RuntimeError(f"Missing release document: {source}")
        shutil.copyfile(source, DIST / name)

    archive_name = allowlist[4]
    archive_prefix = f"SPPT_ASTRA_v{spec['version']}"
    build_source_archive(
        identity["commit"],
        DIST / archive_name,
        prefix=archive_prefix,
        epoch=int(spec["build_epoch_unix"]),
    )

    checksum_names = allowlist[:5]
    checksum_text = "\n".join(f"{sha256(DIST / name)}  {name}" for name in checksum_names) + "\n"
    checksum_path = DIST / "SHA256SUMS"
    checksum_path.write_text(checksum_text, encoding="utf-8", newline="\n")

    detached = expected_detached_identity(spec, identity, allowlist)
    identity_path = DIST / allowlist[6]
    identity_path.write_bytes(canonical_json_bytes(detached))
    verify_release_assets()
    print("Built and verified the exact seven-asset release roster.")


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def expected_detached_identity(
    spec: dict[str, Any], identity: dict[str, str], allowlist: list[str]
) -> dict[str, Any]:
    bound_assets = [
        {"name": name, "bytes": (DIST / name).stat().st_size, "sha256": sha256(DIST / name)}
        for name in allowlist[:6]
    ]
    return {
        "schema": IDENTITY_SCHEMA,
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
        "build_epoch": spec["build_epoch"],
        "assets": bound_assets,
        "sha256sums_sha256": sha256(DIST / "SHA256SUMS"),
        "identity_excludes_self": True,
    }


def verify_release_assets() -> None:
    spec = release_spec()
    allowlist = list(spec["release_asset_allowlist"])
    roster = sorted(path.name for path in DIST.iterdir() if path.is_file())
    if roster != sorted(allowlist):
        raise RuntimeError(f"Release asset roster mismatch: {roster}")
    identity_path = DIST / allowlist[6]
    detached = json.loads(identity_path.read_text(encoding="utf-8"))
    identity = tag_identity(spec["tag"], require_head=True)
    for key, expected in (
        ("schema", IDENTITY_SCHEMA),
        ("version", spec["version"]),
        ("tag", spec["tag"]),
        ("annotated_tag_object", identity["tag_object"]),
        ("commit", identity["commit"]),
        ("tree", identity["tree"]),
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
    sums_path = DIST / "SHA256SUMS"
    if detached.get("sha256sums_sha256") != sha256(sums_path):
        raise RuntimeError("Detached identity SHA256SUMS mismatch")
    sums = parse_sha256sums(sums_path)
    if set(sums) != set(allowlist[:5]):
        raise RuntimeError("SHA256SUMS roster mismatch")
    for name, digest in sums.items():
        if sha256(DIST / name) != digest:
            raise RuntimeError(f"Release asset checksum mismatch: {name}")
    expected_records = [
        {"name": name, "bytes": (DIST / name).stat().st_size, "sha256": sha256(DIST / name)}
        for name in allowlist[:6]
    ]
    if detached.get("assets") != expected_records:
        raise RuntimeError("Detached identity asset records mismatch")
    expected_detached = expected_detached_identity(spec, identity, allowlist)
    if identity_path.read_bytes() != canonical_json_bytes(expected_detached):
        raise RuntimeError("Detached release identity is not the exact canonical expected object")
    verify_archive(
        DIST / allowlist[4],
        commit=identity["commit"],
        prefix=f"SPPT_ASTRA_v{spec['version']}",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("write-manifest")
    verify_manifest_parser = subparsers.add_parser("verify-manifest")
    verify_manifest_parser.add_argument("--tracked", action="store_true")
    subparsers.add_parser("pretag")
    subparsers.add_parser("verify-git-archive")
    subparsers.add_parser("build-assets")
    subparsers.add_parser("verify-assets")
    args = parser.parse_args()
    if args.command == "write-manifest":
        write_manifest()
    elif args.command == "verify-manifest":
        verify_manifest(require_tracked=args.tracked)
        print("Tracked manifest verified.")
    elif args.command == "pretag":
        spec = release_spec()
        assert_clean_worktree()
        verify_manifest(require_tracked=True)
        assert_tag_absent(spec["tag"])
        print(f"Pre-tag gate passed for unused annotated tag {spec['tag']}.")
    elif args.command == "verify-git-archive":
        verify_git_archive_inventory()
    elif args.command == "build-assets":
        build_release_assets()
    elif args.command == "verify-assets":
        assert_clean_worktree()
        verify_manifest(require_tracked=True)
        verify_release_assets()
        print("Release assets and detached identity verified.")


if __name__ == "__main__":
    main()
