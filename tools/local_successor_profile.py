"""Explicit local successor checks, separate from historical release admission."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_INVENTORY_SHA256 = "e30cd7caf9786b91f61a8aa12363a97048b4c441faeddbc0841ed17019100725"
BASE_MAP_SHA256 = "fb4a786729cb372372de6afe84f586ab903d3bd6f9ca73d907cef17310fd9bf6"
RECONCILIATION_SHA256 = "1158b6ccc4417d17f79082e68a332696d67b26776a0f3dfc5e367221b8ac5a3c"
SUCCESSOR_BASE_MAP_SHA256 = "dc5d2eccdeb367c272e2637eb79d7a84a82802a7cc75651e2f2b7df0f4cdb974"
MODIFIED_PATHS = frozenset(("tools/check_repository.py", "tools/verify_linux_companion.py"))
ADDED_PATHS = frozenset(("tools/local_successor_profile.py",))
LOCAL_ONLY_PATHS = frozenset([
    "manuscript/integrated-core-v1.1.0-alpha.1/README.md",
    "manuscript/integrated-core-v1.1.0-alpha.1/document-plan.json",
    "manuscript/integrated-core-v1.1.0-alpha.1/figure-inputs.json",
    "manuscript/integrated-core-v1.1.0-alpha.1/manuscript.md",
    "manuscript/integrated-core-v1.1.0-alpha.1/snapshot-roster.json",
    "manuscript/integrated-core-v1.1.0-alpha.1/source-snapshot.json",
    "manuscript/integrated-core-v1.1.0-alpha.1/supplement.md",
    "manuscript/integrated-draft/README.md",
    "manuscript/integrated-draft/document-plan.json",
    "manuscript/integrated-draft/figure-inputs.json",
    "manuscript/integrated-draft/manuscript.md",
    "manuscript/integrated-draft/source-snapshot.json",
    "manuscript/integrated-draft/supplement.md",
    "resources/integrated-core/v1.1.0-alpha.1/ADMISSION.json",
    "resources/integrated-core/v1.1.0-alpha.1/ADMISSION.md",
    "resources/integrated-core/v1.1.0-alpha.1/CITATION.cff",
    "resources/integrated-core/v1.1.0-alpha.1/LICENSE_BOUNDARIES.md",
    "resources/integrated-core/v1.1.0-alpha.1/PAGES_PLAN.json",
    "resources/integrated-core/v1.1.0-alpha.1/README.md",
    "resources/integrated-core/v1.1.0-alpha.1/RELEASE_NOTES.md",
    "resources/integrated-core/v1.1.0-alpha.1/RELEASE_SPEC.json",
    "resources/integrated-core/v1.1.0-alpha.1/VERSION.json",
    "resources/integrated-core/v1.1.0-alpha.1/build_documents.py",
    "resources/integrated-core/v1.1.0-alpha.1/diagram-specs.json",
    "resources/integrated-core/v1.1.0-alpha.1/pages-overrides/library/index.html",
    "resources/integrated-core/v1.1.0-alpha.1/produce.py",
    "resources/integrated-core/v1.1.0-alpha.1/render_diagrams.py",
    "resources/integrated-core/v1.1.0-alpha.1/test_successor.py",
    "resources/integrated-core/v1.1.0-alpha.1/validate_release_reports.py",
    "resources/integrated-core/v1.1.0-alpha.1/verify_successor.py",
    "resources/integrated-core/v1.1.0-alpha.1/version.py",
    "resources/integrated-edition-proposal/BOUNDARY_EXPECTATIONS.json",
    "resources/integrated-edition-proposal/CITATION_SUPPORT_DISPOSITION.md",
    "resources/integrated-edition-proposal/CITATION_SUPPORT_DRAFT.json",
    "resources/integrated-edition-proposal/CONTRACT_PROPOSAL.md",
    "resources/integrated-edition-proposal/OUTPUTS.json",
    "resources/integrated-edition-proposal/PAGES_ADMISSION_DRAFT.json",
    "resources/integrated-edition-proposal/PAGES_PROPOSAL.json",
    "resources/integrated-edition-proposal/PORTABLE_INPUTS_DRAFT.json",
    "resources/integrated-edition-proposal/PORTABLE_VALIDATION_DRAFT.json",
    "resources/integrated-edition-proposal/READING_OUTPUTS_DRAFT.json",
    "resources/integrated-edition-proposal/README.md",
    "resources/integrated-edition-proposal/RELEASE_INTEGRATION_DRAFT.md",
    "resources/integrated-edition-proposal/RIGHTS.md",
    "resources/integrated-edition-proposal/RUNTIME_ADMISSION_DRAFT.json",
    "resources/integrated-edition-proposal/RUNTIME_PROPOSAL.json",
    "resources/integrated-edition-proposal/SCM_CASE_IDENTITIES.json",
    "resources/integrated-edition-proposal/SOURCE_ADMISSION_DRAFT.json",
    "resources/integrated-edition-proposal/bootstrap_draft.py",
    "resources/integrated-edition-proposal/check_proposals.py",
    "resources/integrated-edition-proposal/citation-corrections/README.md",
    "resources/integrated-edition-proposal/citation-corrections/atlas-v0.1.0.CITATION.cff",
    "resources/integrated-edition-proposal/diagram-specs.json",
    "resources/integrated-edition-proposal/prepare_runtime_paths.py",
    "resources/integrated-edition-proposal/relocate_draft.py",
    "resources/integrated-edition-proposal/render_diagrams.py",
    "resources/integrated-edition-proposal/review-021/RUNTIME_ROUTING.md",
    "resources/integrated-edition-proposal/review-021/WORKFLOW_REVIEW.md",
    "resources/integrated-edition-proposal/review-021/release-integrated-research.yml.disabled",
    "resources/integrated-edition-proposal/review-021/test_pages_destinations.py",
    "resources/integrated-edition-proposal/review-022/GATEWAY_REVIEW_DRAFT.json",
    "resources/integrated-edition-proposal/review-022/PREVIEW_ROUTES_DRAFT.json",
    "resources/integrated-edition-proposal/review-022/atlas-latest.html",
    "resources/integrated-edition-proposal/review-022/core-latest.html",
    "resources/integrated-edition-proposal/review-022/earth-latest.html",
    "resources/integrated-edition-proposal/review-022/explore-alias.html",
    "resources/integrated-edition-proposal/review-022/preview_gateway.py",
    "resources/integrated-edition-proposal/review-022/published-atlas/README.md",
    "resources/integrated-edition-proposal/review-022/published-atlas/SHA256SUMS",
    "resources/integrated-edition-proposal/review-022/published-atlas/dark-medium-response-atlas-v0.1.0-release-identity.json",
    "resources/integrated-edition-proposal/review-022/published-atlas/dark-medium-response-atlas-v0.1.0-source.tar.gz",
    "resources/integrated-edition-proposal/review-022/schema-index.html",
    "resources/integrated-edition-proposal/review-022/test_preview_gateway.py",
    "resources/integrated-edition-proposal/review-024/CITATION.cff",
    "resources/integrated-edition-proposal/review-024/IDENTITY_AND_BASELINE.md",
    "resources/integrated-edition-proposal/review-024/PAGES_EXPECTATIONS.json",
    "resources/integrated-edition-proposal/review-024/RELEASE_IDENTITY_PROPOSAL.json",
    "resources/integrated-edition-proposal/review-024/release-integrated-core.yml.disabled",
    "resources/integrated-edition-proposal/review-024/runtime_routing.py",
    "resources/integrated-edition-proposal/review-024/successor_contracts.py",
    "resources/integrated-edition-proposal/review-024/test_runtime_routing.py",
    "resources/integrated-edition-proposal/review-024/test_successor_contracts.py",
    "resources/integrated-edition-proposal/test_bootstrap_draft.py",
    "resources/integrated-edition-proposal/test_proposal.py",
    "resources/integrated-edition-proposal/test_proposals.py",
    "resources/integrated-edition-proposal/test_relocation.py",
    "resources/integrated-edition-proposal/validate_reports.py",
    "resources/integrated-edition-proposal/verify_edition.py"
])
IGNORED_ROOTS = frozenset((".git", ".venv", "tmp", "dist", "build"))
AUTHORITY = {
    "source_admitted": False, "runtime_admitted": False,
    "pages_admitted": False, "publication_authorized": False,
}
NOT_RUN = {
    "full_repository_validation": "NOT_RUN",
    "runtime_validation": "NOT_RUN", "tests": "NOT_RUN", "replay": "NOT_RUN",
    "historical_source_admission": "UNCHANGED_NOT_RUN",
    "historical_manifest": "UNCHANGED_NOT_RUN",
    "clean_worktree_and_archive": "NOT_RUN", "publication": "NOT_AUTHORIZED",
}

# Every reviewed root test file except the existing retained S1 exclusion.
# Only explicit build/replay/commit operations are deselected; unavailable
# historical identity checks remain visible failures, not synthetic passes.
DEVELOPMENT_TESTS = (
    'tests/test_admission.py',
    'tests/test_astra_layers.py',
    'tests/test_astra_reservoir.py',
    'tests/test_atlas_release_preflight.py',
    'tests/test_benchmark.py',
    'tests/test_boundary_state.py',
    'tests/test_candidate.py',
    'tests/test_claim_source_coverage.py',
    'tests/test_coupling_state.py',
    'tests/test_dark_medium_response_atlas_documents.py',
    'tests/test_dark_medium_response_atlas_publication_successor_overlay_s2.py',
    'tests/test_dark_medium_response_atlas_publish_guard.py',
    'tests/test_dark_medium_response_atlas_release.py',
    'tests/test_dark_medium_response_atlas_successor_overlay_historical.py',
    'tests/test_dark_medium_response_benchmark.py',
    'tests/test_data_integrity.py',
    'tests/test_document_contract.py',
    'tests/test_evidence_contracts.py',
    'tests/test_explorer.py',
    'tests/test_explorer_gateway.py',
    'tests/test_integrated_claim_scope.py',
    'tests/test_integrated_documents.py',
    'tests/test_integration.py',
    'tests/test_link_audits.py',
    'tests/test_linux_baseline.py',
    'tests/test_linux_companion.py',
    'tests/test_linux_portability_diagnosis.py',
    'tests/test_linux_replay_freshness.py',
    'tests/test_linux_replay_inputs.py',
    'tests/test_linux_runtime.py',
    'tests/test_local_successor_profile.py',
    'tests/test_numerical_regressions.py',
    'tests/test_optimizer.py',
    'tests/test_pages_admission.py',
    'tests/test_pages_contract.py',
    'tests/test_release_integrity.py',
    'tests/test_research_companion_pages.py',
    'tests/test_resource_contract.py',
    'tests/test_sector_complete_module.py',
    'tests/test_sppt_core.py',
    'tests/test_wki_successor.py',
)
EXCLUDED_TEST_FILES = {
    "tests/test_dark_medium_response_atlas_successor_overlay.py":
        "Retained S1 program; existing conftest collection policy excludes it",
}
WINDOWS_BROWSER_TESTS = (
    'tests/test_pages_contract.py::test_bauhaus_cover_has_measured_label_clearance_at_repository_scale',
    'tests/test_pages_contract.py::test_pages_home_and_working_paper_reflow_at_narrow_widths',
)
DEFERRED_TESTS = {
    'tests/test_dark_medium_response_atlas_publication_successor_overlay_s2.py::test_committed_roster_and_base_ancestry_are_exact': 'creates Git commits',
    'tests/test_dark_medium_response_atlas_publication_successor_overlay_s2.py::test_committed_snapshot_is_immune_to_ambient_worktree_mutation': 'creates Git commits',
    'tests/test_dark_medium_response_benchmark.py::test_retained_evaluation_reproduces_with_frozen_sources': 'runs retained scientific benchmark',
    'tests/test_linux_runtime.py::test_retained_benchmark_linux_bytes_and_historical_scientific_equivalence': 'runs retained scientific benchmark',
    'tests/test_numerical_regressions.py::ScopedClaimControls::test_CORE08_repeatable_explicit_run': 'runs scientific checks twice',
    'tests/test_release_integrity.py::test_dirty_or_unexplained_worktree_blocks_release': 'creates a Git commit',
    'tests/test_release_integrity.py::test_duplicate_tag_headers_cannot_spoof_a_direct_release_target': 'creates Git commits/tags',
    'tests/test_release_integrity.py::test_nested_annotated_tag_is_not_accepted_as_a_direct_release_tag': 'creates Git commits/tags',
    'tests/test_release_integrity.py::test_restore_authoritative_tag_repairs_v103_checkout_peeled_ref': 'creates Git commits/remotes',
    'tests/test_release_integrity.py::test_unannotated_existing_and_wrong_target_tags_are_rejected': 'creates Git commits/tags',
    'tests/test_research_companion_pages.py::test_approved_fixture_assembly_reports_untested_coverage_without_private_evidence': 'assembles actual site from production inputs',
    'tests/test_research_companion_pages.py::test_artifact_fixture_ignores_source_nested_temp_environment': 'assembles actual site from production inputs',
    'tests/test_research_companion_pages.py::test_companion_assembly_preserves_existing_routes_and_exact_payload': 'assembles actual site from production inputs',
    'tests/test_research_companion_pages.py::test_companion_rejects_collisions_before_writing': 'assembles actual site from production inputs',
    'tests/test_research_companion_pages.py::test_companion_rejects_missing_shell_and_destination_link': 'assembles actual site from production inputs',
    'tests/test_research_companion_pages.py::test_companion_reuses_identical_notice_without_overwriting': 'assembles actual site from production inputs',
    'tests/test_research_companion_pages.py::test_current_review_preserves_coverage_and_obeys_publication_decision': 'assembles actual site from production inputs',
}
DEVELOPMENT_GATES = frozenset((
    "windows_reference_runtime", "non_replay_tests", "maintained_python_lint",
    "source_type_checks", "citation", "maintained_repository_links",
    "retained_external_link_record", "retained_pdf_inspection",
))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_digest(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(character in "0123456789abcdef" for character in value))


def relative_name(value: object) -> bool:
    return (type(value) is str and bool(value) and "\\" not in value and ":" not in value
            and not any(ord(character) < 32 for character in value)
            and all(part not in ("", ".", "..") for part in value.split("/"))
            and value.split("/")[0].casefold() not in IGNORED_ROOTS)


def safe_stat(path: Path):
    info = path.lstat()
    require(not stat.S_ISLNK(info.st_mode)
            and not (getattr(info, "st_file_attributes", 0) & 0x400),
            "Links and reparse points are not allowed")
    return info


def safe_parents(path: Path) -> None:
    for parent in reversed(path.parents):
        require(stat.S_ISDIR(safe_stat(parent).st_mode), "Unsafe ancestor directory")


def signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def read_contract(path: Path) -> bytes:
    safe_parents(path)
    before = safe_stat(path)
    require(stat.S_ISREG(before.st_mode) and before.st_size <= 2_000_000,
            "Contract must be a bounded regular file")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        require(signature(before) == signature(opened), "Contract changed during open")
        data = stream.read(2_000_001)
        after = os.fstat(stream.fileno())
    final = safe_stat(path)
    require(len(data) <= 2_000_000 and signature(before) == signature(after) == signature(final)
            and opened.st_ctime_ns == after.st_ctime_ns
            and before.st_ctime_ns == final.st_ctime_ns, "Contract changed during read")
    return data


def strict_json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(value):
        raise RuntimeError("Nonfinite JSON constant: " + value)

    result = json.loads(data.decode("utf-8"), object_pairs_hook=unique, parse_constant=nonfinite)
    require(type(result) is dict, "Expected a contract object")
    return result


def file_map(value: object, count: int | None = None) -> dict:
    require(type(value) is dict and bool(value), "Expected a nonempty file inventory")
    require(count is None or len(value) == count, "Unexpected contract file count")
    require(all(relative_name(name) for name in value), "Unsafe contract path")
    require(len({name.casefold() for name in value}) == len(value), "Case-colliding contract paths")
    for identity in value.values():
        require(type(identity) is dict and set(identity) == {"bytes", "sha256"},
                "Unexpected file identity fields")
        require(type(identity["bytes"]) is int and identity["bytes"] >= 0
                and is_digest(identity["sha256"]), "Invalid file identity")
    return value


def validate_contract(record: dict) -> dict:
    require(type(record.get("schema_version")) is int and record["schema_version"] in (1, 2),
            "Unexpected contract schema")
    require(record.get("kind") == "local_successor_validation_contract"
            and record.get("profile") == "local-successor"
            and record.get("status") == (
                "PREVIEW_NOT_APPLIED_NOT_VALIDATED" if record["schema_version"] == 1
                else "LOCAL_DEVELOPMENT_NOT_RELEASE_ADMISSION"
            ),
            "Unexpected successor contract scope")
    authority = record.get("authority")
    require(type(authority) is dict and set(authority) == set(AUTHORITY)
            and all(value is False for value in authority.values()), "Admission is not granted")
    basis = record.get("basis")
    require(type(basis) is dict
            and basis.get("inventory_sha256") == BASE_INVENTORY_SHA256
            and basis.get("reconciliation_sha256") == RECONCILIATION_SHA256,
            "Unexpected preserved basis")
    if record["schema_version"] == 1:
        base = file_map(record.get("base_files"), 626)
        require(sha256(canonical(base)) == BASE_MAP_SHA256, "Base inventory identity differs")
        files = file_map(record.get("files"), 627)
        require(set(files) == set(base) | ADDED_PATHS, "Successor roster differs from declared delta")
        require(record.get("modified_paths") == sorted(MODIFIED_PATHS)
                and record.get("added_paths") == sorted(ADDED_PATHS), "Unexpected patch delta")
        require({name for name in base if files[name] != base[name]} == MODIFIED_PATHS,
                "Changes extend outside the two reviewed gate owners")
    else:
        base = file_map(record.get("base_files"), 627)
        require(sha256(canonical(base)) == SUCCESSOR_BASE_MAP_SHA256,
                "Preserved 627-file successor identity differs")
        files = file_map(record.get("files"))
        require(base.keys() <= files.keys(), "Preserved payload paths may not be removed")
        modified = sorted(name for name in base if files[name] != base[name])
        added = sorted(files.keys() - base.keys())
        require(record.get("modified_paths") == modified
                and record.get("added_paths") == added, "Declared successor delta differs")
        require(all(name not in LOCAL_ONLY_PATHS and (
            name in {"README.md", "REPRODUCING.md"}
            or name.startswith(("tools/", "tests/"))
        ) for name in modified + added), "Change outside the local validation repair scope")
    require(record.get("local_only_paths") == sorted(LOCAL_ONLY_PATHS)
            and LOCAL_ONLY_PATHS <= files.keys(), "Local-only partition differs")
    require(type(record.get("payload_bytes")) is int
            and record["payload_bytes"] == sum(item["bytes"] for item in files.values()),
            "Payload byte total differs")
    return files


def observe_payload(root: Path, expected: dict) -> list[Path]:
    safe_parents(root)
    require(stat.S_ISDIR(safe_stat(root).st_mode), "Invalid successor directory")
    observed = set()
    for directory, directories, names in os.walk(root, followlinks=False):
        current = Path(directory)
        for name in tuple(directories):
            child = current / name
            safe_stat(child)
            if current == root and name in IGNORED_ROOTS:
                directories.remove(name)
        for name in names:
            path = current / name
            info = safe_stat(path)
            if current == root and name in IGNORED_ROOTS:
                continue
            require(stat.S_ISREG(info.st_mode), "Nonregular successor payload")
            observed.add(path.relative_to(root).as_posix())
    require(observed == expected.keys(), "Missing or unexpected successor files")
    paths = []
    for name, identity in sorted(expected.items()):
        path = root / name
        before = safe_stat(path)
        require(before.st_size == identity["bytes"], "Successor file size differs: " + name)
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            require(signature(before) == signature(opened), "Payload changed during open")
            remaining = identity["bytes"] + 1
            while remaining:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                digest.update(chunk)
            require(identity["bytes"] + 1 - remaining == identity["bytes"],
                    "Payload length changed during read")
            after = os.fstat(stream.fileno())
        final = safe_stat(path)
        require(signature(before) == signature(after) == signature(final)
                and opened.st_ctime_ns == after.st_ctime_ns
                and before.st_ctime_ns == final.st_ctime_ns,
                "Payload changed during read")
        require(digest.hexdigest() == identity["sha256"], "Successor bytes differ: " + name)
        paths.append(path)
    return paths


def public_check_projection(root: Path, paths: list[Path], checker) -> list[Path]:
    """Use existing public path rules for this exact projection; grant no public admission."""
    selected = []
    for path in paths:
        relative = path.relative_to(root)
        name = relative.as_posix()
        if name in LOCAL_ONLY_PATHS:
            continue
        if len(relative.parts) == 1:
            require(name in checker.ROOT_ALLOWLIST, "Unregistered root path in projection")
        else:
            parent = relative.parent.as_posix()
            matched = next((item for item in checker.DIRECTORY_RULES
                            if parent == item or parent.startswith(item + "/")), None)
            require(matched is not None, "Unregistered directory in projection")
            require(matched != "resources" or name in checker.RESOURCE_PATH_ALLOWLIST,
                    "Unregistered supplemental resource in projection")
            allowed = path.suffix.lower() in checker.DIRECTORY_RULES[matched]
            if matched == "resources" and name in checker.RESOURCE_EXACT_SUFFIX_ALLOWLIST:
                allowed = True
            require(allowed, "Unregistered suffix in projection")
        selected.append(path)
    return selected


def pytest_command(python: list[str], work: Path, *, native_host: bool = False,
                   browser_only: bool = False) -> list[str]:
    targets = WINDOWS_BROWSER_TESTS if browser_only else DEVELOPMENT_TESTS
    deferred = [] if browser_only else list(DEFERRED_TESTS)
    if native_host:
        deferred.extend(WINDOWS_BROWSER_TESTS)
    return [*python, "-m", "pytest", "-q", "-ra", "-o", "addopts=",
            "--strict-config", "--strict-markers", "-p", "no:cacheprovider",
            "--basetemp", str(work / "pytest"), "--junitxml", str(work / "test-results.xml"),
            *targets, *["--deselect=" + name for name in deferred]]


def validate_test_roster(root: Path) -> None:
    observed = {path.relative_to(root).as_posix() for path in (root / "tests").glob("test_*.py")}
    require(observed == set(DEVELOPMENT_TESTS) | set(EXCLUDED_TEST_FILES),
            "Root test-file roster differs from the reviewed local scope")


def run_test_command(command: list[str], root: Path, environment: dict, work: Path) -> dict:
    completed = subprocess.run(command, cwd=root, env=environment, text=True,
                               encoding="utf-8", errors="replace", capture_output=True, check=False)
    result = {"status": "FAIL", "returncode": completed.returncode or 1,
              "pytest_returncode": completed.returncode, "command": command,
              "stdout": completed.stdout, "stderr": completed.stderr}
    try:
        report = work / "test-results.xml"
        require(stat.S_ISREG(safe_stat(report).st_mode), "Missing regular test result report")
        suites = ET.parse(report).getroot().findall("testsuite")
        counts = {key: sum(int(suite.attrib[key]) for suite in suites)
                  for key in ("tests", "failures", "errors", "skipped")}
        result["junit_counts"] = counts
        if completed.returncode == 0 and counts["tests"] > 0 and all(
            counts[key] == 0 for key in ("failures", "errors", "skipped")
        ):
            result.update(status="PASS", returncode=0)
    except (OSError, RuntimeError, ET.ParseError, KeyError, ValueError) as error:
        result["result_error"] = str(error)
    return result


def run_host_tests(root: Path, files: dict, work_directory: str) -> dict:
    """Execute the identical test selection on a native Linux fixture filesystem."""
    require(sys.flags.isolated and sys.dont_write_bytecode, "Host tests require -I -B")
    require(platform.system() == "Linux" and platform.python_version() == "3.12.10"
            and platform.python_implementation() == "CPython",
            "Host tests require Linux CPython 3.12.10")
    observe_payload(root, files)
    work = Path(work_directory)
    require(work.is_absolute() and ".." not in work.parts, "Unsafe host scratch path")
    safe_parents(work)
    work = work.resolve(strict=False)
    root = root.resolve(strict=True)
    require(not work.is_relative_to(root)
            and not root.is_relative_to(work) and not work.is_relative_to("/mnt"),
            "Host scratch must be separate and on the native Linux filesystem")
    work.mkdir()
    (work / "temporary").mkdir()
    import playwright

    from tools import verify

    node_directory = Path(playwright.__file__).parent / "driver"
    require((node_directory / "node").is_file(), "Native Node test runtime is missing")
    environment = {name: value for name, value in os.environ.items()
                   if not verify.is_inherited_controller_variable(name)}
    kernel = json.loads((root / "RUNTIME-linux.json").read_text(encoding="utf-8"))["numeric_kernel"]
    environment.update({
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1",
        "TEMP": str(work / "temporary"), "TMP": str(work / "temporary"),
        "TMPDIR": str(work / "temporary"), "MPLCONFIGDIR": str(work / "matplotlib"),
        "MPLBACKEND": "Agg", "TZ": "UTC", "OPENBLAS_CORETYPE": str(kernel["core_type"]),
        "OPENBLAS_NUM_THREADS": str(kernel["threads"]), "OMP_NUM_THREADS": str(kernel["threads"]),
        "MKL_NUM_THREADS": str(kernel["threads"]), "NUMEXPR_NUM_THREADS": str(kernel["threads"]),
        "NPY_DISABLE_CPU_FEATURES": ",".join(kernel["numpy_disabled_cpu_features"]),
        "PATH": os.pathsep.join((str(Path(sys.executable).parent), str(node_directory),
                                 environment.get("PATH", ""))),
        "GIT_CEILING_DIRECTORIES": str(root.parent), "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_NO_REPLACE_OBJECTS": "1",
    })
    verify.verify_installed_distributions()
    # Probe a real native symlink before claiming the formerly blocked controls can run.
    victim = work / "fixture-target"
    victim.write_bytes(b"fixture")
    link = work / "fixture-link"
    link.symlink_to(victim)
    require(link.is_symlink() and link.read_bytes() == b"fixture", "Native symlink probe failed")
    command = pytest_command([sys.executable, "-I", "-B", "-X", "utf8"], work, native_host=True)
    try:
        result = run_test_command(command, root, environment, work)
    finally:
        observe_payload(root, files)
    return {
        **result, "python": platform.python_version(), "platform": platform.platform(),
        "source_map_sha256": sha256(canonical(files)), "source_unchanged": True,
        "native_symlink_probe": "PASS", "locked_dependency_versions": "PASS",
        "scope": "Functional test host; not canonical Debian runtime or replay admission",
        "test_targets": list(DEVELOPMENT_TESTS), "deferred_tests": dict(DEFERRED_TESTS),
        "windows_browser_tests": list(WINDOWS_BROWSER_TESTS),
    }


def run_wsl_tests(root: Path, files: dict, host: dict) -> dict:
    """Use an explicit provisioned interpreter; transport arguments without a shell."""
    require(set(host) == {"distribution", "python", "work_directory"}
            and all(type(value) is str and value for value in host.values()), "Invalid WSL test host")
    require(host["python"].startswith("/") and host["work_directory"].startswith("/"),
            "WSL interpreter and scratch paths must be absolute")
    prefix = ["wsl.exe", "--distribution", host["distribution"], "--"]
    mapped = subprocess.run([*prefix, "wslpath", "-a", "-u", str(root)], check=True,
                            capture_output=True, text=True, encoding="utf-8")
    source = mapped.stdout.strip()
    require(source.startswith("/") and "\n" not in source, "Invalid WSL source mapping")
    # Verify the host helper before import, then have it verify all payload bytes
    # before and after pytest. A wrong mount/copy is never accepted as this source.
    bootstrap = """import hashlib,json,sys
from pathlib import Path
request=json.load(sys.stdin)
root=Path(request['root'])
helper=root/'tools/local_successor_profile.py'
if hashlib.sha256(helper.read_bytes()).hexdigest()!=request['files']['tools/local_successor_profile.py']['sha256']:
    raise RuntimeError('Test-host helper identity differs')
sys.path.insert(0,str(root))
from tools.local_successor_profile import run_host_tests
result=run_host_tests(root,request['files'],request['work_directory'])
print(json.dumps(result))
raise SystemExit(result['returncode'])
"""
    command = [*prefix, host["python"], "-I", "-B", "-X", "utf8", "-c", bootstrap]
    completed = subprocess.run(command, input=json.dumps({"root": source, "files": files,
                               "work_directory": host["work_directory"]}), capture_output=True,
                               text=True, encoding="utf-8", errors="replace", check=False)
    result = {"status": "FAIL", "returncode": completed.returncode, "command": command,
              "stdout": completed.stdout, "stderr": completed.stderr, "test_host": dict(host)}
    if completed.returncode == 0 or completed.stdout:
        try:
            observation = strict_json(completed.stdout.encode("utf-8"))
        except (ValueError, RuntimeError):
            return result
        result["host_observation"] = observation
        counts = observation.get("junit_counts", {})
        if (completed.returncode == 0 and type(observation.get("returncode")) is int
                and observation["returncode"] == 0 and observation.get("source_unchanged") is True
                and observation.get("source_map_sha256") == sha256(canonical(files))
                and observation.get("native_symlink_probe") == "PASS"
                and observation.get("locked_dependency_versions") == "PASS"
                and observation.get("python") == "3.12.10"
                and type(counts) is dict
                and set(counts) == {"tests", "failures", "errors", "skipped"}
                and all(type(value) is int for value in counts.values()) and counts["tests"] > 0
                and all(counts[key] == 0 for key in ("failures", "errors", "skipped"))
                and observation.get("test_targets") == list(DEVELOPMENT_TESTS)
                and observation.get("deferred_tests") == dict(DEFERRED_TESTS)
                and observation.get("windows_browser_tests") == list(WINDOWS_BROWSER_TESTS)):
            result["status"] = "PASS"
    return result


def run_development(root: Path, selected: list[Path], work_directory: str, *,
                    files: dict | None = None, test_host: dict | None = None) -> dict:
    """Run existing non-replay checks with scratch files outside the inventoried tree."""
    work = Path(os.path.abspath(work_directory))
    safe_parents(work)
    require(not work.is_relative_to(root) and not root.is_relative_to(work),
            "Scratch directory must be separate from the source tree")
    work.mkdir()  # Refuse to overwrite or reuse an earlier trial.
    temporary = work / "temporary"
    temporary.mkdir()
    from tools.verify import is_inherited_controller_variable

    runtime = json.loads((root / "RUNTIME.json").read_text(encoding="utf-8"))
    kernel = runtime["numeric_kernel"]
    environment = {name: value for name, value in os.environ.items()
                   if not is_inherited_controller_variable(name)}
    environment.update({
        "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "TEMP": str(temporary), "TMP": str(temporary), "TMPDIR": str(temporary),
        "MPLCONFIGDIR": str(work / "matplotlib"), "MPLBACKEND": "Agg",
        "GIT_CEILING_DIRECTORIES": str(root.parent),
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_NO_REPLACE_OBJECTS": "1", "TZ": "UTC",
        "OPENBLAS_CORETYPE": str(kernel["core_type"]),
        "OPENBLAS_NUM_THREADS": str(kernel["threads"]),
        "OMP_NUM_THREADS": str(kernel["threads"]), "MKL_NUM_THREADS": str(kernel["threads"]),
        "NUMEXPR_NUM_THREADS": str(kernel["threads"]),
        "NPY_DISABLE_CPU_FEATURES": ",".join(kernel["numpy_disabled_cpu_features"]),
    })
    python = [sys.executable, "-I", "-B", "-X", "utf8"]
    bootstrap = "import sys,os;sys.path.insert(0,os.getcwd());"
    sources = [path.relative_to(root).as_posix() for path in selected]
    link_code = (
        "from pathlib import Path;from tools.check_repository_links import check_repository_links;"
        "print(check_repository_links(sources=[Path(p).absolute() for p in "
        f"{[name for name in sources if name.endswith('.md')]!r}]))"
    )
    commands = {
        "windows_reference_runtime": [*python, "-c", bootstrap
                                      + "from tools.verify import verify_runtime;"
                                      + "verify_runtime(dict(os.environ))"],
        "non_replay_tests": pytest_command(python, work),
        "maintained_python_lint": [*python, "-m", "ruff", "check", "--no-cache",
                                   *[name for name in sources if name.endswith(".py")]],
        "source_type_checks": [*python, "-m", "mypy", "--cache-dir", str(work / "mypy"), "src"],
        "citation": [*python, "-c", "from cffconvert.cli.cli import cli;cli()", "--validate"],
        "maintained_repository_links": [*python, "-c", bootstrap + link_code],
        "retained_external_link_record": [*python, "tools/check_external_links.py"],
        "retained_pdf_inspection": [*python, "tools/inspect_pdf.py"],
    }
    require(set(commands) == DEVELOPMENT_GATES, "Development gate roster differs")
    results = {}
    for name, command in commands.items():
        if name == "non_replay_tests":
            if test_host is None:
                results[name] = run_test_command(command, root, environment, work)
            else:
                require(files is not None, "Cross-host tests require the full pinned payload inventory")
                linux = run_wsl_tests(root, files, test_host)
                browser = run_test_command(pytest_command(python, work, browser_only=True),
                                           root, environment, work)
                results[name] = {
                    "status": "PASS" if linux["status"] == browser["status"] == "PASS" else "FAIL",
                    "linux": linux, "windows_browser": browser,
                }
            continue
        completed = subprocess.run(command, cwd=root, env=environment,
                                   text=True, encoding="utf-8", errors="replace", capture_output=True,
                                   check=False)
        results[name] = {"status": "PASS" if completed.returncode == 0 else "FAIL",
                         "returncode": completed.returncode, "command": command,
                         "stdout": completed.stdout, "stderr": completed.stderr}
    return results


def run(root: Path, contract_path: str, expected_contract_sha256: str, *,
        development: bool = False, work_directory: str | None = None,
        test_host: dict | None = None) -> dict:
    require(os.environ.get("GITHUB_ACTIONS", "").lower() != "true"
            and not os.environ.get("GITHUB_REF", "").startswith("refs/tags/"),
            "The local profile is unavailable in hosted or tag contexts")
    require(is_digest(expected_contract_sha256), "An externally reviewed contract digest is required")
    root = Path(os.path.abspath(root))
    path = Path(os.path.abspath(contract_path))
    safe_parents(root)
    require(stat.S_ISDIR(safe_stat(root).st_mode), "Invalid successor root")
    require(not path.is_relative_to(root), "The contract must remain outside the successor")
    data = read_contract(path)
    require(not path.resolve(strict=True).is_relative_to(root.resolve(strict=True)),
            "The contract aliases a path inside the successor")
    require(sha256(data) == expected_contract_sha256, "External contract digest differs")
    record = strict_json(data)
    files = validate_contract(record)
    require(not development or record["schema_version"] == 2,
            "Development checks require the successor integration contract")
    require(development == (work_directory is not None),
            "Development checks require a fresh external work directory")
    require(test_host is None or development, "An alternate test host requires development checks")
    payload = observe_payload(root, files)
    if development:
        validate_test_roster(root)
    # Import candidate checks only after the externally pinned full inventory passes.
    from tools import check_repository

    require(check_repository.ROOT.resolve(strict=True) == root.resolve(strict=True),
            "Repository checker belongs to a different tree")
    try:
        check_repository.check_cache_boundaries()
        check_repository.check_private_operator_policy_boundary()
        selected = public_check_projection(root, payload, check_repository)
        check_repository.check_repository_contents(selected, payload_paths=payload)
        gates = run_development(root, selected, work_directory, files=files,
                                test_host=test_host) if development else {}
    finally:
        observe_payload(root, files)
        require(read_contract(path) == data, "External contract changed during checks")
    require(not development or set(gates) == DEVELOPMENT_GATES, "Incomplete development results")
    passed = all(gate["status"] == "PASS" for gate in gates.values())
    return {
        "status": ("PASS_LOCAL_DEVELOPMENT_CHECKS_NOT_FULL_VALIDATION" if passed
                   else "FAIL_LOCAL_DEVELOPMENT_CHECKS") if development else
                  "PASS_LOCAL_SUCCESSOR_REPOSITORY_CHECKS_NOT_FULL_VALIDATION",
        "profile": "local-successor",
        "contract_sha256": expected_contract_sha256,
        "files": len(payload), "public_check_projection_files": len(selected),
        "local_only_files": len(LOCAL_ONLY_PATHS),
        "repository_content_checks": "PASS",
        "development_gates": gates,
        "selected_test_targets": list(DEVELOPMENT_TESTS) if development else [],
        "deferred_tests": dict(DEFERRED_TESTS) if development else {},
        "excluded_test_files": dict(EXCLUDED_TEST_FILES) if development else {},
        "windows_browser_tests": list(WINDOWS_BROWSER_TESTS) if development and test_host else [],
        "historical_source_mismatches": "RETAINED",
        "source_contract": "EXPLICIT_SUCCESSOR_IDENTITY_FOR_CHECKING_ONLY",
        "authority": dict(AUTHORITY), "remaining_gates": {
            **dict(NOT_RUN),
            **({"runtime_validation": "SEE_WINDOWS_REFERENCE_RUNTIME_GATE_CANONICAL_LINUX_NOT_RUN",
                "tests": "ALL_REVIEWED_ROOT_TEST_FILES_WITH_EXPLICIT_OPERATION_EXCLUSIONS",
                "clean_worktree_and_archive": "BLOCKED_NO_SUCCESSOR_COMMIT",
                "replay": "NOT_AUTHORIZED", "builds": "NOT_AUTHORIZED"} if development else {}),
        },
        "quality_scope": "Non-retained projection; unchanged 88 local-only files remain archival inputs",
        "local_only_semantics": "IDENTITY_AND_PHYSICAL_SAFETY_PLUS_GENERIC_PNG_CHECKS_ONLY",
        "consistency_scope": "Start/end observations; no exclusive lock or atomic snapshot",
    }
